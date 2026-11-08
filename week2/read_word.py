from pathlib import Path

from docx import Document
from openpyxl import load_workbook

import read_pdf


def extract_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_xlsx(path):
    wb = load_workbook(path, data_only=True)
    lines = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            line = " | ".join(str(c) if c is not None else "" for c in row)
            if line.strip():
                lines.append(line)
    return "\n".join(lines)


def extract_any(path):
    ext = Path(path).suffix.lower()
    try:
        if ext == ".pdf":
            return read_pdf.read_pdf_save_text(path)
        elif ext == ".docx":
            return extract_docx(path)
        elif ext in (".xlsx", ".xlsm"):
            return extract_xlsx(path)
        elif ext == ".txt":
            return Path(path).read_text(encoding="utf-8")
        else:
            return ""
    except Exception as e:
        print(f"[跳过] {path}: {e}")
        return ""
