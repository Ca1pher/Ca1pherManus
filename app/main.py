# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 导入 CORSMiddleware
from app.api.v1 import endpoints as v1_endpoints
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="FastAPI LangGraph Streaming Example",
    description="Demonstrates streaming LangGraph execution states via FastAPI SSE.",
    version="1.0.0",
)

# --- 添加 CORS 中间件 ---
origins = [
    "http://localhost",
    "http://localhost:8000", # 你的 FastAPI 应用运行的地址
    "http://127.0.0.1:8000",
    "http://localhost:5173", # 你的前端服务地址
    "http://127.0.0.1:5173", # 前端服务的 IP 地址版本
    # 如果你的 HTML 文件是从文件系统直接打开的 (file:// )，或者从其他端口提供服务，
    # 你可能需要添加这些源。在生产环境中，请精确列出你的前端域名。
    "null", # 对于 file:// 协议，浏览器会发送 "Origin: null"
    # "http://your-frontend-domain.com", # 如果你有前端域名 ，请在这里添加
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 允许的源列表
    allow_credentials=True, # 允许发送 cookie
    allow_methods=["*"], # 允许所有 HTTP 方法 (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # 允许所有请求头
)
# --- CORS 中间件结束 ---

# 包含 API 路由
app.include_router(v1_endpoints.router, prefix="/api/v1", tags=["Chat"])

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI LangGraph Streaming API!"}
