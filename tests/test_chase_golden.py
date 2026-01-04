"""Golden tests for Chase statement parsing."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import beanout.chase


def test_chase_csv_golden_files() -> None:
    """Render all Chase CSV fixtures and compare to expected output."""
    golden_dir = pathlib.Path("fixtures/golden/chase")
    csv_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".csv"
    )

    assert csv_paths, "No Chase golden .csv files found"

    for csv_path in csv_paths:
        bean_path = csv_path.with_suffix(f"{csv_path.suffix}.bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.chase.render_chase_csv_text(csv_path.read_text())
        expected = bean_path.read_text()
        assert output == expected


def test_chase_qfx_golden_files() -> None:
    """Render all Chase QFX fixtures and compare to expected output."""
    golden_dir = pathlib.Path("fixtures/golden/chase")
    qfx_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".qfx"
    )

    assert qfx_paths, "No Chase golden .qfx files found"

    for qfx_path in qfx_paths:
        bean_path = qfx_path.with_suffix(f"{qfx_path.suffix}.bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.chase.render_chase_qfx_text(qfx_path.read_text())
        expected = bean_path.read_text()
        assert output == expected
