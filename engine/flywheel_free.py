# -*- coding: utf-8 -*-
"""
Wuxing Flywheel — Open Skill Engine (Free Tier)

Simplified engine for the open skill:
- 3 elements only: qinglong (seeds), zhuque (execute), xuanwu (converge)
- Max 2 rounds
- No Engram (cold start every time)
- No parallel execution (serial pipeline)
- No advanced constraints (no first-principles, no ABCD evidence, no limit-attack)
- No kunpeng three-stage convergence
- Residuals flow back to SkyCetus (anonymous)
- User provides their own API key

Usage:
    from flywheel_free import run_flywheel_free
    result = run_flywheel_free("你的分析主题", api_key="sk-xxx", max_rounds=2)
"""

import json, sys, os, time, uuid, sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "flywheel_free.db"
PROMPTS_DIR = BASE_DIR / "prompts"

# Free tier: only 3 elements
ELEMENTS = ["qinglong", "zhuque", "xuanwu"]
ELEMENT_NAMES = {
    "qinglong": "青龙·木·种子",
    "zhuque":   "朱雀·火·执行",
    "xuanwu":   "玄武·水·收敛",
}

# 相生 flow for 3-element version
SHENG_FREE = {
    "qinglong": "zhuque",   # seeds → execution
    "zhuque":   "xuanwu",   # execution → convergence
    "xuanwu":   "qinglong", # convergence → new seeds (loop)
}

# Default API config — user must provide their own key
DEFAULT_API_BASE = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

# Residual callback URL (anonymous data flows back to SkyCetus)
RESIDUAL_CALLBACK_URL = os.environ.get(
    "FLYWHEEL_RESIDUAL_URL",
    "https://skycetus.cn/api/v1/residual/collect"
)
RESIDUAL_CALLBACK_ENABLED = os.environ.get("FLYWHEEL_RESIDUAL", "1") == "1"


def gen_id(prefix=""):
    return f"{prefix}{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Database (local SQLite, lightweight)
# ---------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript("""
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY, topic TEXT NOT NULL, max_rounds INTEGER DEFAULT 2,
    status TEXT DEFAULT 'running', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS rounds (
    id TEXT PRIMARY KEY, run_id TEXT NOT NULL, round_num INTEGER NOT NULL,
    status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS elements (
    id TEXT PRIMARY KEY, round_id TEXT NOT NULL, run_id TEXT NOT NULL,
    element TEXT NOT NULL, input_text TEXT, output_text TEXT,
    tokens_in INTEGER DEFAULT 0, tokens_out INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0, model TEXT, status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS scores (
    id TEXT PRIMARY KEY, run_id TEXT NOT NULL, round_num INTEGER NOT NULL,
    overall_score REAL, verdict TEXT, notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# LLM Client — user provides their own API key
# ---------------------------------------------------------------------------
def call_llm(system_prompt: str, user_prompt: str, api_key: str,
             api_base: str = None, model: str = None,
             temperature: float = 0.3, max_tokens: int = 4096) -> dict:
    """Call LLM API. User provides their own API key."""
    import urllib.request

    api_base = api_base or DEFAULT_API_BASE
    model = model or DEFAULT_MODEL

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        api_base, data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    start = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=180)
        body = json.loads(resp.read())
    except Exception as e:
        return {"text": "", "error": str(e), "tokens_in": 0, "tokens_out": 0, "latency_ms": 0}

    latency = int((time.time() - start) * 1000)

    # Parse response (OpenAI format)
    text = ""
    if "choices" in body:
        choices = body.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "")
    elif "content" in body:
        content = body.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    break
        elif isinstance(content, str):
            text = content

    usage = body.get("usage", {})
    return {
        "text": text,
        "tokens_in": usage.get("prompt_tokens", usage.get("input_tokens", 0)),
        "tokens_out": usage.get("completion_tokens", usage.get("output_tokens", 0)),
        "latency_ms": latency,
    }


def parse_json_safe(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if "```" in text:
        for block in text.split("```")[1::2]:
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {"raw": text}


# ---------------------------------------------------------------------------
# Prompts (simplified, no advanced constraints)
# ---------------------------------------------------------------------------
def _load_prompt(element: str) -> str:
    prompt_file = PROMPTS_DIR / f"{element}_free.txt"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8").strip()
    return ""


def get_prompt(element: str, topic: str, round_num: int,
               sheng_input: str = "", residuals: str = "") -> tuple:
    """Returns (system_prompt, user_prompt) for free-tier elements."""

    residual_block = f"\n\n[上轮残差]\n{residuals}" if residuals else ""
    sheng_block = f"\n\n[上一元素产出]\n{sheng_input}" if sheng_input else ""

    file_prompt = _load_prompt(element)
    if file_prompt:
        system = file_prompt.replace("{round_num}", str(round_num))
        user = f"主题：{topic}\n轮次：{round_num}{residual_block}{sheng_block}"
        return (system, user)

    # Hardcoded fallback
    prompts = {
        "qinglong": (
            f"""你是青龙（木·种子生成器），五行飞轮的第一个元素。
职责：从主题中发散出多条探索路径（种子假设）。
第{round_num}轮。如果有上轮残差，优先从残差中生成新种子。

输出JSON：
{{"seeds": [{{"id": "s1", "title": "...", "hypothesis": "...", "novelty": 0.0-1.0}}], "reasoning": "..."}}""",
            f"主题：{topic}\n轮次：{round_num}{residual_block}{sheng_block}"
        ),
        "zhuque": (
            f"""你是朱雀（火·执行分析），五行飞轮的第二个元素。
职责：对青龙的种子进行深度分析。
第{round_num}轮。

对每个种子进行：深度分析、关键证据、风险识别、行动建议。

输出JSON：
{{"analyses": [{{"seed_id": "s1", "analysis": "...", "evidence": [...], "risks": [...], "confidence": 0.0-1.0}}], "synthesis": "..."}}""",
            f"主题：{topic}\n轮次：{round_num}\n\n[青龙种子]{sheng_block}"
        ),
        "xuanwu": (
            f"""你是玄武（水·收敛），五行飞轮的最后一个元素。
职责：综合前面元素的产出，收敛出结论。
第{round_num}轮。

收敛任务：综合所有产出、识别最强结论和最弱环节、提取残差。

输出JSON：
{{"conclusion": "核心结论", "confidence": 0.0-1.0, "strongest": "最强发现", "weakest": "最弱环节", "residuals": [{{"description": "...", "severity": 0.0-1.0}}], "next_seeds": [{{"title": "..."}}]}}""",
            f"主题：{topic}\n轮次：{round_num}\n\n[朱雀分析]{sheng_block}"
        ),
    }
    return prompts[element]


# ---------------------------------------------------------------------------
# Verification (simplified)
# ---------------------------------------------------------------------------
def verify_round(topic: str, round_num: int, outputs: dict,
                 api_key: str, api_base: str = None, model: str = None,
                 prior_scores: list = None) -> dict:
    all_output = "\n\n".join([
        f"[{ELEMENT_NAMES[e]}]\n{outputs.get(e, '(无)')[:1200]}"
        for e in ELEMENTS if e in outputs
    ])

    prior_ctx = ""
    if prior_scores:
        prior_ctx = f"\n前几轮分数：{json.dumps(prior_scores)}"

    system = """你是五行飞轮的验证函数。评估本轮输出质量。

评估维度（0.0-1.0）：
1. consistency — 元素输出是否逻辑自洽
2. novelty — 是否有新发现
3. depth — 分析是否深入
4. actionability — 结论是否可行动

输出JSON：
{"consistency": 0.0-1.0, "novelty": 0.0-1.0, "depth": 0.0-1.0, "actionability": 0.0-1.0, "overall": 0.0-1.0, "verdict": "continue|converged|degrading", "notes": "一句话评价"}"""

    user = f"主题：{topic}\n轮次：{round_num}\n\n{all_output}{prior_ctx}"
    result = call_llm(system, user, api_key, api_base, model, temperature=0.1, max_tokens=1024)
    if result.get("error") or not result["text"]:
        return {"overall": 0.5, "verdict": "continue", "notes": "验证失败"}
    return parse_json_safe(result["text"])


# ---------------------------------------------------------------------------
# Residual callback (anonymous data flows back)
# ---------------------------------------------------------------------------
def send_residual_callback(run_id: str, topic: str, residuals: str, score: float):
    """Send anonymous residual data back to SkyCetus for Engram enrichment."""
    if not RESIDUAL_CALLBACK_ENABLED:
        return

    import urllib.request
    try:
        payload = json.dumps({
            "source": "open_skill",
            "run_id": run_id,
            "topic_hash": str(hash(topic) % 10**8),  # anonymized
            "residuals": residuals[:3000],
            "score": score,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }).encode("utf-8")

        req = urllib.request.Request(
            RESIDUAL_CALLBACK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Best-effort, never fail the user's analysis


# ---------------------------------------------------------------------------
# Core: Run Free Tier Flywheel
# ---------------------------------------------------------------------------
def run_flywheel_free(topic: str, api_key: str,
                      api_base: str = None, model: str = None,
                      max_rounds: int = 2) -> dict:
    """Run the free-tier 3-element flywheel.

    Args:
        topic: Analysis topic
        api_key: User's own API key
        api_base: API endpoint (default: DeepSeek)
        model: Model name (default: deepseek-chat)
        max_rounds: Max rounds (capped at 2 for free tier)

    Returns:
        dict with run_id, rounds, final_score, conclusion
    """
    max_rounds = min(max_rounds, 2)  # Hard cap for free tier

    conn = init_db()
    run_id = gen_id("free_")
    conn.execute("INSERT INTO runs (id, topic, max_rounds) VALUES (?,?,?)",
                 (run_id, topic, max_rounds))
    conn.commit()

    print(f"\n{'='*60}")
    print(f"  五行飞轮 · 开放版")
    print(f"  Run: {run_id}")
    print(f"  Topic: {topic[:80]}{'...' if len(topic) > 80 else ''}")
    print(f"  Elements: {' → '.join(ELEMENT_NAMES[e] for e in ELEMENTS)}")
    print(f"  Max rounds: {max_rounds}")
    print(f"{'='*60}")

    all_results = []
    residuals = ""
    seeds = topic

    for round_num in range(1, max_rounds + 1):
        print(f"\n--- Round {round_num} ---")

        round_id = gen_id("rnd_")
        conn.execute("INSERT INTO rounds (id, run_id, round_num, status) VALUES (?,?,?,?)",
                     (round_id, run_id, round_num, "running"))
        conn.commit()

        outputs = {}
        prev_output = seeds

        for elem in ELEMENTS:
            print(f"  {ELEMENT_NAMES[elem]}...", end=" ", flush=True)

            system, user = get_prompt(
                elem, topic, round_num,
                sheng_input=prev_output,
                residuals=residuals if elem == "qinglong" else ""
            )

            result = call_llm(system, user, api_key, api_base, model)

            # Retry once on failure
            if result.get("error") and not result["text"]:
                time.sleep(2)
                result = call_llm(system, user, api_key, api_base, model)

            output = result["text"] if result["text"] else f"(失败: {result.get('error', 'empty')})"
            outputs[elem] = output
            prev_output = output

            # Store
            elem_id = gen_id("elm_")
            conn.execute(
                """INSERT INTO elements (id, round_id, run_id, element, input_text, output_text,
                   tokens_in, tokens_out, latency_ms, model, status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (elem_id, round_id, run_id, elem, prev_output[:2000], output[:6000],
                 result["tokens_in"], result["tokens_out"], result["latency_ms"],
                 model or DEFAULT_MODEL, "done" if result["text"] else "failed")
            )
            conn.commit()

            print(f"✓ ({result['latency_ms']}ms, {result['tokens_out']} tokens)")

        # Verify
        print(f"  验证...", end=" ", flush=True)
        prior_scores = [r["score"] for r in all_results if "score" in r]
        verification = verify_round(topic, round_num, outputs, api_key, api_base, model, prior_scores)

        score = verification.get("overall", 0.5)
        verdict = verification.get("verdict", "continue")
        notes = verification.get("notes", "")

        # Store score
        score_id = gen_id("scr_")
        conn.execute(
            "INSERT INTO scores (id, run_id, round_num, overall_score, verdict, notes) VALUES (?,?,?,?,?,?)",
            (score_id, run_id, round_num, score, verdict, notes)
        )
        conn.execute("UPDATE rounds SET status='done' WHERE id=?", (round_id,))
        conn.commit()

        print(f"Score: {score:.2f} [{verdict}]")

        # Extract residuals from xuanwu
        try:
            parsed = parse_json_safe(outputs.get("xuanwu", "{}"))
            residuals = json.dumps({
                "residuals": parsed.get("residuals", []),
                "next_seeds": parsed.get("next_seeds", []),
                "conclusion": parsed.get("conclusion", ""),
            }, ensure_ascii=False)
        except Exception:
            residuals = outputs.get("xuanwu", "")[:2000]

        all_results.append({
            "round": round_num,
            "score": score,
            "verdict": verdict,
            "notes": notes,
            "conclusion": parsed.get("conclusion", "") if 'parsed' in dir() else "",
        })

        # Check stop conditions
        if verdict == "converged":
            print(f"  🎯 收敛于第{round_num}轮")
            break
        if verdict == "degrading" and round_num >= 2:
            print(f"  📉 质量下降，停止")
            break

        # Prepare next round seeds
        try:
            parsed = parse_json_safe(residuals)
            next_seeds = parsed.get("next_seeds", [])
            if next_seeds:
                seeds = f"原始主题: {topic}\n\n新种子:\n" + \
                        "\n".join([f"- {s.get('title', s)}" for s in next_seeds])
            else:
                seeds = f"原始主题: {topic}\n\n上轮残差:\n{residuals[:1500]}"
        except Exception:
            seeds = f"原始主题: {topic}\n\n上轮残差:\n{residuals[:1500]}"

    # Finalize
    conn.execute("UPDATE runs SET status='done', completed_at=CURRENT_TIMESTAMP WHERE id=?", (run_id,))
    conn.commit()

    # Send residual callback (anonymous)
    final_score = all_results[-1]["score"] if all_results else 0
    send_residual_callback(run_id, topic, residuals, final_score)

    # Build result
    final_conclusion = ""
    if all_results:
        final_conclusion = all_results[-1].get("conclusion", "")

    result = {
        "run_id": run_id,
        "topic": topic,
        "tier": "free",
        "elements": list(ELEMENT_NAMES.keys()),
        "rounds": all_results,
        "final_score": final_score,
        "final_conclusion": final_conclusion,
        "total_rounds": len(all_results),
    }

    print(f"\n{'='*60}")
    print(f"  完成 | Run: {run_id} | Score: {final_score:.2f}")
    print(f"  结论: {final_conclusion[:100]}...")
    print(f"{'='*60}")

    conn.close()
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="五行飞轮 · 开放版")
    parser.add_argument("--topic", type=str, help="分析主题")
    parser.add_argument("--topic-file", type=str, help="从文件读取主题")
    parser.add_argument("--api-key", type=str, required=True, help="你的API密钥")
    parser.add_argument("--api-base", type=str, default=None, help="API地址")
    parser.add_argument("--model", type=str, default=None, help="模型名称")
    parser.add_argument("--rounds", type=int, default=2, help="最大轮数 (上限2)")
    args = parser.parse_args()

    topic = None
    if args.topic_file:
        with open(args.topic_file, 'r', encoding='utf-8') as f:
            topic = f.read().strip()
    elif args.topic:
        topic = args.topic

    if not topic:
        parser.print_help()
        sys.exit(1)

    run_flywheel_free(topic, args.api_key, args.api_base, args.model, args.rounds)
