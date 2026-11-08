from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sys, os
# 将项目根目录（rag-study，即 week2 的上一级）加入 sys.path，
# 这样无论从哪个目录启动 uvicorn，都能找到 week1 包
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)
from week1.requests_py import llm_client      # Day6 写的 chat()

app = FastAPI()

# 允许前端页面跨域访问（本地开发必加）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

class AskReq(BaseModel):
    question: str

@app.post("/ask")
def ask(req: AskReq):
    messages = [
        {"role": "system", "content": "你是知识库助手，回答简洁，根据知识库回答，不要回答其他内容。如果没有则回答不知道"},
        {"role": "user", "content": req.question},
    ]
    answer = llm_client.chat(messages)
    return {"answer": answer}

@app.get("/health")
def health():
    return {"status": "ok"}


from fastapi.responses import StreamingResponse
import json

@app.post("/ask/stream")
def ask_stream(req: AskReq):
    messages = [
        {"role": "system", "content": "你是知识库助手"},
        {"role": "user", "content": req.question},
    ]

    def generate():
        # 这里逐段 yield
        for chunk in llm_client.chat_stream2(messages):
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import asyncio
    import uvicorn
    # 不直接用 uvicorn.run()，因为新版 uvicorn 会传 loop_factory 参数，
    # 与 IDEA pydevd 调试器不兼容（TypeError: run() got an unexpected keyword argument 'loop_factory'）。
    # 手动构造 Server 并用 asyncio.run() 启动，断点调试正常。
    config = uvicorn.Config(app, host="127.0.0.1", port=8000)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())

