# -*- coding: utf-8 -*-
"""
CaaS Tier Configuration — Defines what each service tier can access.

Three tiers:
  FREE  — Open Skill (3 elements, 2 rounds, no Engram, user-pays API)
  PRO   — Professional (5 elements, 5 rounds, Engram, we-pay API)
  ENT   — Enterprise (all PRO + custom Engram, priority queue, API access)
"""

from dataclasses import dataclass, field
from typing import List, Optional

# Element sets
ELEMENTS_FREE = ["qinglong", "zhuque", "xuanwu"]  # 3 core: seed, execute, converge
ELEMENTS_FULL = ["qinglong", "zhuque", "diting", "baihu", "xuanwu"]  # all 5

# Model routing per tier
# Free: user provides their own API key → domestic models only
# Pro/Ent: our keys → frontier models
MODEL_ROUTE_FREE = {
    "qinglong": "deepseek",
    "zhuque": "deepseek",
    "xuanwu": "deepseek",
    "verifier": "deepseek",
}

MODEL_ROUTE_PRO_DOMESTIC = {
    "qinglong": "qwen",
    "zhuque": "deepseek",
    "diting": "glm",
    "baihu": "deepseek",
    "xuanwu": "qwen",
    "verifier": "kimi",
}

MODEL_ROUTE_PRO_FRONTIER = {
    "qinglong": "gpt5",
    "zhuque": "claude_opus",
    "diting": "gpt5",
    "baihu": "grok4",
    "xuanwu": "claude_opus",
    "verifier": "grok4",
}


@dataclass
class TierConfig:
    """Configuration for a service tier."""
    name: str
    tier_id: str  # "free", "pro", "ent"
    elements: List[str]
    max_rounds: int
    engram_enabled: bool
    parallel_enabled: bool
    model_route: dict
    report_format: str  # "raw", "formatted", "branded"
    residual_callback: bool  # whether residuals flow back to SkyCetus
    residual_viewable: bool  # whether user can view their residuals
    max_tokens: int = 4096
    advanced_constraints: bool = False  # first-principles, ABCD evidence, limit-attack
    kunpeng_convergence: bool = False  # three-stage convergence
    priority: int = 0  # queue priority (higher = faster)
    api_key_source: str = "user"  # "user" or "system"


# Tier definitions
TIER_FREE = TierConfig(
    name="开放版",
    tier_id="free",
    elements=ELEMENTS_FREE,
    max_rounds=2,
    engram_enabled=False,
    parallel_enabled=False,
    model_route=MODEL_ROUTE_FREE,
    report_format="raw",
    residual_callback=True,    # residuals flow back to us
    residual_viewable=False,   # free users can't view residuals
    max_tokens=4096,
    advanced_constraints=False,
    kunpeng_convergence=False,
    priority=0,
    api_key_source="user",
)

TIER_PRO_DOMESTIC = TierConfig(
    name="专业版·标准模型",
    tier_id="pro_domestic",
    elements=ELEMENTS_FULL,
    max_rounds=5,
    engram_enabled=True,
    parallel_enabled=True,
    model_route=MODEL_ROUTE_PRO_DOMESTIC,
    report_format="formatted",
    residual_callback=True,
    residual_viewable=True,
    max_tokens=8192,
    advanced_constraints=True,
    kunpeng_convergence=True,
    priority=5,
    api_key_source="system",
)

TIER_PRO_FRONTIER = TierConfig(
    name="专业版·旗舰模型",
    tier_id="pro_frontier",
    elements=ELEMENTS_FULL,
    max_rounds=5,
    engram_enabled=True,
    parallel_enabled=True,
    model_route=MODEL_ROUTE_PRO_FRONTIER,
    report_format="formatted",
    residual_callback=True,
    residual_viewable=True,
    max_tokens=8192,
    advanced_constraints=True,
    kunpeng_convergence=True,
    priority=5,
    api_key_source="system",
)

TIER_ENTERPRISE = TierConfig(
    name="企业版",
    tier_id="enterprise",
    elements=ELEMENTS_FULL,
    max_rounds=5,
    engram_enabled=True,
    parallel_enabled=True,
    model_route=MODEL_ROUTE_PRO_FRONTIER,  # default frontier, customizable
    report_format="branded",
    residual_callback=True,
    residual_viewable=True,
    max_tokens=8192,
    advanced_constraints=True,
    kunpeng_convergence=True,
    priority=10,
    api_key_source="system",
)

# Lookup
TIERS = {
    "free": TIER_FREE,
    "pro_domestic": TIER_PRO_DOMESTIC,
    "pro_frontier": TIER_PRO_FRONTIER,
    "enterprise": TIER_ENTERPRISE,
}


def get_tier(tier_id: str) -> TierConfig:
    """Get tier configuration by ID."""
    return TIERS.get(tier_id, TIER_FREE)


def validate_request(tier: TierConfig, requested_rounds: int = 3) -> dict:
    """Validate and cap request parameters based on tier."""
    actual_rounds = min(requested_rounds, tier.max_rounds)
    return {
        "elements": tier.elements,
        "max_rounds": actual_rounds,
        "model_route": tier.model_route,
        "engram_enabled": tier.engram_enabled,
        "parallel_enabled": tier.parallel_enabled,
        "max_tokens": tier.max_tokens,
        "advanced_constraints": tier.advanced_constraints,
        "kunpeng_convergence": tier.kunpeng_convergence,
        "report_format": tier.report_format,
        "capped": actual_rounds < requested_rounds,
    }
