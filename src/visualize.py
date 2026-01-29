"""Visualization module for path rendering."""
from typing import Sequence

from src.map_loader import GameMap


PATH_MARKER = '@'


def render_path(game_map: GameMap, path: Sequence[tuple[int, int]]) -> str:
    """
    Render the map with path marked.

    Path cells that are roads ('.') are replaced with '@'.
    Start ('S'), Goal ('G'), and Wall ('#') are preserved.

    Args:
        game_map: The game map
        path: Sequence of (x, y) positions forming the path

    Returns:
        String representation of the map with path marked
    """
    path_set = set(path)

    result_grid = [row.copy() for row in game_map.grid]

    for x, y in path:
        cell = result_grid[y][x]
        if cell == '.':
            result_grid[y][x] = PATH_MARKER

    lines = [''.join(row) for row in result_grid]
    return '\n'.join(lines)


def format_metrics(
    algorithm_name: str,
    path_length: int,
    execution_time: float,
) -> str:
    """
    Format metrics for display.

    Args:
        algorithm_name: Name of the algorithm used
        path_length: Number of nodes in the path
        execution_time: Time taken in seconds

    Returns:
        Formatted string of metrics
    """
    return (
        f"Algorithm: {algorithm_name}\n"
        f"Path length: {path_length} nodes\n"
        f"Execution time: {execution_time * 1000:.3f} ms"
    )


def format_comparison(
    astar_path_length: int,
    astar_time: float,
    bfs_path_length: int,
    bfs_time: float,
) -> str:
    """
    Format comparison metrics for A* and BFS.

    Args:
        astar_path_length: A* path length
        astar_time: A* execution time in seconds
        bfs_path_length: BFS path length
        bfs_time: BFS execution time in seconds

    Returns:
        Formatted comparison string
    """
    lines = [
        "=== Algorithm Comparison ===",
        f"A*:  Path length = {astar_path_length}, Time = {astar_time * 1000:.3f} ms",
        f"BFS: Path length = {bfs_path_length}, Time = {bfs_time * 1000:.3f} ms",
    ]

    if astar_path_length != bfs_path_length:
        lines.append(f"Note: Path lengths differ (A*: {astar_path_length}, BFS: {bfs_path_length})")

    return '\n'.join(lines)
