"""
飞书机器人推送模块
通过 Webhook 发送消息到飞书群
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import requests
from datetime import datetime
from modules import db
from config import FEISHU_WEBHOOK, FEISHU_ENABLED


def send_text(text):
    """发送纯文本消息"""
    if not FEISHU_ENABLED:
        print(f"📨 [飞书未启用] {text[:50]}...")
        db.log_run('feishu', 'info', '飞书未配置，跳过发送')
        return False
    
    try:
        resp = requests.post(
            FEISHU_WEBHOOK,
            json={
                'msg_type': 'text',
                'content': {'text': text}
            },
            timeout=10,
        )
        if resp.status_code == 200:
            result = resp.json()
            if result.get('StatusCode') == 0:
                db.log_run('feishu', 'success', '文本消息发送成功')
                return True
            else:
                db.log_run('feishu', 'warning', f'飞书返回错误: {result}')
        db.log_run('feishu', 'error', f'飞书请求失败: {resp.status_code}')
        return False
    except Exception as e:
        db.log_run('feishu', 'error', f'飞书发送异常: {e}')
        return False


def send_rich_text(title, content_lines):
    """发送富文本消息（飞书 post 格式）"""
    if not FEISHU_ENABLED:
        print(f"📨 [飞书未启用] {title}")
        for line in content_lines:
            print(f"  {line}")
        return False
    
    # 组装富文本
    content = []
    for line in content_lines:
        if line.startswith('## '):
            content.append([{'tag': 'text', 'text': line[3:], 'style': {'bold': True}}])
        elif line.startswith('---'):
            content.append([{'tag': 'text', 'text': '━━━━━━━━━━━━━━━━'}])
        elif line.startswith('**') and line.endswith('**'):
            content.append([{'tag': 'text', 'text': line[2:-2], 'style': {'bold': True}}])
        else:
            content.append([{'tag': 'text', 'text': line}])
    
    try:
        resp = requests.post(
            FEISHU_WEBHOOK,
            json={
                'msg_type': 'post',
                'content': {
                    'post': {
                        'zh_cn': {
                            'title': title,
                            'content': content,
                        }
                    }
                }
            },
            timeout=10,
        )
        if resp.status_code == 200:
            result = resp.json()
            return result.get('StatusCode') == 0
    except Exception as e:
        db.log_run('feishu', 'error', f'富文本发送失败: {e}')
    return False


# ======= 各类消息模板 =======

def notify_new_opportunity(opportunity):
    """新赚钱机会通知"""
    title = "🎯 发现新赚钱机会"
    lines = [
        f"## {opportunity['keyword']}",
        "---",
        f"📊 评分：{opportunity['score']} 分",
        f"🔥 热度：{opportunity['heat']:.0f}",
        f"💼 竞争程度：{opportunity['competition']:.0%}",
        f"💰 预估均价：{opportunity['avg_price']} 元",
        f"📈 利润率：100%（数字产品零成本）",
        "---",
        "建议：可以立即生成产品上架！",
    ]
    return send_rich_text(title, lines)


def notify_new_product(product, copies_count):
    """新产品生成通知"""
    title = "🎨 新产品已生成"
    lines = [
        f"## {product['name']}",
        "---",
        f"📦 定价：{product['price']} 元",
        f"🎯 目标平台：{product['platforms']}",
        f"✨ 生成了 {copies_count} 套平台文案",
        f"⭐ 质量分：{product['quality_score']}",
        "---",
        "文案已就绪，去上架吧！",
    ]
    return send_rich_text(title, lines)


def notify_daily_report(summary):
    """每日报告"""
    today = datetime.now().strftime('%Y-%m-%d')
    title = f"📈 AI副业每日报告 | {today}"
    lines = [
        "## 💰 财务状况",
        f"总收入：{summary['total_income']} 元",
        f"总支出：{summary['total_cost']} 元",
        f"净利润：{summary['net_profit']} 元",
        f"ROI：{summary['roi']}%",
        "---",
        "## 📦 产品状况",
        f"已生成产品：{summary.get('product_count', 0)} 个",
        f"已上架：{summary.get('listed_count', 0)} 个",
        f"成功售出：{summary.get('sold_count', 0)} 个",
        "---",
        "## 🎯 今日任务",
    ]
    
    # 添加任务
    tasks = summary.get('tasks', [])
    for i, task in enumerate(tasks[:5], 1):
        lines.append(f"{i}. [{task.get('platform', '')}] {task['title']}")
    
    return send_rich_text(title, lines)


def notify_system_status(is_running, uptime_hours=0):
    """系统状态通知"""
    if is_running:
        return send_text(f"✅ AI副业系统运行中 | 已运行 {uptime_hours:.1f} 小时")
    else:
        return send_text("⚠️ AI副业系统可能已断开！请检查！")


def notify_error(error_module, error_msg):
    """错误通知"""
    title = "⚠️ 系统异常"
    lines = [
        f"模块：{error_module}",
        f"错误：{error_msg[:200]}",
        "系统将自动尝试恢复...",
    ]
    return send_rich_text(title, lines)


def notify_transaction(tx_type, amount, platform, description=''):
    """交易通知"""
    emoji = "💰" if tx_type == 'income' else "💸"
    action = "收入" if tx_type == 'income' else "支出"
    text = f"{emoji} {action}通知\n平台：{platform}\n金额：{amount} 元\n{description}"
    return send_text(text)


def notify_weekly_summary(summary):
    """周报"""
    title = "📅 AI副业周报"
    lines = [
        "## 本周数据",
        f"新增机会：{summary.get('new_opps', 0)} 个",
        f"新增产品：{summary.get('new_products', 0)} 个",
        f"本周收入：{summary.get('week_income', 0)} 元",
        "---",
        "## Top 5 机会",
    ]
    for i, opp in enumerate(summary.get('top_opps', [])[:5], 1):
        lines.append(f"{i}. {opp['keyword']} (分数{opp['score']})")
    
    return send_rich_text(title, lines)


# ======= 快捷推送 =======

def quick_push(text):
    """快速推送一条文本"""
    return send_text(text)


if __name__ == '__main__':
    db.init_db()
    print("🧪 飞书模块测试")
    if FEISHU_ENABLED:
        print(f"✅ Webhook 已配置")
        send_text("🤖 AI副业系统测试消息 - 连接成功！")
    else:
        print("⚠️ 未配置 FEISHU_WEBHOOK，消息不会实际发送")
        print("💡 设置环境变量：export FEISHU_WEBHOOK='https://open.feishu.cn/open-apis/bot/v2/hook/xxx'")
