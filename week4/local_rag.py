import logging
import sys
import time

from langchain_core.retrievers import BaseRetriever

# Windows 中文环境 stdio 默认非 UTF-8，统一重配置，避免 print 中文报错
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("local_rag")

from langchain_classic.chains import create_retrieval_chain  # noqa: E402
from langchain_classic.chains.combine_documents import create_stuff_documents_chain  # noqa: E402
from langchain_chroma import Chroma  # noqa: E402
from langchain_community.document_loaders import TextLoader  # noqa: E402
from langchain_core.documents import Document  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_ollama import OllamaEmbeddings, ChatOllama  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402

LLM_MODEL = "qwen2.5:7b-instruct-q4_K_M"
EMB_MODEL = "bge-m3"
DB_DIR = "./chroma_local"
LOG_INTERVAL = 50  # 每处理多少个 chunk 打一次进度


class SafeOllamaEmbeddings(OllamaEmbeddings):
    """分批 + 重试的 Ollama embedding，规避本机 Ollama 0.40.17 的服务端 bug。

    现象：一次性 embed 大批量文本（实测 300 条）时，runner 的 tokenize 阶段
    会异常，报 400 / connection refused；100 条以内则 100% 成功。因此这里
    把文本拆成小批逐批请求，并对单批失败做有限重试。
    """

    batch_size: int = 50
    max_retries: int = 3
    retry_interval: float = 0.5

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._client.embed(self.model, texts)["embeddings"]
            except Exception as e:  # noqa: BLE001
                last_err = e
                logger.warning(
                    "  embedding 批次失败（第 %d/%d 次重试）：%s",
                    attempt, self.max_retries, str(e)[:110],
                )
                time.sleep(self.retry_interval)
        raise last_err  # type: ignore[misc]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        batches = [texts[i:i + self.batch_size] for i in range(0, len(texts), self.batch_size)]
        logger.info(
            "  embedding：共 %d 条文本，分 %d 批（每批 ≤%d 条）",
            len(texts), len(batches), self.batch_size,
        )
        vectors: list[list[float]] = []
        for idx, batch in enumerate(batches, 1):
            vectors.extend(self._embed_batch(batch))
            if idx % 10 == 0 or idx == len(batches):
                logger.info("  embedding 进度：%d/%d 批", idx, len(batches))
        return vectors


class LoggingRetriever(BaseRetriever):
    """包装底层向量检索，打印命中分数与片段，便于调试。"""

    store: Chroma
    k: int = 3

    def _get_relevant_documents(self, query, *, run_manager=None):
        logger.info("向量检索：query=%r, k=%d", query, self.k)
        hits = self.store.similarity_search_with_score(query, k=self.k)
        if not hits:
            logger.warning("向量检索：未命中任何片段")
            return []
        for rank, (doc, score) in enumerate(hits, 1):
            logger.info(
                "  命中 #%d | 相似度=%.4f | 字符数=%d | 来源=%s",
                rank, score, len(doc.page_content), doc.metadata.get("source"),
            )
            logger.debug("  片段预览：%s", doc.page_content[:120].replace("\n", " "))
        return [doc for doc, _ in hits]


def main():
    # 1. 加载 + 分块
    src = "../week2/out_text/法律法规类/中华人民共和国民法典_20200528.txt"
    logger.info("步骤1：加载文档 %s", src)
    docs = TextLoader(src, encoding="utf-8").load()
    total_chars = sum(len(d.page_content) for d in docs)
    logger.info("  文档加载完成：%d 个文档, 共 %d 字符", len(docs), total_chars)

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)
    logger.info("步骤2：开始分块 chunk_size=%d, chunk_overlap=%d", 400, 80)
    chunks = []
    for i, chunk in enumerate(splitter.split_documents(docs), 1):
        chunks.append(chunk)
        if i % LOG_INTERVAL == 0:
            logger.info("  分块进度：已生成 %d 个 chunk ...", i)
    logger.info("  分块完成：共 %d 个 chunk（平均每块 %.0f 字符）",
                len(chunks), total_chars / max(len(chunks), 1))

    # 源文本含大段重复（docx 转换残留，如合同编第 465 条附近出现两次），
    # 分块后会切出内容相同的 chunk。按内容去重，避免向量库出现
    # 「id 不同、内容相同」的重复条目。
    before = len(chunks)
    seen: set[str] = set()
    unique_chunks: list[Document] = []
    for c in chunks:
        if c.page_content not in seen:
            seen.add(c.page_content)
            unique_chunks.append(c)
    chunks = unique_chunks
    logger.info("  去重：%d → %d 个 chunk（移除 %d 个内容重复的 chunk）",
                before, len(chunks), before - len(chunks))

    # 2. 本地 embedding + 本地向量库
    logger.info("步骤3：初始化本地 embedding 模型 %s", EMB_MODEL)
    embedding = SafeOllamaEmbeddings(model=EMB_MODEL)
    logger.info("步骤4：连接本地向量库 %s", DB_DIR)
    vector_store = Chroma(
        collection_name="langchain",
        embedding_function=embedding,
        persist_directory=DB_DIR,
    )
    count = vector_store._collection.count()
    if count:
        logger.info("  向量库已有 %d 条，跳过 embedding 直接复用", count)
    else:
        logger.info("  向量为空，开始写入 %d 个 chunk ...", len(chunks))
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embedding,
            persist_directory=DB_DIR,
        )
        logger.info("  向量库就绪：collection=%s, 条数=%d",
                    vector_store._collection.name, vector_store._collection.count())

    retriever = LoggingRetriever(store=vector_store, k=3)

    # 3. 本地 LLM
    logger.info("步骤5：初始化本地 LLM %s", LLM_MODEL)
    llm = ChatOllama(model=LLM_MODEL, temperature=0.3)

    # 4. 全本地 QA 链
    prompt = ChatPromptTemplate.from_template("""
        仅根据参考资料回答，资料没有就说"资料中未提及"，并标注来源。
        
        参考资料：
        {context}
        
        问题：{input}
        """)
    combine = create_stuff_documents_chain(llm, prompt)
    local_rag = create_retrieval_chain(retriever, combine)
    logger.info("步骤6：QA 链组装完成，开始提问")

    q = "怎么离婚"
    result = local_rag.invoke({"input": q})
    print(f"\n问：{q}")
    print(f"答：{result['answer']}")
    print("\n引用片段：")
    for i, d in enumerate(result["context"], 1):
        # 去掉换行符吧
        print(f"  {i}. {d.metadata.get('source')} | {d.page_content[:60].replace('\n', ' ')}")


if __name__ == "__main__":
    main()
