"""
知识树自动提取 (Knowledge Tree Hook)
从飞轮分析结果中自动提取实体、关系和结论
"""

import json
import re
from typing import List, Dict, Optional


def extract_entities(analysis_text: str) -> List[Dict]:
    """
    从分析文本中提取实体

    Returns:
        [{"name": "...", "type": "concept|technology|company|person", "confidence": 0.0-1.0}]
    """
    # 基础实现：从JSON结构中提取
    entities = []
    try:
        # 尝试解析JSON
        json_match = re.search(r'\{[\s\S]*\}', analysis_text)
        if json_match:
            data = json.loads(json_match.group())
            # 从种子中提取
            for seed in data.get("seeds", []):
                entities.append({
                    "name": seed.get("title", ""),
                    "type": "concept",
                    "confidence": seed.get("novelty", 0.5),
                })
    except (json.JSONDecodeError, AttributeError):
        pass

    return entities


def extract_relations(entities: List[Dict], analysis_text: str) -> List[Dict]:
    """
    从分析中提取实体间关系

    Returns:
        [{"source": "...", "target": "...", "relation": "enables|competes_with|requires|evolves_to", "confidence": 0.0-1.0}]
    """
    relations = []
    # 基础实现：基于共现和关键词
    entity_names = [e["name"] for e in entities]

    for i, name_a in enumerate(entity_names):
        for name_b in entity_names[i+1:]:
            if name_a in analysis_text and name_b in analysis_text:
                # 简单共现关系
                relations.append({
                    "source": name_a,
                    "target": name_b,
                    "relation": "related_to",
                    "confidence": 0.5,
                })

    return relations


def extract_conclusions(xuanwu_output: str) -> List[Dict]:
    """
    从玄武输出中提取验证结论

    Returns:
        [{"conclusion": "...", "confidence": 0.0-1.0, "time_horizon": "...", "evidence_grade": "A|B|C|D"}]
    """
    conclusions = []
    try:
        json_match = re.search(r'\{[\s\S]*\}', xuanwu_output)
        if json_match:
            data = json.loads(json_match.group())
            kun_dive = data.get("kun_dive", {})
            if isinstance(kun_dive, dict):
                conclusions.append({
                    "conclusion": kun_dive.get("conclusion", ""),
                    "confidence": data.get("confidence", 0.5),
                    "time_horizon": "short_term",
                    "evidence_grade": "B",
                })
    except (json.JSONDecodeError, AttributeError):
        pass

    return conclusions


def process_run_result(result: dict) -> dict:
    """
    处理完整的飞轮运行结果，提取知识树数据

    Returns:
        {"entities": [...], "relations": [...], "conclusions": [...]}
    """
    all_entities = []
    all_relations = []
    all_conclusions = []

    for round_data in result.get("rounds", []):
        elements = round_data.get("elements", {})

        # 从青龙提取实体
        qinglong = elements.get("qinglong", {})
        entities = extract_entities(qinglong.get("output", ""))
        all_entities.extend(entities)

        # 从玄武提取结论
        xuanwu = elements.get("xuanwu", {})
        conclusions = extract_conclusions(xuanwu.get("output", ""))
        all_conclusions.extend(conclusions)

    # 提取关系
    all_text = json.dumps(result, ensure_ascii=False)
    all_relations = extract_relations(all_entities, all_text)

    return {
        "entities": all_entities,
        "relations": all_relations,
        "conclusions": all_conclusions,
        "run_id": result.get("run_id", ""),
        "topic": result.get("topic", ""),
    }
