import itertools

class ProbabilisticEngine:
    def __init__(self, size=4, pit_prior=0.2):
        self.size = size
        self.pit_prior = pit_prior
        self.breezes = {} # (x, y) -> bool
        self.visited = set() # (x, y)
        self.known_safe = set() # (x, y)

    def update_observations(self, visited, breezes, known_safe):
        self.visited = visited
        self.breezes = breezes
        self.known_safe = known_safe

    def _get_neighbors(self, x, y):
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                neighbors.append((nx, ny))
        return neighbors

    def get_pit_probabilities(self, frontier):
        """
        Calculates the probability of a pit for each cell in the frontier.
        Frontier: list of unvisited cells adjacent to visited ones.
        """
        if not frontier:
            return {}

        # 1. Identify "Relevant" unvisited cells (the frontier)
        # 2. Identify "Relevant" breezes (breezes adjacent to frontier)
        relevant_breezes = []
        for v in self.visited:
            if self.breezes.get(v):
                # Only keep breeze if it's adjacent to at least one frontier cell
                nb = self._get_neighbors(*v)
                if any(n in frontier for n in nb):
                    relevant_breezes.append(v)
            else:
                # No breeze locations are hard constraints (Pits must be 0 in neighbors)
                pass

        # Since a full joint distribution is exponential, we'll use a simplified 
        # local approach: 
        # A cell (fx, fy) in frontier is likely to have a pit if:
        # - It is adjacent to a Breeze cell
        # - That Breeze cell is NOT explained by other known pits or other frontier cells

        # For this implementation, we will use a "Possible Worlds" counting method 
        # on the local frontier if it's small enough.
        
        probs = {f: self.pit_prior for f in frontier}
        
        # If a frontier cell is adjacent to a 'No-Breeze' visited cell, it's 0% pit.
        for f in frontier:
            nb = self._get_neighbors(*f)
            for n in nb:
                if n in self.visited and not self.breezes.get(n):
                    probs[f] = 0.0
                    break
        
        # Now handle the Breezes
        # For simplicity in this script, we'll assign higher risk to frontier cells 
        # that are the ONLY unvisited neighbors of a Breeze cell.
        for v in self.visited:
            if self.breezes.get(v):
                unvisited_nb = [n for n in self._get_neighbors(*v) if n not in self.visited]
                if len(unvisited_nb) > 0:
                    for u in unvisited_nb:
                        if u in probs and probs[u] > 0:
                            # If 3 neighbors are unvisited, each has roughly ~33% chance? 
                            # More accurately: 1 - (1-p)^n = observed_breeze.
                            # We'll use a simplified heuristic for visualization.
                            probs[u] = max(probs[u], 1.0 / len(unvisited_nb))

        return probs
