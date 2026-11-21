import sys
from pathlib import Path

# 把项目根目录加入 sys.path，保证直接运行脚本能 import util / week3
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import TextLoader
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from util.GetProperties import GetProperties
from week3.embedding_client import get_embeddings

LONGCAT_API_URL = GetProperties().get_property("longcat", "longcat_api_base_url")
LONGCAT_API_KEY = GetProperties().get_property("longcat", "longcat_apikey")
MODEL_NAME = GetProperties().get_property("longcat", "longcat_model_name")


class DashScopeEmbeddings(Embeddings):
    """复用 week3 的阿里云多模态 embedding，适配 LangChain 的 Embeddings 接口。"""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return get_embeddings(texts)

    def embed_query(self, text: str) -> list[float]:
        return get_embeddings([text])[0]


def rag_langchain(input_str: str, input_docs):
    print("RAG with LangChain")
    # 1. 加载
    # docs = TextLoader("test_docs/_txt/民法典.txt", encoding="utf-8").load()

    # 2. 分块
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, chunk_overlap=80,
        separators=["\n\n", "\n", "。", "，", " ", ""]
    )
    chunks = splitter.split_documents(input_docs)

    print(f"分块数: {len(chunks)}")

    # 3. 向量化 + 存库：复用 week3 的阿里云多模态 embedding 封装
    embeddings = DashScopeEmbeddings()

    # 确定性 ID：来源文件名 + 块序号。重复运行时 upsert 按同一 ID 覆盖，避免随机 UUID 导致重复块累积。
    source_name = Path(chunks[0].metadata.get("source", "doc")).name if chunks else "doc"
    ids = [f"{source_name}_{i}" for i in range(len(chunks))]

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        ids=ids,
        persist_directory="./chroma_db_langchain",
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # 4. 模型 + 提示词 + QA 链
    llm = ChatOpenAI(model=MODEL_NAME, base_url=LONGCAT_API_URL,
                     api_key=LONGCAT_API_KEY, temperature=0.3)

    prompt = ChatPromptTemplate.from_template("""
    仅根据下面的参考资料回答问题，资料没有就说"资料中未提及"，并标注来源。
    
    参考资料：
    {context}
    
    问题：{input}
    """)

    combine_chain = create_stuff_documents_chain(llm, prompt) # 创建结合文档的链
    rag_chain = create_retrieval_chain(retriever, combine_chain) # 创建检索链

    result = rag_chain.invoke({"input": input_str})
    print("回答：", result["answer"])
    print("\n引用片段：")
    for doc in result["context"]:
        print(" -", doc.metadata.get("source"), "|", doc.page_content[:60])


if __name__ == "__main__":
    docs = TextLoader("../week2/out_text/中华人民共和国婚姻法_20010428.txt", encoding="utf-8").load()
    rag_langchain("婚姻法是什么时候开始实施的？", docs)

