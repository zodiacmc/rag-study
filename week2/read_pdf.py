from pathlib import Path

from pypdf import PdfReader


def read_pdf_save_text(pdf: str, save_txt_path: str = "./out_text/"):
    """
    读取pdf文件并保存为txt文件，
    :param pdf: 文件路径 传入的可能是路径，也可能是具体的pdf文件，如果是路径，需要拿到里面所有的pdf文件，挨个写入到txt文件中
    :param save_txt_path: 保存的txt文件路径
    :return:
    """
    # 先拿到当前路径
    pdf_path = Path(pdf)  # 拼接路径
    # 判断当前路径是否存在
    if not pdf_path.exists():
        print(f"路径{pdf_path}不存在，请确认路径是否正确【{pdf_path.resolve()}】")
        return
    # 判断当前路径是文件还是文件夹
    if pdf_path.is_file():
        # 是文件，直接调用保存方法
        msg = save_txt(pdf_path, save_txt_path)
        if msg != "":
            print(f"保存文件异常：{msg}")
    elif pdf_path.is_dir():
        # 是文件夹
        print(f"正在处理文件夹：{pdf_path.resolve()}")
        # 拿到文件夹下的pdf文件， 判断一下是否存在pdf
        pdf_list = list(pdf_path.rglob("*.pdf"))
        if not any(pdf_list):
            print(f"文件夹下不存在pdf文件：{pdf_path.resolve()}")
            return
        print(f"文件夹下存在pdf文件：{len(pdf_list)}个，正在处理中...")
        err_file_name_list = []
        for pdf_file in pdf_path.rglob("*.pdf"):
            msg = save_txt(pdf_file, save_txt_path)
            if msg != "":
                print(f"保存文件{pdf_file.resolve()}异常：{msg}")
                err_file_name_list.append(pdf_file.resolve())
        # 如果有异常文件，才输出异常文件个数以及异常文件列表
        if err_file_name_list:
            print(f"保存文件异常：{len(err_file_name_list)}个，共处理{len(pdf_list)}个文件，完成")
            print(f"异常文件列表：{err_file_name_list}")
        else:
            print(f"保存文件完成，共处理{len(pdf_list)}个文件")
    else:
        print(f"路径{pdf_path}既不是文件也不是文件夹，请确认路径是否正确【{pdf_path.resolve()}】")


def save_txt(pdf_path: Path, save_txt_path: str) -> str:
    """
    保存pdf内容到txt文件
    :param pdf_path: pdf文件路径
    :param save_txt_path: 保存的txt文件路径
    :return: 保存成功标识，如果没有返回内容，说明保存成功，如果返回的不是空串，则标识保存文件异常
    """
    if pdf_path is None:
        return "文件不能为空"
    if save_txt_path is None or save_txt_path == "":
        return "保存的txt文件路径不能为空"

    # 判断当前路径是否存在且是一个文件
    if not pdf_path.exists():
        return f"pdf文件不存在：{pdf_path}"
    if not pdf_path.is_file():
        return f"pdf文件路径不是一个文件：{pdf_path}"

    # 读取pdf文件，保存到对于路径中去
    # 获取没有后缀的文件名称
    file_name = pdf_path.stem + ".txt"
    txt_path = Path(save_txt_path) / file_name

    save_type = "a"  # 保存模式，a表示追加，w表示覆盖
    # 判断保存路径是否存在，如果不存在则创建，如果存在则询问用户是否覆盖写还是追加
    if txt_path.exists():
        save_type = input(f"文件【{txt_path}】已存在，是否覆盖写（w）还是追加（a）？（默认追加）：")
        while save_type not in ["w", "a"]:
            save_type = input("输入错误，请重新输入(w/a)：")
    # 如果是覆盖写，则删除原文件
    if save_type == "w":
        txt_path.unlink(missing_ok=True)

    # 创建保存路径
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    # 创建保存的txt文件
    txt_path.touch(exist_ok=True)
    # 读取pdf文件，每一页遍历写入
    all_text = False  # 是否存在内容
    try:
        reader = PdfReader(pdf_path)
        none_page_list = []  # 页码列表，用于保存内容为空的页码
        print(f"正在处理文件：{pdf_path.resolve()}，总页数：{len(reader.pages)}")
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text is None or text == "":
                print(f"文件：{pdf_path.resolve()}，第{i + 1}页，内容为空")
                none_page_list.append(i + 1)
            else:
                print(f"正在处理文件：{pdf_path.resolve()}，第{i + 1}页、、、")
                all_text = True
                with open(txt_path, "a", encoding="utf-8") as f:
                    f.write(text)

        err_page_count = len(none_page_list)
        if err_page_count > 0:
            print(f"文件：{pdf_path}，\
            内容为空的页码有：{none_page_list}，\
            总页数：{len(reader.pages)}，\
            为空的页码：{err_page_count}")
    except Exception as e:
        return f"读取pdf【{pdf_path.resolve()}】文件并写入【{txt_path.resolve()}】异常，中止读取：{e}"

    # 如果获取到的内容全部为空，说明没有提取到内容，将txt文件删除
    if not all_text:
        print(f"文件【{pdf_path}】没有提取到内容，已删除空文件【{txt_path.resolve()}】")
        txt_path.unlink(missing_ok=True)
        return "未获取到文件内容"
    print(f"文件【{pdf_path.resolve()}】保存成功，保存路径【{txt_path.resolve()}】")

    return ""


read_pdf_save_text("../test_docs/")
# path = Path("../test_docs/法律法规类/")
# pdf_list = path.rglob("*.pdf")
# print(sum(1 for _ in pdf_list))


import pdfplumber

# 基于当前脚本定位项目根目录，避免受运行工作目录影响
# PDF_PATH = Path(__file__).resolve().parent.parent / "test_docs" / "法律法规类" / "中华人民共和国劳动合同法_20121228.pdf"
#
# def extract_with_pdfplumber(pdf_path: Path):
#     if not pdf_path.exists():
#         print(f"文件不存在：{pdf_path}")
#         return
#     with pdfplumber.open(pdf_path) as pdf:
#         print(f"总页数：{len(pdf.pages)}")
#         for i, page in enumerate(pdf.pages):
#             # 先输出该页的文本对象/图片对象数量，用于判断是否为扫描件
#             print(f"--- 第{i + 1}页 chars={len(page.chars or [])} images={len(page.images or [])} ---")
#             text = page.extract_text(layout=True)
#             if text:
#                 print(text)
#             else:
#                 print(f"第{i + 1}页未提取到文本（可能是扫描图片版，需OCR）")
#             for t in page.extract_tables():
#                 for row in t:
#                     print("表格行：", row)

# extract_with_pdfplumber(PDF_PATH)