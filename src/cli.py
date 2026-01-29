"""CLI module for game route search."""
import argparse
import sys
from typing import Sequence

from src.map_loader import load_map_from_file, MapValidationError
from src.graph_builder import build_graph
from src.search import search_path, Algorithm, NoPathError
from src.visualize import render_path, format_metrics, format_comparison


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    """
    Parse command line arguments.

    Args:
        args: Command line arguments

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog='game-route-search',
        description='Find shortest path in text-based game maps',
    )

    parser.add_argument(
        'map_file',
        type=str,
        help='Path to the text map file',
    )

    parser.add_argument(
        '--algorithm',
        type=str,
        choices=['astar', 'bfs'],
        default='astar',
        help='Search algorithm to use (default: astar)',
    )

    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare A* and BFS algorithms',
    )

    parser.add_argument(
        '--metrics',
        action='store_true',
        help='Display metrics (path length, execution time)',
    )

    return parser.parse_args(args)


def run(
    map_file: str,
    algorithm: str,
    compare: bool,
    metrics: bool,
) -> int:
    """
    Run the path search.

    Args:
        map_file: Path to the map file
        algorithm: Algorithm name ('astar' or 'bfs')
        compare: Whether to compare algorithms
        metrics: Whether to display metrics

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        game_map = load_map_from_file(map_file)
    except FileNotFoundError:
        print(f"Error: File not found: {map_file}", file=sys.stderr)
        return 1
    except MapValidationError as e:
        print(f"Error: Invalid map: {e}", file=sys.stderr)
        return 1

    graph = build_graph(game_map)

    if compare:
        return run_compare_mode(game_map, graph, metrics)

    algo = Algorithm.ASTAR if algorithm == 'astar' else Algorithm.BFS

    try:
        result = search_path(graph, game_map.start, game_map.goal, algo)
    except NoPathError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    visualization = render_path(game_map, result.path)
    print(visualization)

    if metrics:
        print()
        print(format_metrics(result.algorithm.value.upper(), result.path_length, result.execution_time))

    return 0


def run_compare_mode(game_map, graph, metrics: bool) -> int:
    """
    Run in comparison mode, executing both A* and BFS.

    Args:
        game_map: The loaded game map
        graph: The built graph
        metrics: Whether to display metrics

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        astar_result = search_path(graph, game_map.start, game_map.goal, Algorithm.ASTAR)
        bfs_result = search_path(graph, game_map.start, game_map.goal, Algorithm.BFS)
    except NoPathError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print("=== A* Path ===")
    print(render_path(game_map, astar_result.path))
    print()

    print("=== BFS Path ===")
    print(render_path(game_map, bfs_result.path))
    print()

    if metrics:
        print(format_comparison(
            astar_result.path_length,
            astar_result.execution_time,
            bfs_result.path_length,
            bfs_result.execution_time,
        ))

    return 0


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    args = parse_args(sys.argv[1:])

    return run(
        map_file=args.map_file,
        algorithm=args.algorithm,
        compare=args.compare,
        metrics=args.metrics,
    )


if __name__ == '__main__':
    sys.exit(main())
