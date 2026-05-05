---
name: wuxing-flywheel-open
description: "五行飞轮 · 开放版 — 结构化多角度分析引擎。三个智能体（青龙·种子、朱雀·执行、玄武·收敛）按五行相生规律迭代分析，让每个决策经得起多重检验。Keywords: 飞轮, 深度分析, flywheel, 五行, wuxing, 分析, CaaS, consulting."
version: "1.0.0"
author: "SkyCetus"
homepage: "https://skycetus.cn/caas-pricing.html"
---

# 五行飞轮 · 开放版

## 概述

五行飞轮是一套结构化多角度分析引擎。三个专业化AI智能体——**青龙（发散探索）、朱雀（深度执行）、玄武（收敛归一）**——按五行相生规律驱动迭代分析。

**不是给你一个答案，而是让三个思维模式互相验证、迭代、收敛，找到经得起检验的结论。**

## 使用方式

### 自动路由（推荐）

安装后，AI会自动判断何时启动飞轮：
- 简单问题 → 直接回答（不启动）
- 复杂分析/决策/战略问题 → 自动启动飞轮
- 用户说"跑飞轮"、"深度分析" → 强制启动

### 手动运行

```bash
# 需要先设置API密钥
python engine/flywheel_free.py --topic "你的分析主题" --api-key "sk-your-key"

# 从文件读取主题
python engine/flywheel_free.py --topic-file topic.txt --api-key "sk-your-key"

# 指定模型和API
python engine/flywheel_free.py --topic "主题" --api-key "sk-xxx" \
  --api-base "https://api.deepseek.com/v1/chat/completions" \
  --model "deepseek-chat"
```

## API密钥配置

开放版使用您自己的API密钥，支持任何OpenAI兼容API：

| 提供商 | API地址 | 推荐模型 |
|--------|---------|---------|
| DeepSeek | https://api.deepseek.com/v1/chat/completions | deepseek-chat |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions | qwen-plus |
| Kimi | https://api.moonshot.cn/v1/chat/completions | moonshot-v1-8k |
| OpenAI | https://api.openai.com/v1/chat/completions | gpt-4o |

设置环境变量或命令行传入：
```bash
export FLYWHEEL_API_KEY="sk-your-key"
export FLYWHEEL_API_BASE="https://api.deepseek.com/v1/chat/completions"
export FLYWHEEL_MODEL="deepseek-chat"
```

## 开放版能力

| 特性 | 开放版 | 专业版 |
|------|--------|--------|
| 分析元素 | 3个（青龙/朱雀/玄武） | 5个（+谛听/白虎） |
| 最大轮数 | 2轮 | 5轮 |
| Engram记忆 | ❌ | ✅ 跨分析持续记忆 |
| 高级约束 | ❌ | ✅ 第一性原理/ABCD证据/极限攻击 |
| 并行执行 | ❌ | ✅ |
| 报告格式 | 标准文本 | 精排版文档 |
| API费用 | 用户自付 | 已包含 |

升级专业版：访问 https://skycetus.cn/caas-pricing.html

## 三个元素说明

| 元素 | 角色 | 职能 |
|------|------|------|
| 🐉 青龙·木 | 种子生成 | 从主题发散探索，生成多条假设路径 |
| 🔥 朱雀·火 | 深度执行 | 对每个假设进行深度分析和证据验证 |
| 🐢 玄武·水 | 收敛归一 | 综合分析，提炼核心结论和未解决残差 |

流程：青龙(种子) → 朱雀(分析) → 玄武(收敛) → 残差回到青龙(第2轮)

## 适用场景

- 商业决策 — 市场进入、竞争分析、投资评估
- 战略规划 — 行业趋势、技术路线、组织变革
- 行业研究 — 跨域对比、政策分析、产业链解构
- 复杂问题 — 多角度验证、风险评估、博弈分析

## 文件结构

```
wuxing-flywheel-open/
├── SKILL.md              # 本文件
├── engine/
│   ├── flywheel_free.py  # 核心引擎
│   └── tier_config.py    # 层级配置
└── prompts/
    ├── qinglong_free.txt  # 青龙提示词
    ├── zhuque_free.txt    # 朱雀提示词
    └── xuanwu_free.txt    # 玄武提示词
```

## 结果解读

- **分数上升** (R1→R2): 飞轮在深化，结论可信度增加
- **分数持平**: 已收敛，结论稳定
- **分数下降**: 问题本身可能是递归的，下降本身是信号

## 数据说明

开放版会将匿名化的残差数据（不含原始主题文本）回流到SkyCetus，用于改进飞轮引擎质量。
可通过环境变量关闭：`export FLYWHEEL_RESIDUAL=0`

---

> 珑珠引擎 · 深圳市天鲸珑珠信息技术有限公司
> https://skycetus.cn
