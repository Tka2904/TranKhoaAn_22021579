from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

import cv2
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def main():
    parser = argparse.ArgumentParser(description="Tạo marker ArUco để in đúng kích thước")
    parser.add_argument("--size-mm", type=float, default=50.0)
    parser.add_argument("--id", type=int, default=0)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output = root / "marker"
    output.mkdir(exist_ok=True)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker = cv2.aruco.generateImageMarker(dictionary, args.id, 1200, borderBits=1)
    png = output / f"aruco_id{args.id}.png"
    ok, encoded = cv2.imencode(".png", marker)
    if not ok:
        raise RuntimeError("Không thể mã hóa ảnh marker PNG")
    png_bytes = encoded.tobytes()
    png.write_bytes(png_bytes)

    pdf = output / f"aruco_id{args.id}_{args.size_mm:g}mm.pdf"
    page_w, page_h = A4
    c = canvas.Canvas(str(pdf), pagesize=A4)
    side = args.size_mm * mm
    x = (page_w - side) / 2
    y = (page_h - side) / 2
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_w / 2, y + side + 18 * mm, f"ArUco DICT_4X4_50 - ID {args.id}")
    c.setFont("Helvetica", 11)
    c.drawCentredString(page_w / 2, y + side + 11 * mm, f"Canh den chinh xac: {args.size_mm:g} mm")
    c.drawImage(ImageReader(BytesIO(png_bytes)), x, y, width=side, height=side, preserveAspectRatio=True, mask="auto")
    c.setFont("Helvetica", 9)
    c.drawCentredString(page_w / 2, y - 10 * mm, "In Actual size / 100%, khong chon Fit to page")
    c.save()
    print(f"Da tao marker: {pdf.name}")


if __name__ == "__main__":
    main()
