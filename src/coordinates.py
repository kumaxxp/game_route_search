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
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class IsoConfig:
    """Configuration for isometric projection."""

    tile_width: float = 64.0
    tile_height: float = 32.0
    elevation_scale: float = 16.0


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
