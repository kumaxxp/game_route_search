"""Search algorithms module."""
import time
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

import networkx as nx


class Algorithm(Enum):
    """Available search algorithms."""

    ASTAR = "astar"
    BFS = "bfs"


class NoPathError(Exception):
    """Exception raised when no path exists between start and goal."""

    pass


@dataclass(frozen=True)
class SearchResult:
    """Result of a path search."""

    path: Sequence[tuple[int, int]]
    algorithm: Algorithm
    path_length: int
    execution_time: float


def manhattan_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """
    Calculate Manhattan distance between two points.

    Args:
        a: First point (x, y)
        b: Second point (x, y)

    Returns:
        Manhattan distance
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def search_astar(
    graph: nx.Graph,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """
    Find shortest path using A* algorithm with Manhattan distance heuristic.

    Args:
        graph: NetworkX graph
        start: Start position
        goal: Goal position

    Returns:
        List of positions forming the path

    Raises:
        NoPathError: If no path exists
    """
    try:
        path = nx.astar_path(
            graph,
            start,
            goal,
            heuristic=lambda n, g: manhattan_distance(n, goal),
            weight='weight',
        )
        return list(path)
    except nx.NetworkXNoPath:
        raise NoPathError(f"No path found from {start} to {goal}")


def search_bfs(
    graph: nx.Graph,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """
    Find shortest path using BFS algorithm.

    Args:
        graph: NetworkX graph
        start: Start position
        goal: Goal position

    Returns:
        List of positions forming the path

    Raises:
        NoPathError: If no path exists
    """
    try:
        path = nx.shortest_path(graph, start, goal)
        return list(path)
    except nx.NetworkXNoPath:
        raise NoPathError(f"No path found from {start} to {goal}")


def search_path(
    graph: nx.Graph,
    start: tuple[int, int],
    goal: tuple[int, int],
    algorithm: Algorithm,
) -> SearchResult:
    """
    Find shortest path using specified algorithm.

    Args:
        graph: NetworkX graph
        start: Start position
        goal: Goal position
        algorithm: Search algorithm to use

    Returns:
        SearchResult containing path and metrics

    Raises:
        NoPathError: If no path exists
    """
    start_time = time.perf_counter()

    if algorithm == Algorithm.ASTAR:
        path = search_astar(graph, start, goal)
    else:
        path = search_bfs(graph, start, goal)

    end_time = time.perf_counter()
    execution_time = end_time - start_time

    return SearchResult(
        path=path,
        algorithm=algorithm,
        path_length=len(path),
        execution_time=execution_time,
    )
