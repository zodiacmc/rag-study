import os
from pathlib import Path


# 读取文件并输出
def read_file(path: str):
    with open(path, 'r', encoding='utf-8') as file:
        print(file.read())


# 读取文件 一行一行读，节约内存
def read_file2(path: str):
    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            print(line.strip())


# 写文件
def write_file(path: str):
    with open(path, 'a', encoding='utf-8') as file:
        file.write("Hello, World!\n")
        file.write("写入第二行\n")


# read_file("D:\\my_project\\rag-study\\test\\testfile\\读取测试文件.txt")
# read_file2("D:\\my_project\\rag-study\\test\\testfile\\读取测试文件.txt")
# write_file("D:\\my_project\\rag-study\\test\\testfile\\读取测试文件.txt")

# 当前目录
current_directory = os.getcwd()
print("获取当前目录：", end='')
print(current_directory)

path_obj = Path(current_directory)
# 路径拼接
path = path_obj / 'testfile' / '读取测试文件.txt'  # 用 / 拼接，跨平台安全
path_obj2 = Path(path)
print("地址拼接：", end='')
print(path)

print("path路径对应的文件是否存在：", end='')
print(Path(path).exists())
print("path是否是文件：", end='')
print(path_obj2.is_file())
print("path是否是路径；", end='')
print(path_obj2.is_dir())

# 常用方法
print("path的文件名：", end='')
print(path_obj2.name)  # 文件名 a.txt
print("path的扩展名：", end='')
print(path_obj2.suffix)  # 扩展名 .txt
print("path的去扩展名：", end='')
print(path_obj2.stem)  # 去扩展名 a

print("================")
# 批量读取文件夹里面的txt文件
test_file_folder = Path(current_directory + '\\testfile')
for file in test_file_folder.iterdir():
    if file.is_dir():
        print("找到一个文件夹：", file.name)
        continue
    elif file.is_file():
        is_txt = file.suffix == '.txt'
        print("找到一个文件：", file.name, '，并且他', '是txt文件' if is_txt else '不是一个txt')

print("=============遍历文件夹里面所有的指定文件==================")
# 遍历文件家里面所有的指定文件
for file in test_file_folder.rglob("*.txt"): # rglob 遍历当前目录下及其子目录 glob 不会遍历子目录
    print(file.name)
