# GoWild 架构文档

## 1. 概览

GoWild 当前采用前后端分离架构：

- 前端：Vue 3 + TypeScript + Vite
- 后端：FastAPI + Pydantic + Uvicorn
- LLM：通过硅基流动提供的 OpenAI 兼容接口调用

当前系统只覆盖一条最小闭环：

1. 用户在首页填写旅行需求
2. 前端调用后端生成接口
3. 后端调用 LLM 生成结构化行程
4. 后端返回稳定 JSON
5. 前端展示结果页

第一版不接数据库，后端保持无状态；当前会话数据由前端内存状态保存。

## 2. 整体架构

### 2.1 前端职责

- 渲染首页和结果页
- 管理当前请求、生成结果、loading、错误提示
- 将表单数据提交到 `/api/v1/generate`
- 展示分天行程、预算摘要、注意事项

### 2.2 后端职责

- 校验请求参数
- 组装 Prompt
- 调用硅基流动 Chat Completions 接口
- 规范化并校验 LLM 返回结果
- 在 LLM 输出异常时走模板兜底
- 返回前端稳定可消费的 JSON

### 2.3 调用链路

```text
TripForm
  -> generatePlan()
  -> POST /api/v1/generate
  -> TravelService.generate_plan()
  -> build_generate_messages()
  -> SiliconFlowClient.generate_json()
  -> LLM 返回 JSON
  -> 结果规范化 + Pydantic 校验
  -> TravelResponse
  -> PlanPage 渲染
```

## 3. 目录结构

### 3.1 前端

```text
frontend/src
├── pages
│   ├── HomePage.vue
│   └── PlanPage.vue
├── components
│   ├── BrandHero.vue
│   └── TripForm.vue
├── modules/travel
│   ├── components
│   ├── store.ts
│   ├── types.ts
│   └── mockData.ts
├── services
│   └── generatePlan.ts
├── router
│   └── index.ts
└── styles
    └── main.css
```

说明：

- `pages`：页面级组件
- `components`：通用组件
- `modules/travel`：旅行相关类型、状态和展示组件
- `services/generatePlan.ts`：前端 API 请求封装
- `mockData.ts`：保留前端 mock 数据结构参考，当前真实链路已改为请求后端

### 3.2 后端

```text
backend/app
├── api/v1
│   ├── dependencies.py
│   └── generate.py
├── core
│   ├── config.py
│   ├── errors.py
│   └── logging.py
├── integrations
│   └── siliconflow_client.py
├── prompts
│   └── generate_itinerary.py
├── schemas
│   └── travel.py
├── services
│   ├── fallback_service.py
│   └── travel_service.py
└── main.py
```

说明：

- `main.py`：FastAPI 入口、CORS、异常处理、健康检查
- `api/v1/generate.py`：生成接口路由
- `schemas/travel.py`：请求响应模型定义
- `services/travel_service.py`：生成主流程
- `services/fallback_service.py`：模板兜底
- `integrations/siliconflow_client.py`：LLM 客户端封装
- `prompts/generate_itinerary.py`：Prompt 构造

## 4. 前端设计

### 4.1 页面

#### 首页 `/`

由 [HomePage.vue](/Users/peteryao/projects/Travle_Agent/frontend/src/pages/HomePage.vue) 负责：

- 展示品牌信息
- 渲染 `TripForm`
- 校验基础输入
- 调用 `generatePlan`
- 成功后跳转 `/plan`

#### 结果页 `/plan`

由 [PlanPage.vue](/Users/peteryao/projects/Travle_Agent/frontend/src/pages/PlanPage.vue) 负责：

- 读取当前会话中的请求和结果
- 展示摘要、分天行程、预算、tips
- 支持复制结果
- 当没有结果时跳回首页

### 4.2 状态管理

[store.ts](/Users/peteryao/projects/Travle_Agent/frontend/src/modules/travel/store.ts) 中维护单例会话状态：

- `request`: 当前旅行请求
- `result`: 当前生成结果
- `loading`: 是否正在生成
- `error`: 错误信息
- `notice`: 页面提示信息

状态只存在前端内存中，刷新页面后不会保留。

### 4.3 前端 API 调用

[generatePlan.ts](/Users/peteryao/projects/Travle_Agent/frontend/src/services/generatePlan.ts) 通过 `fetch("/api/v1/generate")` 调用后端。

开发环境中，Vite 代理配置在 [vite.config.ts](/Users/peteryao/projects/Travle_Agent/frontend/vite.config.ts)：

- `/api/*` 转发到 `http://localhost:8000`

## 5. 后端设计

### 5.1 服务入口

[main.py](/Users/peteryao/projects/Travle_Agent/backend/app/main.py) 完成：

- FastAPI 应用初始化
- CORS 配置
- 自定义业务异常转 JSON
- `GET /healthz`
- 注册 `/api/v1/generate`

### 5.2 核心接口

#### `POST /api/v1/generate`

用途：

- 根据用户输入生成一份旅行行程

入口文件：

- [generate.py](/Users/peteryao/projects/Travle_Agent/backend/app/api/v1/generate.py)

处理流程：

1. FastAPI 接收请求
2. Pydantic 校验 `TravelRequest`
3. 依赖注入 `TravelService`
4. `TravelService.generate_plan()` 调用 LLM
5. 返回 `TravelResponse`

#### `GET /healthz`

用途：

- 健康检查

返回：

```json
{
  "status": "ok"
}
```

### 5.3 LLM 调用流程

[travel_service.py](/Users/peteryao/projects/Travle_Agent/backend/app/services/travel_service.py) 是后端核心编排层。

主流程：

1. 调用 `build_generate_messages()` 构造 prompt
2. 调用 `SiliconFlowClient.generate_json()` 请求 LLM
3. 对返回内容做 normalize
4. 用 `TravelResponse` 做二次校验
5. 校验天数是否与请求一致
6. 如果返回内容非法，最多重试 1 次
7. 如果仍失败，走 `FallbackService`

### 5.4 错误策略

- 请求参数非法：FastAPI 返回 `422`
- 缺少 API key / 鉴权失败：返回 `503`
- 上游超时 / 网络错误 / 5xx：返回 `502/503`
- LLM 返回 JSON 非法或字段不合法：重试一次，失败后走模板兜底

## 6. 数据定义

### 6.1 前后端共享请求结构

当前前端类型定义在 [types.ts](/Users/peteryao/projects/Travle_Agent/frontend/src/modules/travel/types.ts)，后端对应定义在 [travel.py](/Users/peteryao/projects/Travle_Agent/backend/app/schemas/travel.py)。

#### TravelRequest

```ts
type TravelRequest = {
  origin: string
  destination: string
  days: number
  budget?: string
  style?: string[]
  prompt?: string
}
```

字段说明：

- `origin`：出发地，必填
- `destination`：目的地，必填
- `days`：天数，必填，当前限制 `1-7`
- `budget`：预算，自由文本
- `style`：风格偏好数组
- `prompt`：额外补充需求

后端允许的 `style` 值：

- `relaxed`
- `photogenic`
- `foodie`
- `city walk`
- `nature`

### 6.2 返回结构

#### ItineraryDay

```ts
type ItineraryDay = {
  day: number
  title: string
  morning?: string
  afternoon?: string
  evening?: string
}
```

#### TravelResult / TravelResponse

```ts
type TravelResult = {
  mode: "itinerary"
  summary: string
  plan: {
    days: ItineraryDay[]
    budgetSummary?: string
    budgetBreakdown?: Record<string, string>
  }
  tips?: string[]
}
```

约束：

- `mode` 固定为 `itinerary`
- `plan.days.length` 必须等于请求中的 `days`
- `budgetBreakdown` 的 value 统一为字符串
- `tips` 最多保留 3 条

### 6.3 后端 Pydantic 模型

后端内部使用这些模型：

- `TravelStyle`
- `TravelRequest`
- `ItineraryDay`
- `TravelPlan`
- `TravelResponse`

模型职责：

- 校验请求
- 约束 LLM 输出
- 保证返回给前端的 JSON 稳定

## 7. Prompt 设计

Prompt 位于 [generate_itinerary.py](/Users/peteryao/projects/Travle_Agent/backend/app/prompts/generate_itinerary.py)。

结构分两部分：

- `system prompt`：定义角色和输出规则
- `user prompt`：填入用户的真实输入

关键约束：

- 只允许输出 JSON
- 必须包含 `mode`、`summary`、`plan`、`tips`
- 行程必须围绕用户给定目的地
- 文风简洁、可执行
- 避免明显折返

## 8. 配置与运行

### 8.1 后端环境变量

[.env.example](/Users/peteryao/projects/Travle_Agent/backend/.env.example) 中当前包含：

- `SILICONFLOW_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `CORS_ORIGINS`

### 8.2 本地运行

后端：

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm run dev
```

## 9. 当前边界

当前版本已实现：

- 首页输入
- 调用真实后端
- 调用真实 LLM
- 返回结构化旅行结果
- 结果页展示
- 错误提示
- LLM 输出异常时模板兜底

当前版本未实现：

- 登录
- 历史记录
- 数据库存储
- 结果保存
- 多版本行程
- 微调生成
- 地图、预订、支付
