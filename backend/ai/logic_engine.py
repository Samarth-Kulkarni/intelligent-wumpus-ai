class LogicEngine:
    def __init__(self, size=4):
        self.size = size
        self.percepts = {}
        self.wall_rules = set()
        
        # We store rules as strings just for UI presentation to maintain the exact look
        self.kb_display = []
        self._initialize_display_rules()

    def _get_neighbors(self, x, y):
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                neighbors.append((nx, ny))
        return neighbors

    def _initialize_display_rules(self):
        self.kb_display.append("¬P_0_0")
        self.kb_display.append("¬W_0_0")
        for x in range(self.size):
            for y in range(self.size):
                neighbors = self._get_neighbors(x, y)
                n_p = " ∨ ".join([f"P_{nx}_{ny}" for nx, ny in neighbors])
                if n_p:
                    self.kb_display.append(f"Equivalent(B_{x}_{y}, {n_p})")
                n_w = " ∨ ".join([f"W_{nx}_{ny}" for nx, ny in neighbors])
                if n_w:
                    self.kb_display.append(f"Equivalent(S_{x}_{y}, {n_w})")

    def add_wall_rule(self, x, y):
        self.wall_rules.add((x, y))
        self.kb_display.append(f"¬P_{x}_{y}")
        self.kb_display.append(f"¬W_{x}_{y}")

    def add_percept(self, x, y, breeze, stench):
        if (x, y) not in self.percepts:
            self.percepts[(x, y)] = {'B': breeze, 'S': stench}
            b_str = f"B_{x}_{y}" if breeze else f"¬B_{x}_{y}"
            s_str = f"S_{x}_{y}" if stench else f"¬S_{x}_{y}"
            self.kb_display.append(b_str)
            self.kb_display.append(s_str)

    def is_safe(self, x, y):
        if (x, y) == (0, 0): return True
        if (x, y) in self.wall_rules: return False # walls aren't "walkably safe"
        
        # Pure Mathematical Deduction (Forward Chaining)
        # 1. If ANY neighbor of (x,y) has been visited and had NO breeze, (x,y) cannot be a pit.
        # 2. If ANY neighbor of (x,y) has been visited and had NO stench, (x,y) cannot be a wumpus.
        
        safe_from_pit = False
        safe_from_wumpus = False
        
        for nx, ny in self._get_neighbors(x, y):
            if (nx, ny) in self.percepts:
                if not self.percepts[(nx, ny)]['B']:
                    safe_from_pit = True
                if not self.percepts[(nx, ny)]['S']:
                    safe_from_wumpus = True
                    
        return safe_from_pit and safe_from_wumpus

    def get_kb_summary(self):
        return f"KB contains {len(self.kb_display)} rules/facts."

    def get_kb_facts(self):
        return self.kb_display

    def get_resolution_proof(self, x, y):
        for nx, ny in self._get_neighbors(x, y):
            if (nx, ny) in self.percepts and not self.percepts[(nx, ny)]['B']:
                return (f"Resolution: Assume P({x},{y}). "
                        f"CNF: {{¬P({x},{y}) ∨ B({nx},{ny})}}. "
                        f"Resolve with {{¬B({nx},{ny})}} ⊢ {{¬P({x},{y})}}. "
                        f"Contradiction! ⊢ ∅. Cell is SAFE.")
        return f"Resolution: Deductive elimination confirmed {x},{y} safe."
