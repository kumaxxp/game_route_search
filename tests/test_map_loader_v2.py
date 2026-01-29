"""Tests for multi-layer map loader (Phase II)."""
import pytest
from io import StringIO
from pathlib import Path
from src.map_loader_v2 import (
    load_multi_layer_map,
    load_terrain_layer,
    load_elevation_layer,
    load_points_layer,
    load_priority_layer,
    MultiLayerMap,
    LayerValidationError,
)


class TestLoadTerrainLayer:
    """Tests for terrain layer loading."""

    def test_load_valid_terrain(self) -> None:
        """Valid terrain should be loaded."""
        terrain_text = "..F\n~=.\n^s#"
        result = load_terrain_layer(StringIO(terrain_text))

        assert result[0][0] == '.'
        assert result[0][2] == 'F'
        assert result[1][0] == '~'
        assert result[1][1] == '='
        assert result[2][0] == '^'
        assert result[2][1] == 's'
        assert result[2][2] == '#'

    def test_invalid_terrain_code(self) -> None:
        """Unknown terrain code should raise error."""
        terrain_text = "..X\n..."
        with pytest.raises(LayerValidationError, match="[Uu]nknown|[Ii]nvalid"):
            load_terrain_layer(StringIO(terrain_text))

    def test_non_rectangular_terrain(self) -> None:
        """Non-rectangular terrain should raise error."""
        terrain_text = "..\n..."
        with pytest.raises(LayerValidationError, match="[Rr]ectangular|[Ss]ize"):
            load_terrain_layer(StringIO(terrain_text))


class TestLoadElevationLayer:
    """Tests for elevation layer loading."""

    def test_load_valid_elevation(self) -> None:
        """Valid elevation data should be loaded."""
        elevation_text = "0 0 1\n0 1 2\n1 2 3"
        result = load_elevation_layer(StringIO(elevation_text))

        assert result[0][0] == 0
        assert result[0][2] == 1
        assert result[1][1] == 1
        assert result[2][2] == 3

    def test_negative_elevation(self) -> None:
        """Negative elevation should be supported."""
        elevation_text = "0 -1\n-2 0"
        result = load_elevation_layer(StringIO(elevation_text))

        assert result[0][1] == -1
        assert result[1][0] == -2

    def test_invalid_elevation_format(self) -> None:
        """Non-integer elevation should raise error."""
        elevation_text = "0 a\n1 2"
        with pytest.raises(LayerValidationError, match="[Ii]nteger|[Ff]ormat"):
            load_elevation_layer(StringIO(elevation_text))


class TestLoadPointsLayer:
    """Tests for points layer loading."""

    def test_load_points_from_terrain(self) -> None:
        """S/G in terrain should be detected."""
        terrain = [['S', '.', '.'], ['.', '.', 'G']]
        start, goal = load_points_layer(terrain_grid=terrain)

        assert start == (0, 0)
        assert goal == (2, 1)

    def test_load_points_from_file(self) -> None:
        """Points from separate file should be loaded."""
        points_text = "S 1 2\nG 5 3"
        start, goal = load_points_layer(points_file=StringIO(points_text))

        assert start == (1, 2)
        assert goal == (5, 3)

    def test_missing_start(self) -> None:
        """Missing start should raise error."""
        terrain = [['.', '.'], ['.', 'G']]
        with pytest.raises(LayerValidationError, match="[Ss]tart"):
            load_points_layer(terrain_grid=terrain)

    def test_missing_goal(self) -> None:
        """Missing goal should raise error."""
        terrain = [['S', '.'], ['.', '.']]
        with pytest.raises(LayerValidationError, match="[Gg]oal"):
            load_points_layer(terrain_grid=terrain)


class TestLoadPriorityLayer:
    """Tests for priority layer loading."""

    def test_load_valid_priority(self) -> None:
        """Valid priority data should be loaded."""
        priority_text = "0.0 1.5\n2.0 0.5"
        result = load_priority_layer(StringIO(priority_text))

        assert result[0][0] == 0.0
        assert result[0][1] == 1.5
        assert result[1][0] == 2.0

    def test_default_priority_zero(self) -> None:
        """Default priority should be zero when no file provided."""
        result = load_priority_layer(None, width=2, height=2)

        assert all(result[y][x] == 0.0 for y in range(2) for x in range(2))


class TestMultiLayerMap:
    """Tests for MultiLayerMap structure."""

    def test_phase2_map_loading(self, tmp_path: Path) -> None:
        """Phase II format with separate layers should work."""
        terrain_file = tmp_path / "terrain.txt"
        elevation_file = tmp_path / "elevation.txt"

        terrain_file.write_text("S.=\n.F.\n~.G")
        elevation_file.write_text("0 0 0\n0 1 1\n0 1 0")

        result = load_multi_layer_map(
            terrain_path=terrain_file,
            elevation_path=elevation_file,
        )

        assert result.width == 3
        assert result.height == 3
        assert result.start == (0, 0)
        assert result.goal == (2, 2)
        assert result.terrain[1][1] == 'F'
        assert result.elevation[1][1] == 1

    def test_size_mismatch_error(self, tmp_path: Path) -> None:
        """Mismatched layer sizes should raise error."""
        terrain_file = tmp_path / "terrain.txt"
        elevation_file = tmp_path / "elevation.txt"

        terrain_file.write_text("S..\n..G")
        elevation_file.write_text("0 0 0\n0 0 0\n0 0 0")

        with pytest.raises(LayerValidationError, match="[Ss]ize|[Mm]ismatch"):
            load_multi_layer_map(
                terrain_path=terrain_file,
                elevation_path=elevation_file,
            )


class TestPhaseICompatibility:
    """Tests for Phase I backward compatibility."""

    def test_legacy_format_with_sg(self) -> None:
        """Legacy S/G/./# format should work."""
        legacy_text = "S..#\n.#..\n...G"
        result = load_multi_layer_map(legacy_text=StringIO(legacy_text))

        assert result.start == (0, 0)
        assert result.goal == (3, 2)
        assert result.terrain[0][3] == '#'
        # All elevations should be 0
        assert all(result.elevation[y][x] == 0 for y in range(3) for x in range(4))
        # All priorities should be 0
        assert all(result.priority[y][x] == 0.0 for y in range(3) for x in range(4))

    def test_legacy_simple_path(self) -> None:
        """Simple legacy map should load correctly."""
        legacy_text = "SG"
        result = load_multi_layer_map(legacy_text=StringIO(legacy_text))

        assert result.width == 2
        assert result.height == 1
        assert result.start == (0, 0)
        assert result.goal == (1, 0)


class TestTerrainCodesFromSpec:
    """Tests for all terrain codes from specification."""

    @pytest.mark.parametrize("code,expected_passable", [
        ('.', True),   # plain
        ('~', True),   # shallow water
        ('F', True),   # forest
        ('^', True),   # cliff
        ('s', True),   # sand
        ('=', True),   # paved
        ('#', False),  # wall
        ('S', True),   # start
        ('G', True),   # goal
    ])
    def test_terrain_code_validity(self, code: str, expected_passable: bool) -> None:
        """All spec terrain codes should be valid."""
        terrain_text = f"S{code}G" if code not in ('S', 'G') else "S.G"
        if code == 'S':
            terrain_text = "SG."
        elif code == 'G':
            terrain_text = "S.G"

        result = load_terrain_layer(StringIO(terrain_text))
        assert result is not None
