# 边界重叠分析
from langchain_text_splitters import RecursiveCharacterTextSplitter

from TextCleaner import TextCleaner

src = "../week2/out_text/产品手册类/debian-参考手册.zh-cn.txt"
text = TextCleaner().clean(open(src, encoding="utf-8").read())

sp = RecursiveCharacterTextSplitter(
    chunk_size=400, chunk_overlap=80,
    separators=["\n\n", "\n", "。", "，", " ", ""])
chunks = sp.split_text(text)


def overlap_len(a, b):
    for i in range(min(len(a), len(b), 120), 0, -1):
        if a.endswith(b[:i]):
            return i
    return 0


ov = [overlap_len(chunks[i], chunks[i + 1]) for i in range(len(chunks) - 1)]
nz = [x for x in ov if x > 0]
print(f"总块数 {len(chunks)}，边界 {len(ov)}")
print(f"有重叠边界 {len(nz)}，平均重叠 {sum(nz) // len(nz)} 字，最大 {max(nz)}")
print(f"零重叠边界 {len(ov) - len(nz)} 对 ({(len(ov) - len(nz)) * 100 // len(ov)}%)")

# 单句长度（按句号切）
sents = [s for s in text.split("。") if s.strip()]
print(
    f"\n按句号切出的句子数 {len(sents)}，平均句长 {sum(len(s) for s in sents) // len(sents)} 字，最长 {max(len(s) for s in sents)} 字")

# 前 4 个边界的重叠
for i in range(4):
    print(f"\n--- 边界 {i} 重叠 {ov[i]} 字 ---")
    print(f"上一块尾: ...{chunks[i][-30:]}")
    print(f"下一块头: {chunks[i + 1][:30]}...")
