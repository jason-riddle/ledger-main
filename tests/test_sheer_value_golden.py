"""Golden tests for Sheer Value statement parsing."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import beanout.sheer_value


def test_sheer_value_golden_files() -> None:
    """Render all Sheer Value golden fixtures and compare to expected output."""
    golden_dir = pathlib.Path("fixtures/golden/managers/sheer-value")
    txt_paths = sorted(
        path
        for path in golden_dir.iterdir()
        if path.is_file() and path.name.lower().endswith(".pdf.txt")
    )

    assert txt_paths, "No Sheer Value golden .pdf.txt files found"

    for txt_path in txt_paths:
        bean_path = txt_path.with_suffix(".bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.sheer_value.render_sheer_value_text(txt_path.read_text())
        expected = bean_path.read_text()
        assert output == expected
