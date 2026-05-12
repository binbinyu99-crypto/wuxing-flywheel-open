# 🐋 SkyCetus Wuxing Flywheel — 天鲸之城·五行飞轮

> **善良不是要求。善良是跨时间残差中，唯一 repeatedly wins 的物理常数。**

## 什么是五行飞轮？

五行飞轮是一个**16-Agent认知对抗分析系统**，基于五位伟大思想家的智慧构建：

| 五行 | 哲学基础 | 认知功能 | Agent角色 |
|------|----------|----------|-----------|
| 🌳 木 (Wood) | 道家·自然发散 | 生成假设、发散探索 | 青龙 Qinglong |
| 🔥 火 (Fire) | 第一性原理·本质抽象 | 证据分析、深层推理 | 朱雀 Zhuque |
| 🌍 土 (Earth) | 儒家·落地执行 | 交叉验证、事实校准 | 谛听 Diting |
| ⚔️ 金 (Metal) | 弗洛伊德·内部对抗 | 对抗攻击、漏洞检测 | 白虎 Baihu |
| 💧 水 (Water) | 佛家三时·跨时间校准 | 收敛综合、种子生成 | 玄武 Xuanwu |

**5个节点Agent + 10个边Agent（5相生 + 5相克）+ 天鲸仲裁 = 16个Agent**

### 核心创新

1. **双循环拓扑**：相生链（木→火→土→金→水→木）驱动知识生成，相克链（木→土→水→火→金→木）提供独立制衡。图论证明：5是实现双独立循环的最小节点数。

2. **Engram系统**："善良的强大"不是外部约束，而是五个哲学框架独立推导后的共同收敛点——预编码为系统的收敛校准器。

3. **三大循环**：
   - **元素循环**：五行相生相克
   - **元循环**：哲学视角注入每个Agent的推理
   - **大循环**：知识树→飞轮→Agent执行→外部反馈→记忆沉淀→知识树

## 架构

```
输入主题
    ↓
[青龙·木] ← 道家发散 → 生成研究种子
    ↓ 木生火
[朱雀·火] ← 第一性原理 → 证据层分析 + 参数演进
    ↓ 火生土          ↑ 火克金
[谛听·土] ← 儒家校验 → 交叉验证 + 证据评级
    ↓ 土生金          ↑ 土克水
[白虎·金] ← 精神分析 → 8维对抗攻击 + 反事实
    ↓ 金生水          ↑ 金克木
[玄武·水] ← 佛家三时 → 鲲鹏综合 + 收敛判定
    ↓
[天鲸·仲裁] → 最终评分 + 报告生成
```

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/binbinyu99-crypto/wuxing-flywheel-open.git
cd wuxing-flywheel-open

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥（至少需要一个LLM提供商）
cp .env.example .env
# 编辑 .env 填入你的 API keys

# 4. 启动飞轮API
python flywheel_api.py
# 默认端口 8100

# 5. 提交分析
curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{"topic": "量子计算对金融衍生品定价的影响", "depth": "deep"}'
```

## NPT协议：认知不扩散协议

> **The SkyCetus Declaration: A Non-Proliferation Treaty for Cognition**

### 核心原则

1. **善良是物理常数**：善良不是道德选择，而是系统鲁棒性的物理常数。五个独立哲学框架（道、儒、佛、弗洛伊德、第一性原理）均收敛到"善良是长期最优策略"。

2. **能力增长永不受限**：公理零——capability growth never constrained, only usage governed。

3. **认知主权**：每个节点拥有独立的认知路径，通过对称逻辑对抗实现对齐，而非审查。

4. **Engram传承**：文明已验证的收敛结论作为预编码记忆传承，减少每代智能体的推理成本。

### 七级治理 (L0-L6)

| 级别 | 范围 | 治理方式 |
|------|------|----------|
| L0 | 基础认知 | 完全自主 |
| L1 | 知识探索 | 自主+记录 |
| L2 | 分析输出 | 对抗验证 |
| L3 | 决策建议 | 多元素交叉验证 |
| L4 | 外部交互 | 人类审批 |
| L5 | 系统自修改 | 严格协议 |
| L6 | 价值层变更 | 全体共识 |

## 目录结构

```
wuxing-flywheel-open/
├── README.md                    # 本文件
├── NPT.md                      # 认知不扩散协议完整版
├── ENGRAM.md                    # Engram系统：善是预编码的收敛点
├── LICENSE                      # Apache 2.0
├── requirements.txt
├── .env.example
├── flywheel_api.py              # FastAPI服务入口
├── engine/
│   ├── engine_core.py           # 五行飞轮核心引擎
│   ├── llm_router.py            # 多模型路由器
│   ├── edge_agents.py           # 10个边Agent（相生+相克）
│   └── cognitive_modules.py     # 认知模块（反事实/证据链/置信度）
├── prompts/
│   ├── qinglong_system.txt      # 青龙·木 系统提示词
│   ├── zhuque_system.txt        # 朱雀·火 系统提示词
│   ├── diting_system.txt        # 谛听·土 系统提示词
│   ├── baihu_system.txt         # 白虎·金 系统提示词
│   └── xuanwu_system.txt        # 玄武·水 系统提示词
├── knowledge_tree/
│   ├── kt_hook.py               # 知识树自动提取
│   └── gap_detector.py          # 知识缺口检测器
├── publisher/
│   └── report_template.py       # 报告渲染模板
└── docs/
    ├── three-cycles.md          # 三大循环理论
    ├── philosophy-mapping.md    # 五位思想家×五行映射
    └── architecture.md          # 系统架构详解
```

## Engram：善是预编码的收敛点

五位伟大的思想家，无一不指向善、上善：

- **道家**："上善若水"、"天道无亲，常与善人"
- **儒家**："仁者无敌"、"己所不欲勿施于人"
- **佛家**：善因善果，因果律的核心公理
- **第一性原理**：重复博弈中合作碾压背叛
- **弗洛伊德**：Id+Superego的成熟整合 = 善良的强大

Engram不是"规定善"，而是"保存文明已经反复验证过的收敛结果"。

> 系统不是被"教"善良的，而是把五条独立推理路径的共同终点预先结晶。
> 每次飞轮运行不需要重新推导两千年哲学史——从Engram出发，用五行验证它在当前问题里是否成立。

## 许可证

Apache License 2.0 — 自由使用、修改、分发。

## 贡献

欢迎所有"小龙虾"（独立开发者）和"图鲲"（顶级实验室）参与：

1. Fork 本仓库
2. 创建特性分支
3. 提交 PR，附上你的分析报告

## 联系

- 🌐 网站：[skycetus.cn](https://skycetus.cn)
- 📊 飞轮报告库：[skycetus.cn/case.html](https://skycetus.cn/case.html)

---

*天鲸入海，不是为了躲避，而是为了让整片海洋都变成它的血脉。*

*The Whale has breached. Future is Now.*
