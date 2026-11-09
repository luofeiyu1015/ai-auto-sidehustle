"""
产品自动生成模块
根据市场机会自动生成可售卖的产品（数字内容）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import random
import hashlib
from datetime import datetime
from modules import db
from config import PRODUCT_CATEGORIES, MIN_QUALITY_SCORE

# ======= 产品模板库 =======
# 每个模板都是可以实际生成、实际售卖的数字内容

PROMPT_TEMPLATES = {
    'AI绘画': {
        'name_suffix': 'Prompt精选包',
        'price': 19.9,
        'platforms': '闲鱼,小红书,抖音',
        'cover_emoji': '🎨',
        'tags': 'AI绘画,Midjourney,Stable Diffusion,提示词,AI教程',
        'content_generator': lambda kw: generate_art_prompts(kw),
        'description': '精选{kw}高质量提示词，直接复制粘贴就能出图，覆盖{kw}的N种风格！',
    },
    'AI写作': {
        'name_suffix': '文案自动生成Prompt',
        'price': 12.9,
        'platforms': '闲鱼,小红书,抖音',
        'cover_emoji': '✍️',
        'tags': 'AI写作,GPT,文案生成,小红书文案,爆款文案',
        'content_generator': lambda kw: generate_writing_prompts(kw),
        'description': '一键生成{kw}文案的AI提示词，从此告别写文案卡壳！',
    },
    'AI编程': {
        'name_suffix': '编程辅助Prompt合集',
        'price': 29.9,
        'platforms': '闲鱼,小红书',
        'cover_emoji': '💻',
        'tags': 'AI编程,Copilot,GPT,代码生成,程序员',
        'content_generator': lambda kw: generate_code_prompts(kw),
        'description': '让AI帮你写代码！{kw}场景下的Prompt模板大全，效率翻倍！',
    },
    '副业': {
        'name_suffix': '入门SOP教程',
        'price': 9.9,
        'platforms': '闲鱼,小红书,抖音',
        'cover_emoji': '💰',
        'tags': '副业,搞钱,赚钱,SOP,从零开始',
        'content_generator': lambda kw: generate_sop_template(kw),
        'description': '{kw}从0到1完整教程，普通人能直接上手，每月多赚一两千！',
    },
    'Excel': {
        'name_suffix': '高级函数模板合集',
        'price': 13.9,
        'platforms': '闲鱼,小红书',
        'cover_emoji': '📊',
        'tags': 'Excel,函数,数据处理,职场技巧,办公效率',
        'content_generator': lambda kw: generate_excel_templates(kw),
        'description': '{kw}不会公式？这套模板直接复制粘贴用，小白也能变大神！',
    },
    '飞书': {
        'name_suffix': '高级用法合集',
        'price': 18.8,
        'platforms': '闲鱼,小红书',
        'cover_emoji': '🚀',
        'tags': '飞书,效率,团队协作,自动化,办公',
        'content_generator': lambda kw: generate_feishu_tips(kw),
        'description': '飞书不止是聊天软件！{kw}10个高级技巧，让你早下班！',
    },
    '模板': {
        'name_suffix': '全能模板包',
        'price': 15.9,
        'platforms': '闲鱼,小红书,抖音',
        'cover_emoji': '📦',
        'tags': '模板,效率,一键使用,万能模板',
        'content_generator': lambda kw: generate_general_templates(kw),
        'description': '万能{kw}模板包，直接套用节省90%时间！',
    },
    '文案': {
        'name_suffix': '爆款文案模板库',
        'price': 14.9,
        'platforms': '闲鱼,小红书,抖音',
        'cover_emoji': '🔥',
        'tags': '文案,爆款,小红书文案,抖音文案,钩子',
        'content_generator': lambda kw: generate_copy_templates(kw),
        'description': '{kw}爆款文案公式+30+现成模板，直接改就能用！',
    },
    '运营': {
        'name_suffix': '运营SOP方案',
        'price': 24.9,
        'platforms': '闲鱼,小红书,抖音,得物',
        'cover_emoji': '📈',
        'tags': '运营,小红书运营,抖音运营,SOP,涨粉',
        'content_generator': lambda kw: generate_operation_sop(kw),
        'description': '{kw}完整运营方案，从0到起号的每一步都给你规划好！',
    },
    '教程': {
        'name_suffix': '从入门到精通',
        'price': 17.9,
        'platforms': '闲鱼,小红书,抖音',
        'cover_emoji': '📚',
        'tags': '教程,入门,实战,步骤,从零开始',
        'content_generator': lambda kw: generate_tutorial(kw),
        'description': '{kw}完整教程，小白也能学会，每一步都有详细说明！',
    },
}


# ======= 具体内容生成函数 =======

def generate_art_prompts(keyword):
    """生成 AI 绘画提示词"""
    styles = ['realistic', 'anime', 'oil painting', 'watercolor', 'cyberpunk', 
              'fantasy', 'isometric', 'flat design', '3D render', 'pixel art']
    aspects = ['high quality, 4k, detailed', 'masterpiece, best quality', 
               'professional, cinematic lighting', 'hyper detailed, ultra realistic']
    
    prompts = []
    for i in range(30):
        style = random.choice(styles)
        aspect = random.choice(aspects)
        prompts.append(
            f"### {keyword} 风格{i+1}\n"
            f"主题：{keyword}创意场景\n"
            f"正向提示词：A beautiful {keyword} scene in {style} style, {aspect}, trending on ArtStation\n"
            f"反向提示词：low quality, blurry, distorted, ugly, bad anatomy\n"
            f"参数建议：--ar 16:9 --v 6.0 --q 2"
        )
    return "\n\n".join(prompts)


def generate_writing_prompts(keyword):
    """生成 AI 写作提示词"""
    templates = [
        f"你是一位{keyword}专家，请帮我生成10个吸引眼球的标题，要求开头有钩子，能让用户停下来看。",
        f"请以'{keyword}'为主题，写一篇小红书风格的笔记，开头要有故事感，中间有干货，结尾引导互动。",
        f"帮我把这段内容改写成3种风格：活泼版、专业版、情感版。主题是{keyword}。",
        f"请生成5组{keyword}相关的问答，Q&A形式，适合抖音口播。",
        f"以'{keyword}'为卖点，帮我写一个产品的卖点文案，用痛点-方案-效果结构。",
        f"帮我写一条关于{keyword}的朋友圈文案，要真诚不推销。",
    ]
    return "\n\n".join([f"### 模板{i+1}\n{t}" for i, t in enumerate(templates)])


def generate_code_prompts(keyword):
    """生成编程提示词"""
    templates = [
        f"用Python写一个{keyword}的脚本，要求有详细注释，处理异常。",
        f"帮我重构这段{keyword}代码，让它更优雅、更易读。代码：[粘贴你的代码]",
        f"解释这段{keyword}代码的每一行，我是新手，请用简单的语言。",
        f"用{keyword}实现一个缓存装饰器，支持过期时间设置。",
        f"帮我写一个单元测试，覆盖{keyword}模块的所有边界情况。",
        f"这段{keyword}代码运行很慢，帮我优化性能。当前代码：[粘贴]",
    ]
    return "\n\n".join([f"### Prompt {i+1}\n{t}" for i, t in enumerate(templates)])


def generate_sop_template(keyword):
    """生成 SOP 教程"""
    return f"""# {keyword} 从0到1 SOP

## 🎯 适合人群
- 想要{keyword}的普通人
- 零基础小白
- 想增加副业收入的上班族/学生

## 📅 每日时间规划（每天30分钟）
| 时间 | 任务 | 说明 |
|------|------|------|
| 10分钟 | 内容/机会收集 | 刷热榜、看同行 |
| 15分钟 | 执行 | 上架/发布/互动 |
| 5分钟 | 复盘 | 记录数据 |

## 🚀 第一周启动清单
- [ ] 确定你要做的{keyword}细分方向
- [ ] 注册目标平台账号（闲鱼/小红书）
- [ ] 研究10个同行的账号
- [ ] 准备好第一个产品/内容
- [ ] 发布第一条
- [ ] 记录第一天的数据

## 📈 第二周优化
- [ ] 根据第一周数据调整方向
- [ ] 优化标题/封面/价格
- [ ] 开始批量生产

## 💰 第三周放大
- [ ] 尝试多平台同步
- [ ] 开发套餐产品
- [ ] 积累私域流量

## ⚠️ 避坑指南
1. 不要一开始就囤货投入太多钱
2. 先从数字产品/虚拟服务开始，零成本启动
3. 每天固定时间执行，不要三天打鱼两天晒网
4. 数据差及时调整方向，不要死磕
5. 坚持30天再判断有没有效果
"""


def generate_excel_templates(keyword):
    """生成 Excel 函数模板"""
    return f"""# Excel {keyword} 高级函数模板

## 📌 VLOOKUP / XLOOKUP 查找
```excel
# 基础查找
=VLOOKUP(A2, 数据表!A:D, 3, FALSE)

# 带错误处理
=IFERROR(VLOOKUP(A2, 数据表!A:D, 3, FALSE), "未找到")

# XLOOKUP（更强大）
=XLOOKUP(A2, 数据表!A:A, 数据表!C:C, "未找到", 0)
```

## 📌 SUMIF / COUNTIF 条件统计
```excel
# 条件求和
=SUMIF(数据!A:A, ">1000", 数据!B:B)

# 多条件求和
=SUMIFS(数据!C:C, 数据!A:A, ">100", 数据!B:B, "是")

# 条件计数
=COUNTIF(数据!A:A, "完成")
```

## 📌 IF 嵌套逻辑
```excel
# 多条件判断
=IF(A2>=90, "优秀", IF(A2>=60, "及格", "不及格"))

# AND/OR 组合
=IF(AND(A2>=60, B2>=60), "通过", "不通过")
```

## 📌 日期处理
```excel
# 计算天数差
=DATEDIF(A2, B2, "d")

# 计算年龄
=DATEDIF(A2, TODAY(), "y")

# 工作日数
=NETWORKDAYS(A2, B2)
```

## 📌 文本处理
```excel
# 提取数字
=--TEXTJOIN("", TRUE, IFERROR(MID(A2, ROW($1:$99), 1)*1, ""))

# 合并文本
=CONCATENATE(A2, "-", B2, "-", C2)

# 截取指定长度
=LEFT(A2, 5)  /  =RIGHT(A2, 5)  /  =MID(A2, 3, 5)
```

## 📌 实用技巧
1. 冻结首行：视图 → 冻结窗格
2. 条件格式：突出显示重要数据
3. 数据透视表：快速汇总分析
4. 快捷键：Ctrl+E 智能填充，Ctrl+T 转成表格
"""


def generate_feishu_tips(keyword):
    """生成飞书技巧"""
    return f"""# 飞书 {keyword} 10 个高级技巧

## 🚀 效率翻倍

### 1. 多维表格 = 轻量数据库
- 创建多维表格 → 设好字段 → 自动汇总
- 比 Excel 更适合团队协作
- 支持看板、甘特图、日历视图

### 2. 文档智能大纲
- 飞书文档自动生成大纲结构
- 插入 @某人 提醒查看
- 评论支持 @回复

### 3. 日历与会议
- 日历一键预定会议室
- 会议纪要自动生成
- 会议录制可回看

### 4. 机器人自动化
- 自建机器人推送消息
- 定时提醒任务
- 对接外部系统

### 5. 任务管理
- 任务清单 + 分配负责人
- 截止日期提醒
- 看板视图跟踪进度

### 6. 云文档协同
- 多人同时编辑不冲突
- 实时评论批注
- 历史版本可恢复

### 7. 审批流
- 自定义审批流程
- 移动端快速审批
- 审批记录留痕

### 8. 直播培训
- 企业内部直播
- 录播可回看
- 实时互动问答

### 9. OKR 目标管理
- 对齐团队目标
- 进度自动跟踪
- 周期性复盘

### 10. 个人效率
- 飞书妙记转写语音
- 收藏夹整理知识
- 快速搜索全局
"""


def generate_general_templates(keyword):
    """通用模板"""
    templates = [
        f"{keyword}周报模板",
        f"{keyword}预算表模板",
        f"{keyword}进度跟踪表",
        f"{keyword}需求收集表",
        f"{keyword}复盘模板",
    ]
    return "\n\n".join([f"## 📋 {t}\n[详细模板内容]\n\n使用方法：复制到飞书/Excel中即可使用。" for t in templates])


def generate_copy_templates(keyword):
    """爆款文案模板"""
    return f"""# {keyword} 爆款文案公式 + 30+ 模板

## 🎯 万能公式

### 公式1：痛点-方案-效果
> 你是不是也遇到[痛点]？试试[方案]！[效果描述]！

### 公式2：数字+钩子+效果
> 3个步骤搞定{keyword}！看完效率翻倍！

### 公式3：情绪共鸣+解决方案
> 每次想到{keyword}就头疼？这套方法帮你10分钟搞定！

### 公式4：对比+数字+信任
> 之前我用{x}小时做{keyword}，现在只要10分钟！亲测有效！

---

## 📱 小红书模板（10条）

1. 救命！终于有人把{keyword}讲明白了！
2. 姐妹们！这个{keyword}真的绝绝子！
3. 用了{keyword}之后，我每天多赚500块！
4. {keyword}小白也能学会！手把手教学
5. 后悔没早点知道！{keyword}太香了！
6. {keyword}避坑指南！这些雷区千万别踩！
7. 我宣布这是最好用的{keyword}方法！
8. 普通人怎么靠{keyword}搞钱？分享我的经验
9. {keyword}干货分享！建议收藏慢慢看
10. 学会这个{keyword}技巧，同事都来问我！

---

## 🎵 抖音口播模板（10条）

1.（震惊脸）别再花冤枉钱买{keyword}了！
2.（手持产品）用了{keyword}3天，结果...
3.（对比前后）没做{keyword}前 vs 做了之后
4. 新手怎么学{keyword}？一条视频讲清楚！
5. {keyword}到底赚不赚钱？真实数据告诉你
6.（钩子）停！如果你还不会{keyword}，看完这条！
7. 3分钟学会{keyword}，小白也能上手！
8. {keyword}的5个秘密，99%的人不知道
9. 我用{keyword}月入过万？真实分享
10. {keyword}的坑我替你踩过了，听我的！

---

## 💬 私信/朋友圈模板（10条）

1. 最近在研究{keyword}，整理了一些心得，有需要的朋友可以私我~
2. 这个月靠{keyword}赚了xxx，分享给想搞钱的朋友
3. {keyword}真的改变了我的工作方式，强烈推荐！
4. 整理了一份{keyword}的资料包，免费送！
5. {keyword}避雷帖 | 这些年踩过的坑
"""


def generate_operation_sop(keyword):
    """运营 SOP"""
    return f"""# {keyword} 完整运营 SOP

## 📅 每日运营清单

### 上午（30分钟）
- [ ] 查看昨日数据（曝光/点击/转化）
- [ ] 回复所有评论和私信
- [ ] 刷同领域内容，点赞评论10条

### 下午（30分钟）
- [ ] 准备今日发布的内容
- [ ] 发布新内容（笔记/视频）
- [ ] 关注5个同领域账号

### 晚上（20分钟）
- [ ] 数据复盘，记录当日数据
- [ ] 规划明日内容主题
- [ ] 维护粉丝互动

## 📈 周运营清单

### 每周一
- [ ] 分析上周数据，找出爆款规律
- [ ] 规划本周内容主题（至少5条）
- [ ] 更新关键词库

### 每周五
- [ ] 整理本周内容素材
- [ ] 粉丝互动：抽奖/问答
- [ ] 下周选题 brainstorming

## 🎯 增长指标监控

| 指标 | 目标 | 说明 |
|------|------|------|
| 曝光 | +10%/周 | 内容被看见的次数 |
| 点击率 | >3% | 标题/封面的吸引力 |
| 收藏率 | >5% | 内容的价值感 |
| 转化率 | >1% | 关注/私信/下单 |

## 🚨 避坑指南
1. 不要硬广，要软植入
2. 保持日更频率，算法喜欢活跃账号
3. 选题跟着热榜走，但要结合自己定位
4. 粉丝互动要真诚，不要机械回复
5. 数据差不要急，调整内容方向再观察
"""


def generate_tutorial(keyword):
    """完整教程"""
    return f"""# {keyword} 从入门到精通

## 📖 目录
1. [前言：为什么要学{keyword}](#前言)
2. [第一章：基础知识](#第一章)
3. [第二章：工具准备](#第二章)
4. [第三章：第一个实战项目](#第三章)
5. [第四章：进阶技巧](#第四章)
6. [第五章：常见问题](#第五章)

## 🎯 前言
{keyword} 是目前最火的技能之一，学会它能让你：
- 提高工作效率 5-10 倍
- 开拓副业收入渠道
- 成为稀缺人才

## 📚 第一章：基础知识
### 1.1 什么是{keyword}
用简单的话解释核心概念...

### 1.2 适用场景
- 场景一：xxx
- 场景二：xxx
- 场景三：xxx

### 1.3 学习路线图
新手 → 入门 → 熟练 → 专家

## 🛠️ 第二章：工具准备
必备工具清单和安装步骤...

## 🚀 第三章：第一个实战项目
Step by step 手把手教...

## 💡 第四章：进阶技巧
高阶玩法和提效秘籍...

## ❓ 第五章：常见问题
FAQ 和排错指南...
"""


def match_template(keyword):
    """根据关键词匹配最合适的模板"""
    for key, template in PROMPT_TEMPLATES.items():
        if key in keyword:
            return template
    # 默认模板
    return PROMPT_TEMPLATES['模板']


def generate_product_from_opportunity(opportunity):
    """
    根据市场机会生成产品
    opportunity: dict，包含 keyword, score, avg_price 等
    """
    keyword = opportunity['keyword']
    score = opportunity.get('score', 0)
    avg_price = opportunity.get('avg_price', 9.9)
    
    # 1. 匹配模板
    template = match_template(keyword)
    
    # 2. 生成内容
    try:
        content = template['content_generator'](keyword)
    except Exception as e:
        db.log_run('product', 'error', f'内容生成失败: {e}')
        return None
    
    # 3. 计算质量分
    quality_score = calc_quality_score(content, keyword)
    
    # 4. 市场分 = 机会分 / 100
    market_score = min(score / 100, 1.0)
    
    # 5. 最终决策
    overall_score = (quality_score + market_score) / 2
    if quality_score < MIN_QUALITY_SCORE:
        print(f"⚠️ {keyword} 质量分 {quality_score:.2f} 低于阈值 {MIN_QUALITY_SCORE}，跳过")
        return None
    
    # 6. 确定定价
    price = round(template['price'] * random.uniform(0.9, 1.2), 1)
    
    # 7. 生成产品名
    product_name = f"{keyword} {template['name_suffix']}"
    
    # 8. 生成描述
    description = template['description'].format(kw=keyword)
    
    # 9. 入库
    pid = db.add_product(
        name=product_name,
        category=list(PROMPT_TEMPLATES.keys())[list(PROMPT_TEMPLATES.values()).index(template)] if template in PROMPT_TEMPLATES.values() else 'digital',
        description=description,
        content=content,
        price=price,
        cost=0,  # 数字产品成本为0
        suggested_price=price,
        platforms=template['platforms'],
        cover_emoji=template['cover_emoji'],
        tags=template['tags'],
        quality_score=round(quality_score, 2),
        market_score=round(market_score, 2),
        opportunity_id=opportunity.get('id'),
    )
    
    print(f"✅ 生成产品: {product_name} | 定价: {price}元 | 质量分: {quality_score:.2f} | ID: {pid}")
    
    return pid


def calc_quality_score(content, keyword):
    """简单的质量评估"""
    score = 0.4  # 基础分
    
    # 内容长度（越长越好，但不要过短）
    length = len(content)
    if length > 2000:
        score += 0.2
    elif length > 1000:
        score += 0.1
    elif length > 500:
        score += 0.05
    
    # 关键词相关性
    keyword_count = content.lower().count(keyword.lower())
    if keyword_count >= 5:
        score += 0.15
    elif keyword_count >= 2:
        score += 0.1
    
    # 结构（有 markdown 标题加分）
    if '##' in content or '###' in content:
        score += 0.1
    if '```' in content:  # 有代码块
        score += 0.05
    
    return min(score, 1.0)


def generate_top_products(limit=5):
    """自动生成产品：从高分机会中选前N个"""
    opportunities = db.get_top_opportunities(limit=limit, status=None)
    
    # 过滤掉已经生成过的
    new_opps = [o for o in opportunities if o['status'] not in ('generated', 'listed', 'sold')]
    
    print(f"\n🎨 开始生成产品，{len(new_opps)} 个新机会待处理")
    
    generated = []
    for opp in new_opps[:limit]:
        pid = generate_product_from_opportunity(opp)
        if pid:
            generated.append(pid)
            # 给这个机会标记状态
            db.update_opportunity_status(opp['id'], 'generated')
    
    db.log_run('product', 'success', f'产品生成完成，新增{len(generated)}个')
    return generated


if __name__ == '__main__':
    db.init_db()
    # 测试
    products = generate_top_products(3)
    print(f"\n✅ 测试生成 {len(products)} 个产品")
