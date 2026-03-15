from .logic_engine import LogicEngine
from .probability_engine import ProbabilisticEngine

class IntelligentAgent:
    def __init__(self, size=4):
        self.size = size
        self.logic = LogicEngine(size)
        self.prob_engine = ProbabilisticEngine(size)
        self.visited = set()
        self.current_pos = [0, 0]
        self.percept_history = {} # (x, y) -> percepts

    def update_knowledge(self, x, y, percepts):
        """Updates the KB with new percepts at the current location."""
        self.current_pos = [x, y]
        self.visited.add(tuple(self.current_pos))
        self.percept_history[tuple(self.current_pos)] = percepts
        
        breeze = percepts.get('breeze', False)
        stench = percepts.get('stench', False)
        
        self.logic.add_percept(x, y, breeze, stench)

    def get_recommendation(self, current_orientation):
        """Asks the logic engine for safe moves or deduced hazards and plans the next action."""
        info_strings = [] 
        confirmed_safe_tiles = []
        
        # 1. Identify neighbors
        x, y = self.current_pos
        neighbor_tiles = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                neighbor_tiles.append((nx, ny))
        
        # 2. Logic First
        unvisited = [(n[0], n[1]) for n in neighbor_tiles if n not in self.visited]
        for nx, ny in unvisited:
            if self.logic.is_safe(nx, ny):
                confirmed_safe_tiles.append((nx, ny))
                info_strings.append(f"Logic: ({nx},{ny}) is proven 100% SAFE.")

        # 3. Probability Second
        target_tile = None
        if confirmed_safe_tiles:
            target_tile = confirmed_safe_tiles[0]
        elif unvisited:
            info_strings.append("Logic cannot prove safety. Engaging probabilistic reasoning...")
            breezes = {pos: p.get('breeze') for pos, p in self.percept_history.items()}
            self.prob_engine.update_observations(self.visited, breezes, set())
            risks = self.prob_engine.get_pit_probabilities(unvisited)
            if risks:
                target_tile = min(risks.keys(), key=lambda k: risks[k])
                info_strings.append(f"Prob: Choosing ({target_tile[0]},{target_tile[1]}) - Lowest Risk ({risks[target_tile]:.1%}).")

        # 4. Action Planning
        best_action = "TURNLEFT"

        if target_tile:
            tx, ty = target_tile
            dx, dy = tx - x, ty - y

            if dx == 1:
                desired_dir = "RIGHT"
            elif dx == -1:
                desired_dir = "LEFT"
            elif dy == 1:
                desired_dir = "UP"
            elif dy == -1:
                desired_dir = "DOWN"

            # Correct clockwise order
            directions = ["UP", "RIGHT", "DOWN", "LEFT"]

            curr_idx = directions.index(current_orientation)
            dest_idx = directions.index(desired_dir)

            if curr_idx == dest_idx:
                best_action = "FORWARD"
            elif (dest_idx - curr_idx) % 4 == 1:
                best_action = "TURNRIGHT"
            else:
                best_action = "TURNLEFT"
        
        # Special case: Grab gold if glitter
        last_percept = self.percept_history.get(tuple(self.current_pos), {})
        if last_percept.get('glitter'):
            best_action = "GRAB"
            info_strings.append("Action: Glitter detected! Grabbing the gold.")

        info_strings.append(f"Action chosen: {best_action}")
        return {
            "thoughts": info_strings,
            "best_action": best_action,
            "kb_count": len(self.logic.kb)
        }
