import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import traceback
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from collections import defaultdict
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = "sk-4c421740ea774d2ab39141df1877a762"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh-v1.5")
CHROMA_DB_FOLDER = "chroma_db"
MAX_HISTORY_TURNS = 5

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

vectorstore = Chroma(
    persist_directory=CHROMA_DB_FOLDER,
    embedding_function=EMBEDDING_MODEL
)

session_history = defaultdict(list)
session_info = defaultdict(dict)

class ChatRequest(BaseModel):
    session_id: str
    query: str

class NewSessionResponse(BaseModel):
    session_id: str
    message: str

class HistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, str]]

class DBStatsResponse(BaseModel):
    total_chunks: int
    collections: List[str]

class DocItem(BaseModel):
    id: str
    content: str
    metadata: Dict

class SearchRequest(BaseModel):
    query: str
    k: int = 3

def log_error(error: Exception, context: str = ""):
    timestamp = datetime.now().isoformat()
    error_msg = f"[{timestamp}] ERROR in {context}: {str(error)}"
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    return error_msg

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        docs = vectorstore.similarity_search(req.query, k=3)
        context = "\n\n".join([d.page_content for d in docs])

        history = session_history[req.session_id][-MAX_HISTORY_TURNS*2:]

        messages = [
            {"role": "system", "content": "你是一位专业、友善的管理知识顾问。请根据提供的参考资料，用自然、清晰的方式回答用户问题。回答要全面有条理，同时保持简洁易懂。使用Markdown格式让内容更易读：用小标题组织结构，用列表展示要点。如果参考资料中没有相关信息，请诚实地说明，不要编造内容。语气要专业但不失亲和力，让用户感到你真正在帮助他们。"}
        ]
        for turn in history:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})

        user_message = f"参考资料：\n{context}\n\n用户问题：{req.query}"
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7
        )
        answer = response.choices[0].message.content

        session_history[req.session_id].append({"user": req.query, "assistant": answer})
        
        if not session_info[req.session_id]:
            session_info[req.session_id] = {"created_at": datetime.now().isoformat()}

        return {"answer": answer}

    except Exception as e:
        log_error(e, "chat endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/new_session", response_model=NewSessionResponse)
async def new_session():
    try:
        session_id = f"session-{datetime.now().timestamp()}"
        session_info[session_id] = {"created_at": datetime.now().isoformat()}
        logger.info(f"New session created: {session_id}")
        return {"session_id": session_id, "message": "新会话已创建"}
    except Exception as e:
        log_error(e, "new_session endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    try:
        history = session_history.get(session_id, [])
        return {"session_id": session_id, "history": history}
    except Exception as e:
        log_error(e, "get_history endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions():
    try:
        sessions = []
        for session_id, info in session_info.items():
            sessions.append({
                "session_id": session_id,
                "created_at": info.get("created_at", ""),
                "message_count": len(session_history.get(session_id, []))
            })
        return {"sessions": sessions}
    except Exception as e:
        log_error(e, "list_sessions endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    try:
        if session_id in session_history:
            del session_history[session_id]
        if session_id in session_info:
            del session_info[session_id]
        logger.info(f"Session deleted: {session_id}")
        return {"message": "会话已删除"}
    except Exception as e:
        log_error(e, "delete_session endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/stats", response_model=DBStatsResponse)
async def get_db_stats():
    try:
        collection = vectorstore._client.get_or_create_collection("langchain")
        count = collection.count()
        collections = [c.name for c in vectorstore._client.list_collections()]
        return {"total_chunks": count, "collections": collections}
    except Exception as e:
        log_error(e, "get_db_stats endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/db/search")
async def search_db(req: SearchRequest):
    try:
        docs = vectorstore.similarity_search(req.query, k=req.k)
        results = []
        for i, doc in enumerate(docs):
            results.append({
                "id": str(i),
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata or {}
            })
        return {"results": results}
    except Exception as e:
        log_error(e, "search_db endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/chunks")
async def get_all_chunks(limit: int = 20, offset: int = 0):
    try:
        collection = vectorstore._client.get_or_create_collection("langchain")
        all_items = collection.get()
        chunks = []
        for i, (id_, content) in enumerate(zip(all_items['ids'], all_items['documents'])):
            if i >= offset and len(chunks) < limit:
                chunks.append({
                    "id": id_,
                    "content": content[:300] + "..." if len(content) > 300 else content
                })
        return {"chunks": chunks, "total": len(all_items['ids'])}
    except Exception as e:
        log_error(e, "get_all_chunks endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
async def get_logs(lines: int = 50):
    try:
        if os.path.exists("app.log"):
            with open("app.log", "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:]
                return {"logs": "".join(recent_lines)}
        return {"logs": "日志文件不存在"}
    except Exception as e:
        log_error(e, "get_logs endpoint")
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="static", html=True), name="static")