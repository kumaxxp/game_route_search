"""Map loading and validation module."""
from dataclasses import dataclass
from typing import TextIO


VALID_CHARS = frozenset({'S', 'G', '#', '.'})


@dataclass(frozen=True)
class GameMap:
    """Represents a loaded and validated game map."""

    grid: list[list[str]]
    start: tuple[int, int]
    goal: tuple[int, int]
    width: int
    height: int


class MapValidationError(Exception):
    """Exception raised when map validation fails."""

    pass


def validate_map(grid: list[list[str]]) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Validate the map grid and return start and goal positions.

    Args:
        grid: 2D list of characters representing the map

    Returns:
        Tuple of (start_position, goal_position)

    Raises:
        MapValidationError: If validation fails
    """
    if not grid or not grid[0]:
        raise MapValidationError("Map is empty")

    width = len(grid[0])
    start_pos: tuple[int, int] | None = None
    goal_pos: tuple[int, int] | None = None

    for y, row in enumerate(grid):
        if len(row) != width:
            raise MapValidationError(
                f"Map is non-rectangular: row {y} has {len(row)} chars, expected {width}"
            )

        for x, char in enumerate(row):
            if char not in VALID_CHARS:
                raise MapValidationError(
                    f"Unknown/invalid character '{char}' at position ({x}, {y})"
                )

            if char == 'S':
                if start_pos is not None:
                    raise MapValidationError(
                        f"Duplicate Start 'S' found at ({x}, {y}), first was at {start_pos}"
                    )
                start_pos = (x, y)

            elif char == 'G':
                if goal_pos is not None:
                    raise MapValidationError(
                        f"Duplicate Goal 'G' found at ({x}, {y}), first was at {goal_pos}"
                    )
                goal_pos = (x, y)

    if start_pos is None:
        raise MapValidationError("Start 'S' not found in map")

    if goal_pos is None:
        raise MapValidationError("Goal 'G' not found in map")

    return start_pos, goal_pos


def load_map(file: TextIO) -> GameMap:
    """
    Load and validate a map from a file-like object.

    Args:
        file: File-like object containing the map text

    Returns:
        GameMap object with validated map data

    Raises:
        MapValidationError: If the map is invalid
    """
    content = file.read()
    lines = content.strip().split('\n')

    if not lines or (len(lines) == 1 and not lines[0]):
        raise MapValidationError("Map is empty")

    grid = [list(line) for line in lines]
    start, goal = validate_map(grid)

    return GameMap(
        grid=grid,
        start=start,
        goal=goal,
        width=len(grid[0]),
        height=len(grid),
    )


def load_map_from_file(filepath: str) -> GameMap:
    """
    Load and validate a map from a file path.

    Args:
        filepath: Path to the map file

    Returns:
        GameMap object with validated map data

    Raises:
        MapValidationError: If the map is invalid
        FileNotFoundError: If the file doesn't exist
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return load_map(f)
