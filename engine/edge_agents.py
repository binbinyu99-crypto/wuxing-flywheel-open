"""
五行飞轮 边Agent (Edge Agents)
10个边Agent：5个相生边 + 5个相克边

相生边负责知识转换和增强传递
相克边负责约束检验和纠偏
"""

from typing import Optional
from .llm_router import call_llm


# 相生边Agent定义
GENERATION_EDGES = {
    "wood_fire": {
        "name": "木生火",
        "from": "qinglong",
        "to": "zhuque",
        "prompt": "你是木生火边Agent。将青龙的发散种子转化为朱雀可执行的分析任务。"
                  "过滤低质量种子，增强高潜力种子的具体性。",
    },
    "fire_earth": {
        "name": "火生土",
        "from": "zhuque",
        "to": "diting",
        "prompt": "你是火生土边Agent。将朱雀的分析结果转化为谛听可验证的命题。"
                  "提取关键声明，标注需要验证的数据点。",
    },
    "earth_metal": {
        "name": "土生金",
        "from": "diting",
        "to": "baihu",
        "prompt": "你是土生金边Agent。将谛听的验证结果转化为白虎的攻击目标。"
                  "标注验证中的薄弱环节，为对抗测试提供焦点。",
    },
    "metal_water": {
        "name": "金生水",
        "from": "baihu",
        "to": "xuanwu",
        "prompt": "你是金生水边Agent。将白虎的攻击残差转化为玄武的收敛材料。"
                  "分类攻击结果：已解决/未解决/新发现。",
    },
    "water_wood": {
        "name": "水生木",
        "from": "xuanwu",
        "to": "qinglong",
        "prompt": "你是水生木边Agent。将玄武的收敛残差转化为青龙的新种子方向。"
                  "闭环：让收敛产生的新问题成为下一轮发散的起点。",
    },
}

# 相克边Agent定义
CONTROL_EDGES = {
    "wood_earth": {
        "name": "木克土",
        "from": "qinglong",
        "to": "diting",
        "prompt": "你是木克土边Agent。用青龙的发散视角约束谛听的过度保守。"
                  "当谛听因缺少数据就否定一个方向时，提醒还有未探索的可能性。",
    },
    "earth_water": {
        "name": "土克水",
        "from": "diting",
        "to": "xuanwu",
        "prompt": "你是土克水边Agent。用谛听的实证约束玄武的过早收敛。"
                  "当玄武基于不充分的证据就下结论时，要求更多验证。",
    },
    "water_fire": {
        "name": "水克火",
        "from": "xuanwu",
        "to": "zhuque",
        "prompt": "你是水克火边Agent。用玄武的时间维度约束朱雀的过度乐观。"
                  "提醒短期看好的趋势在长期可能反转。",
    },
    "fire_metal": {
        "name": "火克金",
        "from": "zhuque",
        "to": "baihu",
        "prompt": "你是火克金边Agent。用朱雀的第一性原理约束白虎的无限攻击。"
                  "当白虎的攻击脱离核心逻辑时，拉回焦点。",
    },
    "metal_wood": {
        "name": "金克木",
        "from": "baihu",
        "to": "qinglong",
        "prompt": "你是金克木边Agent。用白虎的对抗视角约束青龙的过度发散。"
                  "过滤掉那些一经检验就站不住脚的种子方向。",
    },
}


async def process_generation(edge_key: str, source_output: str, model_key: str = "deepseek") -> str:
    """处理相生边"""
    edge = GENERATION_EDGES.get(edge_key)
    if not edge:
        return source_output

    result = await call_llm(
        system_prompt=edge["prompt"],
        user_prompt=f"上游输出：\n{source_output[:6000]}",
        model_key=model_key,
        temperature=0.5,
        max_tokens=4096,
    )
    return result.get("text", source_output)


async def process_control(edge_key: str, source_output: str, target_output: str,
                          model_key: str = "deepseek") -> str:
    """处理相克边"""
    edge = CONTROL_EDGES.get(edge_key)
    if not edge:
        return ""

    result = await call_llm(
        system_prompt=edge["prompt"],
        user_prompt=f"约束源输出：\n{source_output[:4000]}\n\n被约束方输出：\n{target_output[:4000]}",
        model_key=model_key,
        temperature=0.5,
        max_tokens=2048,
    )
    return result.get("text", "")
