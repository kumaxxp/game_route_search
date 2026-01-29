"""Multi-layer map loader for Phase II format."""
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from src.constants.terrain_costs import TERRAIN_COSTS


VALID_TERRAIN_CODES = frozenset(TERRAIN_COSTS.keys())


class LayerValidationError(Exception):
    """Exception raised when layer validation fails."""

    pass


@dataclass(frozen=True)
class MultiLayerMap:
    """Multi-layer map representation for Phase II."""

    terrain: list[list[str]]
    elevation: list[list[int]]
    priority: list[list[float]]
    start: tuple[int, int]
    goal: tuple[int, int]
    width: int
    height: int


def load_terrain_layer(file: TextIO) -> list[list[str]]:
    """
    Load terrain layer from file.

    Args:
        file: File-like object containing terrain codes

    Returns:
        2D list of terrain codes

    Raises:
        LayerValidationError: If validation fails
    """
    content = file.read()
    lines = content.strip().split('\n')

    if not lines or (len(lines) == 1 and not lines[0]):
        raise LayerValidationError("Terrain layer is empty")

    grid: list[list[str]] = []
    width = len(lines[0])

    for row_idx, line in enumerate(lines):
        if len(line) != width:
            raise LayerValidationError(
                f"Non-rectangular terrain: row {row_idx} has {len(line)} chars, expected {width}"
            )

        row: list[str] = []
        for col_idx, char in enumerate(line):
            if char not in VALID_TERRAIN_CODES:
                raise LayerValidationError(
                    f"Unknown/invalid terrain code '{char}' at ({col_idx}, {row_idx})"
                )
            row.append(char)
        grid.append(row)

    return grid


def load_elevation_layer(file: TextIO) -> list[list[int]]:
    """
    Load elevation layer from file.

    Args:
        file: File-like object containing space-separated integers

    Returns:
        2D list of elevation values

    Raises:
        LayerValidationError: If validation fails
    """
    content = file.read()
    lines = content.strip().split('\n')

    if not lines or (len(lines) == 1 and not lines[0]):
        raise LayerValidationError("Elevation layer is empty")

    grid: list[list[int]] = []
    width = None

    for row_idx, line in enumerate(lines):
        try:
            values = [int(v) for v in line.split()]
        except ValueError as e:
            raise LayerValidationError(
                f"Invalid integer format in elevation at row {row_idx}: {e}"
            )

        if width is None:
            width = len(values)
        elif len(values) != width:
            raise LayerValidationError(
                f"Non-rectangular elevation: row {row_idx} has {len(values)} values, expected {width}"
            )

        grid.append(values)

    return grid


def load_points_layer(
    terrain_grid: list[list[str]] | None = None,
    points_file: TextIO | None = None,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Load start and goal positions.

    Can read from terrain grid (S/G markers) or separate points file.

    Args:
        terrain_grid: Optional terrain grid to scan for S/G
        points_file: Optional file with explicit S/G coordinates

    Returns:
        Tuple of (start, goal) coordinates

    Raises:
        LayerValidationError: If S or G not found
    """
    start: tuple[int, int] | None = None
    goal: tuple[int, int] | None = None

    if points_file is not None:
        content = points_file.read()
        for line in content.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                marker = parts[0].upper()
                x, y = int(parts[1]), int(parts[2])
                if marker == 'S':
                    start = (x, y)
                elif marker == 'G':
                    goal = (x, y)
    elif terrain_grid is not None:
        for y, row in enumerate(terrain_grid):
            for x, cell in enumerate(row):
                if cell == 'S':
                    start = (x, y)
                elif cell == 'G':
                    goal = (x, y)

    if start is None:
        raise LayerValidationError("Start 'S' not found")
    if goal is None:
        raise LayerValidationError("Goal 'G' not found")

    return start, goal


def load_priority_layer(
    file: TextIO | None,
    width: int = 0,
    height: int = 0,
) -> list[list[float]]:
    """
    Load priority layer from file, or create default zeros.

    Args:
        file: Optional file with space-separated floats
        width: Width for default layer
        height: Height for default layer

    Returns:
        2D list of priority values
    """
    if file is None:
        return [[0.0 for _ in range(width)] for _ in range(height)]

    content = file.read()
    lines = content.strip().split('\n')

    grid: list[list[float]] = []
    for line in lines:
        values = [float(v) for v in line.split()]
        grid.append(values)

    return grid


def load_multi_layer_map(
    terrain_path: Path | None = None,
    elevation_path: Path | None = None,
    points_path: Path | None = None,
    priority_path: Path | None = None,
    legacy_text: TextIO | None = None,
) -> MultiLayerMap:
    """
    Load multi-layer map from files or legacy format.

    Args:
        terrain_path: Path to terrain layer file
        elevation_path: Path to elevation layer file
        points_path: Optional path to points file (S/G coordinates)
        priority_path: Optional path to priority layer file
        legacy_text: Optional file-like for Phase I legacy format

    Returns:
        MultiLayerMap with all layers

    Raises:
        LayerValidationError: If validation fails
    """
    if legacy_text is not None:
        return _load_legacy_format(legacy_text)

    if terrain_path is None:
        raise LayerValidationError("Terrain path is required for Phase II format")

    with open(terrain_path, 'r', encoding='utf-8') as f:
        terrain = load_terrain_layer(f)

    height = len(terrain)
    width = len(terrain[0]) if terrain else 0

    if elevation_path is not None:
        with open(elevation_path, 'r', encoding='utf-8') as f:
            elevation = load_elevation_layer(f)

        if len(elevation) != height or (elevation and len(elevation[0]) != width):
            raise LayerValidationError(
                f"Size mismatch: terrain is {width}x{height}, elevation is {len(elevation[0]) if elevation else 0}x{len(elevation)}"
            )
    else:
        elevation = [[0 for _ in range(width)] for _ in range(height)]

    if points_path is not None:
        with open(points_path, 'r', encoding='utf-8') as f:
            start, goal = load_points_layer(points_file=f)
    else:
        start, goal = load_points_layer(terrain_grid=terrain)

    if priority_path is not None:
        with open(priority_path, 'r', encoding='utf-8') as f:
            priority = load_priority_layer(f)
    else:
        priority = load_priority_layer(None, width, height)

    return MultiLayerMap(
        terrain=terrain,
        elevation=elevation,
        priority=priority,
        start=start,
        goal=goal,
        width=width,
        height=height,
    )


def _load_legacy_format(file: TextIO) -> MultiLayerMap:
    """
    Load Phase I legacy format (single text map with S/G/#/.).

    Args:
        file: File-like object with legacy map

    Returns:
        MultiLayerMap with default elevation and priority
    """
    content = file.read()
    lines = content.strip().split('\n')

    if not lines or (len(lines) == 1 and not lines[0]):
        raise LayerValidationError("Map is empty")

    terrain: list[list[str]] = []
    width = len(lines[0])

    for row_idx, line in enumerate(lines):
        if len(line) != width:
            raise LayerValidationError(
                f"Non-rectangular map: row {row_idx} has {len(line)} chars, expected {width}"
            )

        row: list[str] = []
        for char in line:
            if char not in VALID_TERRAIN_CODES:
                raise LayerValidationError(f"Unknown terrain code '{char}'")
            row.append(char)
        terrain.append(row)

    height = len(terrain)
    start, goal = load_points_layer(terrain_grid=terrain)

    elevation = [[0 for _ in range(width)] for _ in range(height)]
    priority = [[0.0 for _ in range(width)] for _ in range(height)]

    return MultiLayerMap(
        terrain=terrain,
        elevation=elevation,
        priority=priority,
        start=start,
        goal=goal,
        width=width,
        height=height,
    )
