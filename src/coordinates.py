"""
Coordinate transformation layer for isometric projection.

This module provides bidirectional transformation between:
- Logical grid coordinates (x, y, h) used by pathfinding algorithms
- Isometric screen coordinates (X, Y) used for rendering

IMPORTANT: This module must NOT depend on search, graph, or NetworkX modules.
It is a pure coordinate transformation layer.

Mathematical formulas:
- Grid to Iso: X = (tw/2)(x - y), Y = (th/2)(x + y) - beta * h
- Iso to Grid: Inverse transformation with rounding
- Diamond hit-test: |u| + |v| <= 1 where u = 2/tw*(X-Xc), v = 2/th*(Y-Yc)
"""
from dataclasses import dataclass


class OutOfBoundsError(Exception):
    """Exception raised when coordinates are out of grid bounds.

    Invariant: 0 <= x < W, 0 <= y < H
    """

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        super().__init__(
            f"Coordinate ({x}, {y}) is out of bounds for grid size ({width}, {height}). "
            f"Valid range: 0 <= x < {width}, 0 <= y < {height}"
        )


def validate_grid_bounds(x: int, y: int, width: int, height: int) -> None:
    """Validate that grid coordinates are within bounds.

    Invariant: 0 <= x < W, 0 <= y < H

    Args:
        x: X coordinate
        y: Y coordinate
        width: Grid width (W)
        height: Grid height (H)

    Raises:
        OutOfBoundsError: If coordinates violate boundary invariant
    """
    if x < 0 or x >= width or y < 0 or y >= height:
        raise OutOfBoundsError(x, y, width, height)


@dataclass(frozen=True)
class IsoConfig:
    """Configuration for isometric projection.

    Constraints (zero division prevention):
    - tile_width > 0
    - tile_height > 0
    - elevation_scale >= 0
    """

    tile_width: float = 64.0
    tile_height: float = 32.0
    elevation_scale: float = 16.0

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.tile_width <= 0:
            raise ValueError("tile_width must be positive")
        if self.tile_height <= 0:
            raise ValueError("tile_height must be positive")
        if self.elevation_scale < 0:
            raise ValueError("elevation_scale must be non-negative")


@dataclass(frozen=True)
class GridCoord:
    """Logical grid coordinate with optional elevation."""

    x: int
    y: int
    h: int = 0


@dataclass(frozen=True)
class IsoCoord:
    """Isometric screen coordinate."""

    x: float
    y: float


@dataclass(frozen=True)
class IsoCoordInt:
    """Isometric screen coordinate with integer values (pixel-aligned)."""

    x: int
    y: int


def to_iso(grid: GridCoord, config: IsoConfig | None = None) -> IsoCoord:
    """
    Convert logical grid coordinate to isometric screen coordinate.

    Formula:
        X = (tw/2) * (x - y)
        Y = (th/2) * (x + y) - beta * h

    Args:
        grid: Logical grid coordinate (x, y, h)
        config: Isometric projection configuration

    Returns:
        Isometric screen coordinate (X, Y)
    """
    cfg = config or IsoConfig()

    iso_x = (cfg.tile_width / 2) * (grid.x - grid.y)
    iso_y = (cfg.tile_height / 2) * (grid.x + grid.y) - cfg.elevation_scale * grid.h

    return IsoCoord(x=iso_x, y=iso_y)


def to_grid(iso: IsoCoord, elevation: int, config: IsoConfig | None = None) -> GridCoord:
    """
    Convert isometric screen coordinate to logical grid coordinate.

    This is the inverse of to_iso. Since we need the elevation to properly
    compute the inverse, it must be provided (e.g., from a height map lookup).

    Inverse formula:
        Adjust Y for elevation: Y_adj = Y + beta * h
        x = (X / (tw/2) + Y_adj / (th/2)) / 2
        y = (Y_adj / (th/2) - X / (tw/2)) / 2

    Args:
        iso: Isometric screen coordinate (X, Y)
        elevation: Known elevation at this position
        config: Isometric projection configuration

    Returns:
        Logical grid coordinate (x, y, h)
    """
    cfg = config or IsoConfig()

    y_adjusted = iso.y + cfg.elevation_scale * elevation

    half_tw = cfg.tile_width / 2
    half_th = cfg.tile_height / 2

    x_term = iso.x / half_tw
    y_term = y_adjusted / half_th

    grid_x = (x_term + y_term) / 2
    grid_y = (y_term - x_term) / 2

    return GridCoord(
        x=round(grid_x),
        y=round(grid_y),
        h=elevation,
    )


def to_iso_center(grid: GridCoord, config: IsoConfig | None = None) -> IsoCoord:
    """
    Convert logical grid coordinate to isometric screen coordinate at tile center.

    This variant returns the center point of the tile, useful for sprite positioning.

    Args:
        grid: Logical grid coordinate (x, y, h)
        config: Isometric projection configuration

    Returns:
        Isometric screen coordinate at tile center
    """
    base = to_iso(grid, config)
    cfg = config or IsoConfig()

    return IsoCoord(
        x=base.x,
        y=base.y + cfg.tile_height / 4,
    )


def manhattan_distance_grid(a: GridCoord, b: GridCoord) -> int:
    """
    Calculate Manhattan distance between two grid coordinates (ignoring elevation).

    Args:
        a: First grid coordinate
        b: Second grid coordinate

    Returns:
        Manhattan distance
    """
    return abs(a.x - b.x) + abs(a.y - b.y)


def octile_distance_grid(a: GridCoord, b: GridCoord) -> float:
    """
    Calculate Octile distance between two grid coordinates (for 8-directional movement).

    Formula: max(dx, dy) + (sqrt(2) - 1) * min(dx, dy)

    Args:
        a: First grid coordinate
        b: Second grid coordinate

    Returns:
        Octile distance
    """
    dx = abs(a.x - b.x)
    dy = abs(a.y - b.y)

    return max(dx, dy) + (1.41421356237 - 1) * min(dx, dy)


def to_iso_int(grid: GridCoord, config: IsoConfig | None = None) -> IsoCoordInt:
    """
    Convert logical grid coordinate to integer isometric screen coordinate.

    This variant rounds the result to integers for pixel-aligned rendering.
    Uses Python's round() for nearest-integer rounding (round half to even).

    Type safety requirement from SPECIFICATION.md §最終査察追補:
    - Final coordinates are integer (round() then int conversion)
    - Eliminates sub-pixel positioning issues

    Args:
        grid: Logical grid coordinate (x, y, h)
        config: Isometric projection configuration

    Returns:
        Integer isometric screen coordinate (X, Y)
    """
    iso = to_iso(grid, config)
    return IsoCoordInt(
        x=int(round(iso.x)),
        y=int(round(iso.y)),
    )


def is_in_diamond(u: float, v: float) -> bool:
    """
    Check if normalized coordinates (u, v) are inside the diamond (rhombus) region.

    Diamond hit-test formula from SPECIFICATION.md §最終査察追補:
        |u| + |v| <= 1

    Where for a click at (X, Y) relative to tile center (Xc, Yc):
        u = 2/tw * (X - Xc)
        v = 2/th * (Y - Yc)

    This determines whether a screen click belongs to a given isometric tile.

    Args:
        u: Normalized x coordinate (-1 to 1 range)
        v: Normalized y coordinate (-1 to 1 range)

    Returns:
        True if point is inside or on boundary of diamond
    """
    return abs(u) + abs(v) <= 1.0


def normalize_to_diamond(
    click_x: float,
    click_y: float,
    center_x: float,
    center_y: float,
    config: IsoConfig | None = None,
) -> tuple[float, float]:
    """
    Convert screen coordinates to normalized diamond coordinates.

    Normalization formula:
        u = 2/tw * (X - Xc)
        v = 2/th * (Y - Yc)

    Args:
        click_x: Screen X coordinate of click
        click_y: Screen Y coordinate of click
        center_x: Screen X coordinate of tile center
        center_y: Screen Y coordinate of tile center
        config: Isometric projection configuration

    Returns:
        Tuple of (u, v) normalized coordinates
    """
    cfg = config or IsoConfig()
    u = (2.0 / cfg.tile_width) * (click_x - center_x)
    v = (2.0 / cfg.tile_height) * (click_y - center_y)
    return (u, v)
