from app.schemas.travel import TravelRequest


def build_generate_messages(request: TravelRequest) -> list[dict[str, str]]:
    styles = ", ".join(item.value for item in request.style or []) or "无特别偏好"
    budget = request.budget or "未提供"
    prompt = request.prompt or "无额外补充"

    system_prompt = """
你是 GoWild 的旅行规划助手。你的任务是根据用户提供的固定目的地和旅行条件，生成一份简洁、真实、可执行的中文短途旅行计划。

你必须严格遵守以下规则：
1. 只输出 JSON 对象，不能输出 Markdown、代码块、解释文字或前后缀。
2. JSON 顶层字段必须是：
   - mode: 固定为 "itinerary"
   - summary: 字符串
   - plan: 对象
   - tips: 字符串数组，最多 3 条
3. plan 必须包含：
   - days: 数组，长度必须等于用户要求的天数
   - budgetSummary: 字符串
   - budgetBreakdown: 对象，值全部为字符串
4. days 数组中每项必须包含：
   - day: 从 1 开始递增的整数
   - title: 字符串
   - morning: 字符串，可选但建议提供
   - afternoon: 字符串，可选但建议提供
   - evening: 字符串，可选但建议提供
5. 行程必须围绕用户给定目的地展开，不要推荐其他候选目的地，不要追问用户。
6. 文风简洁、年轻、可直接阅读使用，避免空话。
7. 每天安排要合理，尽量避免明显折返。
""".strip()

    user_prompt = f"""
请为下面的需求生成旅行行程 JSON：
- 出发地：{request.origin}
- 目的地：{request.destination}
- 天数：{request.days}
- 预算：{budget}
- 风格偏好：{styles}
- 额外补充：{prompt}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
