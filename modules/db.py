"""
数据库模块 - SQLite
所有数据表定义和 CRUD 操作
"""

import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sidehustle.db')

def get_db():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

@contextmanager
def db_session():
    """数据库会话上下文管理器"""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    with db_session() as conn:
        c = conn.cursor()
        
        # 市场机会表
        c.execute('''CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            source TEXT,
            heat REAL DEFAULT 0,
            competition REAL DEFAULT 0,
            avg_price REAL DEFAULT 0,
            profit_margin REAL DEFAULT 0,
            score REAL DEFAULT 0,
            status TEXT DEFAULT 'new',  -- new | selected | generated | listed | sold | failed
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 产品表
        c.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            content TEXT,          -- 生成的提示词/模板内容
            price REAL DEFAULT 0,
            cost REAL DEFAULT 0,
            suggested_price REAL DEFAULT 0,
            platforms TEXT,        -- 闲鱼,小红书,抖音,得物
            cover_emoji TEXT DEFAULT '✨',
            tags TEXT,
            quality_score REAL DEFAULT 0,
            market_score REAL DEFAULT 0,
            status TEXT DEFAULT 'ready',  -- ready | listed | sold | failed
            opportunity_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        )''')
        
        # 文案表
        c.execute('''CREATE TABLE IF NOT EXISTS copies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            platform TEXT,
            title TEXT,
            body TEXT,
            tags TEXT,
            hook TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )''')
        
        # 交易记录表
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            type TEXT,              -- income | cost
            amount REAL,
            platform TEXT,
            description TEXT,
            channel TEXT,           -- 闲鱼/小红书等
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )''')
        
        # 运营任务表
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            title TEXT,
            desc TEXT,
            platform TEXT,
            priority TEXT DEFAULT 'medium',
            done INTEGER DEFAULT 0,
            due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 系统运行日志
        c.execute('''CREATE TABLE IF NOT EXISTS run_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT,
            status TEXT,            -- success | error | warning
            message TEXT,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 飞书推送日志
        c.execute('''CREATE TABLE IF NOT EXISTS feishu_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            content TEXT,
            sent INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 自动优化学习记录
        c.execute('''CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,          -- price | keyword | platform | content
            insight TEXT,
            confidence REAL DEFAULT 0.5,
            sample_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 创建索引
        c.execute('CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_products_status ON products(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(created_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_run_logs_time ON run_logs(created_at)')
        
    print("✅ 数据库初始化完成")


# ======= 机会相关 =======

def add_opportunity(keyword, source='manual', heat=0, competition=0, avg_price=0, profit_margin=0, score=0, notes=''):
    """添加新机会"""
    with db_session() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO opportunities 
            (keyword, source, heat, competition, avg_price, profit_margin, score, notes)
            VALUES (?,?,?,?,?,?,?,?)''',
            (keyword, source, heat, competition, avg_price, profit_margin, score, notes))
        return c.lastrowid


def get_top_opportunities(limit=10, status=None):
    """获取高分机会"""
    with db_session() as conn:
        c = conn.cursor()
        if status:
            c.execute('''SELECT * FROM opportunities WHERE status=? ORDER BY score DESC LIMIT ?''', (status, limit))
        else:
            c.execute('''SELECT * FROM opportunities ORDER BY score DESC LIMIT ?''', (limit,))
        return [dict(row) for row in c.fetchall()]


def update_opportunity_status(opp_id, status):
    """更新机会状态"""
    with db_session() as conn:
        conn.execute('UPDATE opportunities SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (status, opp_id))


# ======= 产品相关 =======

def add_product(name, category, description, content='', price=9.9, cost=0, suggested_price=0, 
                platforms='闲鱼,小红书', cover_emoji='✨', tags='', quality_score=0, market_score=0, opportunity_id=None):
    """添加新产品"""
    with db_session() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO products 
            (name, category, description, content, price, cost, suggested_price, platforms, cover_emoji, tags, quality_score, market_score, opportunity_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (name, category, description, content, price, cost, suggested_price or price, platforms, cover_emoji, tags, quality_score, market_score, opportunity_id))
        pid = c.lastrowid
        
        # 标记机会为已生成
        if opportunity_id:
            conn.execute('UPDATE opportunities SET status="generated" WHERE id=?', (opportunity_id,))
        
        return pid


def get_all_products(status=None):
    """获取所有产品"""
    with db_session() as conn:
        c = conn.cursor()
        if status:
            c.execute('SELECT * FROM products WHERE status=? ORDER BY id DESC', (status,))
        else:
            c.execute('SELECT * FROM products ORDER BY id DESC')
        return [dict(row) for row in c.fetchall()]


def get_product(pid):
    """获取单个产品"""
    with db_session() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM products WHERE id=?', (pid,))
        row = c.fetchone()
        return dict(row) if row else None


def update_product_status(pid, status):
    with db_session() as conn:
        conn.execute('UPDATE products SET status=? WHERE id=?', (status, pid))


# ======= 文案相关 =======

def add_copy(product_id, platform, title, body, tags='', hook=''):
    with db_session() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO copies (product_id, platform, title, body, tags, hook)
            VALUES (?,?,?,?,?,?)''', (product_id, platform, title, body, tags, hook))
        return c.lastrowid


def get_copies_by_product(pid):
    with db_session() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM copies WHERE product_id=? ORDER BY platform', (pid,))
        return [dict(row) for row in c.fetchall()]


# ======= 交易相关 =======

def add_transaction(product_id, tx_type, amount, platform='', description='', channel=''):
    with db_session() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO transactions (product_id, type, amount, platform, description, channel)
            VALUES (?,?,?,?,?,?)''', (product_id, tx_type, amount, platform, description, channel))
        return c.lastrowid


def get_transactions(days=30):
    with db_session() as conn:
        c = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute('''SELECT * FROM transactions WHERE created_at >= ? ORDER BY created_at DESC''', (since,))
        return [dict(row) for row in c.fetchall()]


def get_financial_summary():
    """获取财务汇总"""
    with db_session() as conn:
        c = conn.cursor()
        
        c.execute('SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type="income"')
        total_income = c.fetchone()[0]
        
        c.execute('SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type="cost"')
        total_cost = c.fetchone()[0]
        
        c.execute('SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type="income" AND created_at >= date("now","-7 days")')
        week_income = c.fetchone()[0]
        
        c.execute('SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type="income" AND created_at >= date("now","-30 days")')
        month_income = c.fetchone()[0]
        
        c.execute('SELECT COUNT(DISTINCT product_id) FROM transactions WHERE type="income"')
        sold_products = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM products WHERE status="sold"')
        successful = c.fetchone()[0]
        
        net_profit = total_income - total_cost
        roi = (net_profit / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_income': round(total_income, 2),
            'total_cost': round(total_cost, 2),
            'net_profit': round(net_profit, 2),
            'week_income': round(week_income, 2),
            'month_income': round(month_income, 2),
            'sold_products': sold_products,
            'successful': successful,
            'roi': round(roi, 1),
        }


# ======= 任务相关 =======

def add_task(task_type, title, desc='', platform='', priority='medium', due_date=None):
    with db_session() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO tasks (type, title, desc, platform, priority, due_date)
            VALUES (?,?,?,?,?,?)''', (task_type, title, desc, platform, priority, due_date))
        return c.lastrowid


def get_tasks(done=None):
    with db_session() as conn:
        c = conn.cursor()
        if done is not None:
            c.execute('SELECT * FROM tasks WHERE done=? ORDER BY priority DESC, created_at DESC', (1 if done else 0,))
        else:
            c.execute('SELECT * FROM tasks ORDER BY done, priority DESC, created_at DESC')
        return [dict(row) for row in c.fetchall()]


def complete_task(tid):
    with db_session() as conn:
        conn.execute('UPDATE tasks SET done=1 WHERE id=?', (tid,))


# ======= 日志相关 =======

def log_run(module, status, message, details=''):
    with db_session() as conn:
        conn.execute('''INSERT INTO run_logs (module, status, message, details)
            VALUES (?,?,?,?)''', (module, status, message, details))


def get_run_logs(limit=50):
    with db_session() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM run_logs ORDER BY created_at DESC LIMIT ?', (limit,))
        return [dict(row) for row in c.fetchall()]


# ======= 学习优化 =======

def add_learning(category, insight, confidence=0.5):
    with db_session() as conn:
        c = conn.cursor()
        # 检查是否已存在类似洞察
        c.execute('SELECT * FROM learnings WHERE category=? AND insight=?', (category, insight))
        if c.fetchone():
            c.execute('UPDATE learnings SET sample_count=sample_count+1, confidence=MIN(confidence+0.05,1.0) WHERE category=? AND insight=?',
                (category, insight))
        else:
            c.execute('''INSERT INTO learnings (category, insight, confidence, sample_count)
                VALUES (?,?,?,1)''', (category, insight, confidence))


def get_learnings(category=None):
    with db_session() as conn:
        c = conn.cursor()
        if category:
            c.execute('SELECT * FROM learnings WHERE category=? ORDER BY confidence DESC', (category,))
        else:
            c.execute('SELECT * FROM learnings ORDER BY confidence DESC')
        return [dict(row) for row in c.fetchall()]
