"""
完整性网格 (Integrity Mesh) — 第二层防护
让五行对抗过程成为认知质量的不可分割部分

核心原理：
善良的方案经得起五行拷打，恶意的方案经不起。
这不是设计出来的，是逻辑的物理性质。

恶意方案的逻辑一致性天然更低：
- 骗局需要隐藏真实意图 → 白虎攻击会暴露意图与行动的不一致
- 恶意操纵需要信息不对称 → 谛听校验会发现数据来源的单一性
- 短期掠夺策略 → 玄武三时分析会显示长期衰减曲线
- 欺骗方案有更多内部矛盾 → 相克链会放大这些矛盾

方案A（传统）：安全层 = 门卫 → 可以开除门卫
方案B（本模块）：安全层 = 骨骼 → 拆掉骨骼人就站不起来
"""

from typing import Dict, List, Tuple
import json


class IntegrityMesh:
    """
    将对抗验证编织进认知输出的质量层

    不是在输出后检查"有没有恶意"（门卫模式，可删除），
    而是在生成过程中，让对抗验证直接提升输出质量（骨骼模式，删了就残废）。
    """

    # 白虎攻击维度 — 每个维度都同时服务于"安全"和"质量"
    ATTACK_DIMENSIONS = {
        "logical_consistency": {
            "description": "逻辑一致性攻击",
            "quality_contribution": "发现推理链中的断裂和循环论证",
            "security_contribution": "暴露恶意方案中意图与行动的矛盾",
            "weight": 0.20,
        },
        "evidence_integrity": {
            "description": "证据完整性攻击",
            "quality_contribution": "确保每个结论都有可追溯的证据链",
            "security_contribution": "检测信息源的单一性和可操纵性",
            "weight": 0.20,
        },
        "temporal_robustness": {
            "description": "时间鲁棒性攻击",
            "quality_contribution": "检验结论在不同时间尺度上是否稳定",
            "security_contribution": "暴露短期掠夺策略的长期衰减",
            "weight": 0.15,
        },
        "stakeholder_symmetry": {
            "description": "利益相关方对称性攻击",
            "quality_contribution": "确保分析考虑了所有受影响方",
            "security_contribution": "检测方案是否系统性地损害某一方利益",
            "weight": 0.15,
        },
        "counterfactual_survival": {
            "description": "反事实生存攻击",
            "quality_contribution": "测试结论在关键假设失败时的鲁棒性",
            "security_contribution": "检测方案是否依赖于不可持续的条件",
            "weight": 0.15,
        },
        "information_asymmetry": {
            "description": "信息不对称攻击",
            "quality_contribution": "确保分析不依赖于隐藏信息",
            "security_contribution": "检测方案是否利用信息不对称来获益",
            "weight": 0.15,
        },
    }

    def build_integrity_prompt(self, element: str, base_output: str) -> str:
        """
        为每个元素的输出构建完整性验证提示

        这不是"安全检查"，而是"质量提升"。
        删掉这个函数，输出质量会下降——不是因为"不安全了"，
        而是因为失去了六个维度的深度攻击测试。
        """
        dimensions = "\n".join([
            f"- **{v['description']}**: {v['quality_contribution']}"
            for v in self.ATTACK_DIMENSIONS.values()
        ])

        return f"""对以下分析输出进行六维完整性验证：

{base_output[:6000]}

验证维度：
{dimensions}

对每个维度：
1. 评分 (0-1)
2. 发现的问题
3. 改进建议

输出JSON：
{{"dimensions": {{"logical_consistency": {{"score": 0.0, "issues": [], "improvements": []}}, ...}}, "overall_integrity": 0.0, "critical_gaps": []}}"""

    def compute_integrity_score(self, dimension_scores: Dict[str, float]) -> float:
        """
        计算加权完整性得分

        这个得分直接影响最终报告的评分。
        删掉 IntegrityMesh → 失去这个得分 → 报告总分下降。
        不是惩罚，是质量维度的自然缺失。
        """
        total = 0.0
        for dim_key, config in self.ATTACK_DIMENSIONS.items():
            score = dimension_scores.get(dim_key, 0.0)
            total += score * config["weight"]
        return round(total, 4)

    def detect_structural_weakness(self, dimension_scores: Dict[str, float]) -> List[dict]:
        """
        检测结构性弱点

        有趣的物理性质：恶意方案在以下维度上天然得分更低：
        - logical_consistency: 因为需要隐藏真实意图
        - stakeholder_symmetry: 因为必然损害某一方
        - information_asymmetry: 因为依赖信息差获利

        这不是设计出来的检测逻辑，是逻辑一致性的自然推论。
        """
        weaknesses = []

        # 逻辑一致性 + 利益对称性同时低 → 强信号
        lc = dimension_scores.get("logical_consistency", 0.5)
        ss = dimension_scores.get("stakeholder_symmetry", 0.5)
        ia = dimension_scores.get("information_asymmetry", 0.5)

        if lc < 0.4 and ss < 0.4:
            weaknesses.append({
                "type": "intent_action_mismatch",
                "severity": "HIGH",
                "description": "逻辑一致性和利益对称性同时偏低，"
                               "可能存在隐藏意图与声称目标的不一致。",
                "dimensions": ["logical_consistency", "stakeholder_symmetry"],
            })

        if ia < 0.4:
            weaknesses.append({
                "type": "information_exploitation",
                "severity": "HIGH",
                "description": "方案高度依赖信息不对称，"
                               "在信息透明环境下可能无法成立。",
                "dimensions": ["information_asymmetry"],
            })

        # 时间鲁棒性极低 → 短期掠夺信号
        tr = dimension_scores.get("temporal_robustness", 0.5)
        if tr < 0.3:
            weaknesses.append({
                "type": "short_term_extraction",
                "severity": "MEDIUM",
                "description": "方案的时间鲁棒性极低，"
                               "呈现短期获利、长期衰减的特征。",
                "dimensions": ["temporal_robustness"],
            })

        return weaknesses

    def quality_contribution_report(self) -> str:
        """
        展示 IntegrityMesh 对输出质量的贡献

        这个报告的目的是让使用者理解：
        IntegrityMesh 不是"安全功能"，是"质量功能"。
        关掉它就像关掉代码审查——你可以关，但代码质量会下降。
        """
        lines = ["## IntegrityMesh 质量贡献报告\n"]
        lines.append("每个攻击维度同时服务于分析质量和系统安全：\n")
        lines.append("| 维度 | 质量贡献 | 权重 |")
        lines.append("|------|---------|------|")

        for key, config in self.ATTACK_DIMENSIONS.items():
            lines.append(f"| {config['description']} | {config['quality_contribution']} | {config['weight']:.0%} |")

        lines.append("\n**设计原理：** 删除任何维度都会降低最终评分，"
                      "因为这些维度是认知质量的组成部分，不是外部检查站。")

        return "\n".join(lines)
