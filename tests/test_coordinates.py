"""Tests for coordinate transformation layer."""
import pytest
import math
from src.coordinates import (
    to_iso,
    to_grid,
    IsoConfig,
    IsoCoord,
    GridCoord,
)


class TestIsoConfig:
    """Tests for isometric configuration."""

    def test_default_config(self) -> None:
        """Default config should have reasonable values."""
        config = IsoConfig()
        assert config.tile_width > 0
        assert config.tile_height > 0
        assert config.elevation_scale > 0

    def test_custom_config(self) -> None:
        """Custom config values should be used."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        assert config.tile_width == 64
        assert config.tile_height == 32
        assert config.elevation_scale == 16


class TestToIso:
    """Tests for to_iso conversion (logical grid -> isometric)."""

    def test_origin_conversion(self) -> None:
        """Origin (0,0,0) should map to (0,0)."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        result = to_iso(GridCoord(0, 0, 0), config)
        assert result.x == 0
        assert result.y == 0

    def test_x_axis_movement(self) -> None:
        """Moving along x-axis should increase X and Y in iso."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        result = to_iso(GridCoord(1, 0, 0), config)
        # X = (64/2)(1-0) = 32
        # Y = (32/2)(1+0) = 16
        assert result.x == 32
        assert result.y == 16

    def test_y_axis_movement(self) -> None:
        """Moving along y-axis should decrease X and increase Y in iso."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        result = to_iso(GridCoord(0, 1, 0), config)
        # X = (64/2)(0-1) = -32
        # Y = (32/2)(0+1) = 16
        assert result.x == -32
        assert result.y == 16

    def test_elevation_effect(self) -> None:
        """Elevation should decrease Y coordinate."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        result_h0 = to_iso(GridCoord(1, 1, 0), config)
        result_h1 = to_iso(GridCoord(1, 1, 1), config)
        # With elevation, Y should be lower (visually higher)
        assert result_h1.y < result_h0.y
        assert result_h1.y == result_h0.y - 16

    def test_formula_correctness(self) -> None:
        """Verify exact formula: X = (tw/2)(x-y), Y = (th/2)(x+y) - β*h."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        x, y, h = 3, 2, 1
        result = to_iso(GridCoord(x, y, h), config)

        expected_x = (config.tile_width / 2) * (x - y)
        expected_y = (config.tile_height / 2) * (x + y) - config.elevation_scale * h

        assert result.x == expected_x
        assert result.y == expected_y


class TestToGrid:
    """Tests for to_grid conversion (isometric -> logical grid)."""

    def test_origin_conversion(self) -> None:
        """Iso origin should map back to grid origin."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        result = to_grid(IsoCoord(0, 0), 0, config)
        assert result.x == 0
        assert result.y == 0

    def test_basic_conversion(self) -> None:
        """Basic iso coordinates should convert back correctly."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        # Iso coords for grid (1, 0, 0)
        result = to_grid(IsoCoord(32, 16), 0, config)
        assert result.x == 1
        assert result.y == 0

    def test_with_elevation(self) -> None:
        """Conversion with known elevation should be accurate."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        # Grid (1, 1, 2) -> Iso
        iso = to_iso(GridCoord(1, 1, 2), config)
        # Convert back with known elevation
        grid = to_grid(iso, 2, config)
        assert grid.x == 1
        assert grid.y == 1


class TestRoundTrip:
    """Tests for round-trip conversion accuracy."""

    def test_roundtrip_iso_grid_iso(self) -> None:
        """iso -> grid -> iso should have bounded error."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        original_grid = GridCoord(5, 3, 2)

        iso = to_iso(original_grid, config)
        recovered_grid = to_grid(iso, original_grid.h, config)
        recovered_iso = to_iso(GridCoord(recovered_grid.x, recovered_grid.y, original_grid.h), config)

        # Error should be within 0.5 pixels
        assert abs(recovered_iso.x - iso.x) <= 0.5
        assert abs(recovered_iso.y - iso.y) <= 0.5

    def test_roundtrip_grid_iso_grid(self) -> None:
        """grid -> iso -> grid should recover original coordinates."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        original_grid = GridCoord(7, 4, 1)

        iso = to_iso(original_grid, config)
        recovered_grid = to_grid(iso, original_grid.h, config)

        assert recovered_grid.x == original_grid.x
        assert recovered_grid.y == original_grid.y

    @pytest.mark.parametrize("x,y,h", [
        (0, 0, 0),
        (10, 10, 0),
        (5, 8, 3),
        (100, 50, 10),
        (0, 0, 5),
    ])
    def test_roundtrip_various_coords(self, x: int, y: int, h: int) -> None:
        """Multiple coordinates should round-trip correctly."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        original = GridCoord(x, y, h)

        iso = to_iso(original, config)
        recovered = to_grid(iso, h, config)

        assert recovered.x == x
        assert recovered.y == y


class TestMonotonicity:
    """Tests for monotonicity properties."""

    def test_x_monotonic_in_iso_x(self) -> None:
        """Increasing grid x should change iso X monotonically."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        y, h = 0, 0

        prev_iso_x = float('-inf')
        for x in range(10):
            iso = to_iso(GridCoord(x, y, h), config)
            assert iso.x > prev_iso_x
            prev_iso_x = iso.x

    def test_y_monotonic_in_iso_x(self) -> None:
        """Increasing grid y should change iso X monotonically (decreasing)."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        x, h = 0, 0

        prev_iso_x = float('inf')
        for y in range(10):
            iso = to_iso(GridCoord(x, y, h), config)
            assert iso.x < prev_iso_x
            prev_iso_x = iso.x

    def test_elevation_monotonic_in_iso_y(self) -> None:
        """Increasing elevation should decrease iso Y (move up visually)."""
        config = IsoConfig(tile_width=64, tile_height=32, elevation_scale=16)
        x, y = 5, 5

        prev_iso_y = float('inf')
        for h in range(5):
            iso = to_iso(GridCoord(x, y, h), config)
            assert iso.y < prev_iso_y
            prev_iso_y = iso.y


class TestNoSearchDependency:
    """Tests to verify no dependency on search/graph modules."""

    def test_no_networkx_import(self) -> None:
        """coordinates module should not import networkx."""
        import src.coordinates as coords_module
        import sys

        # Check that networkx is not in the module's namespace
        assert not hasattr(coords_module, 'nx')
        assert not hasattr(coords_module, 'networkx')

    def test_no_search_import(self) -> None:
        """coordinates module should not import search modules."""
        import src.coordinates as coords_module

        assert not hasattr(coords_module, 'search_path')
        assert not hasattr(coords_module, 'Algorithm')
