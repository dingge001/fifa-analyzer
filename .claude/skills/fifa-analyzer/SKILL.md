---
name: fifa
description: "[快捷命令：/fifa] 当用户询问以下内容时触发此技能：世界杯比赛（赛程、比分、预测）、足彩/竞彩分析（赔率、盘口、投注建议）、球队分析（实力、状态、伤停、交锋）、今日/明日比赛推荐。触发词：世界杯、World Cup、足彩、竞彩、赔率、盘口、betting、预测、分析、推荐、投注。示例：今天有什么比赛、分析法国vs德国、推荐今晚的投注、C组积分榜"
---

# FIFA Analyzer - 世界杯足彩分析技能

## 目标 (Objective)

为用户提供专业、全面的足球赛事分析和投注建议，覆盖赛程查询、赔率分析、球队实力评估、历史交锋、伤停信息、盘口走势等维度。

## 关键结果 (Key Results)

1. KR1: 准确识别用户意图（14种类型），匹配对应分析流程
2. KR2: 从可靠数据源获取最新、准确的赛事数据
3. KR3: 使用7维度评分模型生成专业的预测报告
4. KR4: 输出清晰、可操作的投注建议
5. KR5: 每次输出强制附加免责声明

---

## 执行流程

### Step 1: 意图识别

根据用户输入，识别对应的意图类型：

| 代码 | 意图 | 触发示例 |
|------|------|----------|
| I01 | 查询今日比赛 | "今天有什么比赛" |
| I02 | 查询明日比赛 | "明天有哪些世界杯比赛" |
| I03 | 查询特定日期 | "6月28日有什么比赛" |
| I04 | 单场预测分析 | "分析法国vs德国"、"预测明天的比赛" |
| I05 | 投注建议 | "推荐今晚的投注"、"有什么值得买的" |
| I06 | 查询赔率 | "西班牙赢球赔率多少" |
| I07 | 查询比分 | "巴西比赛现在几比几"、"实时比分" |
| I08 | 查询积分榜 | "C组积分榜"、"各组排名" |
| I09 | 球队实力分析 | "分析阿根廷实力" |
| I10 | 历史交锋 | "法国和德国历史交锋" |
| I11 | 伤停信息 | "巴西有哪些球员伤停" |
| I12 | 盘口走势 | "分析盘口变化"、"盘口走势" |
| I13 | 多场对比 | "比较今天三场比赛" |
| I14 | 冠军预测 | "谁最可能夺冠" |

### Step 2: 数据采集

按三层降级策略获取数据，详细配置见 `references/data-sources.md`：

**Tier 1（优先）**：
- Sofascore API - 赛程/比分/赔率/阵容/交锋/评分
- 澳客网 - 中文赔率/分析/专家推荐

**Tier 2（补充）**：
- 雷速体育 - 中文比分/积分
- Transfermarkt - 球员身价/伤停

**Tier 3（降级）**：
- WebSearch 搜索引擎获取摘要

**缓存策略**：
- 比分数据：5分钟TTL
- 赔率数据：1小时TTL
- 赛程数据：24小时TTL
- 交锋数据：30天TTL

### Step 3: 分析整合

使用7维度评分模型进行分析，详见 `references/analysis-model.md`：

| 维度 | 权重 | 数据来源 |
|------|------|----------|
| 球队实力 | 25% | FIFA排名 + 身价 + 阵容深度 |
| 近期状态 | 20% | 近10场胜率/进失球 |
| 历史交锋 | 15% | 近5-10次对阵记录 |
| 伤停影响 | 15% | 核心球员缺阵评估 |
| 主客场 | 10% | 主场优势系数 |
| 赔率信号 | 10% | 欧赔隐含概率 + 亚盘水位 |
| 其他因素 | 5% | 天气、裁判、赛程密度 |

### Step 4: 格式化输出

根据意图类型选择对应输出模板，详见 `references/output-templates.md`：

- I01/I02/I03 → T01 赛程列表
- I04 → T04 单场预测报告
- I05 → T05 投注建议卡
- I06 → T06 赔率查询
- I07 → T07 实时比分
- I08 → T08 积分榜
- I09 → T09 球队分析
- I10 → T10 历史交锋
- I11 → T11 伤停信息
- I12 → T12 盘口走势
- I13 → T13 多场对比
- I14 → T14 冠军预测

### Step 5: 免责声明

**每次输出末尾强制附加以下免责声明**：

```
---
⚠️ **免责声明**
1. 本分析仅供参考娱乐，不构成任何投注建议
2. 足球比赛充满不确定性，历史数据不代表未来结果
3. 请通过中国体育彩票等合法渠道参与竞猜
4. 请理性投注，量力而行，切勿沉迷
```

---

## 数据获取指南

### 依赖安装

首次使用前，安装Python依赖：
```bash
pip install -r .claude/skills/fifa-analyzer/scripts/requirements.txt
```

### 比赛数据获取（ESPN API）

**获取今日比赛**：
```bash
python .claude/skills/fifa-analyzer/scripts/fetch_matches.py today
```

**获取指定日期赛程**：
```bash
python .claude/skills/fifa-analyzer/scripts/fetch_matches.py schedule --date 2026-06-28
```

**获取赔率（含完整1X2、亚盘、大小球）**：
```bash
python .claude/skills/fifa-analyzer/scripts/fetch_matches.py odds --team Brazil
python .claude/skills/fifa-analyzer/scripts/fetch_matches.py odds --team France --json
```

**获取积分榜**：
```bash
# 全部小组
python .claude/skills/fifa-analyzer/scripts/fetch_matches.py standings
# 指定小组
python .claude/skills/fifa-analyzer/scripts/fetch_matches.py group --group H
```

### 澳客网（中文数据补充）

```bash
python .claude/skills/fifa-analyzer/scripts/fetch_okooo.py schedule
python .claude/skills/fifa-analyzer/scripts/fetch_okooo.py experts
```

### 缓存管理

```bash
python .claude/skills/fifa-analyzer/scripts/cache_manager.py status
python .claude/skills/fifa-analyzer/scripts/cache_manager.py clean
```

### 降级策略

当主要数据源不可用时：
1. 使用 `WebFetch` 抓取 ESPN/Sofascore 网页版
2. 使用 `WebSearch` 搜索相关信息
3. 标注数据来源和时效性

---

## 分析模型详解

### 7维度评分算法

**球队实力（25%）**：
- FIFA排名：排名1-10得100分，11-20得85分，21-30得70分...
- 球队身价：€1B+得100分，€500M-1B得85分...
- 阵容深度：主力+替补综合评分

**近期状态（20%）**：
- 近10场胜率：每胜10分
- 场均进球：每球10分
- 场均失球：每球-5分

**历史交锋（15%）**：
- 近5次对阵：每胜20分
- 进球数优势：每球5分

**伤停影响（15%）**：
- 核心球员缺阵：每缺一位关键球员扣10分
- 影响系数：0.8-1.0

**主客场（10%）**：
- 主场：系数1.1-1.2
- 中立场：系数1.0
- 客场：系数0.9

**赔率信号（10%）**：
- 欧赔隐含概率：直接转换
- 亚盘水位：水位<0.85看好主队

**其他因素（5%）**：
- 天气影响
- 裁判因素
- 赛程密度

### 信心指数计算

```
信心指数 = Σ(维度得分 × 权重) / 100 × 100%

投注建议等级：
- 强烈推荐：信心指数 > 80%
- 推荐：信心指数 60-80%
- 谨慎推荐：信心指数 40-60%
- 不建议：信心指数 < 40%
```

---

## 最佳实践

1. **数据时效性**：优先使用最新数据，标注数据获取时间
2. **多源验证**：关键数据（如赔率）使用多个数据源交叉验证
3. **缓存优先**：减少重复请求，使用本地缓存
4. **错误处理**：数据源失败时优雅降级，不中断服务
5. **免责声明**：每次输出必须包含免责声明
6. **中文优先**：优先使用中文数据源，输出使用中文

---

## 交付验收 (Verification)

- [ ] 输入"今天有什么比赛" → 输出今日赛程列表（T01格式）
- [ ] 输入"分析法国vs德国" → 输出完整预测报告（T04格式）
- [ ] 输入"推荐今晚的投注" → 输出投注建议卡（T05格式）
- [ ] 输入"C组积分榜" → 输出积分榜（T08格式）
- [ ] 每次输出末尾都有免责声明
- [ ] 数据源失败时能优雅降级
- [ ] 缓存机制正常工作

---

## 参考文档

- `references/data-sources.md` - 数据源配置和API端点
- `references/analysis-model.md` - 分析模型详细算法
- `references/output-templates.md` - 14种输出模板定义
- `references/odds-guide.md` - 盘口解读指南
- `references/world-cup-2026.md` - 2026世界杯信息
