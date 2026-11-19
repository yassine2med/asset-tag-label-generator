"""Build a printable PDF sheet of QR asset labels from a CSV list."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

ID_PATTERN = re.compile(r"^[A-Z]{2,4}-[0-9]{4}$")
REQUIRED = ("asset_id", "name", "building", "location")

COLUMNS = 3
ROWS = 8
LABEL_W = 2.5 * inch
LABEL_H = 1.25 * inch
MARGIN_X = (LETTER[0] - COLUMNS * LABEL_W) / 2
MARGIN_Y = (LETTER[1] - ROWS * LABEL_H) / 2
QR_SIZE = 1.0 * inch


@dataclass(frozen=True)
class Label:
    """Text printed on one label."""

    asset_id: str
    name: str
    building: str
    location: str

    @property
    def payload(self) -> str:
        """Text encoded in the QR code."""
        return f"ASSET:{self.asset_id}"


def read_labels(path: str | Path) -> list[Label]:
    """Read labels from a CSV. Raises ValueError for a missing column or a bad asset ID."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"missing column(s): {', '.join(missing)}")
        labels = []
        for number, row in enumerate(reader, start=1):
            asset_id = (row["asset_id"] or "").strip()
            if not ID_PATTERN.match(asset_id):
                raise ValueError(f"row {number}: bad asset_id {asset_id!r}")
            labels.append(Label(asset_id, row["name"].strip(), row["building"].strip(), row["location"].strip()))
    return labels


def page_count(label_total: int, per_page: int = COLUMNS * ROWS) -> int:
    """Number of pages needed for a number of labels."""
    return -(-label_total // per_page)


def cell_origin(index: int) -> tuple[float, float]:
    """Lower-left corner in points of the label at a position on a page (0 is top left)."""
    position = index % (COLUMNS * ROWS)
    col, row = position % COLUMNS, position // COLUMNS
    x = MARGIN_X + col * LABEL_W
    y = LETTER[1] - MARGIN_Y - (row + 1) * LABEL_H
    return x, y


def fit_text(text: str, limit: int) -> str:
    """Shorten text to a character limit, ending with three dots when cut."""
    return text if len(text) <= limit else text[: limit - 3] + "..."


def build_pdf(labels: list[Label], out_path: str | Path) -> int:
    """Write the label sheet and return the page count."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(out_path), pagesize=LETTER)
    pdf.setTitle("Asset labels")
    for index, label in enumerate(labels):
        if index and index % (COLUMNS * ROWS) == 0:
            pdf.showPage()
        x, y = cell_origin(index)
        pdf.setLineWidth(0.4)
        pdf.rect(x + 2, y + 2, LABEL_W - 4, LABEL_H - 4)
        widget = QrCodeWidget(label.payload)
        x0, y0, x1, y1 = widget.getBounds()
        drawing = Drawing(QR_SIZE, QR_SIZE, transform=[QR_SIZE / (x1 - x0), 0, 0, QR_SIZE / (y1 - y0), 0, 0])
        drawing.add(widget)
        renderPDF.draw(drawing, pdf, x + 8, y + (LABEL_H - QR_SIZE) / 2)
        text_x = x + 8 + QR_SIZE + 6
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(text_x, y + LABEL_H - 26, label.asset_id)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(text_x, y + LABEL_H - 40, fit_text(label.name, 20))
        pdf.drawString(text_x, y + LABEL_H - 52, fit_text(label.building, 20))
        pdf.drawString(text_x, y + LABEL_H - 64, fit_text(label.location, 20))
    pdf.save()
    return page_count(len(labels))
