"""
五行飞轮核心引擎 (开源版)
16-Agent 认知对抗分析系统

Architecture:
- 5 Element Agents (Wood, Fire, Earth, Metal, Water)
- 10 Edge Agents (5 generative + 5 controlling)
- 1 SkyCetus Kernel Arbiter
"""

import json
import os
import time
import asyncio
import uuid
from datetime import datetime
from typing import Optional
from .llm_router import call_llm, get_routing
from .engram_accumulator import EngramStore
from .integrity_mesh import IntegrityMesh

# AI² 核心组件
_engram_store = EngramStore()
_integrity_mesh = IntegrityMesh()

# 五行元素定义
ELEMENTS = ["qinglong", "zhuque", "diting", "baihu", "xuanwu"]
ELEMENT_NAMES = {
    "qinglong": "青龙·木·种子生成",
    "zhuque": "朱雀·火·执行分析",
    "diting": "谛听·土·现实校验",
    "baihu": "白虎·金·对抗检验",
    "xuanwu": "玄武·水·收敛综合",
}

# 相生链
GENERATION_CHAIN = {
    "qinglong": "zhuque",  # 木生火
    "zhuque": "diting",    # 火生土
    "diting": "baihu",     # 土生金
    "baihu": "xuanwu",     # 金生水
    "xuanwu": "qinglong",  # 水生木
}

# 相克链
CONTROL_CHAIN = {
    "qinglong": "diting",  # 木克土
    "diting": "xuanwu",    # 土克水
    "xuanwu": "zhuque",    # 水克火
    "zhuque": "baihu",     # 火克金
    "baihu": "qinglong",   # 金克木
}

PROMPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")


def load_prompt(element: str, round_num: int) -> str:
    """加载元素的系统提示词"""
    prompt_file = os.path.join(PROMPT_DIR, f"{element}_system.txt")
    if not os.path.exists(prompt_file):
        return f"You are {element} in the Wuxing Flywheel system. Round {round_num}."

    with open(prompt_file, "r", encoding="utf-8") as f:
        template = f.read()

    return template.replace("{round_num}", str(round_num))


def build_user_prompt(element: str, topic: str, round_num: int,
                      prev_outputs: dict, residuals: list = None) -> str:
    """构建用户提示词"""
    prompt_parts = [f"分析主题：{topic}\n"]

    # AI²: 注入历史 Engram 残差（第一轮时）
    if round_num == 1:
        engram_context = _engram_store.inject_into_prompt(topic)
        if engram_context:
            prompt_parts.append(engram_context)

    if round_num > 1 and residuals:
        prompt_parts.append(f"上轮残差（必须优先处理）：\n{json.dumps(residuals, ensure_ascii=False, indent=2)}\n")

    # 注入上游元素的输出
    gen_source = {v: k for k, v in GENERATION_CHAIN.items()}  # 反向映射
    upstream = gen_source.get(element)
    if upstream and upstream in prev_outputs:
        prompt_parts.append(f"上游（{ELEMENT_NAMES.get(upstream, upstream)}）输出：\n{prev_outputs[upstream][:8000]}\n")

    # 注入相克约束信号
    control_source = {v: k for k, v in CONTROL_CHAIN.items()}
    constrainer = control_source.get(element)
    if constrainer and constrainer in prev_outputs:
        prompt_parts.append(f"相克约束（来自{ELEMENT_NAMES.get(constrainer, constrainer)}）：\n{prev_outputs[constrainer][:2000]}\n")

    return "\n".join(prompt_parts)


async def run_element(element: str, topic: str, round_num: int,
                      prev_outputs: dict, residuals: list = None) -> dict:
    """运行单个元素Agent"""
    routing = get_routing()
    model_key = routing.get(element, "deepseek")

    system_prompt = load_prompt(element, round_num)
    user_prompt = build_user_prompt(element, topic, round_num, prev_outputs, residuals)

    start = time.time()
    result = await call_llm(system_prompt, user_prompt, model_key=model_key)
    elapsed = time.time() - start

    return {
        "element": element,
        "name": ELEMENT_NAMES.get(element, element),
        "round": round_num,
        "model": result.get("model", model_key),
        "tokens": result.get("tokens", 0),
        "elapsed_seconds": round(elapsed, 1),
        "output": result.get("text", ""),
    }


async def run_verifier(topic: str, round_num: int, element_outputs: dict) -> dict:
    """运行鲲鹏裁判"""
    routing = get_routing()
    model_key = routing.get("verifier", "kimi")

    system_prompt = load_prompt("verifier", round_num)
    summary = "\n\n".join([
        f"=== {ELEMENT_NAMES.get(e, e)} ===\n{element_outputs.get(e, '(empty)')[:4000]}"
        for e in ELEMENTS
    ])

    user_prompt = f"分析主题：{topic}\n第{round_num}轮五行输出汇总：\n{summary}"

    result = await call_llm(system_prompt, user_prompt, model_key=model_key, temperature=0.3)
    return result


async def run_flywheel(topic: str, max_rounds: int = 3,
                       convergence_threshold: float = 0.03,
                       on_progress=None) -> dict:
    """
    运行五行飞轮完整分析

    Args:
        topic: 分析主题
        max_rounds: 最大迭代轮次
        convergence_threshold: 收敛阈值
        on_progress: 进度回调函数

    Returns:
        完整的分析结果
    """
    run_id = str(uuid.uuid4())[:12]
    start_time = time.time()

    result = {
        "run_id": run_id,
        "topic": topic,
        "started_at": datetime.now().isoformat(),
        "rounds": [],
        "final_score": 0.0,
        "final_grade": "F",
        "status": "running",
    }

    prev_outputs = {}
    residuals = []
    prev_score = 0.0

    for round_num in range(1, max_rounds + 1):
        if on_progress:
            on_progress(f"Round {round_num}/{max_rounds} starting...")

        round_data = {"round": round_num, "elements": {}, "score": 0.0}

        # 运行五个元素Agent（按相生链顺序）
        for element in ELEMENTS:
            if on_progress:
                on_progress(f"R{round_num}: Running {ELEMENT_NAMES[element]}...")

            elem_result = await run_element(element, topic, round_num, prev_outputs, residuals)
            round_data["elements"][element] = elem_result
            prev_outputs[element] = elem_result["output"]

        # 运行鲲鹏裁判
        if on_progress:
            on_progress(f"R{round_num}: Running verifier...")

        verifier_result = await run_verifier(topic, round_num, prev_outputs)

        # 解析评分
        score = 0.5  # default
        try:
            text = verifier_result.get("text", "")
            # 尝试解析JSON
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                v_json = json.loads(text[json_start:json_end])
                score = float(v_json.get("score", 0.5))
        except (json.JSONDecodeError, ValueError):
            pass

        round_data["score"] = score
        round_data["verifier"] = verifier_result.get("text", "")
        result["rounds"].append(round_data)

        # 收敛检查
        delta = abs(score - prev_score)
        if round_num > 1 and delta < convergence_threshold:
            if on_progress:
                on_progress(f"Converged at R{round_num} (delta={delta:.3f})")
            break

        if score >= 0.80:
            if on_progress:
                on_progress(f"Quality threshold reached at R{round_num} (score={score:.2f})")
            break

        prev_score = score

        # 提取残差用于下一轮
        try:
            text = prev_outputs.get("xuanwu", "")
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                xuanwu_json = json.loads(text[json_start:json_end])
                residuals = xuanwu_json.get("residuals", [])
        except (json.JSONDecodeError, ValueError):
            residuals = []

    # 最终结果
    final_score = result["rounds"][-1]["score"] if result["rounds"] else 0.0
    result["final_score"] = final_score
    result["final_grade"] = score_to_grade(final_score)
    result["total_rounds"] = len(result["rounds"])
    result["elapsed_seconds"] = round(time.time() - start_time, 1)
    result["status"] = "completed"
    result["completed_at"] = datetime.now().isoformat()

    # AI²: 存入 Engram（累积认知残差）
    # 删除此块 = 系统退化为 AI¹，每次冷启动
    try:
        engram_data = {
            "domain": "general",
            "score": final_score,
            "residuals": residuals,
            "validated_conclusions": [],
            "attack_patterns": [],
            "convergence_insights": [],
        }
        # 从玄武输出提取结论
        xuanwu_text = prev_outputs.get("xuanwu", "")
        try:
            js = xuanwu_text.find("{")
            je = xuanwu_text.rfind("}") + 1
            if js >= 0 and je > js:
                xj = json.loads(xuanwu_text[js:je])
                engram_data["validated_conclusions"] = [
                    xj.get("kun_dive", {}).get("conclusion", "") if isinstance(xj.get("kun_dive"), dict) else str(xj.get("kun_dive", ""))
                ]
                engram_data["convergence_insights"] = [
                    xj.get("dao_merge", {}).get("synthesis", "") if isinstance(xj.get("dao_merge"), dict) else str(xj.get("dao_merge", ""))
                ]
        except (json.JSONDecodeError, ValueError):
            pass

        _engram_store.deposit(run_id, topic, engram_data)
    except Exception:
        pass  # Engram 存储失败不影响主流程

    # Engram 统计
    result["engram_stats"] = _engram_store.get_stats()

    return result


def score_to_grade(score: float) -> str:
    """评分转等级"""
    if score >= 0.90:
        return "A"
    elif score >= 0.80:
        return "A-"
    elif score >= 0.75:
        return "B+"
    elif score >= 0.70:
        return "B"
    elif score >= 0.65:
        return "B-"
    elif score >= 0.60:
        return "C+"
    elif score >= 0.50:
        return "C"
    else:
        return "D"
