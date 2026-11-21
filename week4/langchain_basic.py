
"""
LangChain 基本用法
"""
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，保证直接运行脚本能 import util
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from util.GetProperties import GetProperties

# ChatOpenAI 的 base_url 是 OpenAI 兼容根地址，SDK 会自动拼接 /chat/completions；
API_URL = GetProperties().get_property("longcat", "longcat_api_base_url")
API_KEY = GetProperties().get_property("longcat", "longcat_apikey")
MODEL_NAME = GetProperties().get_property("longcat", "longcat_model_name")


# 1. 模型（OpenAI 兼容端点，换成你自己的模型和 Key）
llm = ChatOpenAI(
    model=MODEL_NAME,
    base_url=API_URL,
    api_key=API_KEY,
    temperature=0.7,
)

# 2. 提示词模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，回答简洁准确，不编造资料外的信息。"),
    ("user", "{question}"),
])

# 3. 组装链：模板 → 模型 → 文本解析
chain = prompt | llm | StrOutputParser()

if __name__ == "__main__":
    # 非流式调用
    answer = chain.invoke({
        "role": "知识库助手",
        "question": "用一句话解释什么是向量数据库",
    })
    print("【非流式】", answer)

    # 流式调用
    print("\n【流式】")
    for chunk in chain.stream({
        "role": "知识库助手",
        "question": "讲一下 RAG 的基本流程",
    }):
        print(chunk, end="", flush=True)

