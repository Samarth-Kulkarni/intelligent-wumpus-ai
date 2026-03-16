import random


class ProbabilisticEngine:
    """Estimates pit probabilities for frontier cells using wall-edge awareness."""

    def __init__(self, size=8):
        self.size = size
        self.visited = set()
        self.breeze_observations = {}
        self.stench_observations = set()

    def _wk(self, c1, c2):
        return (min(c1, c2), max(c1, c2))

    def _neighbors(self, cell, wall_edges=None):
        x, y = cell
        out = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if wall_edges is not None:
                    if self._wk((x, y), (nx, ny)) in wall_edges:
                        continue
                out.append((nx, ny))
        return out

    def update_observations(self, visited, breeze_obs, stench_obs):
        self.visited = visited
        self.breeze_observations = breeze_obs
        self.stench_observations = stench_obs

    def get_pit_probabilities(self, frontier, wall_edges=None):
        """Simple risk estimate: for each frontier cell, count how many
        breeze-visited neighbours it has vs total visited neighbours."""
        risks = {}
        for cell in frontier:
            if cell in self.visited:
                continue
            nbrs = self._neighbors(cell, wall_edges)
            visited_nbrs = [n for n in nbrs if n in self.visited]
            if not visited_nbrs:
                risks[cell] = 0.5  # unknown
                continue
            breeze_count = sum(
                1 for n in visited_nbrs if self.breeze_observations.get(n, False)
            )
            no_breeze = sum(
                1 for n in visited_nbrs if not self.breeze_observations.get(n, True)
            )
            if no_breeze > 0 and breeze_count == 0:
                risks[cell] = 0.05  # very low risk
            elif breeze_count > 0:
                risks[cell] = min(0.9, breeze_count / len(visited_nbrs))
            else:
                risks[cell] = 0.2
        return risks
