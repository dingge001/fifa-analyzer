# 数据源配置参考

本文档定义了所有数据源的API端点、URL映射、字段解析规则和降级策略。

---

## 一、Tier 1 核心数据源

### 1.1 Sofascore API

Sofascore 提供内部JSON API，无需认证，数据全面。

#### 基础配置

```yaml
base_url: https://www.sofascore.com/api/v1
headers:
  User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  Accept: "application/json"
rate_limit: 10 requests/minute
cache_ttl:
  live: 30s      # 实时比分
  odds: 300s     # 赔率
  schedule: 3600s # 赛程
  stats: 86400s  # 统计数据
```

#### API端点列表

| 功能 | 端点 | 参数 | 说明 |
|------|------|------|------|
| 今日比赛 | `/sport/football/events/live` | - | 获取当天所有比赛 |
| 指定日期赛程 | `/sport/football/events/{date}` | date: YYYY-MM-DD | 获取指定日期比赛 |
| 比赛详情 | `/event/{eventId}` | eventId | 单场比赛基本信息 |
| 比赛赔率 | `/event/{eventId}/odds` | eventId | 各家赔率对比 |
| 比赛阵容 | `/event/{eventId}/lineups` | eventId | 首发+替补阵容 |
| 比赛统计 | `/event/{eventId}/statistics` | eventId | 实时比赛统计 |
| 历史交锋 | `/event/{eventId}/h2h` | eventId | 两队历史对阵 |
| 球员评分 | `/event/{eventId}/players-ratings` | eventId | 球员评分数据 |
| 球队信息 | `/team/{teamId}` | teamId | 球队基本信息 |
| 球队赛程 | `/team/{teamId}/events/last/0` | teamId | 球队近期比赛 |

#### 关键字段解析

**比赛列表响应**：
```json
{
  "events": [
    {
      "id": 12345678,
      "tournament": {
        "name": "FIFA World Cup",
        "uniqueTournament": { "id": 16 }
      },
      "season": { "year": "26" },
      "roundInfo": { "round": 3 },
      "homeTeam": {
        "id": 123,
        "name": "France",
        "shortName": "FRA",
        "flag": "🇫🇷"
      },
      "awayTeam": {
        "id": 456,
        "name": "Germany",
        "shortName": "GER",
        "flag": "🇩🇪"
      },
      "homeScore": { "current": 2, "period1": 1 },
      "awayScore": { "current": 1, "period1": 0 },
      "status": {
        "code": 110,  // 110=进行中, 0=未开始, 100=已结束
        "description": "HT"
      },
      "startTimestamp": 1719180000,
      "venue": { "name": "MetLife Stadium" }
    }
  ]
}
```

**赔率响应**：
```json
{
  "odds": {
    "1": {  // 1X2 欧赔
      "marketName": "1X2",
      "choices": [
        { "name": "1", "odds": { "fractional": "6/5", "decimal": 2.20 }, "vendor": { "name": "Bet365" } },
        { "name": "X", "odds": { "fractional": "11/10", "decimal": 3.10 }, "vendor": { "name": "Bet365" } },
        { "name": "2", "odds": { "fractional": "3/1", "decimal": 4.00 }, "vendor": { "name": "Bet365" } }
      ]
    },
    "overUnder": {  // 大小球
      "marketName": "Over/Under",
      "choices": [
        { "name": "Over 2.5", "odds": { "decimal": 1.85 } },
        { "name": "Under 2.5", "odds": { "decimal": 1.95 } }
      ]
    },
    "asianHandicap": {  // 亚盘
      "marketName": "Asian Handicap",
      "choices": [
        { "name": "France -0.5", "odds": { "decimal": 1.90 } },
        { "name": "Germany +0.5", "odds": { "decimal": 2.00 } }
      ]
    }
  }
}
```

**状态码对照**：
| 代码 | 含义 |
|------|------|
| 0 | 未开始 |
| 60 | 中场休息 |
| 70 | 下半场补时 |
| 100 | 已结束 |
| 110 | 进行中 |
| 120 | 加时赛 |

---

### 1.2 澳客网 (okooo.com)

中文足球数据源，提供竞彩赔率和专家分析。

#### URL映射

| 功能 | URL | 说明 |
|------|-----|------|
| 竞彩赛程 | `https://info.sporttery.cn/football/match_list.php` | 当前可竞猜比赛 |
| 单场赔率 | `https://info.sporttery.cn/football/match_info.php?match_id={id}` | 单场详细赔率 |
| 专家推荐 | `https://info.sporttery.cn/football/expert_list.php` | 专家预测汇总 |
| 比分直播 | `https://info.sporttery.cn/football/live_score.php` | 实时比分 |
| 积分榜 | `https://info.sporttery.cn/football/standings.php?tournament={id}` | 各联赛积分榜 |

#### 页面解析规则

**竞彩赛程页面**：
```
表格结构：
- 第一列：编号
- 第二列：赛事
- 第三列：比赛时间
- 第四列：主队 vs 客队
- 第五列起：胜平负赔率、让球胜平负赔率、比分赔率、总进球赔率、半全场赔率
```

**专家推荐页面**：
```
每个专家卡片包含：
- 专家名称
- 命中率（近30场）
- 推荐比赛
- 推荐选项（胜/平/负、让球、大小球）
- 信心指数
```

---

## 二、Tier 2 补充数据源

### 2.1 雷速体育 (leisu.com)

#### URL映射

| 功能 | URL |
|------|-----|
| 即时比分 | `https://live.leisu.com/` |
| 世界杯 | `https://live.leisu.com/worldcup/` |
| 赛程 | `https://www.leisu.com/schedule` |
| 积分榜 | `https://www.leisu.com/standings` |

#### 注意事项

- 数据通过 JavaScript 动态加载
- 需要 WebFetch 解析完整页面后提取
- 优先使用 Sofascore API，雷速作为补充

---

### 2.2 Transfermarkt

球员身价和伤停信息首选。

#### URL映射

| 功能 | URL |
|------|-----|
| 球队身价 | `https://www.transfermarkt.com/{team}/startseite/verein/{id}` |
| 伤停列表 | `https://www.transfermarkt.com/premier-league/verletztespieler/wettbewerb/{comp}` |
| 球员详情 | `https://www.transfermarkt.com/{player}/profil/spieler/{id}` |

#### 数据提取

**球队身价页面**：
```
表格字段：
- 球员姓名
- 位置
- 年龄
- 国籍
- 身价（€）
- 合同到期时间
```

---

### 2.3 Flashscore

#### URL映射

| 功能 | URL |
|------|-----|
| 实时比分 | `https://www.flashscore.com/football/` |
| 世界杯 | `https://www.flashscore.com/football/world/world-cup/` |

#### 注意事项

- 数据通过 JS 动态加载
- 有地区限制警告
- 优先使用 Sofascore

---

## 三、Tier 3 降级方案

### 3.1 WebSearch 搜索引擎

当上述数据源全部不可用时，使用 WebSearch 获取信息。

#### 搜索策略

```
今日比赛：
  query: "2026世界杯今天比赛 赛程 比分"
  query: "FIFA World Cup 2026 today matches schedule"

赔率查询：
  query: "法国vs德国 赔率 博彩"
  query: "France Germany odds betting"

球队分析：
  query: "法国队 实力分析 世界杯2026"
  query: "France national team analysis World Cup"
```

#### 数据标注

使用搜索降级时，输出必须标注：
- 数据来源：搜索引擎摘要
- 时效性：可能不是最新数据
- 可信度：仅供参考，建议交叉验证

---

## 四、数据获取脚本

### 4.1 fetch_matches.py（主数据源：ESPN API）

```bash
# 使用示例
python scripts/fetch_matches.py today
python scripts/fetch_matches.py schedule --date 2026-06-28
python scripts/fetch_matches.py standings
python scripts/fetch_matches.py group --group H
python scripts/fetch_matches.py odds --team Brazil
python scripts/fetch_matches.py odds --team France --json
```

### 4.2 fetch_okooo.py（中文数据补充）

```bash
# 使用示例
python scripts/fetch_okooo.py schedule
python scripts/fetch_okooo.py odds --match-id 12345
python scripts/fetch_okooo.py experts
```

### 4.3 cache_manager.py

```bash
# 使用示例
python scripts/cache_manager.py status
python scripts/cache_manager.py clean
python scripts/cache_manager.py clean --type odds
```

---

## 五、缓存管理

### 5.1 缓存目录结构

```
data/
├── matches/       # 比赛数据 (TTL: 5分钟)
├── odds/          # 赔率数据 (TTL: 1小时)
├── schedules/     # 赛程数据 (TTL: 24小时)
└── head-to-head/  # 交锋数据 (TTL: 30天)
```

### 5.2 缓存文件命名

```
matches/{eventId}_{timestamp}.json
odds/{eventId}_{timestamp}.json
schedules/{date}_{timestamp}.json
head-to-head/{team1}_{team2}_{timestamp}.json
```

### 5.3 缓存清理

```bash
python scripts/cache_manager.py status
python scripts/cache_manager.py clean
python scripts/cache_manager.py clean --type odds
python scripts/cache_manager.py clean-all
```

---

## 六、错误处理

### 6.1 常见错误及应对

| 错误 | 原因 | 应对 |
|------|------|------|
| 403 Forbidden | IP被封或频率限制 | 等待5分钟，降级到Tier 2 |
| 429 Too Many Requests | 超过频率限制 | 使用缓存，减少请求频率 |
| 连接超时 | 网络问题 | 重试3次，降级到Tier 3 |
| 数据格式错误 | 网站改版 | 记录日志，降级到其他源 |

### 6.2 降级流程

```
1. 尝试 Tier 1 (Sofascore)
   ↓ 失败
2. 尝试 Tier 1 (澳客网)
   ↓ 失败
3. 尝试 Tier 2 (雷速/Transfermarkt)
   ↓ 失败
4. 使用 Tier 3 (WebSearch)
   ↓ 失败
5. 返回错误，提示用户稍后重试
```
