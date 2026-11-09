"""
多平台文案自动生成模块
为每个产品生成闲鱼、小红书、抖音、得物 4 套不同风格的文案
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import random
from datetime import datetime
from modules import db

# ======= 各平台文案模板 =======

PLATFORM_CONFIG = {
    '闲鱼': {
        'emojis': ['🔥', '💰', '📦', '✨', '🎁', '💯', '⚡', '📌', '🌟', '🚀'],
        'title_formats': [
            '{emoji} {name} 全新整理 | 秒发！{highlight}',
            '{emoji} 急出！{name} 手慢无 | {highlight}',
            '{emoji} {name} | 今日特价 {price}元',
            '{emoji} {highlight}！{name} 直接上手',
            '{emoji} {name} 买一送N | {highlight}',
        ],
        'hook_templates': [
            '别再花冤枉钱了！这个{name}我整理了半个月',
            '全网最全的{name}！没有之一',
            '{highlight}！一杯奶茶钱就搞定',
        ],
        'body_template': '''{emoji} {name}

{hook}

📦 产品内容：
{content_summary}

💰 价格：{price}元
📌 购买后秒发百度网盘链接

{selling_points}

{risk_reversal}

{urgency}

{call_to_action}''',
        'selling_points': [
            '• 精选整理，品质保证\n• 直接复制粘贴就能用\n• 永久免费更新\n• 附带详细使用说明',
            '• 原创内容，网上找不到第二份\n• 覆盖{highlight}的所有场景\n• 新手也能快速上手\n• 有问题随时找我',
        ],
        'risk_reversal': '💯 不满意全额退款，放心拍！',
        'urgency': '⏰ 限时特价！过几天涨价！',
        'call_to_action': '📦 拍下后自动发货，网盘链接秒收！',
        'hashtags': ['#{tag}' for tag in ['AI', '副业', '赚钱', '咸鱼', '二手', '效率', '教程']],
    },
    
    '小红书': {
        'emojis': ['❤️', '✨', '💫', '🌸', '🎀', '💖', '🌟', '💡', '🔥', '📚'],
        'title_formats': [
            '{emoji} 救命！{name}真的太香了！{highlight}',
            '{emoji} 姐妹们！{name}分享给你们！',
            '{emoji} {name} | 干货分享，建议收藏',
            '{emoji} 用了{name}之后，我{benefit}',
            '{emoji} 普通人也能用{name}？真实分享！',
        ],
        'benefits': ['效率翻倍了', '每天多赚500块', '再也不用熬夜加班', '同事都来问我', '副业月入过万'],
        'hook_templates': [
            '姐妹们！这个{name}我必须分享！',
            '救命啊！谁懂{name}有多好用！',
            '不允许还有人不知道{name}！',
        ],
        'body_template': '''{hook}

💫 为什么推荐这个{name}？
\\t• {highlight}，这个真的绝了！
\\t• 内容都是亲测好用的
\\t• 新手也能快速上手

📌 我的使用感受：
\\t用了之后{benefit}
\\t省了我超多时间！

💰 价格很划算，一杯奶茶钱不到
\\t想要的宝子可以私我

❤️ 觉得有用的话点赞收藏关注哦~
💬 有问题评论区问我！''',
        'hashtags': ['#{tag}' for tag in ['AI', '副业', '小红书运营', '干货', '教程', '效率', '宝藏分享']],
    },
    
    '抖音': {
        'emojis': ['🎬', '🔥', '💥', '⚡', '🎯', '📱', '👀', '💡', '🚀', '📈'],
        'title_formats': [
            '{emoji} 一个视频讲清楚{name}！看完直接上手',
            '{emoji} {name}实测！效果到底怎么样？',
            '{emoji} 用{name}3天，我{benefit}了？',
            '{emoji} {highlight}！{name}最全教程',
            '{emoji} 新手怎么用{name}？一条视频教会你',
        ],
        'benefits': ['效率翻倍', '省了3小时', '副业月入过万', '再也不加班', '领导都夸我'],
        'script_template': '''🎬 抖音短视频脚本 | {name}

【前3秒钩子】（特写画面/手持产品）
    配文：别再花冤枉钱买{name}了！
    字幕：{highlight}！{name}只要{price}元

【中间15秒内容展示】（快速切换画面）
    ① 展示{name}内容的一部分
    ② 对比：之前vs现在的效率/效果
    ③ 展示几个核心亮点

    口播：
    "这个{name}我整理了半个月，
    覆盖了{highlight}的各种场景，
    内容质量比90%同行的都好！"

【最后3秒CTA】（弹出购买引导）
    配文：想要的评论区扣[想要]！或直接私信！
    字幕：主页有更多AI干货！

🎵 背景音乐：热门轻快BGM（剪映推荐）

📌 话题标签：
#AI #副业 #干货分享 #搞钱 #教程''',
        'hashtags': ['#{tag}' for tag in ['AI', '副业', '搞钱', '抖音运营', '教程', '效率提升']],
    },
    
    '得物': {
        'emojis': ['💥', '⚡', '🔥', '🚀', '👟', '💪', '🎯', '✨', '📦', '💰'],
        'title_formats': [
            '{emoji} {name} | {highlight} 科技感拉满',
            '{emoji} {name} 潮酷必备 | 年轻人的选择',
            '{emoji} {highlight}！{name} 冲就完了',
            '{emoji} {name} | {highlight} 潮流新品首发',
        ],
        'hook_templates': [
            '兄弟们！这个{name}必须冲！',
            '{highlight}！{name}直接炸场！',
            '得物潮人都在用的{name}来了！',
        ],
        'body_template': '''{emoji} {name}

🔥 得物专属福利！
{hook}

📦 产品详情：
{content_summary}

💰 得物专属价：{price}元
📦 下单秒发网盘链接

🎯 产品亮点：
• 精选内容，品质保证
• 年轻人都在用
• 得物买家专属售后

{urgency}

冲就完了！''',
        'urgency': '⚡ 限时特惠！库存紧张！',
        'hashtags': ['#{tag}' for tag in ['得物', '潮流', 'AI', '年轻人', '科技', '效率']],
    },
}


def extract_highlight(keyword):
    """从关键词中提取卖点"""
    highlights = [
        ('AI绘画', 'AI一键出图'),
        ('AI写作', 'AI写文案自动生成'),
        ('AI编程', 'AI帮你写代码'),
        ('副业', '零成本搞钱'),
        ('Excel', 'Excel大神必备'),
        ('飞书', '飞书高级用法'),
        ('模板', '直接套用'),
        ('文案', '爆款文案公式'),
        ('运营', '运营SOP'),
        ('赚钱', '每月多赚1千'),
    ]
    for key, highlight in highlights:
        if key in keyword:
            return highlight
    return f'{keyword} 实战教程'


def generate_xianyu_copy(product):
    """生成闲鱼文案"""
    cfg = PLATFORM_CONFIG['闲鱼']
    name = product['name']
    price = product['price']
    emoji = random.choice(cfg['emojis'])
    highlight = extract_highlight(name)
    hook = random.choice(cfg['hook_templates']).format(name=name, highlight=highlight)
    
    # 摘要前50字
    content_summary = product.get('content', '')[:80] + '...'
    
    title = random.choice(cfg['title_formats']).format(
        emoji=emoji, name=name, highlight=highlight, price=price
    )
    
    selling = random.choice(cfg['selling_points'])
    
    body = cfg['body_template'].format(
        emoji=emoji, name=name, hook=hook,
        content_summary=content_summary, price=price,
        selling_points=selling,
        risk_reversal=cfg['risk_reversal'],
        urgency=cfg['urgency'],
        call_to_action=cfg['call_to_action'],
        highlight=highlight,
    )
    
    tags = ' '.join(cfg['hashtags'][:6])
    
    return {
        'platform': '闲鱼',
        'title': title,
        'hook': hook,
        'body': body,
        'tags': tags,
    }


def generate_xiaohongshu_copy(product):
    """生成小红书文案"""
    cfg = PLATFORM_CONFIG['小红书']
    name = product['name']
    emoji = random.choice(cfg['emojis'])
    highlight = extract_highlight(name)
    benefit = random.choice(cfg['benefits'])
    hook = random.choice(cfg['hook_templates']).format(name=name, highlight=highlight)
    
    title = random.choice(cfg['title_formats']).format(
        emoji=emoji, name=name, highlight=highlight, benefit=benefit
    )
    
    body = cfg['body_template'].format(
        hook=hook, name=name, highlight=highlight,
        benefit=benefit, price=product['price'],
    )
    
    tags = ' '.join(cfg['hashtags'][:6])
    
    return {
        'platform': '小红书',
        'title': title,
        'hook': hook,
        'body': body,
        'tags': tags,
    }


def generate_douyin_script(product):
    """生成抖音脚本"""
    cfg = PLATFORM_CONFIG['抖音']
    name = product['name']
    price = product['price']
    emoji = random.choice(cfg['emojis'])
    highlight = extract_highlight(name)
    benefit = random.choice(cfg['benefits'])
    
    title = random.choice(cfg['title_formats']).format(
        emoji=emoji, name=name, highlight=highlight, benefit=benefit
    )
    
    script = cfg['script_template'].format(
        name=name, price=price, highlight=highlight, benefit=benefit,
    )
    
    tags = ' '.join(cfg['hashtags'][:6])
    
    return {
        'platform': '抖音',
        'title': title,
        'hook': f'前3秒钩子：{title}',
        'body': script,
        'tags': tags,
    }


def generate_dewu_copy(product):
    """生成得物文案"""
    cfg = PLATFORM_CONFIG['得物']
    name = product['name']
    price = product['price']
    emoji = random.choice(cfg['emojis'])
    highlight = extract_highlight(name)
    hook = random.choice(cfg['hook_templates']).format(name=name, highlight=highlight)
    
    content_summary = product.get('content', '')[:80] + '...'
    
    title = random.choice(cfg['title_formats']).format(
        emoji=emoji, name=name, highlight=highlight, price=price
    )
    
    body = cfg['body_template'].format(
        emoji=emoji, name=name, hook=hook,
        content_summary=content_summary, price=price,
        urgency=cfg['urgency'], highlight=highlight,
    )
    
    tags = ' '.join(cfg['hashtags'][:6])
    
    return {
        'platform': '得物',
        'title': title,
        'hook': hook,
        'body': body,
        'tags': tags,
    }


def generate_all_platform_copies(product):
    """为一个产品生成所有平台文案"""
    copies = []
    platforms = product.get('platforms', '闲鱼,小红书')
    
    platform_map = {
        '闲鱼': generate_xianyu_copy,
        '小红书': generate_xiaohongshu_copy,
        '抖音': generate_douyin_script,
        '得物': generate_dewu_copy,
    }
    
    for platform in platforms.split(','):
        platform = platform.strip()
        if platform in platform_map:
            try:
                copy = platform_map[platform](product)
                copies.append(copy)
                # 保存到数据库
                db.add_copy(
                    product_id=product['id'],
                    platform=copy['platform'],
                    title=copy['title'],
                    body=copy['body'],
                    tags=copy['tags'],
                    hook=copy['hook'],
                )
            except Exception as e:
                print(f"⚠️ {platform}文案生成失败: {e}")
    
    return copies


def generate_copies_for_all_products():
    """为所有未生成文案的产品批量生成"""
    products = db.get_all_products(status='ready')
    generated_count = 0
    
    for product in products:
        # 检查是否已有文案
        existing = db.get_copies_by_product(product['id'])
        if existing:
            continue
        
        copies = generate_all_platform_copies(product)
        if copies:
            generated_count += 1
            print(f"✅ {product['name']} 生成 {len(copies)} 套文案")
    
    db.log_run('copywriter', 'success', f'文案生成完成，{generated_count}个产品')
    return generated_count


def get_listing_package(product_id):
    """获取完整的上架清单"""
    product = db.get_product(product_id)
    if not product:
        return None
    
    copies = db.get_copies_by_product(product_id)
    
    return {
        'product': product,
        'copies': copies,
        'listing_steps': [
            f"1️⃣ 在{platform}注册/登录账号"
            f"2️⃣ 使用「{copy['title'][:30]}...」作为标题"
            f"3️⃣ 复制粘贴正文内容"
            f"4️⃣ 添加话题标签：{copy['tags'][:30]}..."
            f"5️⃣ 设置价格：{product['price']}元"
            f"6️⃣ 上传封面图（建议用AI生成或文字海报）"
            f"7️⃣ 发布！"
            for copy in copies
            for platform in [copy['platform']]
        ],
    }


if __name__ == '__main__':
    db.init_db()
    # 测试
    products = db.get_all_products()
    if products:
        test = products[0]
        print(f"测试产品：{test['name']}")
        copies = generate_all_platform_copies(test)
        for c in copies:
            print(f"\n【{c['platform']}】标题: {c['title'][:40]}...")
    else:
        print("没有产品，先运行 product.py 生成")
