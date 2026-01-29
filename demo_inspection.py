#!/usr/bin/env python3
"""大本営視察用デモンストレーション - 経路探索システム実演.

演習条件:
- マップ構成: 10x10 Isometricグリッド
- 地形配置: 中央に水辺（高コスト）および段差（高度差）
- 探索任務: 始点 (0,0) → 終点 (9,9)
"""
from src.map_loader_v2 import MultiLayerMap
from src.finder import find_path, FinderAlgorithm
from src.cost_function import CostConfig
from src.coordinates import (
    GridCoord, IsoCoord, IsoConfig, to_iso, to_iso_int, to_grid
)


def create_inspection_map() -> tuple[MultiLayerMap, list[list[str]], list[list[int]]]:
    """Create 10x10 inspection map with water and elevation obstacles."""

    # 地形マップ (10x10)
    # S = Start, G = Goal
    # ~ = 水辺 (shallow water, high cost)
    # ^ = 崖 (cliff, very high ascent cost)
    # = = 舗装路 (paved, low cost)
    # . = 平地 (plain, normal cost)
    # F = 森林 (forest, medium cost)
    terrain = [
        ['S', '.', '.', '.', 'F', 'F', '.', '.', '.', '.'],  # Row 0
        ['.', '.', '.', '.', 'F', 'F', '.', '.', '.', '.'],  # Row 1
        ['.', '.', '~', '~', '~', '~', '~', '~', '.', '.'],  # Row 2 - 水辺帯
        ['.', '.', '~', '~', '~', '~', '~', '~', '.', '.'],  # Row 3 - 水辺帯
        ['.', '.', '^', '^', '^', '^', '^', '^', '.', '.'],  # Row 4 - 崖
        ['.', '.', '^', '^', '^', '^', '^', '^', '.', '.'],  # Row 5 - 崖
        ['.', '.', '.', '.', '=', '=', '.', '.', '.', '.'],  # Row 6 - 舗装路
        ['.', '.', '.', '.', '=', '=', '.', '.', '.', '.'],  # Row 7 - 舗装路
        ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],  # Row 8
        ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'G'],  # Row 9
    ]

    # 高度マップ (10x10)
    # 崖エリアは高度5、その他は0
    elevation = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Row 0
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Row 1
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Row 2
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Row 3
        [0, 0, 5, 5, 5, 5, 5, 5, 0, 0],  # Row 4 - 崖上
        [0, 0, 5, 5, 5, 5, 5, 5, 0, 0],  # Row 5 - 崖上
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Row 6
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Row 7
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Row 8
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Row 9
    ]

    # Priority (all zero for this demo)
    priority = [[0.0] * 10 for _ in range(10)]

    game_map = MultiLayerMap(
        terrain=terrain,
        elevation=elevation,
        priority=priority,
        start=(0, 0),
        goal=(9, 9),
        width=10,
        height=10,
    )

    return game_map, terrain, elevation


def print_terrain_legend() -> None:
    """Print terrain legend."""
    print("=" * 60)
    print("【地形凡例 (Terrain Legend)】")
    print("-" * 60)
    print("  S  = 始点 (Start)")
    print("  G  = 終点 (Goal)")
    print("  .  = 平地 (Plain)      - 基本コスト 1.0")
    print("  ~  = 水辺 (Water)      - 基本コスト 3.0 [高コスト]")
    print("  ^  = 崖   (Cliff)      - 基本コスト 5.0, 上昇コスト 10.0/段 [超高コスト]")
    print("  =  = 舗装 (Paved)      - 基本コスト 0.8 [低コスト]")
    print("  F  = 森林 (Forest)     - 基本コスト 2.0")
    print("  @  = 選択経路 (Selected Path)")
    print("=" * 60)


def print_map_layers(terrain: list[list[str]], elevation: list[list[int]]) -> None:
    """Print terrain and elevation maps side by side."""
    print("\n【マップレイヤー (Map Layers)】")
    print("-" * 60)

    print("\n[地形レイヤー (Terrain Layer)]")
    print("     ", end="")
    for x in range(10):
        print(f" {x}", end="")
    print()
    print("    +" + "-" * 21 + "+")
    for y, row in enumerate(terrain):
        print(f"  {y} |", end="")
        for cell in row:
            print(f" {cell}", end="")
        print(" |")
    print("    +" + "-" * 21 + "+")

    print("\n[高度レイヤー (Elevation Layer)]")
    print("     ", end="")
    for x in range(10):
        print(f" {x}", end="")
    print()
    print("    +" + "-" * 21 + "+")
    for y, row in enumerate(elevation):
        print(f"  {y} |", end="")
        for cell in row:
            print(f" {cell}", end="")
        print(" |")
    print("    +" + "-" * 21 + "+")


def print_coordinate_transformations(path: list[tuple[int, int]], elevation: list[list[int]]) -> None:
    """Print coordinate transformation log for each step."""
    print("\n【座標変換ログ (Coordinate Transformation Log)】")
    print("-" * 80)
    print(f"{'Step':>4} | {'論理座標':^12} | {'高度':^4} | {'Isometric座標(float)':^24} | {'Isometric座標(int)':^18}")
    print("-" * 80)

    config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)

    for i, (x, y) in enumerate(path):
        h = elevation[y][x]
        grid = GridCoord(x, y, h)
        iso = to_iso(grid, config)
        iso_int = to_iso_int(grid, config)

        print(f"{i:>4} | ({x:>3}, {y:>3})    | {h:>4} | ({iso.x:>9.2f}, {iso.y:>9.2f}) | ({iso_int.x:>6}, {iso_int.y:>6})")

    print("-" * 80)


def print_roundtrip_verification(path: list[tuple[int, int]], elevation: list[list[int]]) -> None:
    """Verify round-trip transformation accuracy."""
    print("\n【往復変換検証 (Round-trip Verification)】")
    print("-" * 60)

    config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
    max_error_x = 0.0
    max_error_y = 0.0

    for x, y in path:
        h = elevation[y][x]
        grid_original = GridCoord(x, y, h)
        iso = to_iso(grid_original, config)
        grid_recovered = to_grid(iso, h, config)
        iso_recovered = to_iso(grid_recovered, config)

        error_x = abs(iso_recovered.x - iso.x)
        error_y = abs(iso_recovered.y - iso.y)
        max_error_x = max(max_error_x, error_x)
        max_error_y = max(max_error_y, error_y)

    print(f"往復変換最大誤差 X: {max_error_x:.6f} px")
    print(f"往復変換最大誤差 Y: {max_error_y:.6f} px")
    print(f"仕様要求 (≤ 0.5 px): {'✓ 合格' if max_error_x <= 0.5 and max_error_y <= 0.5 else '✗ 不合格'}")
    print("-" * 60)


def visualize_path(terrain: list[list[str]], path: list[tuple[int, int]]) -> None:
    """Visualize path on terrain map."""
    print("\n【経路可視化 (Path Visualization)】")
    print("-" * 60)

    # Create a copy of terrain for visualization
    viz = [row.copy() for row in terrain]

    # Mark path with '@' (except S and G)
    for x, y in path:
        if viz[y][x] not in ('S', 'G'):
            viz[y][x] = '@'

    print("     ", end="")
    for x in range(10):
        print(f" {x}", end="")
    print()
    print("    +" + "-" * 21 + "+")
    for y, row in enumerate(viz):
        print(f"  {y} |", end="")
        for cell in row:
            print(f" {cell}", end="")
        print(" |")
    print("    +" + "-" * 21 + "+")


def analyze_path_decisions(path: list[tuple[int, int]], terrain: list[list[str]], elevation: list[list[int]]) -> None:
    """Analyze path decisions - what was avoided and why."""
    print("\n【経路判断分析 (Path Decision Analysis)】")
    print("-" * 60)

    # Check what terrains were traversed
    terrain_counts = {}
    for x, y in path:
        t = terrain[y][x]
        terrain_counts[t] = terrain_counts.get(t, 0) + 1

    print("通過した地形:")
    terrain_names = {
        'S': '始点', 'G': '終点', '.': '平地', '~': '水辺',
        '^': '崖', '=': '舗装路', 'F': '森林', '@': '経路'
    }
    for t, count in sorted(terrain_counts.items()):
        print(f"  {terrain_names.get(t, t)}: {count}マス")

    # Check what was avoided
    print("\n回避判断:")
    water_avoided = all(terrain[y][x] != '~' for x, y in path)
    cliff_avoided = all(terrain[y][x] != '^' for x, y in path)

    print(f"  水辺 (~) 回避: {'✓ 成功' if water_avoided else '✗ 通過あり'}")
    print(f"  崖   (^) 回避: {'✓ 成功' if cliff_avoided else '✗ 通過あり'}")

    # Check elevation changes
    max_ascent = 0
    max_descent = 0
    for i in range(1, len(path)):
        prev_x, prev_y = path[i-1]
        curr_x, curr_y = path[i]
        delta_h = elevation[curr_y][curr_x] - elevation[prev_y][prev_x]
        if delta_h > 0:
            max_ascent = max(max_ascent, delta_h)
        else:
            max_descent = max(max_descent, -delta_h)

    print(f"\n高度変化:")
    print(f"  最大上昇: {max_ascent} 段")
    print(f"  最大下降: {max_descent} 段")
    print("-" * 60)


def run_algorithm_comparison(game_map: MultiLayerMap) -> None:
    """Compare Dijkstra and A* algorithms."""
    print("\n【アルゴリズム比較 (Algorithm Comparison)】")
    print("-" * 60)

    config = CostConfig()

    dijkstra_result = find_path(game_map, FinderAlgorithm.DIJKSTRA, cost_config=config)
    astar_result = find_path(game_map, FinderAlgorithm.ASTAR, cost_config=config)

    print(f"{'指標':^20} | {'Dijkstra':^15} | {'A*':^15}")
    print("-" * 60)
    print(f"{'総コスト':^20} | {dijkstra_result.total_cost:^15.3f} | {astar_result.total_cost:^15.3f}")
    print(f"{'経路長':^20} | {len(dijkstra_result.path):^15} | {len(astar_result.path):^15}")
    print(f"{'展開ノード数':^20} | {dijkstra_result.nodes_expanded:^15} | {astar_result.nodes_expanded:^15}")
    print(f"{'実行時間 (ms)':^20} | {dijkstra_result.execution_time*1000:^15.3f} | {astar_result.execution_time*1000:^15.3f}")

    if dijkstra_result.total_cost == astar_result.total_cost:
        print("\n✓ 両アルゴリズムが同一の最適コストを発見")

    if astar_result.nodes_expanded < dijkstra_result.nodes_expanded:
        savings = (1 - astar_result.nodes_expanded / dijkstra_result.nodes_expanded) * 100
        print(f"✓ A* は Dijkstra より {savings:.1f}% 少ないノードで探索完了")

    print("-" * 60)

    return dijkstra_result


def main() -> None:
    """Run inspection demonstration."""
    print("=" * 80)
    print(" 大本営視察用デモンストレーション - ゲーム経路探索シミュレーター")
    print(" Inspection Demonstration - Game Route Search Simulator")
    print("=" * 80)

    # Create map
    game_map, terrain, elevation = create_inspection_map()

    # Print legend
    print_terrain_legend()

    # Print map layers
    print_map_layers(terrain, elevation)

    # Run pathfinding comparison
    result = run_algorithm_comparison(game_map)

    # Print path coordinates
    print("\n【選択経路座標リスト (Selected Path Coordinates)】")
    print("-" * 60)
    print(f"経路: {result.path}")
    print(f"総ステップ数: {len(result.path)}")
    print("-" * 60)

    # Visualize path
    visualize_path(terrain, result.path)

    # Coordinate transformations
    print_coordinate_transformations(result.path, elevation)

    # Round-trip verification
    print_roundtrip_verification(result.path, elevation)

    # Path decision analysis
    analyze_path_decisions(result.path, terrain, elevation)

    print("\n" + "=" * 80)
    print(" 視察完了 - Inspection Complete")
    print("=" * 80)


if __name__ == '__main__':
    main()
