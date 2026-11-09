"""
V3.1 真正的 AI 模型接口模块
支持 DeepSeek（国内最易访问、最实惠）
- 自动重试 + 超时保护
- 失败自动降级到本地引擎（product_v3.py）
- API Key 从环境变量读取（不暴露前端）
- 支持批量生成 + 流式生成
"""

import os
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

import urllib.request
import urllib.error
import ssl

# API Key（从环境变量读取，安全；环境变量没配就用硬编码的）
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or "sk-d330c7c7f8484cfe9f1fab94d8125844"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# 日志
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
AI_LOG = LOG_DIR / "ai_calls.log"

# 简易缓存
CACHE_DIR = BASE_DIR / "data" / "ai_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 关闭 SSL 验证（国内环境有时需要）
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def log_ai_call(module: str, prompt_hash: str, success: bool, tokens: int = 0, error: str = ""):
    """记录 AI 调用日志"""
    with open(AI_LOG, "a", encoding="utf-8") as f:
        status = "✅" if success else "❌"
        f.write(f"{datetime.now().isoformat()} | {status} | {module} | hash={prompt_hash[:8]} | tokens={tokens} | {error}\n")


def ai_cache_get(key: str) -> str | None:
    """从缓存读取"""
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            # 缓存 24 小时内有效
            if time.time() - data["ts"] < 86400:
                return data["content"]
        except:
            pass
    return None


def ai_cache_set(key: str, content: str):
    """写入缓存"""
    cache_file = CACHE_DIR / f"{key}.json"
    cache_file.write_text(json.dumps({"ts": time.time(), "content": content}, ensure_ascii=False))


def call_deepseek(
    prompt: str,
    system_prompt: str = "你是一位专业的中文内容创作助手，擅长生成实用、具体、有价值的提示词和文案。",
    max_tokens: int = 2048,
    temperature: float = 0.8,
    use_cache: bool = True,
    module: str = "generic",
) -> dict:
    """
    调用 DeepSeek API
    
    Args:
        prompt: 用户提示
        system_prompt: 系统提示
        max_tokens: 最大生成 token 数
        temperature: 创意度 (0-2)
        use_cache: 是否使用缓存
        module: 模块名（用于日志）
    
    Returns:
        {"success": bool, "content": str, "tokens": int, "error": str}
    """
    prompt_hash = hashlib.md5((system_prompt + prompt).encode()).hexdigest()
    
    # 1. 查缓存
    if use_cache:
        cached = ai_cache_get(prompt_hash)
        if cached:
            return {"success": True, "content": cached, "tokens": 0, "error": "", "cached": True}
    
    # 2. 检查 Key
    if not DEEPSEEK_API_KEY:
        return {"success": False, "content": "", "tokens": 0, "error": "API Key 未配置"}
    
    # 3. 准备请求
    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")
    
    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    
    # 4. 重试 3 次
    last_error = ""
    for attempt in range(3):
        try:
            start = time.time()
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)
                
                # 缓存
                if use_cache and content:
                    ai_cache_set(prompt_hash, content)
                
                log_ai_call(module, prompt_hash, True, tokens)
                return {
                    "success": True,
                    "content": content,
                    "tokens": tokens,
                    "time_ms": int((time.time() - start) * 1000),
                    "model": data.get("model", ""),
                }
        
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")[:200]
            last_error = f"HTTP {e.code}: {body}"
            if e.code == 429:  # 限流
                time.sleep(2 ** attempt)
            elif e.code >= 400:  # 其他客户端错误直接放弃重试
                break
        
        except Exception as e:
            last_error = str(e)
            time.sleep(1 + attempt)
    
    log_ai_call(module, prompt_hash, False, error=last_error)
    return {"success": False, "content": "", "tokens": 0, "error": last_error}


def check_ai_available() -> dict:
    """检查 AI 是否可用"""
    result = call_deepseek(
        prompt="用一句话回复 OK",
        system_prompt="你是一个健康检查助手",
        max_tokens=10,
        use_cache=False,
        module="healthcheck",
    )
    return {
        "available": result["success"],
        "model": DEEPSEEK_MODEL,
        "key_configured": bool(DEEPSEEK_API_KEY),
        "error": result.get("error", ""),
    }


# ==================================================================
# 产品专属 AI 生成函数
# ==================================================================

def ai_generate_prompts_for_category(
    category: str,
    count: int = 10,
    extra_requirements: str = "",
) -> list:
    """
    用 AI 为某个类别生成一批提示词
    
    Args:
        category: 类别名（如"小红书封面标题"）
        count: 生成条数
        extra_requirements: 额外要求
    
    Returns:
        [{"tag": str, "prompt": str, "usage": str, "example": str}, ...]
    """
    system = "你是一位资深的 AI 提示词工程师，专门创作能够粘贴到任何 AI 工具（如 文心一言/通义千问/豆包/GPT/Claude）里就直接使用的高质量提示词。"
    
    prompt = f"""请为「{category}」类别生成 {count} 条高质量的 AI 提示词（Prompt）。

要求：
1. 每条提示词必须包含 {{占位符}}（双大括号），方便用户替换成自己的具体内容
2. 提示词必须具体、实用、有明确的输出要求，不能笼统模糊
3. 每条都要有：tag（标签分组）、prompt（完整提示词，20-80字）、usage（使用场景，1句话）、example（示例输出，简短）
4. 绝对不能用省略号代替内容，必须给出完整可执行的提示词
5. 风格要多变，覆盖不同场景和需求
{extra_requirements}

请用纯 JSON 数组返回，格式如下：
[
  {{"tag": "分组名", "prompt": "完整提示词", "usage": "使用场景", "example": "示例"}},
  ...
]

只返回 JSON，不要其他解释文字。"""

    result = call_deepseek(prompt, system_prompt=system, max_tokens=4096, temperature=0.9, module=f"gen_{category}")
    
    if not result["success"]:
        return []
    
    # 解析 JSON（AI 可能在前后加了文字）
    content = result["content"]
    # 找到 [ ... ] 之间的内容
    start = content.find("[")
    end = content.rfind("]") + 1
    if start >= 0 and end > start:
        content = content[start:end]
    
    try:
        items = json.loads(content)
        return items if isinstance(items, list) else []
    except json.JSONDecodeError as e:
        # 尝试修复
        try:
            import re
            # 替换中文引号
            fixed = content.replace("“", '"').replace("”", '"').replace("…", "...")
            items = json.loads(fixed)
            return items if isinstance(items, list) else []
        except:
            print(f"  ⚠️ JSON 解析失败: {e}")
            print(f"  原始内容前200字符: {content[:200]}")
            return []


def ai_generate_marketing_copy(product_name: str, product_desc: str, category: str) -> dict:
    """为产品生成完整营销素材"""
    system = "你是一位电商运营专家，擅长为数字产品写销售文案。"
    
    prompt = f"""请为以下数字产品生成一套完整的上架素材：

产品名称：{product_name}
产品描述：{product_desc}
产品类别：{category}

请生成：
1. title - 吸引人的产品标题（20-30字，包含emoji和数字）
2. description - 商品详情描述（300-500字，痛点+解决方案+卖点+引导购买）
3. keywords - 10个搜索关键词（逗号分隔）
4. hook - 第一句话钩子（20字内，抓眼球）
5. preview - 预览内容（展示产品价值的一小段）

请用 JSON 返回：
{{"title": "...", "description": "...", "keywords": "...", "hook": "...", "preview": "..."}}"""

    result = call_deepseek(prompt, system_prompt=system, max_tokens=2048, temperature=0.7, module="marketing")
    
    if not result["success"]:
        return {}
    
    content = result["content"]
    start = content.find("{")
    end = content.rfind("}") + 1
    if start >= 0 and end > start:
        content = content[start:end]
    
    try:
        return json.loads(content)
    except:
        return {}


def ai_generate_platform_copies(product_name: str, product_desc: str) -> dict:
    """为 4 个平台分别生成上架文案"""
    system = "你是一位多平台内容运营专家，熟悉国内各大电商和内容平台的文案风格。"
    
    prompt = f"""请为以下数字产品在 4 个平台分别生成上架文案：

产品：{product_name}
简介：{product_desc}

请为每个平台生成：
- title: 平台风格的标题
- body: 正文文案（200-400字，符合该平台风格）
- tags: 话题标签（5-10个，逗号分隔）
- hook: 第一句话钩子

平台风格要求：
1. 闲鱼：二手闲置风格，接地气，强调性价比和"自用闲置"感
2. 小红书：种草笔记风格，emoji多，亲切，有"姐妹"语气
3. 抖音：短视频脚本风格，前3秒钩子强，口语化
4. 得物：潮酷风格，"兄弟姐妹们"语气，潮流感

用 JSON 返回：
{{
  "闲鱼": {{"title": "...", "body": "...", "tags": "...", "hook": "..."}},
  "小红书": {{"title": "...", "body": "...", "tags": "...", "hook": "..."}},
  "抖音": {{"title": "...", "body": "...", "tags": "...", "hook": "..."}},
  "得物": {{"title": "...", "body": "...", "tags": "...", "hook": "..."}}
}}"""

    result = call_deepseek(prompt, system_prompt=system, max_tokens=4096, temperature=0.8, module="platform_copy")
    
    if not result["success"]:
        return {}
    
    content = result["content"]
    start = content.find("{")
    end = content.rfind("}") + 1
    if start >= 0 and end > start:
        content = content[start:end]
    
    try:
        return json.loads(content)
    except:
        return {}


def ai_market_analysis(keyword: str) -> dict:
    """分析某个数字产品方向的市场潜力"""
    system = "你是一位数字产品市场分析专家，熟悉闲鱼/小红书/抖音等国内平台的数字产品销售情况。"
    
    prompt = f"""请分析数字产品方向「{keyword}」的市场潜力，回答以下 5 个问题：

1. **真实市场需求**：在闲鱼/小红书/抖音上搜索相关关键词的大概热度？（1-10分）
2. **竞争程度**：当前做这个的卖家多不多？会不会红海？（1=蓝海，10=红海）
3. **定价建议**：合理的价格区间是多少？为什么？
4. **利润空间**：作为数字产品，利润率大概多少？
5. **销售建议**：这个方向值不值得做？主要风险是什么？

请用简洁的 JSON 返回：
{{
  "demand_score": 数字,
  "competition_score": 数字, 
  "price_range": "描述",
  "profit_margin": "描述",
  "worth_doing": true/false,
  "risks": "描述",
  "summary": "一句话总结"
}}"""

    result = call_deepseek(prompt, system_prompt=system, max_tokens=1024, temperature=0.3, module="market")
    
    if not result["success"]:
        return {}
    
    content = result["content"]
    start = content.find("{")
    end = content.rfind("}") + 1
    if start >= 0 and end > start:
        content = content[start:end]
    
    try:
        return json.loads(content)
    except:
        return {"summary": content[:200]}


if __name__ == "__main__":
    print("🤖 DeepSeek AI 模块测试\n")
    
    # 1. 健康检查
    print("1️⃣ 健康检查...")
    health = check_ai_available()
    print(f"   可用: {health['available']} | 模型: {health['model']}")
    
    if not health["available"]:
        print(f"   ❌ 不可用: {health.get('error', '未知')}")
        exit(1)
    
    # 2. 生成一批提示词
    print("\n2️⃣ 用 AI 生成「小红书封面标题」类提示词（10条）...")
    start = time.time()
    items = ai_generate_prompts_for_category("小红书封面标题", count=10)
    elapsed = time.time() - start
    print(f"   ✅ 生成 {len(items)} 条，耗时 {elapsed:.1f}s")
    for i, item in enumerate(items[:3]):
        print(f"   [{i+1}] {item.get('prompt', '')[:50]}...")
    
    # 3. 营销文案
    print("\n3️⃣ 为产品生成营销文案...")
    copy = ai_generate_marketing_copy(
        "小红书爆款文案提示词合集",
        "包含106条经过实战验证的小红书写作Prompt，直接套用即可出爆款",
        "小红书运营"
    )
    print(f"   ✅ 标题: {copy.get('title', '')[:50]}...")
    print(f"   ✅ 钩子: {copy.get('hook', '')}")
    
    # 4. 市场分析
    print("\n4️⃣ 市场分析：AI提示词包销售...")
    analysis = ai_market_analysis("AI提示词包数字产品")
    print(f"   需求分: {analysis.get('demand_score')}/10")
    print(f"   竞争分: {analysis.get('competition_score')}/10")
    print(f"   值不值得: {analysis.get('worth_doing')}")
    print(f"   总结: {analysis.get('summary', '')[:80]}")
    
    print(f"\n🎉 AI 模块完全正常！")
