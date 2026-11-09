"""
自动运营任务生成模块
每日自动生成待办任务（人工执行）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import random
from datetime import datetime, timedelta
from modules import db


# ======= 各平台每日运营 SOP =======

PLATFORM_DAILY_TASKS = {
    '闲鱼': {
        'high': [
            '擦亮所有在售产品（每天只能擦亮1次，务必做）',
            '回复所有咨询消息（15分钟内回复率影响排名）',
        ],
        'medium': [
            '逛同类产品评论区，真诚回复3条',
            '去首页"擦亮鱼市"签到领流量',
            '关注10个同行，看他们卖什么',
            '每天发1条店铺动态（新品/促销）',
        ],
        'low': [
            '优化1个产品的标题/主图',
            '检查有没有同行恶意差评',
            '数据复盘：记录今日曝光/点击',
        ],
    },
    '小红书': {
        'high': [
            '发1-2条笔记（用系统生成的文案，配好图）',
            '回复所有评论和私信（小红书对互动率敏感）',
        ],
        'medium': [
            '逛同领域内容，认真点赞+写评论',
            '关注5-10个同行，学习选题',
            '用"创作中心"看数据分析',
        ],
        'low': [
            '主页保持统一风格（封面风格/色调统一）',
            '写一篇复盘笔记总结经验',
            '申请蒲公英开通商业接单',
        ],
    },
    '抖音': {
        'high': [
            '发1条短视频/图文（用系统生成的脚本）',
            '回复所有评论（尤其是带钩子的评论要回）',
        ],
        'medium': [
            '每天15分钟刷同领域内容（看完点赞）',
            '蹭当天的热门话题标签',
            '主页简介要清晰：分享AI干货',
        ],
        'low': [
            '试试直播15分钟（不开挂播也行）',
            '用创作服务中心看数据',
            '剪映里收藏几个模板备用',
        ],
    },
    '得物': {
        'high': [
            '上新1个产品或重新编辑上架',
            '回复所有咨询消息',
        ],
        'medium': [
            '擦亮所有在售产品',
            '关注5个同行看定价',
            '逛潮流话题区互动',
        ],
        'low': [
            '参与平台活动/话题',
            '数据复盘',
        ],
    },
}


def generate_daily_operation_tasks():
    """
    自动生成今日运营待办
    不是自动执行（平台API没开放），而是告诉用户今天该做什么
    """
    # 先清空昨天的未完成任务（避免堆积）
    with db.db_session() as conn:
        conn.execute("DELETE FROM tasks WHERE done=0 AND created_at < date('now')")
    
    today = datetime.now()
    tasks_added = 0
    
    for platform, task_groups in PLATFORM_DAILY_TASKS.items():
        # 每个平台 2个高优 + 1个中优 + 可选低优
        priority_map = {'high': 'high', 'medium': 'medium', 'low': 'low'}
        
        for priority, tasks in task_groups.items():
            if priority == 'high':
                count = len(tasks)  # 高优全加
            elif priority == 'medium':
                count = min(2, len(tasks))  # 中优选2个
            else:
                count = random.randint(0, 1)  # 低优随缘
            
            if count > 0:
                selected = random.sample(tasks, min(count, len(tasks)))
                for task_text in selected:
                    tid = db.add_task(
                        task_type='operation',
                        title=f'[{platform}] {task_text}',
                        desc=f'{platform}平台每日运营任务',
                        platform=platform,
                        priority=priority_map[priority],
                        due_date=(today + timedelta(days=1)).date().isoformat(),
                    )
                    tasks_added += 1
    
    # 添加生成类任务（如果有未生成的）
    opportunities = db.get_top_opportunities(limit=5, status='new')
    if opportunities:
        db.add_task('generate', '生成新产品', 
                   f'有{len(opportunities)}个新机会待生成产品',
                   priority='high')
        tasks_added += 1
    
    # 添加上架类任务
    products = db.get_all_products(status='ready')
    if products:
        db.add_task('list', '上架产品',
                   f'有{len(products)}个产品已就绪，文案也生成好了',
                   priority='high')
        tasks_added += 1
    
    # 添加数据录入提醒（因为真实收入需要手动录）
    db.add_task('record', '录入今日真实收入',
                '今天有没有成交？在Web面板里录入真实到账金额',
                priority='medium')
    tasks_added += 1
    
    print(f"✅ 生成今日待办 {tasks_added} 条")
    db.log_run('tasks', 'success', f'生成{tasks_added}条运营任务')
    return tasks_added


def get_today_tasks():
    """获取今日待办"""
    return db.get_tasks(done=False)


def complete_task(tid):
    """标记完成"""
    db.complete_task(tid)
    
    # 记录学习数据（完成高优任务的平台表现更好）
    task = db.get_tasks()[0] if db.get_tasks() else None
    db.log_run('tasks', 'success', f'任务#{tid}已完成')


# ======= 自动机会识别相关 =======

def get_manual_suggestions():
    """
    给用户的建议（需要人工判断和执行的事情）
    """
    suggestions = []
    
    # 1. 高分机会提醒
    top_opps = db.get_top_opportunities(limit=5, status='new')
    if top_opps:
        suggestions.append({
            'type': 'opportunity',
            'priority': 'high',
            'title': f'有 {len(top_opps)} 个新机会待利用',
            'detail': 'Top 3: ' + ', '.join([o['keyword'] for o in top_opps[:3]]),
        })
    
    # 2. 待上架产品
    ready_products = db.get_all_products(status='ready')
    listed_products = db.get_all_products(status='listed')
    sold_products = db.get_all_products(status='sold')
    
    if ready_products:
        suggestions.append({
            'type': 'listing',
            'priority': 'high',
            'title': f'{len(ready_products)} 个产品已生成，文案也准备好啦！',
            'detail': '打开产品详情 → 复制文案 → 去平台上架',
        })
    
    # 3. 学习优化建议
    learnings = db.get_learnings()
    successful_platforms = [l for l in learnings if l['category'] == 'platform_success']
    if successful_platforms:
        platforms = set(l['insight'].split(' ')[0] for l in successful_platforms)
        suggestions.append({
            'type': 'learning',
            'priority': 'medium',
            'title': f'数据显示 {", ".join(platforms)} 卖得好',
            'detail': '可以重点在这些平台多上产品',
        })
    
    return suggestions


if __name__ == '__main__':
    db.init_db()
    print("🧪 测试自动任务生成")
    count = generate_daily_operation_tasks()
    tasks = get_today_tasks()
    for t in tasks[:5]:
        print(f"  [{t['priority']}] {t['title']}")
