"""读取 PDF 文件（或目录内所有 PDF），提取文本保存为 txt。

分页约定：每一页（包括没有文字的空白页）都以 "\\n\\f\\n" 结尾。
因此 txt 里第 N 个 \\f 就对应 PDF 的第 N 页，后续按页切 chunk、标注引用页码都不会错位。
"""

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_INPUT = PROJECT_ROOT / "test_docs"
DEFAULT_OUTPUT = SCRIPT_DIR / "out_text"

logger = logging.getLogger(__name__)

PDF_SUFFIX = ".pdf"
PAGE_SEP = "\n\f\n"
TXT_TMP_SUFFIX = ".tmp"


class PdfExtractError(Exception):
    """PDF 文本提取或写入失败。"""


class PdfEmptyTextError(PdfExtractError):
    """PDF 未提取到任何文本（多为扫描件，需要 OCR）。"""


def collect_pdf_files(pdf: str | Path) -> list[Path]:
    """把入参（文件或目录）统一解析为待处理的 PDF 列表。"""
    pdf_path = Path(pdf)
    if not pdf_path.exists():
        raise PdfExtractError(f"路径不存在：{pdf_path.resolve()}")
    if pdf_path.is_file():
        if pdf_path.suffix.lower() != PDF_SUFFIX:
            raise PdfExtractError(f"不是 PDF 文件：{pdf_path.resolve()}（仅支持 {PDF_SUFFIX}）")
        return [pdf_path]
    if pdf_path.is_dir():
        files = sorted(
            p for p in pdf_path.rglob("*")
            if p.is_file() and p.suffix.lower() == PDF_SUFFIX
        )
        if not files:
            raise PdfExtractError(f"文件夹下不存在 pdf 文件：{pdf_path.resolve()}")
        return files
    raise PdfExtractError(f"路径既不是文件也不是目录：{pdf_path.resolve()}")


def resolve_txt_path(pdf_path: Path, root: Path) -> Path:
    """保留 PDF 相对 root 的目录层级，避免不同子目录的同名 PDF 写进同一个 txt。"""
    try:
        rel_parent = pdf_path.parent.relative_to(root)
    except ValueError:  # 不在 root 之下（理论上不会发生），退化为扁平输出
        rel_parent = Path()
    return rel_parent / (pdf_path.stem + ".txt")


def stdin_is_interactive() -> bool:
    return sys.stdin is not None and sys.stdin.isatty()


def ask_existing_action(txt_path: Path) -> str:
    """返回 "w" 覆盖 / "a" 追加 / "skip" 跳过；直接回车或标准输入被关闭时按跳过。"""
    prompt = f"文件【{txt_path}】已存在，覆盖(w) / 追加(a) / 跳过(s，默认)？"
    try:
        while True:
            answer = input(prompt).strip().lower()
            if answer in ("", "s", "skip"):
                return "skip"
            if answer in ("w", "overwrite"):
                return "w"
            if answer in ("a", "append"):
                return "a"
            print("输入错误，请输入 w / a / s")
    except (EOFError, KeyboardInterrupt):
        print()
        logger.info("未获取到输入，按跳过处理：%s", txt_path)
        return "skip"


def resolve_write_action(txt_path: Path, overwrite: bool | None) -> str:
    """决定已存在 txt 的处理方式：覆盖 "w" / 追加 "a" / 跳过 "skip"。"""
    if overwrite is True:
        return "w"
    if overwrite is False:
        return "a"
    return ask_existing_action(txt_path) if stdin_is_interactive() else "skip"


def extract_pdf_to_txt(
        pdf_path: Path,
        txt_path: Path,
        overwrite: bool | None = None,
        password: str | None = None,
) -> tuple[int, int] | None:
    """
    提取单个 PDF 文本写入 txt。
    :param pdf_path: PDF 文件路径
    :param txt_path: 输出 txt 文件路径
    :param overwrite: True 覆盖 / False 追加 / None 已存在则询问（非交互环境跳过）
    :param password: 加密 PDF 的密码
    :return: (总页数, 空内容页数)；因文件已存在而跳过时返回 None
    """
    if txt_path.exists():
        action = resolve_write_action(txt_path, overwrite)
        if action == "skip":
            logger.info("跳过（txt 已存在）：%s", txt_path)
            return None
    else:
        action = "w"

    txt_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = txt_path.with_name(txt_path.name + TXT_TMP_SUFFIX)
    try:
        total_pages, empty_pages = _write_pages_to_tmp(pdf_path, txt_path, tmp_path, action, password)
        if total_pages == 0:
            raise PdfEmptyTextError(f"PDF 没有页面：{pdf_path}")
        if len(empty_pages) == total_pages:
            raise PdfEmptyTextError(f"未提取到任何文本内容（可能为扫描件需 OCR）：{pdf_path}")
        os.replace(tmp_path, txt_path)  # 原子替换，避免中断后留下半截文件
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

    if empty_pages:
        logger.warning(
            "%s：空内容页 %s 个，共 %s 页，页码：%s",
            pdf_path.name, len(empty_pages), total_pages, empty_pages,
        )
    return total_pages, len(empty_pages)


def _write_pages_to_tmp(
        pdf_path: Path,
        txt_path: Path,
        tmp_path: Path,
        mode: str,
        password: str | None,
) -> tuple[int, list[int]]:
    """把逐页文本写入临时文件，返回 (总页数, 空内容页页码列表)。"""
    with open(pdf_path, "rb") as fh:  # with 保证 PDF 句柄及时关闭
        reader = PdfReader(fh)
        if reader.is_encrypted:
            if not password:
                raise PdfExtractError(f"PDF 已加密，请用 -p/--password 提供密码：{pdf_path}")
            if not reader.decrypt(password):
                raise PdfExtractError(f"PDF 密码错误：{pdf_path}")

        total_pages = len(reader.pages)
        logger.info("处理文件：%s，总页数：%s，写入模式：%s", pdf_path, total_pages, mode)

        if mode == "a" and txt_path.exists():
            shutil.copyfile(txt_path, tmp_path)  # 追加：基于原内容继续写，最后整体替换
        else:
            tmp_path.unlink(missing_ok=True)

        empty_pages: list[int] = []
        with open(tmp_path, "a", encoding="utf-8") as f:
            if mode == "a" and not _ends_with_newline(tmp_path):
                f.write("\n")
            for i, page in enumerate(reader.pages, start=1):
                try:
                    text = (page.extract_text() or "").replace("\f", "\n")
                except Exception as e:
                    logger.warning("第%s页文本提取失败（按空页处理）：%s：%s", i, pdf_path.name, e)
                    logger.debug("页面提取异常详情", exc_info=True)
                    text = ""
                if not text.strip():
                    empty_pages.append(i)
                    f.write(PAGE_SEP)  # 空页也占一个分页符，保证页码不偏移
                    continue
                f.write(text.rstrip() + PAGE_SEP)
    return total_pages, empty_pages


def _ends_with_newline(path: Path) -> bool:
    """判断文件是否以换行结尾（空文件视为 True）。"""
    if not path.exists() or path.stat().st_size == 0:
        return True
    with open(path, "rb") as f:
        f.seek(-1, os.SEEK_END)
        return f.read(1) == b"\n"


def read_pdf_save_text(
        pdf: str | Path = DEFAULT_INPUT,
        save_txt_path: str | Path = DEFAULT_OUTPUT,
        overwrite: bool | None = None,
        password: str | None = None,
) -> int:
    """
    读取 pdf（文件或目录）并保存为 txt。
    :return: 处理失败（含需 OCR）的文件个数
    """
    pdf_path = Path(pdf)
    try:
        pdf_files = collect_pdf_files(pdf_path)
    except PdfExtractError as e:
        logger.error("%s", e)
        return 1

    base_dir = Path(save_txt_path)
    root = pdf_path if pdf_path.is_dir() else pdf_path.parent
    logger.info("待处理 %s 个文件，输出目录：%s", len(pdf_files), base_dir.resolve())

    failures: list[tuple[Path, str]] = []
    needs_ocr: list[Path] = []
    skipped = 0
    for pdf_file in pdf_files:
        txt_path = base_dir / resolve_txt_path(pdf_file, root)
        try:
            result = extract_pdf_to_txt(pdf_file, txt_path, overwrite, password)
            if result is None:
                skipped += 1
        except PdfEmptyTextError as e:  # 扫描件属于预期情况，只记一行
            logger.error("%s", e)
            needs_ocr.append(pdf_file)
        except PdfExtractError as e:
            logger.error("处理失败：%s", e)
            failures.append((pdf_file, str(e)))
        except Exception as e:
            logger.exception("处理失败：%s", pdf_file)
            failures.append((pdf_file, str(e)))

    ok = len(pdf_files) - len(failures) - len(needs_ocr) - skipped
    logger.info(
        "完成：成功 %s 个，跳过 %s 个，需 OCR %s 个，失败 %s 个",
        ok, skipped, len(needs_ocr), len(failures),
    )
    if needs_ocr:
        logger.warning("以下文件没有可提取的文字，建议接 OCR：")
        for path in needs_ocr:
            logger.warning("  - %s", path.name)
    for path, msg in failures:
        logger.error("  - %s：%s", path.name, msg)
    return len(failures) + len(needs_ocr)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="批量提取 PDF 文本为 txt")
    parser.add_argument("-i", "--input", default=str(DEFAULT_INPUT), help="PDF 文件或目录")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help="txt 输出目录")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--overwrite", action="store_true", help="覆盖已存在的 txt")
    group.add_argument("--append", action="store_true", help="追加到已存在的 txt（会产生重复内容，慎用）")
    parser.add_argument("-p", "--password", default=None, help="加密 PDF 的密码")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出调试日志")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    overwrite = True if args.overwrite else (False if args.append else None)
    failed = read_pdf_save_text(args.input, args.output, overwrite, args.password)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
