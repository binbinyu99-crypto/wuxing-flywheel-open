"""
认知模块 (Cognitive Modules)
提供高阶认知功能：反事实分析、证据链、置信度校准、辩论、认知预算
"""

from typing import List, Dict, Optional
from .llm_router import call_llm


async def counterfactual_analysis(conclusion: str, evidence: List[str],
                                   model_key: str = "deepseek") -> dict:
    """
    反事实分析：如果关键假设不成立，结论会如何改变？
    """
    prompt = f"""对以下结论进行反事实分析：

结论：{conclusion}

支撑证据：
{chr(10).join(f'- {e}' for e in evidence)}

请分析：
1. 识别3个最关键的假设
2. 对每个假设，分析"如果它不成立"会怎样
3. 评估结论的鲁棒性（0-1）

输出JSON：
{{"assumptions": [{{"assumption": "...", "if_false": "...", "impact": "HIGH|MEDIUM|LOW"}}], "robustness": 0.0-1.0, "weakest_point": "..."}}"""

    result = await call_llm(
        system_prompt="你是反事实分析专家。严格审查假设的脆弱性。",
        user_prompt=prompt,
        model_key=model_key,
        temperature=0.3,
    )
    return result


async def evidence_chain(claims: List[str], model_key: str = "deepseek") -> dict:
    """
    证据链分析：追踪每个声明的证据来源和传递链
    """
    prompt = f"""对以下声明进行证据链分析：

{chr(10).join(f'{i+1}. {c}' for i, c in enumerate(claims))}

对每个声明：
1. 追溯证据来源（一手/二手/推理/假设）
2. 评估证据传递链的完整性
3. 标注断裂点

输出JSON：
{{"chains": [{{"claim": "...", "source_type": "PRIMARY|SECONDARY|INFERRED|ASSUMED", "chain": ["来源→传递→当前"], "breaks": ["断裂点描述"], "reliability": 0.0-1.0}}]}}"""

    result = await call_llm(
        system_prompt="你是证据链分析专家。追踪每条信息的来源和可靠性。",
        user_prompt=prompt,
        model_key=model_key,
        temperature=0.3,
    )
    return result


async def confidence_calibration(predictions: List[Dict], model_key: str = "deepseek") -> dict:
    """
    置信度校准：检查预测的置信度是否合理
    """
    import json
    prompt = f"""对以下预测进行置信度校准：

{json.dumps(predictions, ensure_ascii=False, indent=2)}

检查：
1. 置信度是否与证据强度匹配？
2. 是否存在过度自信或过度保守？
3. 给出校准后的置信度

输出JSON：
{{"calibrations": [{{"prediction": "...", "original_confidence": 0.0, "calibrated_confidence": 0.0, "adjustment_reason": "..."}}]}}"""

    result = await call_llm(
        system_prompt="你是置信度校准专家。确保预测的置信度与证据匹配。",
        user_prompt=prompt,
        model_key=model_key,
        temperature=0.3,
    )
    return result


async def dialectic_debate(thesis: str, antithesis: str, model_key: str = "deepseek") -> dict:
    """
    辩证辩论：正反双方交锋后综合
    """
    prompt = f"""进行辩证分析：

正方论点：{thesis}

反方论点：{antithesis}

请：
1. 分析正方的最强论据和最弱环节
2. 分析反方的最强论据和最弱环节
3. 进行综合（合题），找到超越正反对立的更高层次理解

输出JSON：
{{"thesis_strength": "...", "thesis_weakness": "...", "antithesis_strength": "...", "antithesis_weakness": "...", "synthesis": "...", "confidence": 0.0-1.0}}"""

    result = await call_llm(
        system_prompt="你是辩证法专家。不偏袒任何一方，追求更高层次的综合。",
        user_prompt=prompt,
        model_key=model_key,
        temperature=0.5,
    )
    return result
