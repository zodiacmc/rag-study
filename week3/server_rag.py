import json
import sys
from pathlib import Path

from starlette.responses import StreamingResponse

from week1.requests_py import llm_client

# 把项目根目录加入 sys.path，保证直接运行脚本能 import util
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from embedding_client import get_embeddings
from week3.TextCleaner import TextCleaner
from retrieve import retrieve
from rag_chain import rag_answer, get_messages

app = FastAPI(title="RAG 问答服务",
              description="这是用于rag学习的文档",  # API 描述
              version="1.0.0",                    # API 版本
              terms_of_service="http://example.com/terms/",  # 服务条款 URL
              contact={                           # 联系信息
                  "name": "开发者",
                  "url": "http://example.com/contact/",
                  "email": "dev@example.com",
              },
              license_info={                      # 许可证信息
                  "name": "MIT",
                  "url": "https://opensource.org/licenses/MIT",
              },
              # docs_url=None, redoc_url=None  # 禁用文档
              )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path(__file__).resolve().parent / "chroma_db"
client = chromadb.PersistentClient(path=str(DB_PATH))
col = client.get_or_create_collection("policy_docs")
splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)

# 上传安全校验：允许的文本后缀与大小上限（5MB）
ALLOWED_SUFFIXES = {".txt", ".md", ".csv"}
MAX_FILE_SIZE = 5 * 1024 * 1024


class AskReq(BaseModel):
    question: str
    top_k: int = 3


@app.get("/health",
         summary="检查服务健康状态",  # 简短摘要
         description="检查服务健康状态", # 详细描述
         response_description="健康状态对象",   # 响应描述

)
def health():
    """"""
    return {"status": "ok", "chunks_in_db": col.count()}


@app.post("/search")
def search(req: AskReq):
    """向量查询"""
    # 需要捕获错误，如果是这个错误，raise ValueError("Failed to get embedding for question")  返回{"chunks": [], "error": "embedding 调用失败"}
    try:
        search_val = retrieve(req.question, req.top_k)
    except ValueError as e:
        return {"chunks": [], "error": str(e)}
    chunks = []
    if not search_val:
        return {"chunks": chunks}
    for doc, dist, meta in search_val:
        chunks.append({
            "text": doc,
            "source": meta["source"],
            "distance": round(float(dist), 4),
        })
    return {"chunks": chunks}


@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    """上传文本文件：校验类型/大小/文件名后清洗、分块、批量向量化入库。"""
    # 1. 文件名安全：去掉路径只取 basename，防止目录穿越；后缀走白名单
    safe_name = Path(file.filename or "").name
    if not safe_name:
        raise HTTPException(status_code=400, detail="文件名为空")

    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"仅支持 {', '.join(sorted(ALLOWED_SUFFIXES))} 类型文件",
        )

    # 2. 大小校验：先看声明大小，再按实际字节复核
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件超过 5MB 上限")

    raw = file.file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件超过 5MB 上限")

    # 3. 解码校验：必须是可读文本（先 UTF-8，再回退 GBK）
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("gbk")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件不是可识别的 UTF-8/GBK 文本")

    # 4. 清洗后判空
    text = TextCleaner().clean(text)
    if not text.strip():
        raise HTTPException(status_code=400, detail="清洗后文本为空，无可入库内容")

    chunks = splitter.split_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="未切分得到任何文本块")

    print(f"  {safe_name} → {len(chunks)} 块")

    # 5. 批量向量化：一次请求多条文本，避免逐条循环调用
    try:
        vecs = get_embeddings(chunks)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"embedding 调用失败: {e}")

    ids = [f"{safe_name}_{i}" for i in range(len(chunks))]
    metas = [{"source": safe_name, "chunk_id": i} for i in range(len(chunks))]

    # upsert：ID 已存在则覆盖，重复灌入不会报重复 ID 错误
    col.upsert(ids=ids, documents=chunks, embeddings=vecs, metadatas=metas)

    return {"added": len(chunks)}


@app.post("/ask")
def ask(req: AskReq):
    """问答"""
    answer, chunks = rag_answer(req.question, req.top_k)
    return {
        "answer": answer,
        "sources": list({c[:20] for c in chunks}),  # 去重后的片段摘要
    }


@app.post("/ask/stream")
def ask_stream(req: AskReq):
    rtn = get_messages(req.question, req.top_k)
    messages = rtn[0]

    def generate():
        # 这里逐段 yield
        for chunk in llm_client.chat_stream2(messages):
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")



@app.get("/list")
def list_files():
    """列出数据库中的文件"""
    # 遍历 col.get() 的 metadatas，按 source 去重
    col_get = col.get()

    rtn_val = {"files": []}
    if col_get is not None and col_get["metadatas"]:
        files = set()
        for meta in col_get["metadatas"]:
            files.add(meta["source"])
        rtn_val["files"] = list(files)
    return rtn_val


if __name__ == "__main__":
    import asyncio
    import uvicorn

    # 不直接用 uvicorn.run()，因为新版 uvicorn 会传 loop_factory 参数，
    # 与 IDEA pydevd 调试器不兼容（TypeError: run() got an unexpected keyword argument 'loop_factory'）。
    # 手动构造 Server 并用 asyncio.run() 启动，断点调试正常。
    config = uvicorn.Config(app, host="127.0.0.1", port=8000)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())
