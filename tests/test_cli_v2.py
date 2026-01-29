"""Tests for CLI v2 module (Phase II)."""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch
from src.cli_v2 import parse_args, run, main, load_map, format_metrics_v2, format_comparison_v2
from src.finder import FinderResult, FinderAlgorithm


class TestParseArgs:
    """Tests for argument parsing."""

    def test_map_file_required(self) -> None:
        """Map file should be required."""
        with pytest.raises(SystemExit):
            parse_args([])

    def test_map_file_parsed(self) -> None:
        """Map file should be parsed correctly."""
        args = parse_args(["test_map.txt"])
        assert args.map_file == "test_map.txt"

    def test_default_algorithm_is_dijkstra(self) -> None:
        """Default algorithm should be dijkstra."""
        args = parse_args(["test_map.txt"])
        assert args.algo == "dijkstra"

    def test_algorithm_astar(self) -> None:
        """A* algorithm should be accepted."""
        args = parse_args(["test_map.txt", "--algo", "astar"])
        assert args.algo == "astar"

    def test_elevation_option(self) -> None:
        """Elevation option should be parsed."""
        args = parse_args(["test_map.txt", "--elevation", "elevation.txt"])
        assert args.elevation == "elevation.txt"

    def test_priority_option(self) -> None:
        """Priority option should be parsed."""
        args = parse_args(["test_map.txt", "--priority", "priority.txt"])
        assert args.priority == "priority.txt"

    def test_priority_weight_option(self) -> None:
        """Priority weight option should be parsed."""
        args = parse_args(["test_map.txt", "--priority-weight", "2.5"])
        assert args.priority_weight == 2.5

    def test_allow_diagonal_flag(self) -> None:
        """Allow diagonal flag should be parsed."""
        args = parse_args(["test_map.txt", "--allow-diagonal"])
        assert args.allow_diagonal is True

    def test_compare_flag(self) -> None:
        """Compare flag should be parsed."""
        args = parse_args(["test_map.txt", "--compare"])
        assert args.compare is True

    def test_metrics_flag(self) -> None:
        """Metrics flag should be parsed."""
        args = parse_args(["test_map.txt", "--metrics"])
        assert args.metrics is True

    def test_max_cost_cap_default(self) -> None:
        """Default max-cost-cap should be 255."""
        args = parse_args(["test_map.txt"])
        assert args.max_cost_cap == 255.0

    def test_max_cost_cap_custom(self) -> None:
        """Custom max-cost-cap should be parsed."""
        args = parse_args(["test_map.txt", "--max-cost-cap", "128"])
        assert args.max_cost_cap == 128.0


class TestLoadMap:
    """Tests for map loading."""

    def test_load_legacy_map(self, tmp_path: Path) -> None:
        """Legacy map should be loaded."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("SG")

        args = parse_args([str(map_file)])
        game_map = load_map(args)

        assert game_map.start == (0, 0)
        assert game_map.goal == (1, 0)

    def test_load_multi_layer_map(self, tmp_path: Path) -> None:
        """Multi-layer map should be loaded."""
        terrain_file = tmp_path / "terrain.txt"
        elevation_file = tmp_path / "elevation.txt"

        terrain_file.write_text("S.G")
        elevation_file.write_text("0 1 0")

        args = parse_args([str(terrain_file), "--elevation", str(elevation_file)])
        game_map = load_map(args)

        assert game_map.elevation[0][1] == 1

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Missing file should raise error."""
        args = parse_args(["nonexistent.txt"])
        with pytest.raises(FileNotFoundError):
            load_map(args)

    def test_elevation_file_not_found(self, tmp_path: Path) -> None:
        """Missing elevation file should raise error."""
        terrain_file = tmp_path / "terrain.txt"
        terrain_file.write_text("SG")

        args = parse_args([str(terrain_file), "--elevation", "nonexistent.txt"])
        with pytest.raises(FileNotFoundError):
            load_map(args)


class TestRun:
    """Tests for run function."""

    def test_run_with_valid_legacy_map(self, tmp_path: Path) -> None:
        """Run should succeed with valid legacy map."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("SG")

        args = parse_args([str(map_file)])
        exit_code = run(args)

        assert exit_code == 0

    def test_run_with_invalid_file(self, tmp_path: Path) -> None:
        """Run should return non-zero for non-existent file."""
        args = parse_args(["nonexistent.txt"])
        exit_code = run(args)

        assert exit_code == 1

    def test_run_with_invalid_map(self, tmp_path: Path) -> None:
        """Run should return non-zero for invalid map."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("...")

        args = parse_args([str(map_file)])
        exit_code = run(args)

        assert exit_code == 1

    def test_run_with_no_path(self, tmp_path: Path) -> None:
        """Run should return non-zero when no path exists."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S#G")

        args = parse_args([str(map_file)])
        exit_code = run(args)

        assert exit_code == 1

    def test_run_with_astar(self, tmp_path: Path) -> None:
        """Run should succeed with A* algorithm."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S.G")

        args = parse_args([str(map_file), "--algo", "astar"])
        exit_code = run(args)

        assert exit_code == 0

    def test_run_with_compare(self, tmp_path: Path) -> None:
        """Run should succeed in compare mode."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S.G")

        args = parse_args([str(map_file), "--compare"])
        exit_code = run(args)

        assert exit_code == 0

    def test_run_with_metrics(self, tmp_path: Path) -> None:
        """Run should succeed with metrics flag."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S.G")

        args = parse_args([str(map_file), "--metrics"])
        exit_code = run(args)

        assert exit_code == 0

    def test_run_with_diagonal(self, tmp_path: Path) -> None:
        """Run should succeed with diagonal movement."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S.\n.G")

        args = parse_args([str(map_file), "--allow-diagonal"])
        exit_code = run(args)

        assert exit_code == 0

    def test_run_outputs_visualization(self, tmp_path: Path, capsys) -> None:
        """Run should output path visualization."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S.G")

        args = parse_args([str(map_file)])
        run(args)
        captured = capsys.readouterr()

        assert "S@G" in captured.out


class TestFormatFunctions:
    """Tests for format functions."""

    def test_format_metrics_v2(self) -> None:
        """Format metrics should produce readable output."""
        result = FinderResult(
            path=[(0, 0), (1, 0)],
            total_cost=1.5,
            algorithm=FinderAlgorithm.DIJKSTRA,
            nodes_expanded=5,
            execution_time=0.001,
        )
        output = format_metrics_v2(result)

        assert "DIJKSTRA" in output
        assert "1.500" in output
        assert "5" in output

    def test_format_comparison_v2(self) -> None:
        """Format comparison should show both algorithms."""
        dijkstra = FinderResult(
            path=[(0, 0), (1, 0)],
            total_cost=1.5,
            algorithm=FinderAlgorithm.DIJKSTRA,
            nodes_expanded=10,
            execution_time=0.002,
        )
        astar = FinderResult(
            path=[(0, 0), (1, 0)],
            total_cost=1.5,
            algorithm=FinderAlgorithm.ASTAR,
            nodes_expanded=5,
            execution_time=0.001,
        )
        output = format_comparison_v2(dijkstra, astar)

        assert "Dijkstra" in output
        assert "A*" in output
        assert "50.0% fewer nodes" in output


class TestMain:
    """Tests for main entry point."""

    def test_main_returns_exit_code(self, tmp_path: Path) -> None:
        """Main should return exit code."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("SG")

        with patch.object(sys, 'argv', ['game-route-search', str(map_file)]):
            exit_code = main()

        assert exit_code == 0
