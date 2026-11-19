from pathlib import Path

import pytest

from assettags.__main__ import main
from assettags.labels import (
    COLUMNS, LABEL_H, LABEL_W, ROWS, Label, build_pdf, cell_origin, fit_text, page_count, read_labels,
)

EX = Path(__file__).resolve().parent.parent / "examples" / "assets.csv"


def write_csv(path, body):
    path.write_text("asset_id,name,building,location\n" + body, encoding="utf-8")
    return path


def test_read_example_labels():
    labels = read_labels(EX)
    assert len(labels) == 8
    assert labels[0] == Label("HVAC-0001", "Rooftop unit 1", "Building A", "Roof")


def test_payload_format():
    assert Label("HVAC-0001", "x", "y", "z").payload == "ASSET:HVAC-0001"


def test_bad_asset_id_rejected(tmp_path):
    path = write_csv(tmp_path / "a.csv", "bad-id,Unit,Building A,Roof\n")
    with pytest.raises(ValueError, match="row 1"):
        read_labels(path)


def test_missing_column_rejected(tmp_path):
    path = tmp_path / "a.csv"
    path.write_text("asset_id,name\nHVAC-0001,Unit\n", encoding="utf-8")
    with pytest.raises(ValueError, match="building"):
        read_labels(path)


def test_page_count_boundaries():
    per = COLUMNS * ROWS
    assert page_count(0) == 0
    assert page_count(1) == 1
    assert page_count(per) == 1
    assert page_count(per + 1) == 2


def test_cell_origin_first_and_last_on_page():
    x0, y0 = cell_origin(0)
    x_last, y_last = cell_origin(COLUMNS * ROWS - 1)
    assert x_last - x0 == pytest.approx((COLUMNS - 1) * LABEL_W)
    assert y0 - y_last == pytest.approx((ROWS - 1) * LABEL_H)


def test_cell_origin_restarts_on_new_page():
    assert cell_origin(COLUMNS * ROWS) == cell_origin(0)


def test_fit_text():
    assert fit_text("short", 20) == "short"
    assert fit_text("x" * 30, 10) == "xxxxxxx..."


def test_build_pdf_writes_valid_pdf(tmp_path):
    out = tmp_path / "labels.pdf"
    pages = build_pdf(read_labels(EX), out)
    assert pages == 1
    assert out.read_bytes().startswith(b"%PDF")


def test_build_pdf_multiple_pages(tmp_path):
    labels = [Label(f"HVAC-{n:04d}", "Unit", "Building A", "Roof") for n in range(1, 26)]
    out = tmp_path / "many.pdf"
    assert build_pdf(labels, out) == 2
    assert out.stat().st_size > 1000


def test_cli_success_and_failure(tmp_path, capsys):
    out = tmp_path / "x.pdf"
    assert main([str(EX), "-o", str(out)]) == 0
    assert "8 labels, 1 page(s)" in capsys.readouterr().out
    assert main([str(tmp_path / "missing.csv")]) == 1
    empty = write_csv(tmp_path / "empty.csv", "")
    assert main([str(empty)]) == 1
