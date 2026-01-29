"""Cost function for multi-weighted pathfinding."""
from dataclasses import dataclass

from src.constants.terrain_costs import get_terrain_cost
from src.map_loader_v2 import MultiLayerMap

# Maximum cost cap (SPECIFICATION.md §最終査察追補)
# Prevents integer overflow and ensures bounded edge weights.
# C_max = 255 per specification.
MAX_COST_CAP: int = 255


@dataclass(frozen=True)
class CostConfig:
    """Configuration for cost calculation."""

    priority_weight: float = 0.0
    max_cost_cap: float = MAX_COST_CAP


def is_diagonal_move(u: tuple[int, int], v: tuple[int, int]) -> bool:
    """
    Check if movement from u to v is diagonal.

    Args:
        u: Source position (x, y)
        v: Target position (x, y)

    Returns:
        True if diagonal move (both x and y change)
    """
    dx = abs(v[0] - u[0])
    dy = abs(v[1] - u[1])
    return dx == 1 and dy == 1


def calculate_edge_cost(
    u: tuple[int, int],
    v: tuple[int, int],
    game_map: MultiLayerMap,
    config: CostConfig | None = None,
    allow_diagonal: bool = False,
) -> float:
    """
    Calculate edge cost from u to v using multi-weighted formula.

    Formula from specification:
    c(u,v) = b_t(v) * κ_len(u,v; r_t(v))
           + u_t(v) * max(0, Δh)
           + d_t(v) * max(0, -Δh)
           + λ * P(v)

    where:
    - b_t = base cost for terrain at v
    - κ_len = 1 (axial) or r_t (diagonal factor)
    - u_t = ascent cost per level
    - d_t = descent cost per level
    - Δh = h(v) - h(u) (elevation change)
    - λ = priority weight
    - P(v) = tactical priority at v

    Args:
        u: Source position (x, y)
        v: Target position (x, y)
        game_map: Multi-layer map with terrain, elevation, priority
        config: Cost calculation configuration
        allow_diagonal: Whether diagonal movement is allowed

    Returns:
        Total edge cost
    """
    cfg = config or CostConfig()

    terrain_code = game_map.terrain[v[1]][v[0]]
    terrain = get_terrain_cost(terrain_code)

    if not terrain.passable:
        return float('inf')

    is_diagonal = is_diagonal_move(u, v)
    if is_diagonal and not allow_diagonal:
        return float('inf')

    kappa = terrain.diagonal_factor if is_diagonal else 1.0
    base_component = terrain.base_cost * kappa

    h_u = game_map.elevation[u[1]][u[0]]
    h_v = game_map.elevation[v[1]][v[0]]
    delta_h = h_v - h_u

    ascent_component = terrain.ascent_cost * max(0, delta_h)
    descent_component = terrain.descent_cost * max(0, -delta_h)

    priority_v = game_map.priority[v[1]][v[0]]
    priority_component = cfg.priority_weight * priority_v

    total_cost = base_component + ascent_component + descent_component + priority_component

    # Apply cost saturation (SPECIFICATION.md §最終査察追補)
    # c̃(u,v) = min(c(u,v), C_max) where C_max = 255
    if total_cost > cfg.max_cost_cap:
        return cfg.max_cost_cap

    return total_cost


def get_minimum_base_cost(game_map: MultiLayerMap) -> float:
    """
    Get minimum base cost across all terrains in map.

    Used for admissible heuristic calculation.

    Args:
        game_map: Multi-layer map

    Returns:
        Minimum base cost (excluding impassable)
    """
    min_cost = float('inf')

    for row in game_map.terrain:
        for code in row:
            terrain = get_terrain_cost(code)
            if terrain.passable and terrain.base_cost < min_cost:
                min_cost = terrain.base_cost

    return min_cost if min_cost != float('inf') else 1.0
