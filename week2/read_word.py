import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from openpyxl import load_workbook

import read_pdf

# TextCleaner 在 week3 下：把项目根目录加入 sys.path，保证直接运行本脚本也能 import
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
from week3.TextCleaner import TextCleaner


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


PAGE_SEP = "\n\f\n"  # 页分隔符：与 read_pdf_ai优化版本 一致，第 N 个 \f 对应第 N 页


def _paragraph_page_parts(para) -> list[str]:
    """把一个段落按分页符拆成多段文本。

    分页来源有两种：文档里显式插入的分页符 w:br[@w:type='page']，
    以及 Word 渲染后缓存的 w:lastRenderedPageBreak。
    普通换行 w:br / w:cr 只按换行处理，不切页。
    """
    parts: list[str] = []
    buf: list[str] = []
    for node in para._p.iter():
        tag = node.tag
        if not isinstance(tag, str):  # 跳过注释 / 处理指令等非元素节点
            continue
        if tag == qn("w:br"):
            if node.get(qn("w:type")) == "page":
                parts.append("".join(buf))
                buf = []
            else:
                buf.append("\n")
        elif tag == qn("w:cr"):
            buf.append("\n")
        elif tag == qn("w:lastRenderedPageBreak"):
            parts.append("".join(buf))
            buf = []
        elif tag == qn("w:tab"):
            buf.append("\t")
        elif tag == qn("w:t"):
            buf.append(node.text or "")
    parts.append("".join(buf))
    return parts


def extract_docx_pages(path) -> list[str]:
    """把 docx 按分页符切成一页一页的文本；没有分页符时整篇作为一页。

    按文档原始顺序读取段落与表格，避免只取段落而丢掉表格内容。
    """
    doc = Document(path)
    pages: list[str] = []
    buf: list[str] = []

    def flush():
        text = "\n".join(buf).strip()
        if text:
            pages.append(text)
        buf.clear()

    for child in doc.element.body:
        if child.tag == qn("w:p"):
            for i, part in enumerate(_paragraph_page_parts(Paragraph(child, doc))):
                if i > 0:  # 段落内部出现分页符：先收尾当前页
                    flush()
                buf.append(part)
        elif child.tag == qn("w:tbl"):
            for row in Table(child, doc).rows:
                cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                buf.append(" | ".join(cells))
    flush()
    return pages or [""]


def read_word_save_txt(path, save_path=None):
    """读取word文件内容并保存为 txt 文件。

    一页一页读取保存：按文档中的分页符分页（没有分页符时整篇作为一页），
    每页文本都会调用 TextCleaner().clean(text) 做清洗，页与页之间用 PAGE_SEP 分隔。

    :param path: docx 文件路径，或包含 docx 的目录（会递归查找）
    :param save_path: txt 输出目录，默认 week2/out_text
    :return: 处理失败的文件个数
    """
    src = Path(path)
    if not src.exists():
        print(f"路径{src}不存在，请确认路径是否正确【{src.resolve()}】")
        return 1

    if src.is_file():
        if src.suffix.lower() != ".docx":
            print(f"不是 docx 文件：{src.resolve()}")
            return 1
        docx_files = [src]
    elif src.is_dir():
        docx_files = sorted(
            p for p in src.rglob("*.docx")
            # 跳过 Word 打开文档时产生的临时锁文件（~$ 开头）
            if p.is_file() and not p.name.startswith("~$")
        )
        if not docx_files:
            print(f"文件夹下不存在 docx 文件：{src.resolve()}")
            return 1
    else:
        print(f"路径{src}既不是文件也不是文件夹，请确认路径是否正确【{src.resolve()}】")
        return 1

    out_dir = Path(save_path) if save_path else Path(__file__).resolve().parent / "out_text"
    out_dir.mkdir(parents=True, exist_ok=True)

    cleaner = TextCleaner()
    failures = 0
    print(f"待处理 {len(docx_files)} 个 docx 文件，输出目录：{out_dir.resolve()}")
    for docx_file in docx_files:
        txt_path = out_dir / (docx_file.stem + ".txt")
        try:
            pages = [cleaner.clean(page) for page in extract_docx_pages(docx_file)]
            content = PAGE_SEP.join(page for page in pages if page)
            if not content:
                print(f"[跳过] 未提取到内容：{docx_file.resolve()}")
                failures += 1
                continue
            txt_path.write_text(content, encoding="utf-8")
            print(f"保存成功：{docx_file.name} → {txt_path.resolve()}（{len(pages)} 页）")
        except Exception as e:
            print(f"[跳过] {docx_file.resolve()}：{e}")
            failures += 1

    print(f"完成：成功 {len(docx_files) - failures} 个，失败 {failures} 个")
    return failures


if __name__ == "__main__":
    read_word_save_txt(_PROJECT_ROOT / "test_docs")

