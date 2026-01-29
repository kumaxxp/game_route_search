"""Multi-weighted pathfinding engine with Dijkstra and A*."""
import heapq
import time
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from src.map_loader_v2 import MultiLayerMap
from src.cost_function import calculate_edge_cost, get_minimum_base_cost, CostConfig
from src.constants.terrain_costs import get_terrain_cost


class FinderAlgorithm(Enum):
    """Available pathfinding algorithms."""

    DIJKSTRA = "dijkstra"
    ASTAR = "astar"


class NoPathFoundError(Exception):
    """Exception raised when no path exists."""

    pass


@dataclass(frozen=True)
class FinderResult:
    """Result of pathfinding operation."""

    path: Sequence[tuple[int, int]]
    total_cost: float
    algorithm: FinderAlgorithm
    nodes_expanded: int
    execution_time: float


DIRECTIONS_4 = [(0, -1), (0, 1), (-1, 0), (1, 0)]
DIRECTIONS_8 = DIRECTIONS_4 + [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def manhattan_heuristic(
    pos: tuple[int, int],
    goal: tuple[int, int],
    min_cost: float,
) -> float:
    """
    Calculate Manhattan distance heuristic.

    h(x) = d_manhattan(x, G) * min_t(b_t)

    This is admissible because it never overestimates.

    Args:
        pos: Current position
        goal: Goal position
        min_cost: Minimum base terrain cost

    Returns:
        Heuristic estimate
    """
    dx = abs(pos[0] - goal[0])
    dy = abs(pos[1] - goal[1])
    return (dx + dy) * min_cost


def octile_heuristic(
    pos: tuple[int, int],
    goal: tuple[int, int],
    min_cost: float,
) -> float:
    """
    Calculate Octile distance heuristic (for 8-directional movement).

    h(x) = d_octile(x, G) * min_t(b_t)

    Args:
        pos: Current position
        goal: Goal position
        min_cost: Minimum base terrain cost

    Returns:
        Heuristic estimate
    """
    dx = abs(pos[0] - goal[0])
    dy = abs(pos[1] - goal[1])
    d_octile = max(dx, dy) + (1.41421356237 - 1) * min(dx, dy)
    return d_octile * min_cost


def get_neighbors(
    pos: tuple[int, int],
    game_map: MultiLayerMap,
    allow_diagonal: bool,
) -> list[tuple[int, int]]:
    """
    Get valid neighbor positions.

    Args:
        pos: Current position
        game_map: The map
        allow_diagonal: Whether to include diagonal neighbors

    Returns:
        List of valid neighbor positions
    """
    directions = DIRECTIONS_8 if allow_diagonal else DIRECTIONS_4
    neighbors: list[tuple[int, int]] = []

    for dx, dy in directions:
        nx, ny = pos[0] + dx, pos[1] + dy

        if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
            terrain_code = game_map.terrain[ny][nx]
            terrain = get_terrain_cost(terrain_code)
            if terrain.passable:
                neighbors.append((nx, ny))

    return neighbors


def find_path(
    game_map: MultiLayerMap,
    algorithm: FinderAlgorithm,
    allow_diagonal: bool = False,
    cost_config: CostConfig | None = None,
) -> FinderResult:
    """
    Find optimal path using specified algorithm.

    Args:
        game_map: Multi-layer map
        algorithm: Dijkstra or A*
        allow_diagonal: Whether diagonal movement is allowed
        cost_config: Cost calculation configuration

    Returns:
        FinderResult with path and statistics

    Raises:
        NoPathFoundError: If no path exists
    """
    start_time = time.perf_counter()

    start = game_map.start
    goal = game_map.goal
    config = cost_config or CostConfig()

    min_cost = get_minimum_base_cost(game_map)
    heuristic_func = octile_heuristic if allow_diagonal else manhattan_heuristic

    dist: dict[tuple[int, int], float] = {start: 0}
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    if algorithm == FinderAlgorithm.ASTAR:
        h_start = heuristic_func(start, goal, min_cost)
        pq: list[tuple[float, tuple[int, int]]] = [(h_start, start)]
    else:
        pq = [(0.0, start)]

    nodes_expanded = 0

    while pq:
        current_f, current = heapq.heappop(pq)

        if current == goal:
            break

        current_dist = dist.get(current, float('inf'))

        if algorithm == FinderAlgorithm.ASTAR:
            if current_f > current_dist + heuristic_func(current, goal, min_cost) + 1e-9:
                continue
        else:
            if current_f > current_dist + 1e-9:
                continue

        nodes_expanded += 1

        for neighbor in get_neighbors(current, game_map, allow_diagonal):
            edge_cost = calculate_edge_cost(
                current, neighbor, game_map, config, allow_diagonal
            )

            if edge_cost == float('inf'):
                continue

            new_dist = current_dist + edge_cost

            if new_dist < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_dist
                came_from[neighbor] = current

                if algorithm == FinderAlgorithm.ASTAR:
                    f_score = new_dist + heuristic_func(neighbor, goal, min_cost)
                else:
                    f_score = new_dist

                heapq.heappush(pq, (f_score, neighbor))

    end_time = time.perf_counter()

    if goal not in came_from:
        raise NoPathFoundError(f"No path from {start} to {goal}")

    path = _reconstruct_path(came_from, goal)
    total_cost = dist[goal]

    return FinderResult(
        path=path,
        total_cost=total_cost,
        algorithm=algorithm,
        nodes_expanded=nodes_expanded,
        execution_time=end_time - start_time,
    )


def _reconstruct_path(
    came_from: dict[tuple[int, int], tuple[int, int] | None],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """
    Reconstruct path from came_from dictionary.

    Args:
        came_from: Dictionary mapping node to its predecessor
        goal: Goal position

    Returns:
        List of positions from start to goal
    """
    path: list[tuple[int, int]] = []
    current: tuple[int, int] | None = goal

    while current is not None:
        path.append(current)
        current = came_from.get(current)

    path.reverse()
    return path
