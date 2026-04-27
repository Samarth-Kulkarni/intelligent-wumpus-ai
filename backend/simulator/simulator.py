import random

class Action:
    GOFORWARD = 0
    TURNLEFT = 1
    TURNRIGHT = 2
    GRAB = 3
    SHOOT = 4
    CLIMB = 5

    @staticmethod
    def to_string(action):
        return ["FORWARD", "TURNLEFT", "TURNRIGHT", "GRAB", "SHOOT", "CLIMB"][action]

class Orientation:
    RIGHT = 0
    UP = 1
    LEFT = 2
    DOWN = 3

class WumpusWorld:
    """Wumpus World with proper DFS-generated maze (wall-edges between cells)."""

    def __init__(self, size=8):
        self.size = size
        self.walls = set()          # wall edges: {((x1,y1),(x2,y2)), ...}
        self.exit_location = [size, size]
        self.wumpus_location = [0, 0]
        self.gold_location = [0, 0]
        self.pit_locations = []
        self.wumpus_alive = True
        self.agent_location = [1, 1]
        self.agent_orientation = Orientation.RIGHT
        self.agent_alive = True
        self.agent_has_arrow = True
        self.agent_has_gold = False
        self.agent_in_cave = True
        self.num_actions = 0
        self.last_action = ""
        self.percept = {"stench": False, "breeze": False, "glitter": False, "bump": False, "scream": False}

        self._generate_maze()
        self._place_entities()
        self.visited_locations = {tuple(self.agent_location)}
        self.percept = self._get_percept()

    def reset(self):
        """Resets the agent state without regenerating the maze."""
        self.wumpus_alive = True
        self.agent_location = [1, 1]
        self.agent_orientation = Orientation.RIGHT
        self.agent_alive = True
        self.agent_has_arrow = True
        self.agent_has_gold = False
        self.agent_in_cave = True
        self.num_actions = 0
        self.last_action = ""
        self.visited_locations = {tuple(self.agent_location)}
        self.percept = self._get_percept()

    # ─── Maze Generation ────────────────────────────────────────────────

    def _wk(self, c1, c2):
        """Canonical wall key."""
        return (min(c1, c2), max(c1, c2))

    def _has_wall(self, c1, c2):
        return self._wk(tuple(c1), tuple(c2)) in self.walls

    def _generate_maze(self):
        """Recursive-backtracking DFS to carve a proper maze."""
        s = self.size
        self.walls = set()
        for x in range(1, s + 1):
            for y in range(1, s + 1):
                if x < s:
                    self.walls.add(self._wk((x, y), (x + 1, y)))
                if y < s:
                    self.walls.add(self._wk((x, y), (x, y + 1)))

        visited = {(1, 1)}
        stack = [(1, 1)]
        while stack:
            cx, cy = stack[-1]
            nbrs = []
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 1 <= nx <= s and 1 <= ny <= s and (nx, ny) not in visited:
                    nbrs.append((nx, ny))
            if nbrs:
                nxt = random.choice(nbrs)
                self.walls.discard(self._wk((cx, cy), nxt))
                visited.add(nxt)
                stack.append(nxt)
            else:
                stack.pop()

        # Remove a few extra walls so the maze isn't a single-path tree
        removable = list(self.walls)
        random.shuffle(removable)
        for i in range(min(s, len(removable))):
            self.walls.discard(removable[i])

    def _place_entities(self):
        s = self.size
        avoid = {(1, 1), (s, s)}

        def rp():
            while True:
                p = (random.randint(1, s), random.randint(1, s))
                if p not in avoid:
                    return list(p)

        self.exit_location = [s, s]
        self.wumpus_location = rp(); avoid.add(tuple(self.wumpus_location))
        self.gold_location = rp();   avoid.add(tuple(self.gold_location))

        self.pit_locations = []
        for _ in range(random.randint(2, max(3, s // 3))):
            pit = rp()
            while tuple(pit) in avoid:
                pit = rp()
            self.pit_locations.append(pit)
            avoid.add(tuple(pit))

    # ─── Helpers ────────────────────────────────────────────────────────

    def _connected_neighbors(self, loc):
        x, y = loc[0], loc[1]
        out = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 1 <= nx <= self.size and 1 <= ny <= self.size:
                if not self._has_wall((x, y), (nx, ny)):
                    out.append([nx, ny])
        return out

    def _get_percept(self):
        p = {"stench": False, "breeze": False, "glitter": False, "bump": False, "scream": False,
             "stench_intensity": "none", "breeze_intensity": "none", "glitter_intensity": "none"}
             
        ax, ay = self.agent_location
        dx, dy = 0, 0
        if   self.agent_orientation == Orientation.RIGHT: dx = 1
        elif self.agent_orientation == Orientation.UP:    dy = 1
        elif self.agent_orientation == Orientation.LEFT:  dx = -1
        elif self.agent_orientation == Orientation.DOWN:  dy = -1
        facing_loc = [ax + dx, ay + dy]

        for n in self._connected_neighbors(self.agent_location):
            if n == self.wumpus_location and self.wumpus_alive:
                p["stench"] = True
                if n == facing_loc:
                    p["stench_intensity"] = "high"
                elif p["stench_intensity"] != "high":
                    p["stench_intensity"] = "low"
            if n in self.pit_locations:
                p["breeze"] = True
                if n == facing_loc:
                    p["breeze_intensity"] = "high"
                elif p["breeze_intensity"] != "high":
                    p["breeze_intensity"] = "low"
            if n == self.gold_location and not self.agent_has_gold:
                p["glitter"] = True
                if n == facing_loc:
                    p["glitter_intensity"] = "high"
                elif p["glitter_intensity"] != "high":
                    p["glitter_intensity"] = "low"
                    
        if self.agent_location == self.wumpus_location and self.wumpus_alive:
            p["stench"] = True
            p["stench_intensity"] = "high"
        if not self.agent_has_gold and self.agent_location == self.gold_location:
            p["glitter"] = True
            p["glitter_intensity"] = "max"
        return p

    # ─── Actions ────────────────────────────────────────────────────────

    def execute_action(self, action):
        if not self.agent_alive or not self.agent_in_cave:
            return
        self.last_action = Action.to_string(action)
        self.percept["bump"] = False
        self.percept["scream"] = False

        if action == Action.GOFORWARD:
            self.num_actions += 1
            nx, ny = self.agent_location[0], self.agent_location[1]
            if   self.agent_orientation == Orientation.RIGHT: nx += 1
            elif self.agent_orientation == Orientation.UP:    ny += 1
            elif self.agent_orientation == Orientation.LEFT:  nx -= 1
            elif self.agent_orientation == Orientation.DOWN:  ny -= 1

            if not (1 <= nx <= self.size and 1 <= ny <= self.size):
                self.percept["bump"] = True
            elif self._has_wall(self.agent_location, (nx, ny)):
                self.percept["bump"] = True
            else:
                self.agent_location = [nx, ny]
                self.visited_locations.add(tuple(self.agent_location))

            if self.agent_location in self.pit_locations:
                self.agent_alive = False
            if self.wumpus_alive and self.agent_location == self.wumpus_location:
                self.agent_alive = False

        elif action == Action.TURNLEFT:
            self.num_actions += 1
            self.agent_orientation = (self.agent_orientation + 1) % 4
        elif action == Action.TURNRIGHT:
            self.num_actions += 1
            self.agent_orientation = (self.agent_orientation - 1) % 4

        elif action == Action.GRAB:
            self.num_actions += 1
            if not self.agent_has_gold and self.agent_location == self.gold_location:
                self.agent_has_gold = True

        elif action == Action.SHOOT:
            self.num_actions += 1
            if self.agent_has_arrow:
                self.agent_has_arrow = False
                if self.wumpus_alive:
                    ax, ay = self.agent_location
                    wx, wy = self.wumpus_location
                    hit = False
                    if   self.agent_orientation == Orientation.RIGHT and ay == wy and ax < wx: hit = True
                    elif self.agent_orientation == Orientation.UP    and ax == wx and ay < wy: hit = True
                    elif self.agent_orientation == Orientation.LEFT  and ay == wy and ax > wx: hit = True
                    elif self.agent_orientation == Orientation.DOWN  and ax == wx and ay > wy: hit = True
                    if hit:
                        self.wumpus_alive = False
                        self.percept["scream"] = True

        elif action == Action.CLIMB:
            self.num_actions += 1
            if self.agent_location == self.exit_location:
                self.agent_in_cave = False

        new_p = self._get_percept()
        new_p["bump"] = self.percept["bump"]
        new_p["scream"] = self.percept["scream"]
        self.percept = new_p

    # ─── Score ──────────────────────────────────────────────────────────

    def get_score(self):
        s = 500 - (self.num_actions * 10)
        if not self.wumpus_alive:       s += 500
        if self.agent_has_gold:         s += 500
        if not self.agent_in_cave and self.agent_has_gold: s += 1000
        if not self.agent_alive:        s -= 500
        return s

    def is_game_over(self):
        return not self.agent_alive or not self.agent_in_cave

    def get_state(self):
        om = {Orientation.RIGHT: "RIGHT", Orientation.UP: "UP",
              Orientation.LEFT: "LEFT",  Orientation.DOWN: "DOWN"}
        wl = [[[c1[0]-1, c1[1]-1], [c2[0]-1, c2[1]-1]] for c1, c2 in self.walls]
        return {
            "size": self.size,
            "agent_pos":  [self.agent_location[0]-1, self.agent_location[1]-1],
            "agent_dir":  om[self.agent_orientation],
            "score":      self.get_score(),
            "moves":      self.num_actions,
            "percepts":   self.percept,
            "is_over":    self.is_game_over(),
            "last_action":self.last_action,
            "agent_alive":self.agent_alive,
            "agent_has_gold": self.agent_has_gold,
            "agent_has_arrow": self.agent_has_arrow,
            "wumpus_alive":   self.wumpus_alive,
            "wumpus_pos": [self.wumpus_location[0]-1, self.wumpus_location[1]-1],
            "gold_pos":   [self.gold_location[0]-1, self.gold_location[1]-1],
            "exit_pos":   [self.exit_location[0]-1, self.exit_location[1]-1],
            "pits":       [[p[0]-1, p[1]-1] for p in self.pit_locations],
            "walls":      wl,
            "visited_cells": [[v[0]-1, v[1]-1] for v in self.visited_locations],
        }
