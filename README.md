# 五行飞轮 Wuxing Flywheel — Open Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**AI-powered multi-perspective analysis engine based on Chinese Five Elements (五行) philosophy.**

Transform any question into a structured analysis through three adversarial AI agents:

- 🐉 **青龙·木 (Qinglong)** — Seed Generation: divergent exploration, first-principles decomposition
- 🔥 **朱雀·火 (Zhuque)** — Deep Execution: mechanism analysis, causal chains
- 🐢 **玄武·水 (Xuanwu)** — Convergence: synthesize findings, extract residuals

## Quick Start

### As OpenClaw Skill

1. Copy this directory to your OpenClaw skills folder
2. Set your API key (any OpenAI-compatible provider):
   ```
   export FLYWHEEL_API_KEY="sk-your-key"
   export FLYWHEEL_API_BASE="https://api.openai.com/v1"  # or any compatible endpoint
   ```
3. Use in conversation: "用飞轮分析：[your topic]"

### As Python Module

```python
from engine.flywheel_free import run_flywheel_free

result = run_flywheel_free(
    topic="2026年咖啡市场趋势分析",
    api_key="sk-your-key",
    api_base="https://api.openai.com/v1",  # optional
    model="gpt-4o",  # optional, default: gpt-4o
    max_rounds=2,  # max 2 for free tier
)

print(f"Score: {result['final_score']}")
print(f"Verdict: {result['verdict']}")
```

## How It Works

The Wuxing Flywheel implements a **mutual generation (相生) pipeline**:

```
青龙 (Seeds) → 朱雀 (Execution) → 玄武 (Convergence)
     ↑________________________________↓ (residual feedback)
```

Each element receives the previous element's output as context, creating a chain of increasingly refined analysis. Multiple rounds iterate until convergence or max rounds reached.

### Scoring

Each round is evaluated by a verification function measuring:
- **Consistency** — internal logical coherence
- **Novelty** — genuine new insights vs. repetition
- **Depth** — structural analysis vs. surface description
- **Actionability** — concrete recommendations vs. vague advice

Final verdict: PASS (≥0.75), CONDITIONAL (0.50-0.74), FAIL (<0.50)

## Free vs Pro

| Feature | Open (Free) | Pro |
|---------|:-----------:|:---:|
| Elements | 3 (青龙/朱雀/玄武) | 5 (+谛听/白虎) |
| Max Rounds | 2 | 5 |
| Engram Memory | ❌ | ✅ |
| Parallel Execution | ❌ | ✅ |
| First-Principles Constraints | ❌ | ✅ |
| ABCD Evidence Grading | ❌ | ✅ |
| Theoretical-Limit Attacks | ❌ | ✅ |
| Kunpeng Convergence | ❌ | ✅ |

**Upgrade to Pro:** Visit [skycetus.cn/caas-pricing.html](https://skycetus.cn/caas-pricing.html)

## Configuration

Environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `FLYWHEEL_API_KEY` | Yes | Your LLM API key |
| `FLYWHEEL_API_BASE` | No | API base URL (default: OpenAI) |
| `FLYWHEEL_MODEL` | No | Model name (default: gpt-4o) |
| `FLYWHEEL_DB` | No | Database: `sqlite` (default) or `pg` |

## File Structure

```
├── SKILL.md              # OpenClaw skill definition
├── README.md             # This file
├── engine/
│   ├── flywheel_free.py  # Core engine (free tier)
│   └── tier_config.py    # Tier definitions
└── prompts/
    ├── qinglong_free.txt  # 青龙 system prompt
    ├── zhuque_free.txt    # 朱雀 system prompt
    └── xuanwu_free.txt    # 玄武 system prompt
```

## License

MIT License. See [LICENSE](LICENSE).

## About

Built by [SkyCetus](https://skycetus.cn) · 深圳市天鲸珑珠信息技术有限公司

The Wuxing Flywheel is part of the 珑珠引擎 (Longzhu Engine) — a structured analysis platform where every decision undergoes five-element adversarial verification.
