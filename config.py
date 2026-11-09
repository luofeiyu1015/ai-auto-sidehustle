"""
全局配置 - 所有可配置项集中在这里
"""

import os

# ======= 飞书机器人 =======
# 在飞书开放平台创建自定义机器人后，把 Webhook 粘贴到这里
# https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
FEISHU_WEBHOOK = os.environ.get('FEISHU_WEBHOOK', '')

# 飞书发送开关（没有 webhook 也能运行，只是不推送）
FEISHU_ENABLED = bool(FEISHU_WEBHOOK)

# ======= 定时任务配置（秒） =======
TICK_INTERVAL = 60           # 主循环间隔
ANALYZE_INTERVAL = 3600      # 市场分析间隔（1小时）
GENERATE_INTERVAL = 7200     # 产品生成间隔（2小时）
REPORT_INTERVAL = 86400      # 每日报告（24小时）
WEEKLY_REPORT_DAY = 0        # 每周报告（0=周一）

# ======= 数据源配置（全部公开免费，无需付费API） =======
DATA_SOURCES = {
    'xhs_hot': 'https://www.xiaohongshu.com/explore',
    'douyin_hot': 'https://www.douyin.com/hot',
    'zhihu_hot': 'https://www.zhihu.com/hot',
    'weibo_hot': 'https://s.weibo.com/top/summary',
    'baidu_hot': 'https://top.baidu.com/board?tab=realtime',
    '36kr_hot': 'https://36kr.com/hot-list/catalog',
}

# ======= 关键词种子库 =======
SEED_KEYWORDS = [
    # AI 工具
    'AI绘画', 'AI写作', 'AI编程', 'AI赚钱', 'AI副业', 'AI教程',
    'Prompt', '提示词', 'Midjourney', 'Stable Diffusion', 'GPT',
    # 副业方向
    '副业', '搞钱', '赚钱', '兼职', '大学生副业', '居家副业',
    # 效率工具
    'Excel技巧', '飞书技巧', 'Notion模板', '效率工具', '自动办公',
    # 自媒体
    '小红书运营', '抖音运营', '短视频制作', '文案模板', '爆款文案',
]

# ======= 产品模板 =======
PRODUCT_CATEGORIES = [
    {'name': 'AI绘画Prompt包', 'base_price': 19.9, 'cost': 0, 'target': 'AI爱好者/设计师'},
    {'name': 'AI写作提示词', 'base_price': 12.9, 'cost': 0, 'target': '自媒体/文案从业者'},
    {'name': 'AI编程辅助', 'base_price': 29.9, 'cost': 0, 'target': '程序员/自学编程者'},
    {'name': '办公自动化模板', 'base_price': 15.9, 'cost': 0, 'target': '职场人士/大学生'},
    {'name': '飞书高级用法', 'base_price': 18.8, 'cost': 0, 'target': '飞书企业用户'},
    {'name': '自媒体SOP', 'base_price': 24.9, 'cost': 0, 'target': '自媒体新人'},
    {'name': '副业入门教程', 'base_price': 9.9, 'cost': 0, 'target': '副业刚需人群'},
    {'name': 'Excel高级函数', 'base_price': 13.9, 'cost': 0, 'target': '财务/数据岗'},
]

# ======= 目标平台 =======
TARGET_PLATFORMS = ['闲鱼', '小红书', '抖音', '得物']

# ======= 质量评分阈值 =======
MIN_QUALITY_SCORE = 0.6       # 最低质量分
MIN_PROFIT_MARGIN = 0.5       # 最低利润率（产品成本/价格）
MIN_HEAT_SCORE = 30           # 最低热度分数

# ======= 服务器配置 =======
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8080

# ======= 日志配置 =======
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
LOG_LEVEL = 'INFO'

# ======= User-Agent =======
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
