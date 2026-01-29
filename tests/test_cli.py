"""Tests for CLI module."""
import pytest
import sys
from io import StringIO
from unittest.mock import patch
from src.cli import main, parse_args, run


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

    def test_default_algorithm_is_astar(self) -> None:
        """Default algorithm should be astar."""
        args = parse_args(["test_map.txt"])
        assert args.algorithm == "astar"

    def test_algorithm_bfs(self) -> None:
        """BFS algorithm should be accepted."""
        args = parse_args(["test_map.txt", "--algorithm", "bfs"])
        assert args.algorithm == "bfs"

    def test_algorithm_astar(self) -> None:
        """A* algorithm should be accepted."""
        args = parse_args(["test_map.txt", "--algorithm", "astar"])
        assert args.algorithm == "astar"

    def test_compare_flag(self) -> None:
        """Compare flag should be parsed."""
        args = parse_args(["test_map.txt", "--compare"])
        assert args.compare is True

    def test_metrics_flag(self) -> None:
        """Metrics flag should be parsed."""
        args = parse_args(["test_map.txt", "--metrics"])
        assert args.metrics is True

    def test_all_flags_combined(self) -> None:
        """All flags should work together."""
        args = parse_args(["test_map.txt", "--algorithm", "bfs", "--compare", "--metrics"])
        assert args.map_file == "test_map.txt"
        assert args.algorithm == "bfs"
        assert args.compare is True
        assert args.metrics is True


class TestRun:
    """Tests for run function."""

    def test_run_with_valid_map(self, tmp_path) -> None:
        """Run should succeed with valid map."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("SG")

        exit_code = run(str(map_file), "astar", compare=False, metrics=False)

        assert exit_code == 0

    def test_run_with_invalid_file(self) -> None:
        """Run should return non-zero for non-existent file."""
        exit_code = run("nonexistent_file.txt", "astar", compare=False, metrics=False)

        assert exit_code != 0

    def test_run_with_invalid_map(self, tmp_path) -> None:
        """Run should return non-zero for invalid map."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("...")

        exit_code = run(str(map_file), "astar", compare=False, metrics=False)

        assert exit_code != 0

    def test_run_with_no_path(self, tmp_path) -> None:
        """Run should return non-zero when no path exists."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S#G")

        exit_code = run(str(map_file), "astar", compare=False, metrics=False)

        assert exit_code != 0

    def test_run_with_compare_mode(self, tmp_path) -> None:
        """Run should succeed in compare mode."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S.G")

        exit_code = run(str(map_file), "astar", compare=True, metrics=False)

        assert exit_code == 0

    def test_run_with_metrics(self, tmp_path) -> None:
        """Run should succeed with metrics flag."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S.G")

        exit_code = run(str(map_file), "astar", compare=False, metrics=True)

        assert exit_code == 0

    def test_run_outputs_visualization(self, tmp_path, capsys) -> None:
        """Run should output path visualization."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("S.G")

        run(str(map_file), "astar", compare=False, metrics=False)
        captured = capsys.readouterr()

        assert "S@G" in captured.out


class TestMain:
    """Tests for main entry point."""

    def test_main_returns_exit_code(self, tmp_path) -> None:
        """Main should return exit code."""
        map_file = tmp_path / "test.txt"
        map_file.write_text("SG")

        with patch.object(sys, 'argv', ['game-route-search', str(map_file)]):
            exit_code = main()

        assert exit_code == 0
