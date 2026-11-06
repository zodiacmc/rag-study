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

## 运行
1. python -m venv venv && venv\Scripts\activate
2. pip install -r requirements.txt（逐周补充）
3. python week1/llm_client.py

## 进度
- [x] 第1周：环境 + Python基础 + API调用
- [ ] 第2周：文档解析 + 简易后端
- [ ] 第3-5周：RAG核心（向量/检索/LangChain/Ollama）
- [ ] 第6-7周：开源项目作品集
- [ ] 第8周：求职 + 接单