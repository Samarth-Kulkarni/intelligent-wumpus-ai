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
    def __init__(self, size=4, world_file=None):
        self.size = size
        self.wumpus_location = [0, 0]
        self.gold_location = [0, 0]
        self.pit_locations = []
        self.wumpus_alive = True
        self.num_actions = 0
        self.agent_location = [1, 1]
        self.agent_orientation = Orientation.RIGHT
        self.agent_alive = True
        self.agent_has_arrow = True
        self.agent_has_gold = True
        self.agent_in_cave = True
        self.last_action = None
        self.percept = {"stench": False, "breeze": False, "glitter": False, "bump": False, "scream": False}
        
        if world_file:
            self._load_world(world_file)
        else:
            self._generate_world()
            
        self.initialize()

    def _load_world(self, world_file):
        # Placeholder for loading from file if needed
        pass

    def _generate_world(self):
        def get_rand_pos():
            while True:
                x = random.randint(1, self.size)
                y = random.randint(1, self.size)
                if x != 1 or y != 1:
                    return [x, y]

        self.wumpus_location = get_rand_pos()
        self.gold_location = get_rand_pos()
        
        self.pit_locations = []
        for x in range(1, self.size + 1):
            for y in range(1, self.size + 1):
                if x != 1 or y != 1:
                    if random.random() < 0.2:
                        self.pit_locations.append([x, y])

    def initialize(self):
        self.num_actions = 0
        self.agent_location = [1, 1]
        self.agent_orientation = Orientation.RIGHT
        self.agent_alive = True
        self.agent_has_arrow = True
        self.agent_has_gold = False
        self.agent_in_cave = True
        self.wumpus_alive = True
        self.last_action = None
        self.percept = self._get_percept()

    def _is_adjacent(self, loc1, loc2):
        dx = abs(loc1[0] - loc2[0])
        dy = abs(loc1[1] - loc2[1])
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)

    def _get_percept(self):
        p = {
            "stench": False,
            "breeze": False,
            "glitter": False,
            "bump": False,
            "scream": False
        }
        
        # Stench
        if self._is_adjacent(self.agent_location, self.wumpus_location) or self.agent_location == self.wumpus_location:
            p["stench"] = True
            
        # Breeze
        for pit in self.pit_locations:
            if self._is_adjacent(self.agent_location, pit):
                p["breeze"] = True
                break
                
        # Glitter
        if not self.agent_has_gold and self.agent_location == self.gold_location:
            p["glitter"] = True
            
        return p

    def execute_action(self, action):
        if not self.agent_alive or not self.agent_in_cave:
            return
            
        self.num_actions += 1
        self.last_action = Action.to_string(action)
        self.percept["bump"] = False
        self.percept["scream"] = False

        if action == Action.GOFORWARD:
            if self.agent_orientation == Orientation.RIGHT:
                if self.agent_location[0] < self.size: self.agent_location[0] += 1
                else: self.percept["bump"] = True
            elif self.agent_orientation == Orientation.UP:
                if self.agent_location[1] < self.size: self.agent_location[1] += 1
                else: self.percept["bump"] = True
            elif self.agent_orientation == Orientation.LEFT:
                if self.agent_location[0] > 1: self.agent_location[0] -= 1
                else: self.percept["bump"] = True
            elif self.agent_orientation == Orientation.DOWN:
                if self.agent_location[1] > 1: self.agent_location[1] -= 1
                else: self.percept["bump"] = True
            
            # Check for death
            for pit in self.pit_locations:
                if self.agent_location == pit:
                    self.agent_alive = False
            if self.wumpus_alive and self.agent_location == self.wumpus_location:
                self.agent_alive = False
                
        elif action == Action.TURNLEFT:
            self.agent_orientation = (self.agent_orientation + 1) % 4
        elif action == Action.TURNRIGHT:
            self.agent_orientation = (self.agent_orientation - 1) % 4
        elif action == Action.GRAB:
            if not self.agent_has_gold and self.agent_location == self.gold_location:
                self.agent_has_gold = True
        elif action == Action.SHOOT:
            if self.agent_has_arrow:
                self.agent_has_arrow = False
                if self.wumpus_alive:
                    ax, ay = self.agent_location
                    wx, wy = self.wumpus_location
                    hit = False
                    if self.agent_orientation == Orientation.RIGHT:
                        if ay == wy and ax < wx: hit = True
                    elif self.agent_orientation == Orientation.UP:
                        if ax == wx and ay < wy: hit = True
                    elif self.agent_orientation == Orientation.LEFT:
                        if ay == wy and ax > wx: hit = True
                    elif self.agent_orientation == Orientation.DOWN:
                        if ax == wx and ay > wy: hit = True
                    
                    if hit:
                        self.wumpus_alive = False
                        self.percept["scream"] = True
        elif action == Action.CLIMB:
            if self.agent_location == [1, 1]:
                self.agent_in_cave = False

        # Update percepts after action
        new_percept = self._get_percept()
        new_percept["bump"] = self.percept["bump"]
        new_percept["scream"] = self.percept["scream"]
        self.percept = new_percept

    def get_score(self):
        score = -self.num_actions
        if not self.agent_has_arrow:
            score -= 9
        if self.agent_has_gold and not self.agent_in_cave:
            score += 1000
        if not self.agent_alive:
            score -= 1000
        return score

    def is_game_over(self):
        return not self.agent_alive or not self.agent_in_cave

    def get_state(self):
        orient_map = {Orientation.RIGHT: "RIGHT", Orientation.UP: "UP", Orientation.LEFT: "LEFT", Orientation.DOWN: "DOWN"}
        return {
            "size": self.size,
            "agent_pos": [self.agent_location[0]-1, self.agent_location[1]-1],
            "agent_dir": orient_map[self.agent_orientation],
            "score": self.get_score(),
            "moves": self.num_actions,
            "percepts": self.percept,
            "is_over": self.is_game_over(),
            "last_action": self.last_action,
            "agent_alive": self.agent_alive,
            "agent_has_gold": self.agent_has_gold,
            "wumpus_alive": self.wumpus_alive,
            "wumpus_pos": [self.wumpus_location[0]-1, self.wumpus_location[1]-1],
            "gold_pos": [self.gold_location[0]-1, self.gold_location[1]-1],
            "pits": [[p[0]-1, p[1]-1] for p in self.pit_locations]
        }
