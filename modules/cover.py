"""
封面图自动生成模块 V3.0
使用 Pillow 生成专业的商品封面图
- 渐变色背景
- 大标题（产品名）
- 副标题（卖点）
- emoji 图标
- 价格标签
- 平台标签（闲鱼/小红书/抖音/得物）
- 多种配色方案
- 可保存为 PNG/JPG
"""

import os
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = Path(__file__).parent.parent
COVER_DIR = BASE_DIR / "static" / "covers"
COVER_DIR.mkdir(parents=True, exist_ok=True)


# ========== 配色方案（为不同产品选择不同风格） ==========

COLOR_THEMES = [
    # (背景起始色, 背景结束色, 标题色, 副标题色, 价格标签色, emoji)
    # 小红书风 - 粉橙渐变
    {"bg1": (255, 182, 193), "bg2": (255, 140, 0),
     "title": (255, 255, 255), "subtitle": (255, 255, 255),
     "tag": (255, 59, 48), "emoji": ["✨", "💖", "🔥", "🌟", "🎀"]},
    # 科技蓝 - AI风
    {"bg1": (0, 102, 204), "bg2": (0, 255, 255),
     "title": (255, 255, 255), "subtitle": (240, 240, 240),
     "tag": (255, 204, 0), "emoji": ["🤖", "⚡", "🚀", "💡", "🧠"]},
    # 紫色 - 高端感
    {"bg1": (75, 0, 130), "bg2": (148, 0, 211),
     "title": (255, 255, 255), "subtitle": (230, 230, 250),
     "tag": (255, 215, 0), "emoji": ["👑", "💎", "🎯", "🏆", "⭐"]},
    # 绿色 - 自然/效率
    {"bg1": (34, 197, 94), "bg2": (16, 185, 129),
     "title": (255, 255, 255), "subtitle": (240, 255, 240),
     "tag": (220, 38, 38), "emoji": ["🌿", "🍀", "✅", "📈", "💰"]},
    # 橙红 - 活力/促销
    {"bg1": (255, 69, 0), "bg2": (255, 140, 0),
     "title": (255, 255, 255), "subtitle": (255, 255, 255),
     "tag": (255, 255, 0), "emoji": ["🎉", "🎊", "🔥", "⚡", "💥"]},
    # 深色 - 高级感
    {"bg1": (30, 30, 46), "bg2": (77, 77, 120),
     "title": (255, 255, 255), "subtitle": (200, 200, 220),
     "tag": (255, 107, 53), "emoji": ["🌙", "✨", "💫", "🎨", "🎭"]},
]


def get_font(size):
    """获取可用字体"""
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/root/.fonts/SimHei.ttf",
        "/workspace/fonts/SimHei.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                continue
    return ImageFont.load_default()


def pick_theme(product_name: str) -> dict:
    """根据产品名挑选配色（稳定但多样化）"""
    h = int(hashlib.md5(product_name.encode()).hexdigest(), 16)
    return COLOR_THEMES[h % len(COLOR_THEMES)]


def pick_emoji(product_name: str) -> str:
    """挑选 emoji"""
    theme = pick_theme(product_name)
    h = int(hashlib.md5((product_name + "e").encode()).hexdigest(), 16)
    return theme["emoji"][h % len(theme["emoji"])]


def draw_gradient(width, height, color1, color2):
    """画渐变背景"""
    img = Image.new("RGB", (width, height))
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    return img


def wrap_text(text, font, max_width):
    """中文自动换行"""
    lines = []
    current = ""
    for char in text:
        test = current + char
        # 估算宽度（中文字符约等于字体大小）
        if font.getlength(test) > max_width:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def generate_cover(
    product_name: str,
    price: float,
    subtitle: str = "",
    platforms: str = "",
    num_items: int = 0,
    size: tuple = (800, 800),
    use_transparent: bool = True,
) -> str:
    """
    生成商品封面图
    
    Args:
        product_name: 产品名称
        price: 建议售价
        subtitle: 副标题/卖点
        platforms: 目标平台
        num_items: 包含条数
        size: 图片尺寸 (宽, 高)
    
    Returns:
        保存的文件路径
    """
    theme = pick_theme(product_name)
    emoji = pick_emoji(product_name)
    width, height = size
    
    # 1. 渐变背景
    bg = draw_gradient(width, height, theme["bg1"], theme["bg2"])
    
    # 2. 模糊光晕效果（中间加亮）
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # 中心光晕
    od.ellipse(
        [width * 0.2, height * 0.15, width * 0.8, height * 0.65],
        fill=(255, 255, 255, 30)
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=40))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    
    draw = ImageDraw.Draw(bg)
    
    # 3. 顶部小标签（如果有平台）
    y_offset = 50
    if platforms:
        font_small = get_font(22)
        draw.text((50, y_offset), f"📦 {platforms}", fill=theme["subtitle"], font=font_small)
        y_offset += 35
    
    # 4. emoji 大图标
    font_big_emoji = get_font(120)
    draw.text((width // 2 - 60, y_offset), emoji, fill=(255, 255, 255), font=font_big_emoji)
    y_offset += 140
    
    # 5. 产品标题（大）
    font_title = get_font(64)
    title_lines = wrap_text(product_name, font_title, width - 100)
    line_height = 72
    for i, line in enumerate(title_lines[:3]):  # 最多3行
        draw.text((50, y_offset + i * line_height), line, 
                  fill=theme["title"], font=font_title)
    y_offset += len(title_lines[:3]) * line_height + 20
    
    # 6. 副标题（卖点）
    if subtitle:
        font_sub = get_font(28)
        sub_lines = wrap_text(subtitle, font_sub, width - 100)
        for i, line in enumerate(sub_lines[:2]):
            draw.text((50, y_offset + i * 36), line,
                      fill=theme["subtitle"], font=font_sub)
        y_offset += len(sub_lines[:2]) * 36 + 20
    
    # 7. 包含条数
    if num_items > 0:
        font_tag = get_font(24)
        # 画个标签框
        tag_text = f"📋 包含 {num_items}+ 条"
        bbox = draw.textbbox((50, y_offset), tag_text, font=font_tag)
        draw.rounded_rectangle(
            [bbox[0] - 12, bbox[1] - 6, bbox[2] + 12, bbox[3] + 6],
            radius=12, fill=(255, 255, 255, 40)
        )
        draw.text((56, y_offset), tag_text, fill=theme["title"], font=font_tag)
        y_offset += 50
    
    # 8. 价格标签（右下）
    font_price = get_font(72)
    price_text = f"¥{price:.0f}"
    # 价格背景圆
    price_bbox = draw.textbbox((0, 0), price_text, font=font_price)
    pw = price_bbox[2] - price_bbox[0] + 40
    ph = price_bbox[3] - price_bbox[1] + 20
    px = width - pw - 40
    py = height - ph - 40
    # 画圆角矩形背景
    price_bg = theme["tag"]
    if price_bg == (255, 255, 0):  # 黄色太亮，加描边
        draw.rounded_rectangle(
            [px, py, px + pw, py + ph],
            radius=20, fill=(255, 215, 0), outline=(200, 150, 0), width=3
        )
    else:
        draw.rounded_rectangle(
            [px, py, px + pw, py + ph],
            radius=20, fill=price_bg
        )
    draw.text((px + 20, py + 10), price_text, fill=(255, 255, 255), font=font_price)
    
    # 9. 水印/标识（左下）
    font_watermark = get_font(20)
    draw.text((50, height - 40), "AI副业工坊 · 数字产品", fill=(255, 255, 255, 180), font=font_watermark)
    
    # 10. 保存
    safe_name = hashlib.md5(product_name.encode()).hexdigest()[:12]
    filename = f"cover_{safe_name}.png"
    filepath = COVER_DIR / filename
    bg.save(filepath, "PNG")
    
    return str(filepath)


def generate_cover_for_product(product: dict) -> str:
    """为产品字典生成封面"""
    return generate_cover(
        product_name=product.get("name", "AI产品"),
        price=product.get("price", 9.9),
        subtitle=product.get("subtitle", product.get("description", "")[:40]),
        platforms=product.get("platforms", ""),
        num_items=product.get("item_count", 0),
    )


if __name__ == "__main__":
    # 测试生成
    test_products = [
        {"name": "小红书爆款文案提示词", "price": 19.9, "subtitle": "86条现成提示词，直接套用", "platforms": "小红书", "item_count": 86},
        {"name": "AI办公效率神器包", "price": 29.9, "subtitle": "让AI帮你干活，每天省2小时", "platforms": "全平台", "item_count": 52},
        {"name": "普通人副业工具包", "price": 9.9, "subtitle": "0成本启动的10个副业方向", "platforms": "闲鱼/小红书", "item_count": 40},
    ]
    for p in test_products:
        path = generate_cover_for_product(p)
        print(f"✅ {p['name']} → {path}")
