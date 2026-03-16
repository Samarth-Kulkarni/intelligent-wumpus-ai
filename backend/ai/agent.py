from .logic_engine import LogicEngine
from .probability_engine import ProbabilisticEngine
from collections import deque


class IntelligentAgent:
    def __init__(self, size=8):
        self.size = size
        self.logic = LogicEngine(size)
        self.prob_engine = ProbabilisticEngine(size)
        self.visited = set()
        self.current_pos = (0, 0)
        self.percept_history = {}
        self.has_gold = False
        self.has_arrow = True
        self.wumpus_alive = True
        self.stench_cells = set()
        self.wall_edges = set()
        self.known_safe = set()
        # Committed navigation plan to avoid spinning
        self._plan = []          # list of cells to follow
        self._plan_target = None # what we're navigating towards

    # ── helpers ──────────────────────────────────────────────────────────

    def _wk(self, c1, c2):
        return (min(c1, c2), max(c1, c2))

    def _reachable(self, pos):
        """Neighbours of pos reachable through the maze (no wall between)."""
        x, y = pos
        out = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if self._wk((x, y), (nx, ny)) not in self.wall_edges:
                    out.append((nx, ny))
        return out

    # ── knowledge ────────────────────────────────────────────────────────

    def update_knowledge(self, x, y, percepts, wall_edges=None):
        self.current_pos = (x, y)
        self.visited.add((x, y))
        self.known_safe.add((x, y))
        self.percept_history[(x, y)] = percepts

        if wall_edges is not None:
            self.wall_edges = set()
            for c1, c2 in wall_edges:
                self.wall_edges.add(self._wk(tuple(c1), tuple(c2)))

        breeze = percepts.get('breeze', False)
        stench = percepts.get('stench', False)
        scream = percepts.get('scream', False)
        self.logic.add_percept(x, y, breeze, stench)

        if stench:
            self.stench_cells.add((x, y))
        if scream:
            self.wumpus_alive = False

        # Deduction: no breeze AND no stench => all reachable neighbours safe
        if not breeze and (not stench or not self.wumpus_alive):
            for n in self._reachable((x, y)):
                self.known_safe.add(n)

        # Invalidate plan if we moved and the plan is stale
        if self._plan and self._plan[0] == (x, y):
            self._plan.pop(0)
        elif self._plan and self._plan[0] != (x, y):
            # We didn't reach the expected next step (bump?), clear plan
            nbrs = self._reachable((x, y))
            if self._plan[0] not in [(n[0], n[1]) for n in nbrs]:
                self._plan = []

    # ── decision ─────────────────────────────────────────────────────────

    def get_recommendation(self, current_orientation):
        info = []
        pos = self.current_pos
        percept = self.percept_history.get(pos, {})

        # 0. Grab gold
        if not self.has_gold and percept.get('glitter'):
            self._plan = []
            info.append("Glitter detected! Grabbing gold.")
            return self._result(info, "GRAB")

        # 0b. Shoot Wumpus if we smell stench and have arrow
        if self.has_arrow and self.wumpus_alive and percept.get('stench'):
            self._plan = []
            info.append("Stench detected! Shooting arrow at the Wumpus!")
            return self._result(info, "SHOOT")

        # 1. Homing with gold
        exit_pos = (self.size - 1, self.size - 1)
        if self.has_gold:
            if pos == exit_pos:
                info.append("At EXIT with gold. Climbing out!")
                return self._result(info, "CLIMB")
            info.append("Have gold! Navigating to EXIT.")
            return self._follow_plan_or_make(exit_pos, current_orientation, info, allow_unvisited=True)

        # 2. If we have a committed plan, follow it
        if self._plan:
            next_cell = self._plan[0]
            # Verify next_cell is still reachable from current pos
            if next_cell in self._reachable(pos):
                info.append(f"Following plan towards {self._plan_target}, next: {next_cell}")
                action = self._face_and_go(next_cell, current_orientation, info)
                return self._result(info, action)
            else:
                self._plan = []  # plan invalid

        # 3. Safe unvisited neighbour from current cell
        nbrs = self._reachable(pos)
        safe_new = [n for n in nbrs if n in self.known_safe and n not in self.visited]
        if safe_new:
            target = safe_new[0]
            info.append(f"Logic: {target} proven SAFE.")
            action = self._face_and_go(target, current_orientation, info)
            return self._result(info, action)

        # 4. BFS to nearest unvisited safe cell through visited cells
        target = self._bfs_to_unvisited_safe()
        if target:
            info.append(f"Backtracking towards safe cell {target}.")
            return self._follow_plan_or_make(target, current_orientation, info, allow_unvisited=False)

        # 5. Probabilistic risk – pick lowest-risk frontier cell
        frontier = self._frontier()
        if frontier:
            info.append("No safe cells left. Probabilistic reasoning...")
            breezes = {p: pc.get('breeze') for p, pc in self.percept_history.items()}
            self.prob_engine.update_observations(self.visited, breezes, set())
            risks = self.prob_engine.get_pit_probabilities(list(frontier), self.wall_edges)
            if risks:
                best = min(risks, key=lambda k: risks[k])
                info.append(f"Prob: {best} risk {risks[best]:.0%}")
                return self._follow_plan_or_make(best, current_orientation, info, allow_unvisited=True)

        # 6. Truly stuck — just move forward if possible
        for n in self._reachable(pos):
            info.append(f"Fallback: moving to {n}.")
            action = self._face_and_go(n, current_orientation, info)
            return self._result(info, action)

        info.append("Completely stuck.")
        return self._result(info, "FORWARD")

    # ── navigation helpers ───────────────────────────────────────────────

    def _result(self, info, action):
        info.append(f"→ {action}")
        return {"thoughts": info, "best_action": action, "kb_count": len(self.known_safe)}

    def _face_and_go(self, target, orientation, info):
        """Return the action to face target and move forward."""
        x, y = self.current_pos
        tx, ty = target
        dx, dy = tx - x, ty - y
        desired = "RIGHT"
        if dx == 1:  desired = "RIGHT"
        elif dx == -1: desired = "LEFT"
        elif dy == 1:  desired = "UP"
        elif dy == -1: desired = "DOWN"

        dirs = ["UP", "RIGHT", "DOWN", "LEFT"]
        ci = dirs.index(orientation)
        di = dirs.index(desired)
        if ci == di:
            return "FORWARD"
        # Turn via shortest path
        diff = (di - ci) % 4
        if diff == 1:
            return "TURNRIGHT"
        elif diff == 3:
            return "TURNLEFT"
        else:
            # 180° — just pick one direction consistently
            return "TURNLEFT"

    def _follow_plan_or_make(self, goal, orientation, info, allow_unvisited=False):
        """Create a BFS plan to goal and follow it."""
        # If we already have a plan for this goal, follow it
        if self._plan and self._plan_target == goal:
            next_cell = self._plan[0]
            if next_cell in self._reachable(self.current_pos):
                info.append(f"Plan: next step {next_cell}")
                action = self._face_and_go(next_cell, orientation, info)
                return self._result(info, action)

        # Make a new plan via BFS
        path = self._bfs_path(self.current_pos, goal, allow_unvisited)
        if path:
            self._plan = path[1:]  # exclude current position
            self._plan_target = goal
            if self._plan:
                next_cell = self._plan[0]
                info.append(f"Path home: Found route of length {len(self._plan)}")
                action = self._face_and_go(next_cell, orientation, info)
                return self._result(info, action)

        # No path found — try direct neighbor
        info.append(f"No path to {goal}. Moving to nearest reachable.")
        nbrs = self._reachable(self.current_pos)
        unvisited = [n for n in nbrs if n not in self.visited]
        if unvisited:
            action = self._face_and_go(unvisited[0], orientation, info)
            return self._result(info, action)
        if nbrs:
            action = self._face_and_go(nbrs[0], orientation, info)
            return self._result(info, action)
        return self._result(info, "FORWARD")

    def _bfs_path(self, start, goal, allow_unvisited=False):
        """BFS to find path from start to goal."""
        queue = deque([(start, [start])])
        seen = {start}
        while queue:
            curr, path = queue.popleft()
            if curr == goal:
                return path
            for n in self._reachable(curr):
                if n not in seen:
                    if allow_unvisited or n in self.visited or n == goal:
                        seen.add(n)
                        queue.append((n, path + [n]))
        return None

    def _bfs_to_unvisited_safe(self):
        """Find nearest unvisited safe cell reachable through visited cells."""
        queue = deque([(self.current_pos, [])])
        seen = {self.current_pos}
        while queue:
            curr, path = queue.popleft()
            for n in self._reachable(curr):
                if n not in seen:
                    seen.add(n)
                    if n in self.known_safe and n not in self.visited:
                        return n
                    if n in self.visited:
                        queue.append((n, path + [n]))
        return None

    def _frontier(self):
        """All unvisited cells reachable from any visited cell."""
        out = set()
        for v in self.visited:
            for n in self._reachable(v):
                if n not in self.visited:
                    out.add(n)
        return out
