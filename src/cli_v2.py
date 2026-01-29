"""CLI module for game route search (Phase II)."""
import argparse
import sys
from io import StringIO
from pathlib import Path
from typing import Sequence

from src.map_loader_v2 import load_multi_layer_map, MultiLayerMap, LayerValidationError
from src.finder import find_path, FinderAlgorithm, FinderResult, NoPathFoundError
from src.cost_function import CostConfig
from src.visualize import render_path


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
        description='Find optimal path in text-based game maps with terrain and elevation costs',
    )

    parser.add_argument(
        'map_file',
        type=str,
        help='Path to the terrain map file (or legacy single-file map)',
    )

    parser.add_argument(
        '--algo',
        type=str,
        choices=['dijkstra', 'astar'],
        default='dijkstra',
        help='Search algorithm to use (default: dijkstra)',
    )

    parser.add_argument(
        '--elevation',
        type=str,
        default=None,
        help='Path to elevation layer file',
    )

    parser.add_argument(
        '--priority',
        type=str,
        default=None,
        help='Path to tactical priority layer file',
    )

    parser.add_argument(
        '--priority-weight',
        type=float,
        default=0.0,
        help='Weight for tactical priority (default: 0.0)',
    )

    parser.add_argument(
        '--allow-diagonal',
        action='store_true',
        help='Allow diagonal (8-directional) movement',
    )

    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare Dijkstra and A* algorithms',
    )

    parser.add_argument(
        '--metrics',
        action='store_true',
        help='Display detailed metrics (cost, nodes expanded, time)',
    )

    parser.add_argument(
        '--max-cost-cap',
        type=float,
        default=255.0,
        help='Maximum cost cap for saturation (default: 255)',
    )

    return parser.parse_args(args)


def load_map(args: argparse.Namespace) -> MultiLayerMap:
    """
    Load map from arguments.

    Supports both legacy single-file format and Phase II multi-layer format.

    Args:
        args: Parsed arguments

    Returns:
        MultiLayerMap

    Raises:
        LayerValidationError: If map is invalid
        FileNotFoundError: If file not found
    """
    map_path = Path(args.map_file)

    if not map_path.exists():
        raise FileNotFoundError(f"Map file not found: {args.map_file}")

    if args.elevation:
        elevation_path = Path(args.elevation)
        if not elevation_path.exists():
            raise FileNotFoundError(f"Elevation file not found: {args.elevation}")

        priority_path = Path(args.priority) if args.priority else None

        return load_multi_layer_map(
            terrain_path=map_path,
            elevation_path=elevation_path,
            priority_path=priority_path,
        )
    else:
        with open(map_path, 'r', encoding='utf-8') as f:
            return load_multi_layer_map(legacy_text=f)


def render_path_v2(game_map: MultiLayerMap, path: Sequence[tuple[int, int]]) -> str:
    """
    Render path on map.

    Args:
        game_map: Multi-layer map
        path: Path to render

    Returns:
        String visualization
    """
    from src.map_loader import GameMap

    legacy_map = GameMap(
        grid=game_map.terrain,
        start=game_map.start,
        goal=game_map.goal,
        width=game_map.width,
        height=game_map.height,
    )
    return render_path(legacy_map, path)


def format_metrics_v2(result: FinderResult) -> str:
    """
    Format detailed metrics.

    Args:
        result: Finder result

    Returns:
        Formatted metrics string
    """
    lines = [
        f"Algorithm: {result.algorithm.value.upper()}",
        f"Total cost: {result.total_cost:.3f}",
        f"Path length: {len(result.path)} nodes",
        f"Nodes expanded: {result.nodes_expanded}",
        f"Execution time: {result.execution_time * 1000:.3f} ms",
    ]
    return '\n'.join(lines)


def format_comparison_v2(dijkstra: FinderResult, astar: FinderResult) -> str:
    """
    Format comparison between algorithms.

    Args:
        dijkstra: Dijkstra result
        astar: A* result

    Returns:
        Formatted comparison string
    """
    lines = [
        "=== Algorithm Comparison ===",
        f"Dijkstra: Cost={dijkstra.total_cost:.3f}, Expanded={dijkstra.nodes_expanded}, Time={dijkstra.execution_time * 1000:.3f}ms",
        f"A*:       Cost={astar.total_cost:.3f}, Expanded={astar.nodes_expanded}, Time={astar.execution_time * 1000:.3f}ms",
    ]

    if dijkstra.total_cost != astar.total_cost:
        lines.append(f"Note: Cost difference = {abs(dijkstra.total_cost - astar.total_cost):.6f}")

    if astar.nodes_expanded < dijkstra.nodes_expanded:
        savings = (1 - astar.nodes_expanded / dijkstra.nodes_expanded) * 100
        lines.append(f"A* expanded {savings:.1f}% fewer nodes")

    return '\n'.join(lines)


def run(args: argparse.Namespace) -> int:
    """
    Run the path search.

    Args:
        args: Parsed arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        game_map = load_map(args)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except LayerValidationError as e:
        print(f"Error: Invalid map: {e}", file=sys.stderr)
        return 1

    cost_config = CostConfig(
        priority_weight=args.priority_weight,
        max_cost_cap=args.max_cost_cap,
    )

    if args.compare:
        return run_compare_mode(game_map, args, cost_config)

    algorithm = FinderAlgorithm.DIJKSTRA if args.algo == 'dijkstra' else FinderAlgorithm.ASTAR

    try:
        result = find_path(
            game_map,
            algorithm,
            allow_diagonal=args.allow_diagonal,
            cost_config=cost_config,
        )
    except NoPathFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    visualization = render_path_v2(game_map, result.path)
    print(visualization)

    if args.metrics:
        print()
        print(format_metrics_v2(result))

    return 0


def run_compare_mode(
    game_map: MultiLayerMap,
    args: argparse.Namespace,
    cost_config: CostConfig,
) -> int:
    """
    Run in comparison mode, executing both Dijkstra and A*.

    Args:
        game_map: The loaded game map
        args: Parsed arguments
        cost_config: Cost configuration

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        dijkstra_result = find_path(
            game_map,
            FinderAlgorithm.DIJKSTRA,
            allow_diagonal=args.allow_diagonal,
            cost_config=cost_config,
        )
        astar_result = find_path(
            game_map,
            FinderAlgorithm.ASTAR,
            allow_diagonal=args.allow_diagonal,
            cost_config=cost_config,
        )
    except NoPathFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print("=== Dijkstra Path ===")
    print(render_path_v2(game_map, dijkstra_result.path))
    print()

    print("=== A* Path ===")
    print(render_path_v2(game_map, astar_result.path))
    print()

    if args.metrics:
        print(format_comparison_v2(dijkstra_result, astar_result))

    return 0


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    args = parse_args(sys.argv[1:])
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
