from app.schemas.travel import ItineraryDay, TravelPlan, TravelRequest, TravelResponse, TravelStyle


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _has_style(request: TravelRequest, style: TravelStyle) -> bool:
    return style in (request.style or [])


class FallbackService:
    def build(self, request: TravelRequest) -> TravelResponse:
        if "杭州" in _normalize(request.destination):
            return self._build_hangzhou(request)
        if "厦门" in _normalize(request.destination) or _has_style(request, TravelStyle.PHOTOGENIC):
            return self._build_xiamen(request)
        if _has_style(request, TravelStyle.CITY_WALK) or _has_style(request, TravelStyle.RELAXED):
            return self._build_city_walk(request)
        return self._build_generic(request)

    def _build_hangzhou(self, request: TravelRequest) -> TravelResponse:
        days = [
            ItineraryDay(
                day=1,
                title="西湖慢热开场",
                morning=f"从{request.origin}出发抵达{request.destination}，先去湖滨一带放松节奏，喝一杯手冲咖啡。",
                afternoon="沿西湖步行到杨公堤，安排轻量拍照和湖边骑行，不赶景点。",
                evening="在河坊街附近吃杭帮菜，夜里去南宋御街散步收尾。",
            ),
            ItineraryDay(
                day=2,
                title="山寺与茶园",
                morning="早点去灵隐飞来峰，避开人流高峰，保留完整半天体验。",
                afternoon="转去龙井村喝茶、看山景，收束在九溪一线的轻徒步。",
                evening=f"返程回{request.origin}，路上整理照片和消费清单。",
            ),
        ][: request.days]
        return TravelResponse(
            summary=f"{request.destination}{request.days}天轻松漫游",
            plan=TravelPlan(
                days=days,
                budgetSummary=f"可控制在 {request.budget} / 人" if request.budget else "预计 1200 元 / 人左右",
                budgetBreakdown={"交通": "300 元", "住宿": "380 元", "餐饮": "320 元", "门票与体验": "180 元"},
            ),
            tips=[
                "周末西湖核心区较拥挤，建议上午先逛、傍晚再回湖边。",
                "灵隐寺和龙井村路线顺路，避免同一天反复折返。",
                "带一双轻便好走的鞋，九溪和茶园拍照更舒服。",
            ],
        )

    def _build_xiamen(self, request: TravelRequest) -> TravelResponse:
        days = [
            ItineraryDay(
                day=1,
                title="沙坡尾热身",
                morning=f"从{request.origin}飞抵{request.destination}，入住思明区，优先压缩交通成本。",
                afternoon="先逛沙坡尾、艺术西区和顶澳仔猫街，完成第一波城市漫游拍照。",
                evening="去八市吃海鲜，再沿中山路夜逛，感受老城烟火。",
            ),
            ItineraryDay(
                day=2,
                title="鼓浪屿轻节奏",
                morning="提前订船班，上午上鼓浪屿，走万国建筑和海边路段。",
                afternoon="安排咖啡馆、老别墅和观景平台，留足自由拍摄时间。",
                evening="回本岛吃闽南菜，早点回酒店休息。",
            ),
            ItineraryDay(
                day=3,
                title="滨海收尾",
                morning="环岛路骑行或曾厝垵慢逛，不堆景点。",
                afternoon="预留伴手礼和返程缓冲，结束旅行。",
            ),
        ][: request.days]
        return TravelResponse(
            summary=f"{request.destination}{request.days}天海风拍照线",
            plan=TravelPlan(
                days=days,
                budgetSummary=f"建议按 {request.budget} 做中等舒适配置" if request.budget else "预计 1800 元 / 人左右",
                budgetBreakdown={"交通": "620 元", "住宿": "520 元", "餐饮": "420 元", "门票与交通杂项": "240 元"},
            ),
            tips=[
                "鼓浪屿建议预约上午船次，拍照光线和人流都更友好。",
                "城市漫游路线尽量集中在思明区，减少打车切换。",
                "海边日晒强，准备防晒和可折叠外套。",
            ],
        )

    def _build_city_walk(self, request: TravelRequest) -> TravelResponse:
        days = []
        for index in range(request.days):
            days.append(
                ItineraryDay(
                    day=index + 1,
                    title="抵达与熟悉城市" if index == 0 else "松弛收尾" if index == request.days - 1 else "在地体验",
                    morning=f"从{request.origin}前往{request.destination}，入住交通便利的核心城区。"
                    if index == 0
                    else "上午优先安排本地街区、市场或有氛围的街巷散步。",
                    afternoon="围绕一个片区深挖吃喝与拍照点，不追求打卡数量。",
                    evening=f"整理消费和行李，预留返程缓冲，回{request.origin}。"
                    if index == request.days - 1
                    else "晚餐选择评价稳定的本地餐馆，夜里回酒店休息。",
                )
            )
        return TravelResponse(
            summary=f"{request.destination}{request.days}天低压城市漫游",
            plan=TravelPlan(
                days=days,
                budgetSummary=f"建议按 {request.budget} 控制整体花费" if request.budget else "预计 1500 元 / 人左右",
                budgetBreakdown={"交通": "450 元", "住宿": "420 元", "餐饮": "360 元", "灵活开销": "270 元"},
            ),
            tips=[
                "首版建议住在地铁或景点较集中的区域，体验更顺。",
                "每天只设 1 到 2 个核心片区，旅行节奏会更舒服。",
                f"你的补充需求“{request.prompt}”已经体现在整体节奏上，建议现场再灵活微调。"
                if request.prompt
                else "如果遇到天气变化，优先保留室内咖啡馆、展览或商圈备选。",
            ],
        )

    def _build_generic(self, request: TravelRequest) -> TravelResponse:
        days = []
        for index in range(request.days):
            days.append(
                ItineraryDay(
                    day=index + 1,
                    title=f"Day {index + 1} 重点安排",
                    morning=f"从{request.origin}出发前往{request.destination}，先完成入住与交通熟悉。"
                    if index == 0
                    else "上午安排城市代表性片区或核心景点，避免跨城式折返。",
                    afternoon="中午后放缓节奏，穿插吃饭、散步和轻量体验。",
                    evening=f"整理返程，结束本次{request.destination}旅行。"
                    if index == request.days - 1
                    else "夜间安排本地美食或夜景路线，控制体力消耗。",
                )
            )
        return TravelResponse(
            summary=f"{request.destination}{request.days}天清爽出游计划",
            plan=TravelPlan(
                days=days,
                budgetSummary=f"预算目标：{request.budget} / 人" if request.budget else "预计 1300 元 / 人左右",
                budgetBreakdown={"交通": "400 元", "住宿": "400 元", "餐饮": "300 元", "体验与杂项": "200 元"},
            ),
            tips=[
                "每天尽量围绕一个区域展开，减少折返。",
                "把返程前的 2 小时留作弹性缓冲，更适合短途旅行。",
                "如果预算有限，住宿优先靠近交通枢纽。",
            ],
        )
