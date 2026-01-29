"""Tests for graph_builder module."""
import pytest
from io import StringIO
import networkx as nx
from src.map_loader import load_map
from src.graph_builder import build_graph


class TestBuildGraph:
    """Tests for build_graph function."""

    def test_simple_map_creates_graph(self) -> None:
        """Simple map should create a valid graph."""
        map_text = "SG\n.."
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 4

    def test_wall_excluded_from_graph(self) -> None:
        """Wall cells should not be included in the graph."""
        map_text = "S#G\n..."
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        assert (1, 0) not in graph.nodes()
        assert (0, 0) in graph.nodes()
        assert (2, 0) in graph.nodes()

    def test_four_neighbors_adjacency(self) -> None:
        """Center cell should have 4 neighbors (up, down, left, right)."""
        map_text = "...\n.S.\n..G"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        center = (1, 1)
        neighbors = list(graph.neighbors(center))

        assert len(neighbors) == 4
        assert (0, 1) in neighbors  # left
        assert (2, 1) in neighbors  # right
        assert (1, 0) in neighbors  # up
        assert (1, 2) in neighbors  # down

    def test_no_diagonal_neighbors(self) -> None:
        """Diagonal cells should not be connected."""
        map_text = "S.\n.G"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        assert not graph.has_edge((0, 0), (1, 1))
        assert not graph.has_edge((1, 0), (0, 1))

    def test_edge_weight_is_one(self) -> None:
        """All edges should have weight 1."""
        map_text = "SG\n.."
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        for u, v, data in graph.edges(data=True):
            assert data.get('weight', 1) == 1

    def test_undirected_graph(self) -> None:
        """Graph should be undirected."""
        map_text = "SG\n.."
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        assert not graph.is_directed()

    def test_wall_blocks_connection(self) -> None:
        """Wall should block connections between adjacent cells."""
        map_text = "S#G"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        assert not graph.has_edge((0, 0), (2, 0))

    def test_start_and_goal_in_graph(self) -> None:
        """Start and Goal positions should be in the graph."""
        map_text = "S...#\n.#.#.\n.#.G."
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        assert game_map.start in graph.nodes()
        assert game_map.goal in graph.nodes()
