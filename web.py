"""
Web 管理面板 v2 - 增加独立文案生成工具页
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from flask import Flask, render_template, request, redirect, url_for, jsonify
from modules import db, market, product, copywriter, finance, operations
from config import SERVER_HOST, SERVER_PORT

app = Flask(__name__, 
            template_folder=str(BASE_DIR / 'static' / 'templates'))


def get_nav_items(active=''):
    """底部导航"""
    items = [
        ('/', '仪表盘', '🏠'),
        ('/products', '产品', '📦'),
        ('/copywriter', '文案', '✍️'),
        ('/opportunities', '市场', '🎯'),
        ('/finance', '财务', '💰'),
        ('/report', '报告', '📈'),
    ]
    return [(url, name, icon, url == active) for url, name, icon in items]


@app.context_processor
def inject_nav():
    return {'nav_items': get_nav_items()}


@app.route('/')
def index():
    """首页 - 系统状态仪表盘"""
    financial = db.get_financial_summary()
    products = db.get_all_products()
    opportunities = db.get_top_opportunities(limit=5)
    tasks = db.get_tasks(done=False)
    learnings = db.get_learnings()
    
    stats = {
        'total_products': len(products),
        'ready_products': sum(1 for p in products if p['status'] == 'ready'),
        'listed_products': sum(1 for p in products if p['status'] == 'listed'),
        'sold_products': financial['sold_products'],
        'top_opportunities': opportunities,
        'pending_tasks': len(tasks),
        'learnings_count': len(learnings),
    }
    
    return render_template('index.html', 
                         financial=financial,
                         stats=stats,
                         tasks=tasks[:5])


@app.route('/products')
def products_page():
    """产品列表"""
    status = request.args.get('status')
    products = db.get_all_products(status)
    return render_template('products.html', products=products)


@app.route('/product/<int:pid>')
def product_detail(pid):
    """产品详情 - 查看所有平台文案"""
    p = db.get_product(pid)
    if not p:
        return "产品不存在", 404
    
    copies = db.get_copies_by_product(pid)
    return render_template('product_detail.html', product=p, copies=copies)


@app.route('/product/<int:pid>/generate-copies')
def regen_copies(pid):
    """重新生成文案"""
    p = db.get_product(pid)
    if p:
        copywriter.generate_all_platform_copies(p)
    return redirect(url_for('product_detail', pid=pid))


# ======= 新增：独立文案生成工具页 =======

@app.route('/copywriter')
def copywriter_page():
    """文案生成工具 - 选产品 → 一键生成4平台文案"""
    products = db.get_all_products()
    copies = []
    product_copies_map = {}
    
    # 如果有产品，默认展示第一个的文案
    if products:
        pid = request.args.get('pid', products[0]['id'], type=int)
        current_product = db.get_product(pid)
        if current_product:
            copies = db.get_copies_by_product(pid)
            # 如果还没有文案，自动生成
            if not copies:
                copies = copywriter.generate_all_platform_copies(current_product)
                # 转为 dict 列表（从函数返回值）
                if copies and isinstance(copies[0], dict):
                    pass
                else:
                    copies = db.get_copies_by_product(pid)
        
        # 预处理所有产品的 copies（给底部概览用）
        for p in products:
            product_copies_map[p['id']] = db.get_copies_by_product(p['id'])
    else:
        current_product = None
    
    return render_template('copywriter.html', 
                         products=products, 
                         current_product=current_product,
                         copies=copies,
                         product_copies_map=product_copies_map)


@app.route('/copywriter/generate', methods=['POST'])
def copywriter_generate():
    """手动触发文案生成"""
    pid = int(request.form.get('product_id', 0))
    if pid:
        # 先清掉旧文案
        with db.db_session() as conn:
            conn.execute('DELETE FROM copies WHERE product_id=?', (pid,))
        
        p = db.get_product(pid)
        if p:
            copywriter.generate_all_platform_copies(p)
    
    return redirect(url_for('copywriter_page', pid=pid))


@app.route('/opportunities')
def opportunities_page():
    """市场机会列表"""
    opps = db.get_top_opportunities(limit=30)
    return render_template('opportunities.html', opportunities=opps)


@app.route('/tasks')
def tasks_page():
    """待办任务"""
    tasks = db.get_tasks()
    return render_template('tasks.html', tasks=tasks)


@app.route('/task/<int:tid>/done')
def mark_task_done(tid):
    """标记任务完成"""
    db.complete_task(tid)
    return redirect(url_for('tasks_page'))


@app.route('/finance')
def finance_page():
    """财务面板"""
    report = finance.get_full_financial_report()
    transactions = db.get_transactions(days=90)
    return render_template('finance.html', 
                         report=report,
                         transactions=transactions)


@app.route('/finance/record', methods=['POST'])
def record_finance():
    """录入真实收入/支出"""
    tx_type = request.form.get('type', 'income')
    amount = float(request.form.get('amount', 0))
    platform = request.form.get('platform', '')
    description = request.form.get('description', '')
    product_id = request.form.get('product_id')
    
    if amount <= 0:
        return redirect(url_for('finance_page'))
    
    db.add_transaction(
        product_id=int(product_id) if product_id else None,
        tx_type=tx_type,
        amount=amount,
        platform=platform,
        description=description,
    )
    
    return redirect(url_for('finance_page'))


@app.route('/report')
def daily_report():
    """每日报告"""
    report_text = finance.generate_daily_report()
    return render_template('report.html', report=report_text)


@app.route('/learnings')
def learnings_page():
    """学习记录"""
    learnings = db.get_learnings()
    return render_template('learnings.html', learnings=learnings)


# ======= 手动触发 =======

@app.route('/action/<action_name>')
def manual_action(action_name):
    """手动触发系统动作"""
    if action_name == 'analyze':
        results = market.analyze_market()
        return jsonify({'status': 'ok', 'message': f'市场分析完成，发现 {len(results)} 个机会'})
    
    elif action_name == 'generate':
        pids = product.generate_top_products(5)
        return jsonify({'status': 'ok', 'message': f'生成 {len(pids)} 个产品'})
    
    elif action_name == 'copies':
        count = copywriter.generate_copies_for_all_products()
        return jsonify({'status': 'ok', 'message': f'为 {count} 个产品生成了文案'})
    
    elif action_name == 'tasks':
        count = operations.generate_daily_operation_tasks()
        return jsonify({'status': 'ok', 'message': f'生成 {count} 条今日任务'})
    
    else:
        return jsonify({'status': 'error', 'message': f'未知动作: {action_name}'})


@app.route('/api/status')
def api_status():
    """系统状态 API"""
    financial = db.get_financial_summary()
    products = db.get_all_products()
    opps = db.get_top_opportunities(limit=1)
    logs = db.get_run_logs(limit=5)
    
    return jsonify({
        'status': 'ok',
        'financial': financial,
        'product_count': len(products),
        'top_opportunity': opps[0] if opps else None,
        'recent_logs': logs,
    })


if __name__ == '__main__':
    db.init_db()
    print(f"🌐 Web面板启动：http://{SERVER_HOST}:{SERVER_PORT}")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
