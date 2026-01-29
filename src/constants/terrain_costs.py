"""Terrain cost constants generated from CSV."""
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class TerrainCost:
    """Cost parameters for a terrain type."""

    code: str
    terrain: str
    base_cost: float
    ascent_cost: float
    descent_cost: float
    diagonal_factor: float
    passable: bool


DEFAULT_CSV_PATH = Path(__file__).parent.parent.parent / "docs" / "strategy" / "terrain_costs.csv"

DEFAULT_TERRAIN = TerrainCost(
    code=".",
    terrain="plain",
    base_cost=1.0,
    ascent_cost=2.0,
    descent_cost=0.5,
    diagonal_factor=1.414,
    passable=True,
)


def load_terrain_costs(csv_path: Path | None = None) -> Mapping[str, TerrainCost]:
    """
    Load terrain costs from CSV file.

    Args:
        csv_path: Path to CSV file. If None, uses default path.

    Returns:
        Dictionary mapping terrain code to TerrainCost.
    """
    path = csv_path or DEFAULT_CSV_PATH

    if not path.exists():
        return {".": DEFAULT_TERRAIN}

    costs: dict[str, TerrainCost] = {}

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cost = TerrainCost(
                code=row["code"],
                terrain=row["terrain"],
                base_cost=float(row["base_cost"]),
                ascent_cost=float(row["ascent_cost"]),
                descent_cost=float(row["descent_cost"]),
                diagonal_factor=float(row["diagonal_factor"]),
                passable=row["passable"].lower() == "true",
            )
            costs[cost.code] = cost

    return costs


TERRAIN_COSTS: Mapping[str, TerrainCost] = load_terrain_costs()


def get_terrain_cost(code: str) -> TerrainCost:
    """
    Get terrain cost for a given code.

    Args:
        code: Terrain code character.

    Returns:
        TerrainCost for the terrain, or DEFAULT_TERRAIN if unknown.
    """
    return TERRAIN_COSTS.get(code, DEFAULT_TERRAIN)
