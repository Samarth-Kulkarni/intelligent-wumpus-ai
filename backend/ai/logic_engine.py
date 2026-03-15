from sympy import symbols, Not, Or, And, Implies, Equivalent
from sympy.logic.inference import satisfiable

class LogicEngine:
    def __init__(self, size=4):
        self.size = size
        # Generate symbols for each cell
        # P_x_y: Pit at (x, y)
        # W_x_y: Wumpus at (x, y)
        # B_x_y: Breeze at (x, y)
        # S_x_y: Stench at (x, y)
        self.symbols = {}
        for x in range(size):
            for y in range(size):
                self.symbols[f"P_{x}_{y}"] = symbols(f"P_{x}_{y}")
                self.symbols[f"W_{x}_{y}"] = symbols(f"W_{x}_{y}")
                self.symbols[f"B_{x}_{y}"] = symbols(f"B_{x}_{y}")
                self.symbols[f"S_{x}_{y}"] = symbols(f"S_{x}_{y}")

        self.kb = []
        self._initialize_rules()

    def _get_neighbors(self, x, y):
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                neighbors.append((nx, ny))
        return neighbors

    def _initialize_rules(self):
        """Initializes the background rules of the Wumpus World."""
        # 1. Start square (0,0) is always safe
        self.kb.append(Not(self.symbols["P_0_0"]))
        self.kb.append(Not(self.symbols["W_0_0"]))

        # 2. Breeze <=> Pit in neighbor
        for x in range(self.size):
            for y in range(self.size):
                neighbors = self._get_neighbors(x, y)
                neighbor_pits = [self.symbols[f"P_{nx}_{ny}"] for nx, ny in neighbors]
                self.kb.append(Equivalent(self.symbols[f"B_{x}_{y}"], Or(*neighbor_pits)))

        # 3. Stench <=> Wumpus in neighbor
        for x in range(self.size):
            for y in range(self.size):
                neighbors = self._get_neighbors(x, y)
                neighbor_wumpus = [self.symbols[f"W_{nx}_{ny}"] for nx, ny in neighbors]
                self.kb.append(Equivalent(self.symbols[f"S_{x}_{y}"], Or(*neighbor_wumpus)))

    def add_percept(self, x, y, breeze, stench):
        """Adds observed percepts at a specific location to the KB."""
        if breeze:
            self.kb.append(self.symbols[f"B_{x}_{y}"])
        else:
            self.kb.append(Not(self.symbols[f"B_{x}_{y}"]))
            
        if stench:
            self.kb.append(self.symbols[f"S_{x}_{y}"])
        else:
            self.kb.append(Not(self.symbols[f"S_{x}_{y}"]))

    def is_safe(self, x, y):
        """Returns True if the square (x, y) is proven safe (No Pit AND No Wumpus)."""
        # A cell is safe if KB |= (~P_x_y AND ~W_x_y)
        # This is equivalent to checking if (KB AND P_x_y) is unsatisfiable 
        # AND (KB AND W_x_y) is unsatisfiable.
        
        kb_and = And(*self.kb)
        
        # Check if P_x_y is possible
        # satisfiable returns False if unsatisfiable
        can_be_pit = satisfiable(And(kb_and, self.symbols[f"P_{x}_{y}"]))
        if can_be_pit is not False:
            return False
            
        # Check if W_x_y is possible
        can_be_wumpus = satisfiable(And(kb_and, self.symbols[f"W_{x}_{y}"]))
        if can_be_wumpus is not False:
            return False
            
        return True

    def get_kb_summary(self):
        return f"KB contains {len(self.kb)} rules/facts."

if __name__ == "__main__":
    # Quick Test
    engine = LogicEngine(4)
    print("Initial (0,0) safe?", engine.is_safe(0, 0))
    
    # Move to (0,0), perceive nothing
    engine.add_percept(0, 0, False, False)
    print("After no breeze at (0,0), is (0,1) safe?", engine.is_safe(0, 1))
    print("After no breeze at (0,0), is (1,0) safe?", engine.is_safe(1, 0))
    
    # Perceive breeze at (0,1)
    engine.add_percept(0, 1, True, False)
    print("Breeze at (0,1). Is (0,2) safe?", engine.is_safe(0, 2))
    print("Breeze at (0,1). Is (1,1) safe?", engine.is_safe(1, 1))
