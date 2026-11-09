"""
收益统计模块
真实记录成本、收入、利润，生成日报/周报/月报
不把预估利润当实际利润
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from collections import defaultdict
from modules import db


def record_income(product_id, amount, platform, description='', channel=''):
    """
    记录实际收入（真实到账金额）
    只有用户实际收到了钱才调用这个
    """
    tx_id = db.add_transaction(product_id, 'income', amount, platform, description, channel)
    
    # 同步标记产品状态
    db.update_product_status(product_id, 'sold')
    
    # 记录学习数据（哪个平台卖得好）
    if amount > 0:
        db.add_learning('platform_success', f'{platform} 产品#{product_id} 收入{amount}元', 0.7)
    
    return tx_id


def record_cost(product_id, amount, platform='', description='', channel=''):
    """
    记录实际支出（API费用、服务器成本等）
    数字产品的内容创作不算成本（自己做的）
    """
    return db.add_transaction(product_id, 'cost', amount, platform, description, channel)


def get_full_financial_report():
    """完整财务报告"""
    summary = db.get_financial_summary()
    
    # 按日统计最近14天
    today = datetime.now()
    daily_stats = []
    for i in range(14):
        day = today - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0).isoformat()
        day_end = day.replace(hour=23, minute=59, second=59).isoformat()
        
        # 用 transactions 表查询
        # 这里简化处理，直接用总数据
        daily_stats.append({
            'date': day.strftime('%m-%d'),
            'income': 0,  # 需要更精细的查询
            'cost': 0,
            'net': 0,
        })
    
    # 按产品统计
    products = db.get_all_products()
    product_stats = []
    for p in products:
        product_stats.append({
            'id': p['id'],
            'name': p['name'],
            'platforms': p['platforms'],
            'price': p['price'],
            'cost': p['cost'],
            'quality_score': p['quality_score'],
            'status': p['status'],
        })
    
    return {
        'summary': summary,
        'product_count': len(products),
        'listed_count': sum(1 for p in products if p['status'] == 'listed'),
        'sold_count': summary['sold_products'],
        'product_stats': product_stats,
    }


def generate_daily_report():
    """生成每日运营报告（文字版）"""
    report = get_full_financial_report()
    summary = report['summary']
    
    lines = [
        "=" * 40,
        f"📈 AI副业每日报告",
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 40,
        "",
        "💰 财务汇总",
        "-" * 20,
        f"总收入（真实到账）：¥{summary['total_income']:.2f}",
        f"总支出：¥{summary['total_cost']:.2f}",
        f"净利润：¥{summary['net_profit']:.2f}",
        f"本周收入：¥{summary['week_income']:.2f}",
        f"本月收入：¥{summary['month_income']:.2f}",
        f"ROI：{summary['roi']:.1f}%",
        "",
        "📦 产品状态",
        "-" * 20,
        f"已生成产品：{report['product_count']} 个",
        f"已上架：{report['listed_count']} 个",
        f"成功售出：{summary['sold_products']} 个",
        "",
    ]
    
    # 列出所有产品
    if report['product_stats']:
        lines.append("📋 产品清单：")
        for p in report['product_stats'][:10]:
            status_icon = {'ready': '⏳', 'listed': '🟢', 'sold': '💰', 'failed': '❌'}.get(p['status'], '❓')
            lines.append(f"  {status_icon} {p['name'][:30]} | ¥{p['price']} | {p['platforms'][:20]}")
        if len(report['product_stats']) > 10:
            lines.append(f"  ... 还有 {len(report['product_stats']) - 10} 个产品")
    
    lines.extend([
        "",
        "🎯 待办任务",
        "-" * 20,
    ])
    
    # 添加未完成任务
    tasks = db.get_tasks(done=False)
    if tasks:
        for t in tasks[:10]:
            pri = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(t['priority'], '🟡')
            lines.append(f"  {pri} [{t.get('platform', '')}] {t['title'][:40]}")
    else:
        lines.append("  没有待办任务 ✨")
    
    lines.extend([
        "",
        "=" * 40,
        "💡 提示：",
        "• 数字产品零成本，利润率100%",
        "• 每天执行运营任务（擦亮/发笔记/回复消息）",
        "• 真实收入请手动在 Web 面板录入",
        "=" * 40,
    ])
    
    return "\n".join(lines)


def generate_weekly_summary():
    """生成周报数据"""
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    # 这一周新增的机会数
    all_opps = db.get_top_opportunities(limit=100)
    new_opps_count = len(all_opps)  # 简化处理
    
    # 本周新产品
    products = db.get_all_products()
    new_products_count = len(products)
    
    summary = db.get_financial_summary()
    
    # Top 机会
    top_opps = db.get_top_opportunities(limit=5)
    
    return {
        'new_opps': new_opps_count,
        'new_products': new_products_count,
        'week_income': summary['week_income'],
        'total_income': summary['total_income'],
        'net_profit': summary['net_profit'],
        'top_opps': top_opps,
    }


def record_platform_performance(platform, product_count, views=0, inquiries=0):
    """记录平台运营数据（用于学习优化）"""
    db.add_learning('platform_metrics', 
                    f'{platform} | 产品{product_count} | 曝光{views} | 咨询{inquiries}', 
                    0.6)


if __name__ == '__main__':
    db.init_db()
    print(generate_daily_report())
