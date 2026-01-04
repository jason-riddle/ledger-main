"""Golden tests for Fidelity statement parsing."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import beanout.fidelity


def test_fidelity_golden_files() -> None:
    """Render all Fidelity golden fixtures and compare to expected output."""
    golden_dir = pathlib.Path("fixtures/golden/institutions/brokerages/fidelity")
    csv_paths = sorted(
        path
        for path in golden_dir.iterdir()
        if path.is_file() and path.name.lower().endswith(".csv")
    )

    assert csv_paths, "No Fidelity golden .csv files found"

    for csv_path in csv_paths:
        bean_path = csv_path.with_suffix(".csv.bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.fidelity.render_fidelity_csv_text(csv_path.read_text())
        expected = bean_path.read_text()
        assert output == expected
