import os
from pathlib import Path

'''
读取文件夹下所有txt文件
1、注意文件编码问题
2、Windows 路径手写反斜杠 → 换行转义冲突，用 Path 拼接
3、注意异常处理
'''

os_folder = os.getcwd()  # 当前系统路径
txt_folder_path = Path(os_folder) / ".." / "test" / "testfile"  # 进去测试的文件夹

success, failed, total = 0, 0, 0

for file in txt_folder_path.rglob("*.txt"):
    try:
        text = file.read_text(encoding='utf-8')
        success += 1
        print(f'读取文件{file.name}成功，其中一个{len(text)}字')
    except Exception as e:
        failed += 1
        print(f"读取文件{file.name}失败，失败原因{e}")
    finally:
        total += 1

print(f"本次获取到txt文件一共{total}个，其中读取成功{success}份，读取失败{failed}份")
