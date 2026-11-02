"""
这是练习的一些内容在这边
"""

# str='123456789'
#
# print(str)                 # 输出字符串
# print(str[0:-1])           # 输出第一个到倒数第二个的所有字符
# print(str[0])              # 输出字符串第一个字符
# print(str[2:5])            # 输出从第三个开始到第六个的字符（不包含）
# print(str[2:])             # 输出从第三个开始后的所有字符
# print(str[1:5:2])          # 输出从第二个开始到第五个且每隔一个的字符（步长为2）
# print(str * 2)             # 输出字符串两次
# print(str + '你好')         # 连接字符串
#
# print('------------------------------')
#
# print('hello\nrunoob')      # 使用反斜杠(\)+n转义特殊字符
# print(r'hello\nrunoob')     # 在字符串前面添加一个 r，表示原始字符串，不会发生转义


# import sys;
# x = 'runoob';
# sys.stdout.write(x + '\n')
# sys.stdout.write(" hi ")


# import sys
# print('================Python import mode==========================')
# print ('命令行参数为:')
# for i in sys.argv:
#     print (i)
# print ('\n python 路径为',sys.path)

# from sys import argv,path  #  导入特定的成员

# print('================python from import===================================')
# print('path:',path) # 因为已经导入path成员，所以此处引用时不需要加sys.path


# a = 1
# b = "2"
# c = True
# d = 3.13
#
# print(type(a))
# print(type(b))
# print(type(c))
# print(type(d))


# 布尔类型的值和类型
# a = True
# b = False
# print(type(a))  # <class 'bool'>
# print(type(b))  # <class 'bool'>

# 布尔类型的整数表现
# print(int(True))   # 1
# print(int(False))  # 0

# 使用 bool() 函数进行转换
# print(bool(0))          # False
# print(bool(42))         # True
# print(bool(''))         # False
# print(bool('Python'))   # True
# print(bool([]))         # False
# print(bool([1, 2, 3]))  # True
#
# # 布尔逻辑运算
# print(True and False)  # False
# print(True or False)   # True
# print(not True)        # False
#
# # 布尔比较运算
# print(5 > 3)   # True
# print(2 == 2)  # True
# print(7 < 4)   # False
#
# # 布尔值在控制流中的应用
# if True:
#     print("This will always print")
#
# if not False:
#     print("This will also always print")
#
# x = 10
# if x:
#     print("x 是非零值，在布尔上下文中为 True")


# !/usr/bin/python3

# my_list = ['abcd', 786, 2.23, 'runoob', 70.2]  # 避免使用 list 作为变量名，会覆盖内置类型
# tinylist = [123, 'runoob']
#
# print(my_list)             # 打印整个列表：['abcd', 786, 2.23, 'runoob', 70.2]
# print(my_list[0])          # 打印第一个元素（索引 0）：abcd
# print(my_list[1:3])        # 打印索引 1 和 2 的元素（不含索引 3）：[786, 2.23]
# print(my_list[2:])         # 打印从索引 2 开始到末尾的所有元素：[2.23, 'runoob', 70.2]
# print(tinylist * 2)        # 重复打印 tinylist 两次：[123, 'runoob', 123, 'runoob']
# print(my_list + tinylist)  # 拼接两个列表


# def reverseWords(input):
#
#     # 通过空格将字符串分隔，把各个单词分隔为列表
#     inputWords = input.split(" ")
#
#     # inputWords[-1::-1] 三个参数说明：
#     # 第一个参数 -1 表示从最后一个元素开始
#     # 第二个参数为空，表示移动到列表开头
#     # 第三个参数 -1 表示逆向步进（每次向左移动一个位置）
#     inputWords = inputWords[-1::-1]
#
#     # 重新用空格拼接单词
#     output = ' '.join(inputWords)
#
#     return output
#
# if __name__ == "__main__":
#     input = 'I like runoob'
#     rw = reverseWords(input)
#     print(rw)


# !/usr/bin/python3

# sites = {'Google', 'Taobao', 'Runoob', 'Facebook', 'Zhihu', 'Baidu'}
# list = [1, 2, 3, 4, 5]
#
# print(sites)   # 输出集合（无序，重复元素会被自动去掉）
#
# for i, v in enumerate(sites) :
#     print(i, v)
# else:
#     print("执行完成")
#
# print("--------------")
#
# for i in range(0,5) :
#     if i > 2 :
#         print(i)
#         print(list[i])
#     else:
#         print(-i)

# file = open("D:\\my_project\\rag-study\\test\\读取测试文件.txt", 'r', encoding='utf-8')
#
# try :
#     content = file.read();
#     print(content)
# finally:
#     file.close()
#
#
# print("-----------")
#
# with open("D:\\my_project\\rag-study\\test\\读取测试文件.txt", 'r', encoding='utf-8') as file :
#     content = file.read();
#     print(content)


# from contextlib import contextmanager
#
# @contextmanager
# def tag(name):
#     print(f"<{name}>")
#     yield
#     print(f"</{name}>")
#
# # 使用示例
# with tag("h1"):
#     print("这是一个标题")
#
#
# def read_file(file_path):
#     with open(file_path, 'r', encoding='utf-8') as file1:
#         content1 = file1.read()
#         print(content1)
#
#
# read_file("D:\\my_project\\rag-study\\test\\读取测试文件.txt")


# numbers = [1, 3, 6]
# newNumbers = tuple(map(lambda x: x , numbers))
# print(newNumbers)


# def decorator_function(original_function):
#     def wrapper(*args, **kwargs):
#         # 调用前
#         print("执行前")
#
#         result = original_function(*args, **kwargs)
#
#         # 调用后
#         print("执行后")
#
#         return result
#     return wrapper
#
#
#
# @decorator_function
# def target_function():
#     print("原函数执行")
#
# target_function()


# print(__name__)
# print(__file__)
#
#
# x = 10
# if x > 5:
#     raise Exception('x 不能大于 5。x 的值为: {}'.format(x))

# 复杂类型注解


# a: int = 1
#
# numbers: List[int] = [1, 2, 3, 4, 5]
#
# def fnc(mm: str = '2222') -> str:
#     global a
#     a = 4
#     b:int = 2
#     c:str = ''
#     d:set = {1,2}
#     print(a, b, c, d, mm)
#     return f"aaaaa {mm}"
#
#
# def fnc2():
#     print(a)
#
#
# str1 = fnc('1')
# fnc2()
#
# print(str1)

# numbers: List[int] = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
#
# minNum: int = min(numbers)
# maxNum: int = max(numbers)
#
# print(minNum, maxNum)

# class MyClass:
#     def __init__(self, name:str, age:int):
#         self.name:str = name
#         self.age:int = age
#
#     @classmethod
#     def test_class_method(cls, name:str, age:int) -> "MyClass":
#         return cls(name, age)
#
# classA = MyClass.test_class_method("姓名", 10)
# print(classA.name, classA.age)


# for i in range(1, 10):
#     for j in range(1, i + 1):
#         print(f"{i} * {j} = {i * j}", end="\t")
#     print("")

# a = [1,2,3,None,(),[],]
# print(len(a))
