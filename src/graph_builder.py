"""Graph building module for map representation."""
import networkx as nx
from src.map_loader import GameMap


DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]


def is_passable(char: str) -> bool:
    """
    Check if a cell is passable (not a wall).

    Args:
        char: Character representing the cell

    Returns:
        True if passable, False if wall
    """
    return char != '#'


def build_graph(game_map: GameMap) -> nx.Graph:
    """
    Build a NetworkX graph from a GameMap.

    Creates an undirected graph where:
    - Nodes are (x, y) coordinates of passable cells
    - Edges connect 4-adjacent passable cells (no diagonals)
    - All edges have weight 1

    Args:
        game_map: Validated GameMap object

    Returns:
        NetworkX Graph representing the map
    """
    graph: nx.Graph = nx.Graph()
    grid = game_map.grid
    height = game_map.height
    width = game_map.width

    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            if not is_passable(cell):
                continue

            graph.add_node((x, y))

            for dx, dy in DIRECTIONS:
                nx_coord = x + dx
                ny_coord = y + dy

                if 0 <= nx_coord < width and 0 <= ny_coord < height:
                    neighbor_cell = grid[ny_coord][nx_coord]
                    if is_passable(neighbor_cell):
                        graph.add_edge((x, y), (nx_coord, ny_coord), weight=1)

    return graph
