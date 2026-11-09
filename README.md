# rag-study — RAG 应用工程师学习仓库

## 项目简介

8周系统学习 RAG（检索增强生成）应用开发，目标：私有知识库
问答系统的搭建、开源项目改造、接单与求职。

## 环境

- Python 3.11+，Windows + RTX4060（本地可跑7B量化模型）
- 依赖：requests / pypdf / pdfplumber / openpyxl / langchain / chromadb（逐周添加）

## 目录

- week1/：Python基础 + 大模型API调用（见各文件头注释）
    - llm_client.py：可复用的大模型对话函数（流式/非流式）
- week2/：文档解析 + 简易后端
    - read_pdf.py / read_word.py：PDF、Word 解析为纯文本
    - server.py：FastAPI 后端，提供非流式 `/ask` 与流式 `/ask/stream` 接口
    - chat_html/：前端问答页面（流式输出、思考中动画、请求锁、空文本校验）
- week3/：Embedding、文本分块与向量库检索（Day15–Day18）
    - embedding_client.py：调用阿里云 qwen3-vl-embedding 把文本转向量；手写余弦相似度，对问题与候选句子算相似度并逆序排序
    - TextCleaner.py：文档文本清洗器（Unicode 规范化、去控制字符/页眉页脚水印、短行合并、CJK 空格清理、压缩空行）
    - chunking_demo.py：用 RecursiveCharacterTextSplitter 分块，对比 chunk_size=200/400/800 的块数与效果
    - diag_chunk.py：相邻块重叠（chunk_overlap）统计诊断脚本
    - chroma_demo.py：Chroma 本地向量库 Demo，集合创建、写入向量与元数据、相似度查询（query_embeddings）
    - ingest.py：入库链路——读 txt → 清洗 → 分块 → 算 embedding → upsert 写入 Chroma
    - retrieve.py：检索链路——问题算向量 → query_embeddings 检索 TopK → 打印命中片段、距离与来源
    - diag_chroma.py：Chroma 通用排查脚本（sqlite 直读 + 客户端核对条数/维度/样本）

## 运行

```
pip install requests
pip install pypdf pdfplumber
pip install python-docx openpyxl
pip install fastapi uvicorn
pip install langchain langchain-text-splitters
```

## 进度

- [x] 第1周：环境 + Python基础 + API调用
- [x] 第2周：文档解析 + 简易后端
- [~] 第3周：RAG核心 —— Day15 Embedding、Day16 文本分块（进行中）
- [ ] 第3-5周：RAG核心（向量库/检索/LangChain/Ollama）
- [ ] 第6-7周：开源项目作品集
- [ ] 第8周：求职 + 接单

## 已完成能力（前两周）

- ✅ 环境搭建：Python/venv/Github
- ✅ 大模型 API 调用：非流式/流式/多轮
- ✅ 多格式文档解析：PDF/Word/Excel → 纯文本
- ✅ 端到端 Demo：网页提问 → 后端 → 大模型 → 流式回答

## 已完成能力（第三周 Day15–Day17）

- ✅ 文本向量化：API 生成 Embedding 向量，余弦相似度计算与相似度排序
- ✅ 文本清洗：去水印/控制字符、合并短行、清理中英文混排空格
- ✅ 文本分块：递归字符切分器，可调块大小（chunk_size）与重叠（chunk_overlap）
- ✅ 向量库 Chroma：本地持久化集合，写入向量/文本/元数据，按向量做相似度检索

### Day16 分块踩坑备忘

- LangChain 0.1 起包拆分：`langchain.text_splitter` 已移除，需 `pip install langchain-text-splitters` 并从 `langchain_text_splitters` 导入。
- `chunk_overlap` 是"按整句/整段保留的重叠预算"，不是固定复制前一块末尾 N 个字；句子长于预算或边界落在句中时，该相邻块可能零重叠。验证时看最大重叠是否接近设定值，不要逐块肉眼找重复。

### Day17 Chroma 踩坑备忘

- 查询参数是复数 `query_embeddings=[[向量]]`，不是 `query_embedding`；批量接口单个向量也要外层包一层列表。
- 首次用 `query_texts` 会下载默认 ONNX 模型（S3，国内慢）；插入和查询必须用同一个 embedding 模型，占位向量与查询向量不在同一向量空间，相似度不可信。
- 集合维度按首批向量锁定：旧占位 3 维集合再写入 2560 维真实向量会报维度冲突，需 `delete_collection` 删旧集合重建；真实入库后改用 `upsert` 增量灌库。
