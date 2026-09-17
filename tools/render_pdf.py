"""Render every page of a PDF to PNG images.

Used to read image-only JEDEC drawings (e.g. MO-309) that have no text layer.

Usage:
    py -3.11 tools/render_pdf.py <input.pdf> <output_dir> [dpi]

Requires PyMuPDF:  py -3.11 -m pip install --user pymupdf
"""
import os
import sys

import pymupdf


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 130
    os.makedirs(out, exist_ok=True)

    doc = pymupdf.open(src)
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=dpi)
        path = os.path.join(out, f"p{i:02d}.png")
        pix.save(path)
        print(f"{path}  {pix.width}x{pix.height}")


if __name__ == "__main__":
    main()
