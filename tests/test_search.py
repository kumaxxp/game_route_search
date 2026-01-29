"""Tests for search module."""
import pytest
from io import StringIO
from src.map_loader import load_map
from src.graph_builder import build_graph
from src.search import search_path, SearchResult, NoPathError, Algorithm


class TestSearchPath:
    """Tests for search_path function."""

    def test_simple_path_astar(self) -> None:
        """A* should find path in simple map."""
        map_text = "SG"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        result = search_path(graph, game_map.start, game_map.goal, Algorithm.ASTAR)

        assert result.path == [(0, 0), (1, 0)]
        assert result.algorithm == Algorithm.ASTAR
        assert result.path_length == 2

    def test_simple_path_bfs(self) -> None:
        """BFS should find path in simple map."""
        map_text = "SG"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        result = search_path(graph, game_map.start, game_map.goal, Algorithm.BFS)

        assert result.path == [(0, 0), (1, 0)]
        assert result.algorithm == Algorithm.BFS
        assert result.path_length == 2

    def test_longer_path(self) -> None:
        """Should find correct path through maze."""
        map_text = "S...#\n.#.#.\n.#.G."
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        result = search_path(graph, game_map.start, game_map.goal, Algorithm.ASTAR)

        assert result.path[0] == (0, 0)
        assert result.path[-1] == (3, 2)
        assert result.path_length == 6

    def test_astar_and_bfs_same_length(self) -> None:
        """A* and BFS should find paths of same length."""
        map_text = "S...#\n.#.#.\n.#.G."
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        astar_result = search_path(graph, game_map.start, game_map.goal, Algorithm.ASTAR)
        bfs_result = search_path(graph, game_map.start, game_map.goal, Algorithm.BFS)

        assert astar_result.path_length == bfs_result.path_length

    def test_no_path_raises_error(self) -> None:
        """Should raise NoPathError when no path exists."""
        map_text = "S#G"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        with pytest.raises(NoPathError, match="[Nn]o path|到達"):
            search_path(graph, game_map.start, game_map.goal, Algorithm.ASTAR)

    def test_no_path_bfs_raises_error(self) -> None:
        """BFS should also raise NoPathError when no path exists."""
        map_text = "S#G"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        with pytest.raises(NoPathError, match="[Nn]o path|到達"):
            search_path(graph, game_map.start, game_map.goal, Algorithm.BFS)

    def test_execution_time_recorded(self) -> None:
        """Search should record execution time."""
        map_text = "SG"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        result = search_path(graph, game_map.start, game_map.goal, Algorithm.ASTAR)

        assert result.execution_time >= 0

    def test_path_includes_start_and_goal(self) -> None:
        """Path should include both start and goal positions."""
        map_text = "S..G"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        result = search_path(graph, game_map.start, game_map.goal, Algorithm.ASTAR)

        assert result.path[0] == game_map.start
        assert result.path[-1] == game_map.goal


class TestManhattanDistance:
    """Tests for Manhattan distance heuristic."""

    def test_astar_uses_manhattan_distance(self) -> None:
        """A* should use Manhattan distance heuristic for optimal path."""
        map_text = "S....\n.....\n....G"
        game_map = load_map(StringIO(map_text))
        graph = build_graph(game_map)

        result = search_path(graph, game_map.start, game_map.goal, Algorithm.ASTAR)

        expected_length = abs(4 - 0) + abs(2 - 0) + 1
        assert result.path_length == expected_length
