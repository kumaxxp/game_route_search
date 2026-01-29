"""Tests for visualize module."""
import pytest
from io import StringIO
from src.map_loader import load_map
from src.visualize import render_path


class TestRenderPath:
    """Tests for render_path function."""

    def test_simple_path_visualization(self) -> None:
        """Simple path should be visualized correctly."""
        map_text = "SG"
        game_map = load_map(StringIO(map_text))
        path = [(0, 0), (1, 0)]

        result = render_path(game_map, path)

        assert result == "SG"

    def test_road_replaced_with_at_sign(self) -> None:
        """Road cells on path should be replaced with '@'."""
        map_text = "S.G"
        game_map = load_map(StringIO(map_text))
        path = [(0, 0), (1, 0), (2, 0)]

        result = render_path(game_map, path)

        assert result == "S@G"

    def test_start_preserved(self) -> None:
        """Start 'S' should be preserved."""
        map_text = "S..G"
        game_map = load_map(StringIO(map_text))
        path = [(0, 0), (1, 0), (2, 0), (3, 0)]

        result = render_path(game_map, path)

        assert result[0] == 'S'

    def test_goal_preserved(self) -> None:
        """Goal 'G' should be preserved."""
        map_text = "S..G"
        game_map = load_map(StringIO(map_text))
        path = [(0, 0), (1, 0), (2, 0), (3, 0)]

        result = render_path(game_map, path)

        assert result[-1] == 'G'

    def test_wall_preserved(self) -> None:
        """Wall '#' should be preserved."""
        map_text = "S#.G\n....\n...."
        game_map = load_map(StringIO(map_text))
        path = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (3, 0)]

        result = render_path(game_map, path)
        lines = result.split('\n')

        assert lines[0][1] == '#'

    def test_multiline_visualization(self) -> None:
        """Multiline map should be visualized correctly."""
        map_text = "S...#\n.#.#.\n.#.G."
        game_map = load_map(StringIO(map_text))
        path = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2)]

        result = render_path(game_map, path)
        lines = result.split('\n')

        assert len(lines) == 3
        assert lines[0] == "S@@.#"
        assert lines[1] == ".#@#."
        assert lines[2] == ".#@G."

    def test_spec_example(self) -> None:
        """Example from specification should work correctly."""
        map_text = "S...#\n.#.#.\n.#.G."
        game_map = load_map(StringIO(map_text))
        path = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2)]

        result = render_path(game_map, path)
        expected = "S@@.#\n.#@#.\n.#@G."

        assert result == expected

    def test_non_path_cells_unchanged(self) -> None:
        """Cells not on path should remain unchanged."""
        map_text = "S..\n...\n..G"
        game_map = load_map(StringIO(map_text))
        path = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]

        result = render_path(game_map, path)
        lines = result.split('\n')

        assert lines[0][2] == '.'
        assert lines[1][1] == '.'
        assert lines[1][2] == '.'
