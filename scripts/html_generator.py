#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML生成器 - 总览页 + 专业两栏详情页"""

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "docs" / "data" / "matches.json"
DOCS = ROOT / "docs"
DETAILS = DOCS / "details"

# ============================================================
# 分组积分榜数据（硬编码，从ESPN获取）
# ============================================================
GROUP_STANDINGS = {
    "D": [
        {"pos": 1, "flag": "🇺🇸", "team": "美国", "p": 2, "w": 2, "d": 0, "l": 0, "gf": 6, "ga": 1, "gd": "+5", "pts": 6, "s": "已出线"},
        {"pos": 2, "flag": "🇦🇺", "team": "澳大利亚", "p": 2, "w": 1, "d": 0, "l": 1, "gf": 2, "ga": 2, "gd": "0", "pts": 3, "s": "已出线"},
        {"pos": 3, "flag": "🇵🇾", "team": "巴拉圭", "p": 2, "w": 1, "d": 0, "l": 1, "gf": 2, "ga": 4, "gd": "-2", "pts": 3, "s": "待定"},
        {"pos": 4, "flag": "🇹🇷", "team": "土耳其", "p": 2, "w": 0, "d": 0, "l": 2, "gf": 0, "ga": 3, "gd": "-3", "pts": 0, "s": "已淘汰"},
    ],
    "E": [
        {"pos": 1, "flag": "🇩🇪", "team": "德国", "p": 2, "w": 2, "d": 0, "l": 0, "gf": 9, "ga": 2, "gd": "+7", "pts": 6, "s": "已出线"},
        {"pos": 2, "flag": "🇨🇮", "team": "科特迪瓦", "p": 2, "w": 1, "d": 0, "l": 1, "gf": 2, "ga": 2, "gd": "0", "pts": 3, "s": "已出线"},
        {"pos": 3, "flag": "🇪🇨", "team": "厄瓜多尔", "p": 2, "w": 0, "d": 1, "l": 1, "gf": 0, "ga": 1, "gd": "-1", "pts": 1, "s": "待定"},
        {"pos": 4, "flag": "🇨🇼", "team": "库拉索", "p": 2, "w": 0, "d": 1, "l": 1, "gf": 1, "ga": 7, "gd": "-6", "pts": 1, "s": "已淘汰"},
    ],
    "F": [
        {"pos": 1, "flag": "🇳🇱", "team": "荷兰", "p": 2, "w": 1, "d": 0, "l": 0, "gf": 7, "ga": 3, "gd": "+4", "pts": 4, "s": "已出线"},
        {"pos": 2, "flag": "🇯🇵", "team": "日本", "p": 2, "w": 1, "d": 0, "l": 0, "gf": 6, "ga": 2, "gd": "+4", "pts": 4, "s": "已出线"},
        {"pos": 3, "flag": "🇸🇪", "team": "瑞典", "p": 2, "w": 1, "d": 0, "l": 1, "gf": 6, "ga": 6, "gd": "0", "pts": 3, "s": "待定"},
        {"pos": 4, "flag": "🇹🇳", "team": "突尼斯", "p": 2, "w": 0, "d": 0, "l": 2, "gf": 1, "ga": 9, "gd": "-8", "pts": 0, "s": "已淘汰"},
    ],
}

# ============================================================
# 维度分析文字自动生成
# ============================================================
DIM_ANALYSIS_TEMPLATES = {
    "球队实力": {
        "big_gap": "双方实力差距悬殊。{winner}FIFA排名{wr}，身价{strong}是{weak}的{ratio}倍，{strong}球员主要效力于{major_league}，整体实力明显占优。",
        "small_gap": "双方实力接近。{home}FIFA排名{home_rank}，{away}排名{away_rank}，{diff}实力差距不大。",
    },
    "近期状态": {
        "big_gap": "{winner}近期状态明显更好，{strong_text}；而{loser}近期表现低迷，{weak_text}。",
        "small_gap": "双方近期状态接近，{home_text}；{away_text}。",
    },
    "历史交锋": {
        "big_gap": "历史交锋中{winner}占优，过往记录明显偏向{winner}一方。",
        "neutral": "两队此前交手记录较少，无明确参考价值，本维度取中立分。",
    },
    "伤停影响": {
        "big_gap": "{winner}阵容更为齐整，{loser}存在一定的伤病困扰。",
        "small_gap": "双方目前均无重大伤停报告，阵容较为完整。",
        "note": "但{away}已出线，可能对部分球员进行轮换保护。",
    },
    "主客场": {
        "neutral": "世界杯为中立场，无明显主客场优势。",
        "home_adv": "{home}享有主场优势（东道主/地理接近），观众支持明显偏向{home}。",
    },
    "赔率信号": {
        "big_gap": "赔率极度看好{winner}（客胜1.15），隐含概率高达{prob}%，机构对其取胜信心极强。",
        "favor": "赔率偏向{winner}（{odds}），隐含概率{prob}%，机构较为看好。",
        "draw_favor": "平局赔率最低（{odds}），机构最看好双方战平。",
    },
    "其他因素": {
        "neutral": "比赛动机、天气、裁判等方面无明显倾向。",
        "motivation": "{home}动力因素占优：{home_reason}；{away}可能{away_reason}。",
    },
}


def fmt_odds(odds_val) -> str:
    try:
        return f"{float(odds_val):.2f}"
    except:
        return str(odds_val)


def generate_dim_text(dim: dict, match: dict) -> str:
    """为一个维度生成分析文字"""
    name = dim["name"]
    home_name = match.get("home", "主队")
    away_name = match.get("away", "客队")
    home_score = dim["home"]
    away_score = dim["away"]
    gap = abs(away_score - home_score)
    templates = DIM_ANALYSIS_TEMPLATES.get(name, {})

    if home_score > away_score:
        winner = home_name
        loser = away_name
        w_score = home_score
        l_score = away_score
    else:
        winner = away_name
        loser = home_name
        w_score = away_score
        l_score = home_score

    ti = match.get("team_info", {})
    hi = ti.get("home", {})
    ai = ti.get("away", {})
    odds = match.get("odds", {})

    if name == "球队实力":
        if gap > 30:
            strong = winner
            weak = loser
            wr = ai.get("fifa_rank", "?") if winner == away_name else hi.get("fifa_rank", "?")
            sv = ai.get("value", "?") if winner == away_name else hi.get("value", "?")
            wv = hi.get("value", "0") if winner == home_name else ai.get("value", "0")
            ml = "欧洲顶级联赛" if winner != home_name or "欧洲" in (ai.get("value", "")) else "欧洲主流联赛"
            return templates["big_gap"].format(winner=winner, wr=wr, strong=strong, weak=weak, ratio="多倍", major_league=ml)
        else:
            return templates["small_gap"].format(home=home_name, away=away_name, home_rank=hi.get("fifa_rank", "?"), away_rank=ai.get("fifa_rank", "?"), diff="整体" if gap < 15 else "略有")

    elif name == "近期状态":
        if gap > 30:
            form = match.get("recent_form", {})
            hf = form.get("home", [])
            af = form.get("away", [])
            strong_wins = sum(1 for f in (hf if winner == home_name else af) if f.get("result") in ["W", "D"])
            weak_loses = sum(1 for f in (hf if loser == home_name else af) if f.get("result") == "L")
            return templates["big_gap"].format(winner=winner, loser=loser, strong_text=f"近{len(hf if winner==home_name else af)}场表现强势", weak_text=f"近{len(hf if loser==home_name else af)}场表现低迷")
        else:
            return templates["small_gap"].format(home_text=f"{home_name}状态一般", away_text=f"{away_name}状态一般")

    elif name == "历史交锋":
        if gap > 20:
            return templates["big_gap"].format(winner=winner)
        return templates.get("neutral", "暂无历史交锋数据。")

    elif name == "伤停影响":
        if gap > 15:
            text = templates["big_gap"].format(winner=winner, loser=loser)
        else:
            text = templates["small_gap"]
        if match.get("notes", "").find("轮换") >= 0:
            text += " " + templates.get("note", "")
        return text

    elif name == "主客场":
        if match.get("home") == "美国":
            return templates["home_adv"].format(home=home_name)
        return templates.get("neutral", "中立场，无主客场偏向。")

    elif name == "赔率信号":
        away_odds = odds.get("away", 0)
        home_odds = odds.get("home", 0)
        draw_odds = odds.get("draw", 0)
        if away_odds <= 1.20:
            prob = round((1 / away_odds) * 100)
            return templates["big_gap"].format(winner=away_name, prob=prob)
        if draw_odds <= 2.5 and draw_odds < home_odds and draw_odds < away_odds:
            return templates["draw_favor"].format(odds=fmt_odds(draw_odds))
        best = away_name if away_odds < home_odds else home_name
        best_odds = min(away_odds, home_odds)
        prob = round((1 / best_odds) * 100)
        return templates["favor"].format(winner=best, odds=fmt_odds(best_odds), prob=prob)

    elif name == "其他因素":
        return templates.get("neutral", "没有明显倾向。")

    return ""


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# CSS
# ============================================================
CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f4f8;color:#1e293b;line-height:1.5}
.container{max-width:1500px;margin:0 auto;padding:14px 18px}

/* ===== 索引页 ===== */
.header{text-align:center;padding:18px 30px 14px;background:linear-gradient(135deg,#e0f2fe,#bae6fd,#7dd3fc);border-radius:14px;margin-bottom:14px}
.header h1{font-size:1.5rem;font-weight:700;color:#0c4a6e}
.header .sub{color:#0369a1;font-size:.8rem}
.stats{display:flex;justify-content:center;gap:14px;margin-top:12px;flex-wrap:wrap}
.stat-card{background:white;border-radius:10px;padding:8px 18px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.stat-num{font-size:1.3rem;font-weight:700;color:#0284c7}
.stat-label{font-size:.7rem;color:#64748b}

.filter-bar{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;align-items:center;background:white;border-radius:12px;padding:10px 16px;box-shadow:0 1px 4px rgba(0,0,0,.03)}
.filter-bar .lb{font-size:.8rem;color:#64748b;font-weight:600}
.filter-bar select{padding:7px 12px;border:1px solid #e2e8f0;border-radius:8px;background:#f8fafc;color:#334155;font-size:.82rem;outline:none}

.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.card{background:white;border-radius:12px;padding:16px 18px;box-shadow:0 1px 6px rgba(0,0,0,.03);border:1px solid #e2e8f0;transition:all .2s;cursor:pointer}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,.08);border-color:#3b82f6}
.card-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.group-badge{display:inline-flex;gap:3px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:white;padding:3px 10px;border-radius:16px;font-size:.75rem;font-weight:700}
.match-time{color:#64748b;font-size:.78rem}
.teams-row{display:flex;align-items:center;justify-content:center;gap:10px;margin:12px 0}
.team-block{flex:1;text-align:center}
.team-flag{font-size:1.6rem}
.team-name{font-weight:700;font-size:.92rem}
.vs-text{font-size:.9rem;color:#cbd5e1;font-weight:800}
.odds-bar{display:flex;height:6px;border-radius:3px;overflow:hidden;background:#e2e8f0;margin-top:8px}
.odds-bar div{height:100%}
.odds-legend{display:flex;justify-content:space-between;margin-top:5px;font-size:.7rem;color:#64748b}
.pred-box{background:#f8fafc;border-radius:10px;padding:12px;margin-top:10px}
.pred-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;font-size:.8rem}
.pred-label{color:#64748b}
.pred-val{font-weight:700;color:#1e293b}
.conf-badge{padding:2px 10px;border-radius:12px;font-size:.74rem;font-weight:600}
.conf-5{background:#22c55e1a;color:#15803d}
.conf-4{background:#3b82f61a;color:#1d4ed8}
.conf-3{background:#f59e0b1a;color:#b45309}
.detail-link{display:block;text-align:center;margin-top:12px;padding:9px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;color:#2563eb;text-decoration:none;font-weight:600;font-size:.8rem}
.detail-link:hover{background:#dbeafe}
.result-badge{font-size:.72rem;padding:2px 8px;border-radius:10px;font-weight:600}
.result-hit{background:#dcfce7;color:#15803d}
.result-miss{background:#fef2f2;color:#dc2626}
.result-pending{background:#f0f9ff;color:#0284c7}

@media(max-width:1200px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:768px){.grid{grid-template-columns:1fr}}

/* ===== 详情页 ===== */
.d-back{display:inline-flex;align-items:center;gap:4px;color:#3b82f6;text-decoration:none;font-size:.78rem;margin-bottom:8px;font-weight:500}
.d-back:hover{color:#1d4ed8}

/* Hero区 */
.d-hero{background:linear-gradient(135deg,#e0f2fe,#bae6fd,#7dd3fc);border-radius:14px;padding:18px 28px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}
.d-hero-left{flex:1}
.d-hero-title{font-size:1.5rem;font-weight:800;color:#0c4a6e;margin-bottom:6px}
.d-hero-meta{display:flex;gap:16px;flex-wrap:wrap;font-size:.78rem;color:#0369a1}
.d-hero-meta span{background:rgba(255,255,255,.6);padding:3px 10px;border-radius:10px}
.d-hero-right{text-align:center;background:white;border-radius:12px;padding:14px 22px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.d-hero-score{font-size:2rem;font-weight:800;color:#1e293b}
.d-hero-pred{font-size:.8rem;color:#64748b;margin-top:4px}

/* 两栏主内容 */
.d-main{display:flex;gap:12px}
.d-left{flex:1.2;min-width:0}
.d-right{flex:1;min-width:0}

/* Section通用 */
.section{background:white;border-radius:12px;padding:16px 18px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.03)}
.section h2{font-size:.95rem;color:#1e293b;margin-bottom:12px;padding-bottom:7px;border-bottom:1.5px solid #e2e8f0}
.section h3{font-size:.85rem;color:#334155;margin-bottom:8px}

/* 赔率Grid */
.odds-row{display:flex;gap:8px}
.odds-cell{flex:1;background:#f8fafc;border-radius:8px;padding:10px;text-align:center}
.odds-cell.best{background:#eff6ff;border:1.5px solid #3b82f6}
.odds-cell .ol{font-size:.7rem;color:#64748b}
.odds-cell .ov{font-size:1.1rem;font-weight:800;color:#1e293b}
.odds-cell .op{font-size:.68rem;color:#3b82f6;margin-top:2px}

/* 7维度 */
.dim-item{margin-bottom:8px;border-left:3px solid #e2e8f0;padding-left:10px}
.dim-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px}
.dim-name{font-size:.8rem;font-weight:700;color:#334155}
.dim-scores{font-size:.75rem;color:#64748b}
.dim-scores .s-home{color:#f59e0b;font-weight:700}
.dim-scores .s-away{color:#6366f1;font-weight:700}
.dim-track{display:flex;height:5px;border-radius:3px;overflow:hidden;background:#f1f5f9;margin:4px 0}
.dim-track .t-home{background:linear-gradient(90deg,#f59e0b,#fbbf24)}
.dim-track .t-away{background:linear-gradient(90deg,#6366f1,#8b5cf6)}
.dim-text{font-size:.73rem;color:#64748b;line-height:1.5;margin-top:3px}

/* 积分榜表格 */
.standings-table{width:100%;border-collapse:collapse;font-size:.72rem}
.standings-table th{background:#f1f5f9;padding:5px 6px;text-align:center;font-weight:600;color:#475569}
.standings-table td{padding:5px 6px;text-align:center;border-bottom:1px solid #f1f5f9;color:#475569}
.standings-table .team-col{text-align:left}
.standings-table .hl{background:#eff6ff}
.standings-table .hl td{color:#1d4ed8;font-weight:600}

/* 近期战绩小表 */
.form-mini{width:100%;border-collapse:collapse;font-size:.7rem;margin-bottom:8px}
.form-mini th{background:#f8fafc;padding:3px 6px;text-align:left;font-weight:600;color:#94a3b8}
.form-mini td{padding:3px 6px;border-bottom:1px solid #f1f5f9;color:#64748b}
.rw{color:#22c55e;font-weight:700}
.rd{color:#f59e0b;font-weight:700}
.rl{color:#ef4444;font-weight:700}

/* 球员对位 */
.matchup-row{display:flex;align-items:center;gap:8px;padding:6px 10px;border-bottom:1px solid #f1f5f9;font-size:.78rem}
.matchup-row:last-child{border-bottom:none}
.mu-home{flex:1;text-align:right;font-weight:600;color:#f59e0b}
.mu-vs{color:#94a3b8;font-size:.7rem}
.mu-away{flex:1;text-align:left;font-weight:600;color:#6366f1}
.mu-pos{font-size:.68rem;color:#94a3b8;min-width:40px;text-align:center}

/* 投注建议 */
.bet-table{width:100%;border-collapse:collapse;font-size:.76rem}
.bet-table th{background:#f1f5f9;padding:6px 10px;text-align:left;font-weight:600;color:#475569}
.bet-table td{padding:6px 10px;border-bottom:1px solid #f1f5f9;color:#475569}

/* 备注 */
.note-box{font-size:.75rem;color:#92400e;line-height:1.6;background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;padding:10px 14px}

/* 小免责 */
.mini-disclaimer{font-size:.65rem;color:#94a3b8;text-align:center;padding:6px;background:white;border-radius:6px;margin-top:10px}

@media(max-width:1000px){.d-main{flex-direction:column}}

.rw{color:#22c55e;font-weight:700}
.rd{color:#f59e0b;font-weight:700}
.rl{color:#ef4444;font-weight:700}
"""

# ============================================================
# 索引页模板
# ============================================================
INDEX_TMP = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>2026世界杯分析报告</title><style>__CSS__</style></head><body><div class="container">
<div class="header"><h1>2026世界杯分析报告</h1><div class="sub">专业数据分析 · 7维度评分模型</div><div class="stats" id="stats"></div></div>
<div class="filter-bar"><span class="lb">日期:</span><select id="ds" onchange="f()"><option value="all">全部</option></select><span class="lb" style="margin-left:12px">分组:</span><select id="gs" onchange="f()"><option value="all">全部</option></select><span class="lb" style="margin-left:12px">信心:</span><select id="cs" onchange="f()"><option value="all">全部</option><option value="5">强烈推荐</option><option value="4">推荐</option><option value="3">谨慎推荐</option></select></div>
<div class="grid" id="grid"></div>
<div style="text-align:center;color:#94a3b8;font-size:.7rem;padding:10px">免责：本分析仅供参考娱乐，不构成投注建议</div>
</div>
<script>
var ALL=[];__DATA__
function init(){
 var t=ALL.length,a=ALL.filter(function(m){return m.p}).length,h=ALL.filter(function(m){return m.l>=4}).length;
 document.getElementById('stats').innerHTML='<div class="stat-card"><div class="stat-num">'+t+'</div><div class="stat-label">比赛场次</div></div><div class="stat-card"><div class="stat-num">'+a+'</div><div class="stat-label">已分析</div></div><div class="stat-card"><div class="stat-num">'+h+'</div><div class="stat-label">高信心推荐</div></div>';
 var ds=document.getElementById('ds'),gs=document.getElementById('gs'),dates=[],groups=[];
 ALL.forEach(function(m){if(dates.indexOf(m.d)===-1)dates.push(m.d);if(groups.indexOf(m.g)===-1&&m.g)groups.push(m.g)});
 dates.sort().reverse();groups.sort();
 dates.forEach(function(d){ds.innerHTML+='<option value="'+d+'">'+d+' ('+ALL.filter(function(m){return m.d===d}).length+'场)</option>'});
 groups.forEach(function(g){gs.innerHTML+='<option value="'+g+'">'+g+'组</option>'});
 f();
}
function f(){
 var dd=document.getElementById('ds').value,gg=document.getElementById('gs').value,cc=document.getElementById('cs').value;
 var fl=ALL;
 if(dd!=='all')fl=fl.filter(function(m){return m.d===dd});
 if(gg!=='all')fl=fl.filter(function(m){return m.g===gg});
 if(cc!=='all')fl=fl.filter(function(m){return m.l>=parseInt(cc)});
 r(fl);
}
function r(matches){
 var h='';
 matches.forEach(function(m){
  var rb='';
  if(m.r&&typeof m.r==='object')rb='<span class="result-badge '+(m.r.h?'result-hit':'result-miss')+'">'+(m.r.h?'命中':'未中')+' '+m.r.s+'</span>';
  else if(m.p)rb='<span class="result-badge result-pending">待赛</span>';
  h+='<div class="card"><div class="card-top"><span class="group-badge">'+(m.g||'?')+'组</span><span class="match-time">'+m.d+' '+m.t+'</span>'+rb+'</div>'
  +'<div class="teams-row"><div class="team-block"><div class="team-flag">'+m.hf+'</div><div class="team-name">'+m.h+'</div></div>'
  +'<div class="vs-text">VS</div><div class="team-block"><div class="team-flag">'+m.af+'</div><div class="team-name">'+m.a+'</div></div></div>'
  +'<div><div class="odds-bar"><div style="width:'+m.hp+'%;background:#22c55e"></div><div style="width:'+m.dp+'%;background:#94a3b8"></div><div style="width:'+m.ap+'%;background:#ef4444"></div></div>'
  +'<div class="odds-legend"><span>主 '+m.oh+'</span><span>平 '+m.od+'</span><span>客 '+m.oa+'</span></div></div>'
  +'<div class="pred-box"><div class="pred-row"><span class="pred-label">推荐</span><span class="pred-val">'+m.pl+'</span></div>'
  +'<div class="pred-row"><span class="pred-label">预测比分</span><span class="pred-val">'+m.ps+'</span></div>'
  +'<div class="pred-row"><span class="pred-label">信心</span><span class="conf-badge conf-'+m.cls+'">'+m.cs+' '+m.cl+'</span></div></div>'
  +'<a href="details/'+m.fid+'.html" class="detail-link">查看详细分析</a></div>';
 });
 document.getElementById('grid').innerHTML=h||'<p style="text-align:center;color:#64748b;padding:50px;background:white;border-radius:16px">暂无比赛</p>';
}
init();
</script></body></html>"""

# ============================================================
# 详情页模板
# ============================================================
DETAIL_TMP = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>__TITLE__</title><style>__CSS__</style></head><body><div class="container">
<a href="../index.html" class="d-back">← 返回总览</a>

<!-- Hero -->
<div class="d-hero">
  <div class="d-hero-left">
    <div class="d-hero-title">__HOME_FLAG__ __HOME__  VS  __AWAY__ __AWAY_FLAG__</div>
    <div class="d-hero-meta">
      <span>__DATE__ __TIME__</span>
      <span>__GROUP__组</span>
      <span>__VENUE__</span>
    </div>
  </div>
  <div class="d-hero-right">
    <div class="d-hero-score">__PRED_SCORE__</div>
    <div class="d-hero-pred">预测 · <strong>__PRED_LABEL__</strong> @ __BEST_ODDS__</div>
    <div style="margin-top:6px"><span class="conf-badge __CONF_CLASS__" style="font-size:.78rem">__CONF_STARS__ __CONF_LABEL__ · __CONF_PCT__%</span></div>
  </div>
</div>

<!-- 两栏主体 -->
<div class="d-main">

  <!-- 左栏 -->
  <div class="d-left">

    <!-- 赔率 + 出线形势 -->
    <div class="section">
      <div style="display:flex;gap:14px">
        <div style="flex:1">
          <h2>赔率 (DraftKings)</h2>
          <div class="odds-row">
            <div class="odds-cell"><div class="ol">主胜</div><div class="ov">__HOME_ODDS__</div><div class="op">__HOME_PROB__%</div></div>
            <div class="odds-cell"><div class="ol">平局</div><div class="ov">__DRAW_ODDS__</div><div class="op">__DRAW_PROB__%</div></div>
            <div class="odds-cell best"><div class="ol">客胜</div><div class="ov">__AWAY_ODDS__</div><div class="op">__AWAY_PROB__%</div></div>
          </div>
        </div>
        <div style="flex:1">
          <h2>__GROUP__组积分榜</h2>
          <table class="standings-table"><thead><tr><th>#</th><th class="team-col">球队</th><th>场</th><th>净胜</th><th>分</th></tr></thead>
          <tbody>__STANDINGS__</tbody></table>
        </div>
      </div>
    </div>

    <!-- 7维度 -->
    <div class="section">
      <h2>7维度评分分析</h2>
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:14px">
        <div style="text-align:center;background:#f8fafc;border-radius:10px;padding:10px 18px"><div style="font-size:1.4rem;font-weight:800;color:#f59e0b">__HOME_SCORE__</div><div style="font-size:.7rem;color:#64748b">__HOME__</div></div>
        <div style="flex:1;text-align:center;font-size:.75rem;color:#94a3b8">综合评分对比</div>
        <div style="text-align:center;background:#eff6ff;border-radius:10px;padding:10px 18px"><div style="font-size:1.4rem;font-weight:800;color:#6366f1">__AWAY_SCORE__</div><div style="font-size:.7rem;color:#64748b">__AWAY__</div></div>
      </div>
      __DIMENSIONS__
    </div>

  </div>

  <!-- 右栏 -->
  <div class="d-right">

    <!-- 近期战绩 -->
    <div class="section">
      <h2>近期战绩</h2>
      <div><h3>__HOME_FLAG__ __HOME__</h3>
        <table class="form-mini"><thead><tr><th>对手</th><th>比分</th><th>R</th></tr></thead><tbody>__HOME_FORM__</tbody></table></div>
      <div style="margin-top:10px"><h3>__AWAY_FLAG__ __AWAY__</h3>
        <table class="form-mini"><thead><tr><th>对手</th><th>比分</th><th>R</th></tr></thead><tbody>__AWAY_FORM__</tbody></table></div>
    </div>

    <!-- 投注建议 -->
    <div class="section">
      <h2>投注建议</h2>
      <table class="bet-table"><thead><tr><th>玩法</th><th>推荐</th><th>赔率</th></tr></thead>
      <tbody>
        <tr><td><strong>胜负</strong></td><td><strong>__PRED_LABEL__</strong></td><td>__BEST_ODDS__</td></tr>
        <tr><td><strong>比分</strong></td><td>__PRED_SCORE__</td><td>-</td></tr>
        <tr><td>投注金额</td><td colspan="2">CNY __BET_AMOUNT__</td></tr>
      </tbody></table>
    </div>

    <!-- 核心对位 -->
    <div class="section">
      <h2>核心对位</h2>
      __MATCHUPS__
    </div>

    <!-- 备注 -->
    <div class="section">
      <h2>备注</h2>
      __NOTES__
    </div>

  </div>
</div>

<div class="mini-disclaimer">免责：本分析仅供参考娱乐，不构成投注建议。数据来源：ESPN API (DraftKings)</div>
</div></body></html>"""


# ============================================================
# 渲染函数
# ============================================================
def render_index(data):
    dates = data.get("dates", {})
    arr = []
    for ds, ms in dates.items():
        for m in ms:
            if not m.get("prediction"):
                continue
            o = m.get("odds", {})
            ho = float(o.get("home", 2.5))
            do = float(o.get("draw", 3.5))
            ao = float(o.get("away", 3.0))
            hp = 1 / ho; dp = 1 / do; ap = 1 / ao; t = hp + dp + ap
            a = m.get("analysis", {})
            c = a.get("confidence", 50)
            cl = 3 if c < 40 else (4 if c < 60 else 5)
            fid = "match_" + str(m.get("id", ""))
            rs = m.get("result")
            st = None
            if rs:
                st = {"s": str(rs.get("home_score", 0)) + "-" + str(rs.get("away_score", 0)), "h": m.get("pnl", {}).get("hit", False)}
            arr.append({
                "d": ds, "t": m.get("time", ""), "g": m.get("group", ""),
                "h": m.get("home", ""), "a": m.get("away", ""),
                "hf": m.get("home_flag", ""), "af": m.get("away_flag", ""),
                "oh": str(o.get("home", "-")), "od": str(o.get("draw", "-")), "oa": str(o.get("away", "-")),
                "hp": round(hp / t * 100, 1), "dp": round(dp / t * 100, 1), "ap": round(ap / t * 100, 1),
                "pl": str(m.get("prediction", {}).get("label", "-")),
                "ps": str(m.get("prediction", {}).get("score", "-")),
                "cs": str(a.get("confidence_stars", "")), "cl": str(a.get("confidence_label", "")),
                "cls": str(cl), "l": cl, "p": bool(m.get("prediction", {}).get("result")),
                "fid": fid, "r": st
            })
    js = "ALL=" + json.dumps(arr, ensure_ascii=False) + ";"
    return INDEX_TMP.replace("__CSS__", CSS).replace("__DATA__", js)


def render_detail(match):
    m = match
    o = m.get("odds", {})
    p = m.get("prediction", {})
    a = m.get("analysis", {})
    dims = a.get("dimensions", [])
    form = m.get("recent_form", {})
    ti = m.get("team_info", {})
    home = m.get("home", "")
    away = m.get("away", "")
    grp = m.get("group", "?")

    ho = float(o.get("home", 2.5))
    do = float(o.get("draw", 3.5))
    ao = float(o.get("away", 3.0))
    hp = 1 / ho; dp2 = 1 / do; ap2 = 1 / ao; t = hp + dp2 + ap2

    # 7维度HTML
    dims_html = ""
    for d in dims:
        hs = d["home"]
        aws = d["away"]
        tot = hs + aws or 1
        hpct = int(hs / tot * 100)
        apct = int(aws / tot * 100)
        text = generate_dim_text(d, match) or ""
        dims_html += f"""<div class="dim-item">
<div class="dim-header"><span class="dim-name">{d['name']} (权重{d['weight']}%)</span><span class="dim-scores"><span class="s-home">{home} {hs}</span> · <span class="s-away">{away} {aws}</span></span></div>
<div class="dim-track"><div class="t-home" style="width:{hpct}%"></div><div class="t-away" style="width:{apct}%"></div></div>
<div class="dim-text">{text}</div></div>"""

    # 积分榜
    standings = GROUP_STANDINGS.get(grp, [])
    st_html = ""
    for s in standings:
        hl = " hl" if s["team"] in [home, away] else ""
        st_html += f'<tr class="{hl}"><td>{s["pos"]}</td><td class="team-col">{s["flag"]} {s["team"]}</td><td>{s["p"]}</td><td>{s["gd"]}</td><td><strong>{s["pts"]}</strong></td></tr>'

    # 近期战绩
    def form_rows(data):
        r = ""
        for f in data:
            rc = f['result'].lower()
            r += f'<tr><td>{f["opponent"]}</td><td>{f["score"]}</td><td class="r{rc}">{f["result"]}</td></tr>'
        return r

    hf_html = form_rows(form.get("home", []))
    af_html = form_rows(form.get("away", []))

    # 球员对位
    home_players = ti.get("home", {}).get("key_players", [])
    away_players = ti.get("away", {}).get("key_players", [])
    positions = ["中场", "后卫", "前锋", "边锋", "门将"]
    mu_html = ""
    for i in range(max(len(home_players), len(away_players))):
        hp_name = home_players[i] if i < len(home_players) else "-"
        ap_name = away_players[i] if i < len(away_players) else "-"
        pos = positions[i] if i < len(positions) else "其他"
        mu_html += f'<div class="matchup-row"><span class="mu-home">{hp_name}</span><span class="mu-pos">{pos}</span><span class="mu-vs">VS</span><span class="mu-away">{ap_name}</span></div>'

    # 备注
    notes = m.get("notes", "")
    if not notes:
        notes = f"综合7维度模型评分，{away if a.get('scores',{}).get('away',0)>a.get('scores',{}).get('home',0) else home}整体占优。信心指数{a.get('confidence',50):.0f}%，推荐{p.get('label','?')}。"

    conf = a.get("confidence", 50)
    conf_class = "conf-5" if conf >= 75 else ("conf-4" if conf >= 60 else "conf-3")

    html = DETAIL_TMP
    html = html.replace("__CSS__", CSS)
    html = html.replace("__TITLE__", f"{home} vs {away}")
    html = html.replace("__HOME_FLAG__", m.get("home_flag", ""))
    html = html.replace("__AWAY_FLAG__", m.get("away_flag", ""))
    html = html.replace("__HOME__", home)
    html = html.replace("__AWAY__", away)
    html = html.replace("__DATE__", m.get("date", ""))
    html = html.replace("__TIME__", m.get("time", ""))
    html = html.replace("__GROUP__", grp)
    html = html.replace("__VENUE__", m.get("venue", "待定"))
    html = html.replace("__HOME_ODDS__", str(o.get("home", "-")))
    html = html.replace("__DRAW_ODDS__", str(o.get("draw", "-")))
    html = html.replace("__AWAY_ODDS__", str(o.get("away", "-")))
    html = html.replace("__HOME_PROB__", str(round(hp / t * 100, 1)))
    html = html.replace("__DRAW_PROB__", str(round(dp2 / t * 100, 1)))
    html = html.replace("__AWAY_PROB__", str(round(ap2 / t * 100, 1)))
    html = html.replace("__PRED_SCORE__", str(p.get("score", "-")))
    html = html.replace("__PRED_LABEL__", str(p.get("label", "-")))
    html = html.replace("__BEST_ODDS__", str(p.get("best_odds", "-")))
    html = html.replace("__BET_AMOUNT__", f'{p.get("bet_amount",0):,.2f}')
    html = html.replace("__CONF_PCT__", str(int(conf)))
    html = html.replace("__CONF_STARS__", str(a.get("confidence_stars", "")))
    html = html.replace("__CONF_LABEL__", str(a.get("confidence_label", "")))
    html = html.replace("__CONF_CLASS__", conf_class)
    html = html.replace("__HOME_SCORE__", str(a.get("scores", {}).get("home", 0)))
    html = html.replace("__AWAY_SCORE__", str(a.get("scores", {}).get("away", 0)))
    html = html.replace("__DIMENSIONS__", dims_html)
    html = html.replace("__STANDINGS__", st_html)
    html = html.replace("__HOME_FORM__", hf_html)
    html = html.replace("__AWAY_FORM__", af_html)
    html = html.replace("__MATCHUPS__", mu_html)
    html = html.replace("__NOTES__", notes)
    return html


def generate_all():
    data = load_data()
    dates = data.get("dates", {})

    # 首页
    (DOCS / "index.html").write_text(render_index(data), encoding="utf-8")
    print(f"Generated: {DOCS}/index.html")

    # 详情
    DETAILS.mkdir(parents=True, exist_ok=True)
    n = 0
    for ds, ms in dates.items():
        for m in ms:
            if not m.get("prediction"): continue
            fid = "match_" + str(m.get("id", ""))
            (DETAILS / f"{fid}.html").write_text(render_detail(m), encoding="utf-8")
            n += 1
    print(f"Generated {n} detail pages")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("action", nargs="?", default="all", choices=["all"])
    args = p.parse_args()
    generate_all()
