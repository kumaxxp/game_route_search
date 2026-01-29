"""Tests for map_loader module."""
import pytest
from io import StringIO
from src.map_loader import load_map, validate_map, MapValidationError


class TestLoadMap:
    """Tests for load_map function."""

    def test_load_valid_map_from_string(self) -> None:
        """Valid map should be loaded correctly."""
        map_text = "S...#\n.#.#.\n.#.G."
        result = load_map(StringIO(map_text))

        assert result.grid == [
            ['S', '.', '.', '.', '#'],
            ['.', '#', '.', '#', '.'],
            ['.', '#', '.', 'G', '.'],
        ]
        assert result.start == (0, 0)
        assert result.goal == (3, 2)
        assert result.width == 5
        assert result.height == 3

    def test_load_simple_map(self) -> None:
        """Simple 2x2 map should work."""
        map_text = "SG\n.."
        result = load_map(StringIO(map_text))

        assert result.start == (0, 0)
        assert result.goal == (1, 0)
        assert result.width == 2
        assert result.height == 2


class TestValidateMap:
    """Tests for map validation."""

    def test_non_rectangular_map_raises_error(self) -> None:
        """Non-rectangular map should raise error."""
        map_text = "S...\n.#\n.#.G."
        with pytest.raises(MapValidationError, match="non-rectangular|矩形"):
            load_map(StringIO(map_text))

    def test_unknown_character_raises_error(self) -> None:
        """Unknown character should raise error."""
        map_text = "S..X\n.#.G"
        with pytest.raises(MapValidationError, match="unknown|未知|invalid"):
            load_map(StringIO(map_text))

    def test_missing_start_raises_error(self) -> None:
        """Missing start should raise error."""
        map_text = "....\n.#.G"
        with pytest.raises(MapValidationError, match="[Ss]tart|S"):
            load_map(StringIO(map_text))

    def test_missing_goal_raises_error(self) -> None:
        """Missing goal should raise error."""
        map_text = "S...\n.#.."
        with pytest.raises(MapValidationError, match="[Gg]oal|G"):
            load_map(StringIO(map_text))

    def test_duplicate_start_raises_error(self) -> None:
        """Duplicate start should raise error."""
        map_text = "S..S\n.#.G"
        with pytest.raises(MapValidationError, match="[Dd]uplicate|重複|[Mm]ultiple"):
            load_map(StringIO(map_text))

    def test_duplicate_goal_raises_error(self) -> None:
        """Duplicate goal should raise error."""
        map_text = "S..G\n.#.G"
        with pytest.raises(MapValidationError, match="[Dd]uplicate|重複|[Mm]ultiple"):
            load_map(StringIO(map_text))

    def test_empty_map_raises_error(self) -> None:
        """Empty map should raise error."""
        map_text = ""
        with pytest.raises(MapValidationError, match="empty|空"):
            load_map(StringIO(map_text))

    def test_all_valid_characters(self) -> None:
        """All valid characters (S, G, #, .) should be accepted."""
        map_text = "S.#\n..G"
        result = load_map(StringIO(map_text))
        assert result is not None
