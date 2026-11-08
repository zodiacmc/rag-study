# 对文本进行分块
# pip install langchain-text-splitters
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from TextCleaner import TextCleaner

def test_text_chunking():
    """测试对文本进行分块"""
    text = open("../week2/out_text/法律法规类/中华人民共和国民法典_20200528.txt", encoding="utf-8").read()
    text = TextCleaner().clean(text)

    print(f"原文长度：{len(text)} 字")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,  # 每块约 400 字
        chunk_overlap=80,  # 重叠 80 字
        separators=["\n\n", "\n", "。", "，", " ", ""]  # 优先在段落/句号处切
    )

    chunks = splitter.split_text(text)
    print(f"切成了 {len(chunks)} 块")
    print("---第1块---")
    print(chunks[0])
    print("---第2块---")
    print(chunks[1])

    # 不同块大小的对比
    for size in [200, 400, 800]:
        sp = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=size // 5)
        cs = sp.split_text(text)
        print(f"块大小={size} → {len(cs)} 块，平均 {len(text) // len(cs)} 字/块")


def file_text_chunking(file:str):
    """对文件进行分块"""
    # 空判断和是否是txt文件
    if file is None or file == "" or not Path(file).is_file() or not file.endswith(".txt"):
        print("请传入正确的文件路径")
        return
    text = ""
    try :
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
        if text == "":
            print("文件内容为空")
            return

        text = TextCleaner().clean(text) # 先都去清理一下吧
        print(f"文件内容长度：{len(text)} 字")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,  # 每块约 400 字
            chunk_overlap=80,  # 重叠 80 字
            separators=["\n\n", "\n", "。", "，", " ", ""]  # 优先在段落/句号处切
        )
        chunks = splitter.split_text(text)
        print(f"切成了 {len(chunks)} 块")
        print("---第1块---")
        print(chunks[0])
        print("---第2块---")
        print(chunks[1])

    except Exception as e:
        print(f"读取文件出错：{e}")
        return


if __name__ == "__main__":
    # test_text_chunking()
    file_text_chunking("../week2/out_text/产品手册类/debian-参考手册.zh-cn.txt")
    file_text_chunking("../week2/out_text/产品手册类/LibreOffice 6.2 快速参考指南.txt")
