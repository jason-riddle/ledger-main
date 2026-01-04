"""Golden tests for Ally Bank statement parsing."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import beanout.ally_bank


def test_ally_bank_csv_golden_files() -> None:
    """Render all Ally Bank CSV fixtures and compare to expected output."""
    golden_dir = pathlib.Path("fixtures/golden/institutions/banking/ally-bank")
    csv_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".csv"
    )

    assert csv_paths, "No Ally Bank golden .csv files found"

    for csv_path in csv_paths:
        bean_path = csv_path.with_suffix(f"{csv_path.suffix}.bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.ally_bank.render_ally_bank_csv_text(csv_path.read_text())
        expected = bean_path.read_text()
        assert output == expected


def test_ally_bank_qfx_golden_files() -> None:
    """Render all Ally Bank QFX fixtures and compare to expected output."""
    golden_dir = pathlib.Path("fixtures/golden/institutions/banking/ally-bank")
    qfx_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".qfx"
    )

    assert qfx_paths, "No Ally Bank golden .qfx files found"

    for qfx_path in qfx_paths:
        bean_path = qfx_path.with_suffix(f"{qfx_path.suffix}.bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.ally_bank.render_ally_bank_qfx_text(qfx_path.read_text())
        expected = bean_path.read_text()
        assert output == expected
