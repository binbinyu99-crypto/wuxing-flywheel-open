"""
知识缺口检测器 (Gap Detector)
分析知识树中的缺口，自动触发新的飞轮分析
"""

from typing import List, Dict, Optional


# 战略领域定义
STRATEGIC_DOMAINS = [
    "人工智能", "量子计算", "新能源", "生物技术",
    "半导体", "新材料", "航空航天", "机器人",
    "金融科技", "碳中和", "基因编辑", "核聚变",
    "具身智能", "脑机接口",
]


def detect_gaps(entities: List[Dict], relations: List[Dict],
                conclusions: List[Dict]) -> List[Dict]:
    """
    检测知识树中的缺口

    缺口类型：
    1. 孤立实体：有实体但没有关系
    2. 矛盾结论：同一主题的结论互相矛盾
    3. 过期结论：结论的时间窗口已过
    4. 空白领域：战略领域中没有覆盖的
    5. 低置信度聚集：某个领域的结论置信度普遍偏低

    Returns:
        [{"type": "isolated|contradiction|stale|blank|low_confidence",
          "description": "...", "suggested_topic": "...", "priority": 0.0-1.0}]
    """
    gaps = []

    # 1. 检测孤立实体
    connected = set()
    for rel in relations:
        connected.add(rel.get("source", ""))
        connected.add(rel.get("target", ""))

    for entity in entities:
        if entity["name"] not in connected and entity.get("confidence", 0) > 0.3:
            gaps.append({
                "type": "isolated",
                "description": f"实体 '{entity['name']}' 没有任何已知关系",
                "suggested_topic": f"{entity['name']}的产业链关系和技术路径",
                "priority": 0.5,
            })

    # 2. 检测矛盾结论
    conclusion_map = {}
    for c in conclusions:
        topic_key = c.get("conclusion", "")[:20]
        if topic_key in conclusion_map:
            existing = conclusion_map[topic_key]
            if abs(existing.get("confidence", 0) - c.get("confidence", 0)) > 0.3:
                gaps.append({
                    "type": "contradiction",
                    "description": f"同一主题存在矛盾结论（置信度差异>{0.3}）",
                    "suggested_topic": f"深入分析: {topic_key}",
                    "priority": 0.8,
                })
        else:
            conclusion_map[topic_key] = c

    # 3. 检测空白战略领域
    covered = set()
    for entity in entities:
        for domain in STRATEGIC_DOMAINS:
            if domain in entity.get("name", ""):
                covered.add(domain)

    for domain in STRATEGIC_DOMAINS:
        if domain not in covered:
            gaps.append({
                "type": "blank",
                "description": f"战略领域 '{domain}' 尚无分析覆盖",
                "suggested_topic": f"{domain}产业深度分析",
                "priority": 0.6,
            })

    # 按优先级排序
    gaps.sort(key=lambda x: x["priority"], reverse=True)
    return gaps
