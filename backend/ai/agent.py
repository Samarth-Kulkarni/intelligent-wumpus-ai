from .logic_engine import LogicEngine
from .probability_engine import ProbabilisticEngine
from collections import deque
import heapq


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
        self.known_pits = set()
        # Committed navigation plan to avoid spinning
        self._plan = []          # list of cells to follow
        self._plan_target = None # what we're navigating towards
        
        self.pathfinding_algo = 'BFS'
        self.last_nodes_expanded = 0

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
        
        dx, dy = 0, 0
        if current_orientation == "RIGHT": dx = 1
        elif current_orientation == "UP": dy = 1
        elif current_orientation == "LEFT": dx = -1
        elif current_orientation == "DOWN": dy = -1
        facing_cell = (pos[0]+dx, pos[1]+dy)

        # ---- LIVE MATH FOR UI ----
        breezes = {p: pc.get('breeze') for p, pc in self.percept_history.items()}
        self.prob_engine.update_observations(self.visited, breezes, set())
        frontier = self._frontier()
        self.last_probabilities = self.prob_engine.get_pit_probabilities(list(frontier), self.wall_edges) if frontier else {}

        # ---- DYNAMIC SAFETY DEDUCTION ----
        breeze = percept.get('breeze')
        bint = percept.get('breeze_intensity')
        stench = percept.get('stench')
        stint = percept.get('stench_intensity')
        glitter = percept.get('glitter')
        glint = percept.get('glitter_intensity')

        if facing_cell in self._reachable(pos):
            facing_is_safe = True
            if breeze and bint == 'high': 
                facing_is_safe = False
                self.known_pits.add(facing_cell)
            if self.wumpus_alive and stench and stint == 'high': facing_is_safe = False
            
            if facing_is_safe:
                self.known_safe.add(facing_cell)

        # ---- 0. WUMPUS COMBAT ----
        if self.wumpus_alive and stench:
            if stint == 'high' and self.has_arrow:
                self._plan = []
                info.append("Stench (Strong) ahead! SHOOTING Wumpus.")
                return self._result(info, "SHOOT")
            elif stint == 'low' and self.has_arrow:
                self._plan = []
                info.append("Stench (Faint). Turning to locate Wumpus.")
                return self._result(info, "TURNRIGHT")

        # ---- 1. GRAB GOLD ----
        if not self.has_gold and glitter:
            if glint == 'max':
                self._plan = []
                info.append("Glitter (Max)! Grabbing gold.")
                return self._result(info, "GRAB")
            elif glint == 'high':
                if facing_cell in self.known_safe:
                    self._plan = []
                    info.append("Glitter (Strong) ahead! Moving forward.")
                    return self._result(info, "FORWARD")
                else:
                    info.append("Glitter (Strong) ahead, but it's a PIT! Cannot proceed.")
            elif glint == 'low':
                self._plan = []
                info.append("Glitter (Faint). Turning to find gold.")
                return self._result(info, "TURNRIGHT")

        # ---- 2. BREEZE LOW (SAFE PATH) OVERRIDE ----
        if breeze and bint == 'low' and facing_cell in self.known_safe and facing_cell not in self.visited:
            self._plan = []
            info.append("Breeze (Faint). Path ahead is clear! Continuing forward.")
            return self._result(info, "FORWARD")

        # ---- 3. HOMING (EXIT) ----
        exit_pos = (self.size - 1, self.size - 1)
        if self.has_gold:
            if pos == exit_pos:
                info.append("At EXIT with gold. Climbing out!")
                return self._result(info, "CLIMB")
            
            # Only home if a safe path actually exists; otherwise resume exploring!
            if self._find_path(pos, exit_pos):
                info.append("Navigating to EXIT.")
                return self._follow_plan_or_make(exit_pos, current_orientation, info)
            else:
                info.append("Exit not yet reachable. Resuming exploration.")

        # ---- 4. COMMITTED PLAN ----
        if self._plan:
            next_cell = self._plan[0]
            danger = False
            if breeze and bint == 'high' and next_cell == facing_cell: danger = True
            if self.wumpus_alive and stench and stint == 'high' and next_cell == facing_cell: danger = True

            if next_cell in self._reachable(pos) and not danger:
                info.append(f"Following plan towards {self._plan_target}, next: {next_cell}")
                action = self._face_and_go(next_cell, current_orientation, info)
                return self._result(info, action)
            else:
                self._plan = []  # plan invalid

        # ---- 5. UNVISITED SAFE NEIGHBOR ----
        nbrs = self._reachable(pos)
        safe_new = [n for n in nbrs if n in self.known_safe and n not in self.visited]
        if safe_new:
            target = safe_new[0]
            info.append(f"Logic: {target} proven SAFE.")
            info.append(self.logic.get_resolution_proof(target[0], target[1]))
            action = self._face_and_go(target, current_orientation, info)
            return self._result(info, action)

        # ---- 6. BFS TO UNVISITED SAFE CELL ----
        target = self._bfs_to_unvisited_safe()
        if target:
            info.append(f"Backtracking towards safe cell {target}.")
            return self._follow_plan_or_make(target, current_orientation, info)

        # ---- 7. GIVE UP IF NO SAFE PATHS ----
        safe_path_to_exit = self._find_path_safe(pos, exit_pos)
        if safe_path_to_exit:
            if pos == exit_pos:
                info.append("No safe paths left. Giving up and Climbing out to survive!")
                return self._result(info, "CLIMB")
            else:
                info.append("No safe exploration paths left. Giving up and navigating to EXIT.")
                self._plan = safe_path_to_exit[1:]
                self._plan_target = exit_pos
                next_cell = self._plan[0]
                action = self._face_and_go(next_cell, current_orientation, info)
                return self._result(info, action)

        # ---- 8. PROBABILISTIC GAMBLE ----
        if frontier:
            info.append("No safe cells left. Probabilistic reasoning...")
            risks = self.last_probabilities
            if risks:
                if breeze and bint == 'high' and facing_cell in risks:
                    risks[facing_cell] = 1.0
                best = min(risks, key=lambda k: risks[k])
                info.append(f"Prob: {best} risk {risks[best]:.0%}")
                return self._follow_plan_or_make(best, current_orientation, info)

        # ---- 9. COMPLETELY STUCK OR FULLY EXPLORED ----
        if not frontier:
            exit_pos = (self.size - 1, self.size - 1)
            if pos == exit_pos:
                info.append("Fully explored reachable maze. Gold is inaccessible. Giving up.")
                return self._result(info, "CLIMB")
            else:
                info.append("Fully explored. Navigating to EXIT to give up.")
                return self._follow_plan_or_make(exit_pos, current_orientation, info)

        for n in self._reachable(pos):
            if breeze and bint == 'high' and n == facing_cell: continue
            if self.wumpus_alive and stench and stint == 'high' and n == facing_cell: continue
            info.append(f"Fallback: moving to {n}.")
            action = self._face_and_go(n, current_orientation, info)
            return self._result(info, action)

        info.append("Completely stuck. Waiting for death.")
        return self._result(info, "FORWARD")

    # ── navigation helpers ───────────────────────────────────────────────

    def _result(self, info, action):
        info.append(f"→ {action}")
        return {
            "thoughts": info, 
            "best_action": action, 
            "kb_count": len(self.logic.get_kb_facts()),
            "kb_facts": self.logic.get_kb_facts(),
            "probabilities": {f"{x},{y}": prob for (x, y), prob in getattr(self, 'last_probabilities', {}).items()},
            "nodes_expanded": getattr(self, 'last_nodes_expanded', 0),
            "pathfinding_algo": self.pathfinding_algo
        }

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

    def _follow_plan_or_make(self, goal, orientation, info):
        """Create a BFS plan to goal and follow it."""
        # If we already have a plan for this goal, follow it
        if self._plan and self._plan_target == goal:
            next_cell = self._plan[0]
            if next_cell in self._reachable(self.current_pos):
                info.append(f"Plan: next step {next_cell}")
                action = self._face_and_go(next_cell, orientation, info)
                return self._result(info, action)

        # Make a new plan via BFS or A*
        path = self._find_path(self.current_pos, goal)
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

    def _find_path(self, start, goal):
        """Dispatch to BFS or A* based on configuration."""
        if self.pathfinding_algo == 'ASTAR':
            return self._astar_path(start, goal)
        return self._bfs_path(start, goal)

    def _find_path_safe(self, start, goal):
        """Dispatch to BFS or A* using ONLY known_safe cells."""
        if self.pathfinding_algo == 'ASTAR':
            return self._astar_path_safe(start, goal)
        return self._bfs_path_safe(start, goal)

    def _bfs_path(self, start, goal):
        """BFS to find path from start to goal."""
        self.last_nodes_expanded = 0
        queue = deque([(start, [start])])
        seen = {start}
        while queue:
            self.last_nodes_expanded += 1
            curr, path = queue.popleft()
            if curr == goal:
                return path
            for n in self._reachable(curr):
                if n not in seen:
                    if n in self.visited or n in self.known_safe or n == goal:
                        seen.add(n)
                        queue.append((n, path + [n]))
        return None

    def _bfs_path_safe(self, start, goal):
        """BFS to find path from start to goal using ONLY known_safe cells."""
        self.last_nodes_expanded = 0
        queue = deque([(start, [start])])
        seen = {start}
        while queue:
            self.last_nodes_expanded += 1
            curr, path = queue.popleft()
            if curr == goal:
                return path
            for n in self._reachable(curr):
                if n not in seen and n in self.known_safe:
                    seen.add(n)
                    queue.append((n, path + [n]))
        return None

    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _astar_path(self, start, goal):
        """A* Search to find path from start to goal."""
        self.last_nodes_expanded = 0
        # Priority queue stores tuples of (f_score, g_score, (x, y), path)
        queue = [(self._heuristic(start, goal), 0, start, [start])]
        seen = {start: 0}
        while queue:
            self.last_nodes_expanded += 1
            f, g, curr, path = heapq.heappop(queue)
            if curr == goal:
                return path
            for n in self._reachable(curr):
                if n in self.visited or n in self.known_safe or n == goal:
                    new_g = g + 1
                    if n not in seen or new_g < seen[n]:
                        seen[n] = new_g
                        h = self._heuristic(n, goal)
                        heapq.heappush(queue, (new_g + h, new_g, n, path + [n]))
        return None

    def _astar_path_safe(self, start, goal):
        """A* Search to find path from start to goal using ONLY known_safe cells."""
        self.last_nodes_expanded = 0
        queue = [(self._heuristic(start, goal), 0, start, [start])]
        seen = {start: 0}
        while queue:
            self.last_nodes_expanded += 1
            f, g, curr, path = heapq.heappop(queue)
            if curr == goal:
                return path
            for n in self._reachable(curr):
                if n in self.known_safe:
                    new_g = g + 1
                    if n not in seen or new_g < seen[n]:
                        seen[n] = new_g
                        h = self._heuristic(n, goal)
                        heapq.heappush(queue, (new_g + h, new_g, n, path + [n]))
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
                if n not in self.visited and n not in getattr(self, 'known_pits', set()):
                    out.add(n)
        return out
