"""
主程序 - 定时调度器
长期后台运行，自动循环执行：
1. 市场分析（每小时）
2. 产品生成（每2小时）
3. 文案生成（紧跟产品生成）
4. 每日报告（每天早上8点）
5. 每周报告（每周一早8点）
6. 飞书推送（有新发现时）
7. 日志 & 错误恢复
"""

import sys
import os
import signal
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# 确保模块路径正确
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from modules import db, market, product, copywriter, feishu, finance, operations
from config import (
    ANALYZE_INTERVAL, GENERATE_INTERVAL, REPORT_INTERVAL,
    TICK_INTERVAL, WEEKLY_REPORT_DAY, LOG_DIR,
)

# ======= 全局状态 =======
class BotState:
    running = True
    last_analyze = None
    last_generate = None
    last_daily_report = None
    last_weekly_report = None
    start_time = None
    error_count = 0
    max_errors = 10  # 连续错误超过这个数就暂停


state = BotState()


def log(s):
    """控制台输出 + 写日志"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] {s}")
    
    # 写文件日志
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, 'bot.log'), 'a', encoding='utf-8') as f:
        f.write(f"[{now}] {s}\n")


def signal_handler(sig, frame):
    """优雅退出"""
    log("🛑 收到退出信号，正在停止...")
    state.running = False
    feishu.quick_push("🛑 AI副业系统已停止")


def run_with_retry(name, func, max_retries=3):
    """带重试的执行"""
    for attempt in range(max_retries):
        try:
            log(f"▶️ 执行 {name}（尝试 {attempt+1}/{max_retries}）")
            result = func()
            log(f"✅ {name} 完成")
            state.error_count = 0
            return result
        except Exception as e:
            log(f"❌ {name} 失败: {e}")
            db.log_run(name, 'error', str(e), traceback.format_exc())
            state.error_count += 1
            
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 5
                log(f"⏳ {wait}秒后重试...")
                time.sleep(wait)
            else:
                log(f"❌ {name} 最终失败，跳过")
                feishu.notify_error(name, str(e)[:200])
                return None


def tick():
    """一个 tick：检查所有定时任务"""
    now = datetime.now()
    
    # 1. 市场分析（每 ANALYZE_INTERVAL 秒）
    if (state.last_analyze is None or 
        (now - state.last_analyze).total_seconds() >= ANALYZE_INTERVAL):
        
        results = run_with_retry('market_analysis', market.analyze_market)
        
        if results:
            # 推送前3个好机会
            for opp in results[:3]:
                if opp['score'] >= 60:
                    feishu.notify_new_opportunity(opp)
        
        state.last_analyze = now
    
    # 2. 产品生成 + 文案（每 GENERATE_INTERVAL 秒）
    if (state.last_generate is None or 
        (now - state.last_generate).total_seconds() >= GENERATE_INTERVAL):
        
        product_ids = run_with_retry('product_generation', 
                                     lambda: product.generate_top_products(5))
        
        if product_ids:
            for pid in product_ids:
                p = db.get_product(pid)
                if p:
                    copies = copywriter.generate_all_platform_copies(p)
                    feishu.notify_new_product(p, len(copies))
        
        state.last_generate = now
    
    # 3. 每天早上生成今日运营任务
    today = now.date()
    if state.last_daily_report is None or state.last_daily_report != today:
        # 先等市场分析和产品生成都跑完
        run_with_retry('daily_tasks', operations.generate_daily_operation_tasks)
        
        # 再发送每日报告（包含财务+任务）
        report = finance.generate_daily_report()
        summary = finance.get_full_financial_report()
        tasks = operations.get_today_tasks()
        summary['tasks'] = [dict(t) for t in tasks[:5]]
        
        feishu.notify_daily_report(summary)
        
        state.last_daily_report = today
        log(f"📅 今日运营任务生成完毕：{len(tasks)} 条")
    
    # 4. 每周报告
    if now.weekday() == WEEKLY_REPORT_DAY:
        monday = today - timedelta(days=now.weekday())
        if state.last_weekly_report != monday:
            weekly = finance.generate_weekly_summary()
            feishu.notify_weekly_summary(weekly)
            state.last_weekly_report = monday
            log("📊 周报已发送")
    
    # 5. 健康检查（每10分钟）
    # 不用太频繁，防止过度请求
    if state.error_count >= state.max_errors:
        log("⚠️ 连续错误过多，暂停运行")
        feishu.quick_push("⚠️ 系统连续出错太多，已暂停。请检查日志。")
        state.running = False


def main():
    """主循环"""
    # 1. 初始化
    db.init_db()
    state.start_time = datetime.now()
    
    log("=" * 50)
    log("🚀 AI副业自动化系统启动")
    log(f"📍 配置：市场分析每{ANALYZE_INTERVAL//3600}h，产品生成每{GENERATE_INTERVAL//3600}h")
    log(f"🔔 飞书：{'已启用' if feishu.FEISHU_ENABLED else '未启用（设置 FEISHU_WEBHOOK 开启）'}")
    log("=" * 50)
    
    # 2. 注册信号
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 3. 启动通知
    feishu.notify_system_status(True, 0)
    
    # 4. 先立即执行一次（不等定时器）
    log("🔥 立即执行首轮扫描...")
    run_with_retry('market_analysis', market.analyze_market)
    run_with_retry('product_generation', lambda: product.generate_top_products(5))
    run_with_retry('copywriting', copywriter.generate_copies_for_all_products)
    run_with_retry('daily_tasks', operations.generate_daily_operation_tasks)
    
    # 5. 主循环
    log("⏳ 进入主循环，每 60 秒检查一次...")
    
    while state.running:
        try:
            tick()
            
            # 计算已运行时长
            uptime = (datetime.now() - state.start_time).total_seconds() / 3600
            
            # 每小时发一次心跳
            if int(uptime) > 0 and int(uptime) != int((uptime - TICK_INTERVAL/3600)):
                feishu.notify_system_status(True, uptime)
            
            time.sleep(TICK_INTERVAL)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"⚠️ 主循环异常: {e}")
            db.log_run('main', 'error', str(e), traceback.format_exc())
            time.sleep(30)
    
    # 6. 退出
    log("🏁 系统停止")
    uptime = (datetime.now() - state.start_time).total_seconds() / 3600
    feishu.quick_push(f"🏁 AI副业系统已停止 | 本次运行 {uptime:.1f} 小时")


if __name__ == '__main__':
    main()
