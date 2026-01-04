"""Golden tests for CloverLeaf statement parsing."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import beanout.clover_leaf


def test_clover_leaf_golden_files() -> None:
    """Render all CloverLeaf golden fixtures and compare to expected output."""
    golden_dir = pathlib.Path("fixtures/golden/managers/clover-leaf")
    txt_paths = sorted(
        path
        for path in golden_dir.iterdir()
        if path.is_file() and path.name.lower().endswith(".pdf.txt")
    )
    csv_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".csv"
    )
    json_paths = sorted(
        path for path in golden_dir.iterdir() if path.suffix.lower() == ".json"
    )

    assert txt_paths or csv_paths or json_paths, "No CloverLeaf golden files found"

    for txt_path in txt_paths:
        bean_path = txt_path.with_suffix(".bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.clover_leaf.render_clover_leaf_text(txt_path.read_text())
        expected = bean_path.read_text()
        assert output == expected

    for csv_path in csv_paths:
        bean_path = csv_path.with_suffix(f"{csv_path.suffix}.bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.clover_leaf.render_clover_leaf_csv_text(csv_path.read_text())
        expected = bean_path.read_text()
        assert output == expected

    for json_path in json_paths:
        bean_path = json_path.with_suffix(f"{json_path.suffix}.bean")
        assert bean_path.exists(), f"Missing golden file: {bean_path}"

        output = beanout.clover_leaf.render_clover_leaf_json_text(json_path.read_text())
        expected = bean_path.read_text()
        assert output == expected
