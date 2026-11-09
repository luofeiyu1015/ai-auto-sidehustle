"""
市场分析模块
自动收集公开热榜数据，识别赚钱机会，打分排序
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
import re
import random
import json
import time
from datetime import datetime, timedelta
from modules import db
from config import SEED_KEYWORDS, MIN_HEAT_SCORE, HEADERS, DATA_SOURCES

# 真实的热榜数据源（公开免费，无需登录）
HOT_API_SOURCES = [
    {
        'name': '知乎热榜',
        'url': 'https://www.zhihu.com/api/v4/feed/topstory/hot-lists/total',
        'parser': 'zhihu',
    },
    {
        'name': '百度热搜',
        'url': 'https://top.baidu.com/api/board?platform=wise&tab=realtime',
        'parser': 'baidu',
    },
    {
        'name': '微博热搜',
        'url': 'https://weibo.com/ajax/side/hotSearch',
        'parser': 'weibo',
    },
]


def fetch_hot_baidu():
    """爬百度热搜（公开API）"""
    try:
        resp = requests.get(
            'https://top.baidu.com/api/board?platform=wise&tab=realtime',
            headers=HEADERS, timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            hot_words = []
            cards = data.get('data', {}).get('cards', [])
            for card in cards:
                for item in card.get('content', []):
                    word = item.get('word', '').strip()
                    heat = item.get('hotScore', 0) or item.get('desc', '')
                    if word:
                        hot_words.append({
                            'keyword': word,
                            'heat': int(heat) if isinstance(heat, (int, float)) else random.randint(20, 100),
                            'source': '百度热搜',
                        })
            return hot_words[:30]
    except Exception as e:
        db.log_run('market', 'warning', f'百度热榜抓取失败: {e}')
    return []


def fetch_hot_weibo():
    """爬微博热搜（公开API）"""
    try:
        resp = requests.get(
            'https://weibo.com/ajax/side/hotSearch',
            headers={**HEADERS, 'Referer': 'https://weibo.com/'}, timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            hot_words = []
            for item in data.get('data', {}).get('realtime', [])[:30]:
                word = item.get('note', '').strip()
                num = item.get('num', 0)
                if word:
                    hot_words.append({
                        'keyword': word,
                        'heat': int(num) if num else random.randint(30, 100),
                        'source': '微博热搜',
                    })
            return hot_words[:30]
    except Exception as e:
        db.log_run('market', 'warning', f'微博热榜抓取失败: {e}')
    return []


def fetch_hot_zhihu():
    """爬知乎热榜"""
    try:
        resp = requests.get(
            'https://www.zhihu.com/api/v4/feed/topstory/hot-lists/total',
            headers={**HEADERS, 'Referer': 'https://www.zhihu.com/hot'},
            params={'limit': 50},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            hot_words = []
            for item in data.get('data', [])[:30]:
                target = item.get('target', {})
                title = target.get('title', '').strip()
                excerpt = target.get('excerpt', '')
                heat = item.get('detail_text', '')
                if title:
                    hot_words.append({
                        'keyword': title,
                        'heat': random.randint(40, 100),
                        'source': '知乎热榜',
                    })
            return hot_words[:30]
    except Exception as e:
        db.log_run('market', 'warning', f'知乎热榜抓取失败: {e}')
    return []


def fetch_all_hot():
    """获取所有热榜"""
    all_hot = []
    for func in [fetch_hot_baidu, fetch_hot_weibo, fetch_hot_zhihu]:
        try:
            results = func()
            all_hot.extend(results)
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ {func.__name__} 失败: {e}")
    return all_hot


def calc_keyword_heat(keyword, hot_list):
    """计算关键词在热榜中的热度"""
    score = 0
    keyword_lower = keyword.lower()
    for item in hot_list:
        word = item['keyword'].lower()
        if keyword_lower in word or word in keyword_lower:
            score += min(item['heat'], 100)
        # 部分匹配也给分
        for char in keyword_lower:
            if char in word:
                score += item['heat'] * 0.05
                break
    return min(score, 100)


def estimate_competition(keyword):
    """估算竞争程度（简单启发式）"""
    # 关键词越长越细分，竞争越小
    word_len = len(keyword)
    if word_len >= 8:
        base = 0.3
    elif word_len >= 5:
        base = 0.5
    else:
        base = 0.7
    
    # 常见高竞争词加成
    high_comp = ['赚钱', '副业', '赚钱方法', '创业']
    for w in high_comp:
        if w in keyword:
            base += 0.15
    
    return min(base + random.uniform(-0.1, 0.1), 1.0)


def estimate_avg_price(keyword):
    """估算产品均价（基于市场定位）"""
    price_map = {
        'AI': (15, 30),
        'Prompt': (12, 25),
        '提示词': (10, 20),
        '副业': (8, 20),
        '赚钱': (8, 18),
        'Excel': (10, 18),
        '飞书': (12, 25),
        '模板': (5, 15),
        '教程': (15, 30),
        '文案': (8, 18),
    }
    base = 9.9  # 默认价
    for key, (low, high) in price_map.items():
        if key in keyword:
            base = random.uniform(low, high)
            break
    return round(base, 1)


def score_opportunity(keyword, heat, competition, avg_price):
    """
    综合评分
    满分 100，越高越值得做
    """
    # 热度权重 40%
    heat_score = min(heat / 100, 1.0) * 40
    
    # 低竞争权重 30%（竞争越低分越高）
    comp_score = (1 - competition) * 30
    
    # 合理定价权重 20%（10-30元区间最优）
    if 10 <= avg_price <= 30:
        price_score = 20
    elif 5 <= avg_price < 10 or 30 < avg_price <= 50:
        price_score = 15
    else:
        price_score = 10
    
    # 零成本加成 10%（数字产品成本为0）
    cost_score = 10  # 数字产品默认零成本
    
    return round(heat_score + comp_score + price_score + cost_score, 1)


def analyze_market():
    """
    主入口：执行市场分析
    返回高分机会列表
    """
    print("🔍 开始市场分析...")
    db.log_run('market', 'info', '开始市场分析')
    
    try:
        # 1. 获取热榜
        hot_list = fetch_all_hot()
        print(f"📊 抓取到 {len(hot_list)} 条热榜数据")
        
        # 2. 从热榜和种子关键词中提取机会
        all_keywords = list(SEED_KEYWORDS)
        
        # 从热榜中提取含 AI/副业/赚钱 的关键词
        hot_keywords = set()
        for item in hot_list:
            word = item['keyword']
            for seed in ['AI', '副业', '赚钱', 'Prompt', '提示词', 'Excel', '飞书', '模板', '运营', '文案', '教程']:
                if seed in word and len(word) >= 3:
                    hot_keywords.add(word)
        
        all_keywords.extend(hot_keywords)
        
        # 3. 对每个关键词评分
        opportunities = []
        for kw in set(all_keywords):
            heat = calc_keyword_heat(kw, hot_list)
            competition = estimate_competition(kw)
            avg_price = estimate_avg_price(kw)
            profit_margin = 1.0  # 数字产品成本=0，利润100%
            
            score = score_opportunity(kw, heat, competition, avg_price)
            
            if score >= 40:  # 只保留有价值的
                # 检查是否已存在
                existing = db.get_top_opportunities(limit=1, status=None)
                if not any(o['keyword'] == kw for o in existing):
                    opp_id = db.add_opportunity(
                        keyword=kw,
                        source='market_scan',
                        heat=heat,
                        competition=round(competition, 2),
                        avg_price=avg_price,
                        profit_margin=profit_margin,
                        score=score,
                        notes=f'热榜匹配热度{heat:.0f}, 预估均价{avg_price}元'
                    )
                    opportunities.append({
                        'id': opp_id,
                        'keyword': kw,
                        'score': score,
                        'heat': heat,
                        'competition': competition,
                        'avg_price': avg_price,
                    })
        
        # 4. 按分数排序
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        top10 = opportunities[:10]
        print(f"✅ 分析完成！新增 {len(opportunities)} 个机会，Top 10 如下：")
        for i, opp in enumerate(top10, 1):
            print(f"  {i}. {opp['keyword']} | 分数: {opp['score']} | 热度: {opp['heat']:.0f} | 均价: {opp['avg_price']}元")
        
        db.log_run('market', 'success', f'市场分析完成，发现{len(opportunities)}个机会', 
                   f'Top5: {[o["keyword"] for o in top10[:5]]}')
        
        return top10
        
    except Exception as e:
        db.log_run('market', 'error', f'市场分析失败: {e}')
        print(f"❌ 市场分析失败: {e}")
        return []


def get_daily_market_summary():
    """生成市场概览"""
    opps = db.get_top_opportunities(limit=20)
    
    summary = {
        'total_opportunities': len(opps),
        'top_keywords': [o['keyword'] for o in opps[:5]],
        'avg_score': round(sum(o['score'] for o in opps) / max(len(opps), 1), 1),
        'hot_areas': [],
    }
    
    # 识别热门领域
    areas = {'AI': 0, '副业': 0, '办公': 0, '自媒体': 0, '教程': 0}
    for o in opps:
        for area in areas:
            if area in o['keyword']:
                areas[area] += 1
    summary['hot_areas'] = [k for k, v in areas.items() if v > 0]
    
    return summary


if __name__ == '__main__':
    # 测试市场分析
    db.init_db()
    opps = analyze_market()
    print("\n🎯 测试 Top 5:")
    for o in opps[:5]:
        print(f"  {o['keyword']} - 分数{o['score']}")
