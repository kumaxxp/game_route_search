"""Tests for cost function."""
import pytest
from src.cost_function import (
    calculate_edge_cost,
    is_diagonal_move,
    CostConfig,
)
from src.map_loader_v2 import MultiLayerMap


class TestIsDiagonalMove:
    """Tests for diagonal move detection."""

    def test_horizontal_move_not_diagonal(self) -> None:
        """Horizontal move should not be diagonal."""
        assert not is_diagonal_move((0, 0), (1, 0))
        assert not is_diagonal_move((5, 3), (4, 3))

    def test_vertical_move_not_diagonal(self) -> None:
        """Vertical move should not be diagonal."""
        assert not is_diagonal_move((0, 0), (0, 1))
        assert not is_diagonal_move((2, 5), (2, 4))

    def test_diagonal_move_detected(self) -> None:
        """Diagonal moves should be detected."""
        assert is_diagonal_move((0, 0), (1, 1))
        assert is_diagonal_move((3, 3), (2, 4))
        assert is_diagonal_move((5, 2), (4, 1))


class TestCalculateEdgeCost:
    """Tests for edge cost calculation."""

    @pytest.fixture
    def simple_map(self) -> MultiLayerMap:
        """Create a simple test map."""
        return MultiLayerMap(
            terrain=[['S', '.', '.'], ['.', '.', '.'], ['.', '.', 'G']],
            elevation=[[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            priority=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            start=(0, 0),
            goal=(2, 2),
            width=3,
            height=3,
        )

    def test_flat_plain_cost(self, simple_map: MultiLayerMap) -> None:
        """Flat plain movement should have base cost 1.0."""
        cost = calculate_edge_cost(
            (0, 0), (1, 0),
            simple_map,
            allow_diagonal=False,
        )
        assert cost == pytest.approx(1.0)

    def test_paved_road_cheaper(self) -> None:
        """Paved road should be cheaper than plain."""
        paved_map = MultiLayerMap(
            terrain=[['S', '=', '='], ['=', '=', '='], ['=', '=', 'G']],
            elevation=[[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            priority=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            start=(0, 0),
            goal=(2, 2),
            width=3,
            height=3,
        )
        cost = calculate_edge_cost((0, 0), (1, 0), paved_map)
        assert cost == pytest.approx(0.8)  # Paved base cost

    def test_ascent_increases_cost(self) -> None:
        """Ascending should increase cost."""
        hill_map = MultiLayerMap(
            terrain=[['S', '.'], ['.', 'G']],
            elevation=[[0, 1], [0, 0]],
            priority=[[0.0, 0.0], [0.0, 0.0]],
            start=(0, 0),
            goal=(1, 1),
            width=2,
            height=2,
        )
        flat_cost = calculate_edge_cost((0, 0), (0, 1), hill_map)
        ascent_cost = calculate_edge_cost((0, 0), (1, 0), hill_map)

        # Ascending (+1 elevation) adds ascent cost
        # Plain: base=1.0, ascent=2.0, so total = 1.0 + 2.0*1 = 3.0
        assert ascent_cost == pytest.approx(3.0)
        assert ascent_cost > flat_cost

    def test_descent_cheaper_than_ascent(self) -> None:
        """Descending should be cheaper than ascending."""
        hill_map = MultiLayerMap(
            terrain=[['S', '.'], ['.', 'G']],
            elevation=[[1, 0], [1, 0]],
            priority=[[0.0, 0.0], [0.0, 0.0]],
            start=(0, 0),
            goal=(1, 1),
            width=2,
            height=2,
        )
        # From (0,0) h=1 to (1,0) h=0: descent
        descent_cost = calculate_edge_cost((0, 0), (1, 0), hill_map)
        # Plain: base=1.0, descent=0.5, so total = 1.0 + 0.5*1 = 1.5
        assert descent_cost == pytest.approx(1.5)

    def test_diagonal_applies_factor(self) -> None:
        """Diagonal movement should apply diagonal factor."""
        simple_map = MultiLayerMap(
            terrain=[['S', '.'], ['.', 'G']],
            elevation=[[0, 0], [0, 0]],
            priority=[[0.0, 0.0], [0.0, 0.0]],
            start=(0, 0),
            goal=(1, 1),
            width=2,
            height=2,
        )
        diagonal_cost = calculate_edge_cost(
            (0, 0), (1, 1),
            simple_map,
            allow_diagonal=True,
        )
        # Plain: base=1.0, diagonal_factor=1.414
        assert diagonal_cost == pytest.approx(1.414)

    def test_priority_adds_penalty(self) -> None:
        """Tactical priority should add penalty."""
        priority_map = MultiLayerMap(
            terrain=[['S', '.'], ['.', 'G']],
            elevation=[[0, 0], [0, 0]],
            priority=[[0.0, 5.0], [0.0, 0.0]],
            start=(0, 0),
            goal=(1, 1),
            width=2,
            height=2,
        )
        config = CostConfig(priority_weight=1.0)
        cost_with_priority = calculate_edge_cost(
            (0, 0), (1, 0),
            priority_map,
            config=config,
        )
        # base=1.0 + priority_weight*P = 1.0 + 1.0*5.0 = 6.0
        assert cost_with_priority == pytest.approx(6.0)

    def test_cliff_terrain_high_cost(self) -> None:
        """Cliff terrain should have high base cost."""
        cliff_map = MultiLayerMap(
            terrain=[['S', '^'], ['^', 'G']],
            elevation=[[0, 0], [0, 0]],
            priority=[[0.0, 0.0], [0.0, 0.0]],
            start=(0, 0),
            goal=(1, 1),
            width=2,
            height=2,
        )
        cost = calculate_edge_cost((0, 0), (1, 0), cliff_map)
        # Cliff: base=5.0
        assert cost == pytest.approx(5.0)

    def test_cliff_ascent_very_expensive(self) -> None:
        """Climbing a cliff should be very expensive."""
        cliff_map = MultiLayerMap(
            terrain=[['S', '^'], ['^', 'G']],
            elevation=[[0, 3], [0, 0]],
            priority=[[0.0, 0.0], [0.0, 0.0]],
            start=(0, 0),
            goal=(1, 1),
            width=2,
            height=2,
        )
        cost = calculate_edge_cost((0, 0), (1, 0), cliff_map)
        # Cliff: base=5.0, ascent=10.0, delta_h=3
        # 5.0 + 10.0*3 = 35.0
        assert cost == pytest.approx(35.0)


class TestCostConfigDefaults:
    """Tests for cost configuration."""

    def test_default_priority_weight_zero(self) -> None:
        """Default priority weight should be zero."""
        config = CostConfig()
        assert config.priority_weight == 0.0

    def test_custom_priority_weight(self) -> None:
        """Custom priority weight should be used."""
        config = CostConfig(priority_weight=2.5)
        assert config.priority_weight == 2.5


class TestCostFormula:
    """Tests verifying the exact cost formula from specification."""

    def test_full_formula(self) -> None:
        """Test complete formula: c(u,v) = b*κ + u*max(0,Δh) + d*max(0,-Δh) + λ*P."""
        test_map = MultiLayerMap(
            terrain=[['S', 'F'], ['~', 'G']],  # Forest and shallow water
            elevation=[[0, 2], [1, 0]],
            priority=[[0.0, 1.5], [0.5, 0.0]],
            start=(0, 0),
            goal=(1, 1),
            width=2,
            height=2,
        )
        config = CostConfig(priority_weight=2.0)

        # Move to forest at elevation 2
        # Forest: b=2.0, u=1.5, d=1.0, r=1.414
        # Δh = 2 - 0 = 2 (ascent)
        # P = 1.5, λ = 2.0
        # Cost = 2.0*1 + 1.5*2 + 1.0*0 + 2.0*1.5 = 2.0 + 3.0 + 0 + 3.0 = 8.0
        cost = calculate_edge_cost((0, 0), (1, 0), test_map, config=config)
        assert cost == pytest.approx(8.0)
