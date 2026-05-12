"""
五行飞轮 API 服务
FastAPI 入口

启动: uvicorn flywheel_api:app --host 0.0.0.0 --port 8100
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

from engine.engine_core import run_flywheel

app = FastAPI(
    title="SkyCetus Wuxing Flywheel",
    description="🐋 天鲸之城·五行飞轮 — 16-Agent 认知对抗分析系统",
    version="1.0.0-open",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储运行结果（生产环境建议用PostgreSQL）
_results = {}
_progress = {}


class AnalyzeRequest(BaseModel):
    topic: str
    depth: str = "deep"  # "quick" (1 round) or "deep" (3 rounds)
    max_rounds: Optional[int] = None


class AnalyzeResponse(BaseModel):
    run_id: str
    status: str
    message: str


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0-open",
        "engine": "wuxing-flywheel",
        "agents": 16,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """提交分析任务"""
    max_rounds = req.max_rounds or (1 if req.depth == "quick" else 3)

    # 后台运行飞轮
    async def _run():
        def on_progress(msg):
            _progress[result["run_id"]] = msg

        try:
            result_data = await run_flywheel(
                topic=req.topic,
                max_rounds=max_rounds,
                on_progress=on_progress,
            )
            _results[result_data["run_id"]] = result_data
        except Exception as e:
            _results[result["run_id"]] = {"status": "error", "error": str(e)}

    # 创建一个占位
    import uuid
    run_id = str(uuid.uuid4())[:12]
    result = {"run_id": run_id}
    _progress[run_id] = "queued"

    asyncio.create_task(_run())

    return AnalyzeResponse(
        run_id=run_id,
        status="accepted",
        message=f"Analysis started: {req.topic} ({req.depth} mode, max {max_rounds} rounds)",
    )


@app.get("/result/{run_id}")
async def get_result(run_id: str):
    """获取分析结果"""
    if run_id in _results:
        return _results[run_id]
    elif run_id in _progress:
        return {"run_id": run_id, "status": "running", "progress": _progress[run_id]}
    else:
        raise HTTPException(status_code=404, detail="Run not found")


@app.get("/progress/{run_id}")
async def get_progress(run_id: str):
    """获取运行进度"""
    return {
        "run_id": run_id,
        "progress": _progress.get(run_id, "unknown"),
        "completed": run_id in _results,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("FLYWHEEL_PORT", "8100"))
    uvicorn.run(app, host="0.0.0.0", port=port)
