# rag-study — RAG 应用工程师学习仓库

## 项目简介

8 周系统学习 RAG（检索增强生成）应用开发，目标：私有知识库

问答系统的搭建、开源项目改造、接单与求职。

## 环境



* Python 3.11+，Windows + RTX4060（本地可跑 7B 量化模型）

* 依赖：requests /pypdf/pdfplumber /openpyxl/langchain /chromadb（逐周添加）

## 目录



* week1/：Python 基础 + 大模型 API 调用（见各文件头注释）


  * llm\_client.py：可复用的大模型对话函数（流式 / 非流式）

* week2/：文档解析 + 简易后端


  * read\_pdf.py/read\_word.py：PDF、Word 解析为纯文本

  * server.py：FastAPI 后端，提供非流式 `/ask` 与流式 `/ask/stream` 接口

  * chat\_html/：前端问答页面（流式输出、思考中动画、请求锁、空文本校验）

* week3/：Embedding、文本分块、向量库检索、RAG 链路与接口（Day15–Day20）


  * embedding\_client.py：调用阿里云 qwen3-vl-embedding 把文本转向量；手写余弦相似度，对问题与候选句子算相似度并逆序排序

  * TextCleaner.py：文档文本清洗器（Unicode 规范化、去控制字符 / 页眉页脚水印、短行合并、CJK 空格清理、压缩空行）

  * chunking\_demo.py：用 RecursiveCharacterTextSplitter 分块，对比 chunk\_size=200/400/800 的块数与效果

  * diag\_chunk.py：相邻块重叠（chunk\_overlap）统计诊断脚本

  * chroma\_demo.py：Chroma 本地向量库 Demo，集合创建、写入向量与元数据、相似度查询（query\_embeddings）

  * ingest.py：入库链路 —— 读 txt → 清洗 → 分块 → 算 embedding → upsert 写入 Chroma

  * retrieve.py：检索链路 —— 问题算向量 → query\_embeddings 检索 TopK → 去重后打印命中片段、距离与来源

  * rag\_chain.py：最小 RAG 链 —— 检索片段 + 来源 → 拼上下文 → 约束 Prompt → 调大模型生成

  * diag\_chroma.py：Chroma 通用排查脚本（sqlite 直读 + 客户端核对条数 / 维度 / 样本）

  * server\_rag.py：RAG 后端 FastAPI 服务，提供 /health、/search、/upload、/ask、/ask/stream 接口；文件上传需 python-multipart

* week4/：LangChain 入门 + 本地 Ollama RAG + 检索优化（Day22–Day27）


  * langchain\_basic.py（Day22）：PromptTemplate | ChatOpenAI | StrOutputParser 最小链，非流式 + 流式调用

  * rag\_langchain.py（Day23）：LangChain 版 RAG 链；自定义 DashScopeEmbeddings 复用 week3 向量化；确定性 ID 幂等入库

  * local\_chat\_cli.py：本地 Ollama 命令行多轮对话脚本（流式输出、保留历史）；顶部常量 `MODEL_BACKEND` 可切换本地 /longcat 后端，`OLLAMA_MODEL` 可改模型名；运行 `python week4/local_chat_cli.py`（本地后端需先启动 Ollama 并拉取模型，longcat 后端需配置 week1 的 longcat 属性）

  * ollama\_client.py：本地 Ollama 的 OpenAI 兼容对话封装，`local_chat` 非流式 / `local_chat_stream` 流式

  * local\_rag.py（Day25）：全本地 RAG——bge-m3 embedding + Chroma `chroma_local` + ChatOllama；`SafeOllamaEmbeddings` 分批重试规避本机 Ollama 大批量 embed 缺陷

  * retrieval\_optimized.py（Day27）：混合检索优化版 —— 向量召回 + BM25（jieba 分词）关键词召回，RRF 融合去重，向量距离 / BM25 分数双阈值兜底，复用本地库与本地 LLM 生成

* week5/：复杂文档解析 + 开源 RAG 部署选型 + 自研前端（Day29–Day35，细化文档见计划表 H 列）


  * Day29 复杂文档解析：MinerU / Docling 对比，扫描件 OCR、表格还原、图片 VLM 图注

  * Day30 MaxKB：Docker Compose 部署，对接本地 Ollama，建知识库问答

  * Day31 RAGFlow / LocalGPT：部署第二个开源 RAG，对照产品型与代码型定位

  * Day32 AnythingLLM：工作区多文档问答，易用性评估

  * Day33 自研前端：上传 + 流式问答 + 引用展示，接自研 FastAPI 后端（辅线 FDE）

  * Day34 方案对比：MaxKB / RAGFlow / AnythingLLM / 自研横向对比，定主打与备选

  * Day35 复盘周5：部署经验归档、多方案演示、能力清单与作品集规划

## 运行



```
pip install requests
pip install pypdf pdfplumber
pip install python-docx openpyxl
pip install fastapi uvicorn
pip install langchain langchain-text-splitters
pip install python-multipart   # FastAPI 表单 / 文件上传需要这个依赖
```

## 进度



* [x] 第 1 周：环境 + Python 基础 + API 调用

* [x] 第 2 周：文档解析 + 简易后端

* [x] 第 3 周：RAG 核心 —— Day15–Day20（Embedding / 分块 / 向量库 / 入库检索 / 接口 / RAG 链路）

* [x] 第 4 周：LangChain + 本地 Ollama + 检索优化（Day22–Day27）

* [ ] 第 5 周：复杂文档解析 + 开源 RAG 部署选型

* [ ] 第 6-7 周：开源项目作品集

* [ ] 第 8 周：求职 + 接单

## 已完成能力（前两周）



* ✅ 环境搭建：Python/venv/Github

* ✅ 大模型 API 调用：非流式 / 流式 / 多轮

* ✅ 多格式文档解析：PDF/Word/Excel → 纯文本

* ✅ 端到端 Demo：网页提问 → 后端 → 大模型 → 流式回答

## 已完成能力（第三周 Day15–Day20）



* ✅ 文本向量化：API 生成 Embedding 向量，余弦相似度计算与相似度排序

* ✅ 文本清洗：去水印 / 控制字符、合并短行、清理中英文混排空格

* ✅ 文本分块：递归字符切分器，可调块大小（chunk\_size）与重叠（chunk\_overlap）

* ✅ 向量库 Chroma：本地持久化集合，写入向量 / 文本 / 元数据，按向量做相似度检索

* ✅ 入库与检索排查：空库 / 覆盖不全 / 向量空间不一致分层定位，sqlite 直读核对条数与维度

* ✅ RAG 后端接口：FastAPI 提供健康检查、检索、文件上传、问答，非流式 + SSE 流式

* ✅ 最小 RAG 链路：检索片段 + 来源 → 拼上下文 → 约束 Prompt → 大模型生成

## 已完成能力（第四周 Day22–Day27）



* ✅ LangChain 入门：PromptTemplate | ChatOpenAI | StrOutputParser 最小链，非流式 + 流式调用

* ✅ LangChain 版 RAG 链：Loader / 分块 / 检索器 / QA 链重组手写链路；自定义 Embeddings 适配云端报文；确定性 `ids` 幂等入库

* ✅ Ollama 本地模型：OpenAI 兼容封装，`local_chat` 非流式 / 流式；RTX4060 跑 7B 量化，本地 API 调用

* ✅ 全本地私有化 RAG：bge-m3 embedding + Chroma `chroma_local` + ChatOllama，数据不上公有云；`SafeOllamaEmbeddings` 分批 + 重试规避本机大批量 embed 缺陷

* ✅ 检索优化：向量 + BM25（jieba）混合召回，RRF 融合去重，向量距离 / BM25 分数双阈值兜底；了解元数据过滤、查询扩展、rerank 精排原理

* ✅ 端侧方案了解：WebLLM 浏览器内推理体验，记录与本地 RAG 的取舍（辅线）

* ⬜ 完整演示录屏：本地私有化 + 优化检索全链路演示（复盘日补录）

### Day16 分块踩坑备忘



* LangChain 0.1 起包拆分：`langchain.text_splitter` 已移除，需 `pip install langchain-text-splitters` 并从 `langchain_text_splitters` 导入。

* `chunk_overlap` 是 "按整句 / 整段保留的重叠预算"，不是固定复制前一块末尾 N 个字；句子长于预算或边界落在句中时，该相邻块可能零重叠。验证时看最大重叠是否接近设定值，不要逐块肉眼找重复。

### Day17 Chroma 踩坑备忘



* 查询参数是复数 `query_embeddings=[[向量]]`，不是 `query_embedding`；批量接口单个向量也要外层包一层列表。

* 首次用 `query_texts` 会下载默认 ONNX 模型（S3，国内慢）；插入和查询必须用同一个 embedding 模型，占位向量与查询向量不在同一向量空间，相似度不可信。

* 集合维度按首批向量锁定：旧占位 3 维集合再写入 2560 维真实向量会报维度冲突，需 `delete_collection` 删旧集合重建；真实入库后改用 `upsert` 增量灌库。

### Day18 入库与检索排查备忘



* 检索查不到先查库里有没有数据：`col.count()`；条数为 0 是入库链路问题，不要一上来就改检索代码。

* 子目录脚本直接运行找不到 `util`：顶部用 `Path(__file__).resolve().parent.parent` 把项目根目录加入 `sys.path`，否则在写入之前就崩溃。

* 不要在模块顶层无条件 `delete_collection`：中断后只剩空集合；删库做成 `RESET` 开关，写入改用 `upsert` 支持增量入库。

* DB 路径按脚本目录锚定绝对路径，避免工作目录不同写到另一个 `chroma_db`。

* 只灌一份手册会造成覆盖不全：问库内没有的主题只能命中最不相关段落；全量遍历 `rglob("*.txt")` 入库。

* 空库 / 无命中要给提示，不要静默返回；必要时直读 `chroma_db/chroma.sqlite3` 核对向量、元数据、队列三张表的条数与维度。

### Day19 后端接口踩坑备忘



* 接口参数出现 `UploadFile / File / Form` 必须先装 `python-multipart`，否则在路由注册阶段就抛 `RuntimeError`，不是等请求进来才报错。

* 跨模块返回值与解包数量严格对齐：`retrieve()` 返回 3 元组 `(doc, dist, meta)`，判重用的归一化正文放内部列表，不暴露给调用方。

* 检索函数空库 / 无命中返回 `None` 或空列表，调用方必须先判空再迭代。

* 本地库路径一律用 `__file__` 推导绝对路径，不依赖相对工作目录。

* `/upload` 安全校验：文件名取 basename 防目录穿越、后缀白名单（.txt/.md/.csv）、5MB 大小上限、UTF-8/GBK 解码校验、清洗后判空。

* 向量化改批量请求：`get_embeddings(texts)` 一次携带多条文本、按 16 条分批，返回顺序对齐并校验条数，避免逐块循环调用。

### Day22 LangChain 入门踩坑备忘



* `ChatOpenAI` 的 `base_url` 传 OpenAI 兼容**根地址**（SDK 自动拼 `/chat/completions`）；把完整 `chat/completions` 路径传入会路径重复报 404，取配置里的 `*_api_base_url` 而非 `*_api_url`。

* 子目录脚本直接运行找不到 `util`：顶部用 `Path(__file__).resolve().parent.parent` 把项目根目录加入 `sys.path`。

### Day23 LangChain 版 RAG 链踩坑备忘



* langchain 1.x 经典 chains 拆到独立包 `langchain-classic`：`create_retrieval_chain` / `create_stuff_documents_chain` 从 `langchain_classic.chains` 导入，旧 `langchain.chains` 路径取不到。

* `OpenAIEmbeddings` 只兼容 OpenAI `/embeddings` 协议；阿里云多模态 embedding 报文（`input.contents` → `output.embeddings`）不同会 404，需自定义 `Embeddings` 封装复用现有 `get_embeddings`。

* `from_documents` 不传 `ids` 时每条生成随机 UUID，重复运行 `upsert` 也覆盖不了旧块、会重复累积；传确定性 `ids`（文件名\_序号）实现幂等更新，改后需先清一次旧持久化目录。

### Day24/25 本地 Ollama RAG 踩坑备忘



* 本机 Ollama 0.40.17 的 `/api/embed` 有大批量缺陷：批量 ≤100 条稳定成功，300 条约 50% 失败，报 `400 / tokenize connection refused`，`ollama stop` 清理 runner 无效；与请求参数（options/keep\_alive）无关。规避：embedding 分批 ≤50 条 + 单批重试 3 次（`week4/local_rag.py` 的 `SafeOllamaEmbeddings`）。

* 向量库重复运行会累积重复向量：先连集合判空，非空复用、空库才写入。

* 完整排查过程与代码要点见 [week4/local\_rag - 调试记录 - 2026-11-23.md](week4/local_rag-调试记录-2026-11-23.md)。

### Day27 混合检索优化备忘



* 示意骨架里的 `chunks` / `retriever` 未定义跑不起来：BM25 语料直接从本地 Chroma 库 `collection.get(include=["documents","metadatas"])` 读出全部片段构建，向量检索复用同一库，LLM 复用 `ollama_client.local_chat`，不重新读文件分块。

* BM25 中文按字分词噪声大：通用单字权重虚高，跨领域问题也能刷出高分；改用 `jieba.lcut` 分词并过滤空白 token。

* 兜底要双阈值：向量 L2 距离 ≤ `VECTOR_DIST_THRESHOLD`（本机实测相关 ≈0.55–0.70、无关 ≈1.18–1.30，取 1.0）**或** BM25 最高分 ≥ `BM25_SCORE_THRESHOLD`（取 6.0）才算有效召回；两路都不达标才答 "资料中未提及"。阈值按评测集先松后紧微调，换库 / 换模型需重测分布。

* RRF 融合按片段文本为键去重，两路排名分数累加后取 TopK。

* 内存版 BM25（全库读出建 `BM25Okapi`）只适合中小库；库大后内存膨胀、冷启动重建索引、全量拉原文。生产换持久化全文引擎（SQLite FTS5 / Whoosh / Meilisearch / ES），向量库与全文引擎各自召回 TopK 再 RRF 融合。