# GoWild 架构文档

## 1. 概览

GoWild 当前采用前后端分离架构：

- 前端：Vue 3 + TypeScript + Vite
- 后端：FastAPI + Pydantic + Uvicorn
- Agent Runtime：单 Agent 规划链路，基于通用 `BaseAgent`
- LLM Provider：当前默认使用 SiliconFlow

当前闭环是：

1. 用户输入旅行需求
2. 前端请求后端生成接口
3. 后端通过 `PlanAgent` 编排一次规划
4. Agent 通过已注册工具调用 LLM
5. 后端将结果规范化为稳定 JSON
6. 前端展示行程结果

第一版不接数据库，后端保持无状态；当前会话状态仍由前端保存。

## 2. 架构分层

### 2.1 前端职责

- 展示首页与结果页
- 管理当前请求、结果、loading、错误信息
- 调用 `/api/v1/generate`
- 渲染摘要、行程、预算和 tips

### 2.2 后端职责

- 校验请求参数
- 通过 Agent 层完成一次规划
- 通过 Tool Registry 调用工具
- 通过 Provider Registry 调用默认 LLM provider
- 对模型输出做 normalize 和校验
- 在模型输出异常时走 fallback
- 返回稳定的 `TravelResponse`

### 2.3 调用链路

```text
TripForm
  -> generatePlan()
  -> POST /api/v1/generate
  -> PlanAgent.generate_result()
  -> BaseAgent.run()
  -> build_goal / plan / act / observe / finalize
  -> ToolRegistry.execute("llm_generate_itinerary")
  -> ItineraryGenerationService.generate()
  -> ProviderRegistry.get("siliconflow")
  -> SiliconFlowProvider.generate_json()
  -> PlanAssemblyService.assemble()
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

### 3.2 后端

```text
backend/app
├── agents
│   ├── base.py
│   ├── plan_agent.py
│   ├── registry.py
│   └── runtime.py
├── api/v1
│   ├── agent.py
│   ├── dependencies.py
│   └── generate.py
├── core
│   ├── config.py
│   ├── errors.py
│   └── logging.py
├── integrations
│   └── siliconflow_client.py
├── models
│   ├── agent.py
│   └── travel.py
├── prompts
│   └── generate_itinerary.py
├── providers
│   ├── base.py
│   ├── registry.py
│   └── siliconflow.py
├── schemas
│   └── travel.py
├── services
│   ├── fallback_service.py
│   ├── itinerary_generation_service.py
│   └── plan_assembly_service.py
├── tools
│   ├── adapters.py
│   ├── base.py
│   └── registry.py
└── main.py
```

### 3.3 各层职责

- `agents/`
  - `BaseAgent` 定义统一执行模板
  - `PlanAgent` 定义旅行规划特有逻辑
  - `AgentRuntime` 负责 step trace 和日志
  - `AgentRegistry` 负责按名称获取 agent
- `providers/`
  - 定义统一的 LLM provider 抽象
  - 当前注册 `siliconflow`
- `tools/`
  - 定义强类型 `ToolSpec`
  - 负责工具注册、执行与 schema 适配
- `services/`
  - `ItineraryGenerationService` 负责 prompt + provider 调用
  - `PlanAssemblyService` 负责结果规范化与校验
  - `FallbackService` 负责模板兜底
- `models/`
  - 存放产品模型和 agent 内部模型
- `schemas/`
  - 当前作为兼容导出层，内部实际模型定义已迁到 `models/`

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

[store.ts](/Users/peteryao/projects/Travle_Agent/frontend/src/modules/travel/store.ts) 维护单例会话状态：

- `request`
- `result`
- `loading`
- `error`
- `notice`

状态仅保存在前端内存中，刷新后不会保留。

### 4.3 前端 API 调用

[generatePlan.ts](/Users/peteryao/projects/Travle_Agent/frontend/src/services/generatePlan.ts) 通过 `fetch("/api/v1/generate")` 调用后端。

开发环境中，Vite 代理配置在 [vite.config.ts](/Users/peteryao/projects/Travle_Agent/frontend/vite.config.ts)：

- `/api/*` 转发到 `http://localhost:8000`

## 5. 后端设计

### 5.1 服务入口

[main.py](/Users/peteryao/projects/Travle_Agent/backend/app/main.py) 负责：

- FastAPI 应用初始化
- CORS 配置
- 自定义业务异常转 JSON
- `GET /healthz`
- 注册 `/api/v1/generate`
- 注册 `/api/v1/agent/plan`

### 5.2 核心接口

#### `POST /api/v1/generate`

用途：

- 兼容产品接口，直接返回 `TravelResponse`

处理流程：

1. 接收 `TravelRequest`
2. 注入 `PlanAgent`
3. 调用 `PlanAgent.generate_result()`
4. 返回 `TravelResponse`

#### `POST /api/v1/agent/plan`

用途：

- 返回 agent 风格的包装结果

返回结构：

- `request_id`
- `status`
- `result`

#### `GET /healthz`

用途：

- 健康检查

返回：

```json
{
  "status": "ok"
}
```

### 5.3 Agent 执行流程

[base.py](/Users/peteryao/projects/Travle_Agent/backend/app/agents/base.py) 定义统一执行模板：

1. 创建 `request_id`
2. 初始化 `AgentContext`
3. 执行 `build_goal`
4. 执行 `plan`
5. 执行 `act`
6. 执行 `observe`
7. 执行 `finalize`
8. 记录 trace 和 latency

当 `observe` 阶段出现 JSON 结构异常、字段校验异常等问题时：

- 最多重试 1 次
- 再失败则调用 fallback

[plan_agent.py](/Users/peteryao/projects/Travle_Agent/backend/app/agents/plan_agent.py) 的当前逻辑：

- `build_goal`：生成旅行规划目标
- `plan`：固定选择 `llm_generate_itinerary`
- `act`：通过 `ToolRegistry` 执行工具
- `observe`：调用 `PlanAssemblyService`
- `fallback_if_needed`：调用 `FallbackService`

### 5.4 Provider 层

当前 Provider 抽象定义在 [base.py](/Users/peteryao/projects/Travle_Agent/backend/app/providers/base.py)：

- `generate_json(messages, model=None, **kwargs) -> dict`

当前实现：

- `SiliconFlowProvider`

Provider 注册在 [dependencies.py](/Users/peteryao/projects/Travle_Agent/backend/app/api/v1/dependencies.py) 中完成：

- `ProviderRegistry(default_provider="siliconflow")`

### 5.5 Tool 层

工具系统由 [base.py](/Users/peteryao/projects/Travle_Agent/backend/app/tools/base.py) 和 [registry.py](/Users/peteryao/projects/Travle_Agent/backend/app/tools/registry.py) 提供。

当前 `ToolSpec` 包含：

- `name`
- `description`
- `input_model`
- `output_model`
- `executor`
- `retryable`
- `timeout_seconds`

当前已注册工具：

- `llm_generate_itinerary`

这个工具当前对应：

- 输入：`TravelRequest`
- 输出：`LLMGenerateItineraryOutput`
- 执行器：`ItineraryGenerationService.generate`

另外 [adapters.py](/Users/peteryao/projects/Travle_Agent/backend/app/tools/adapters.py) 预留了 `ToolSpec -> OpenAI tool schema` 的适配函数，方便后续切到 function calling 模式。

### 5.6 错误策略

- 请求参数非法：FastAPI 返回 `422`
- 缺少 API key / 鉴权失败：返回 `503`
- 上游超时 / 网络错误 / 5xx：返回 `502/503`
- LLM 返回 JSON 非法或字段不合法：重试一次，失败后走模板兜底

## 6. 数据定义

### 6.1 产品层请求结构

前端类型定义在 [types.ts](/Users/peteryao/projects/Travle_Agent/frontend/src/modules/travel/types.ts)，后端对应模型在 [travel.py](/Users/peteryao/projects/Travle_Agent/backend/app/models/travel.py)。

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
- `days`：天数，必填，限制 `1-7`
- `budget`：预算，自由文本
- `style`：风格偏好数组
- `prompt`：补充需求

允许的 `style`：

- `relaxed`
- `photogenic`
- `foodie`
- `city walk`
- `nature`

### 6.2 产品层返回结构

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

#### TravelResponse

```ts
type TravelResponse = {
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
- `days.length` 必须等于请求中的 `days`
- `tips` 最多保留 3 条
- `budgetBreakdown` 的值统一为字符串

### 6.3 Agent 内部模型

[agent.py](/Users/peteryao/projects/Travle_Agent/backend/app/models/agent.py) 当前包含：

- `AgentInput`
  - 包装单次请求和 `request_id`
- `AgentStep`
  - 记录生命周期步骤和执行状态
- `AgentContext`
  - 记录 `request_id`、`agent_name`、`provider_name`、`attempt`、`tool_results`、`tool_calls`、`provider_calls`、`steps`
- `ToolCallRecord`
  - 记录工具调用名称、是否可重试、是否成功
- `ProviderCallRecord`
  - 预留 provider 调用记录
- `AgentOutput`
  - 包含 `request_id`、`result`、`fallback_used`、`latency_ms`、`agent_name`、`provider_name`
- `AgentPlanResponse`
  - `/api/v1/agent/plan` 的对外响应包装

### 6.4 中间输出模型

[itinerary_generation_service.py](/Users/peteryao/projects/Travle_Agent/backend/app/services/itinerary_generation_service.py) 中定义：

- `LLMGenerateItineraryOutput`

它表示工具层对 LLM 原始结构化输出的宽松约束，后续再由 `PlanAssemblyService` 归一化成严格的 `TravelResponse`。

## 7. Prompt 设计

Prompt 位于 [generate_itinerary.py](/Users/peteryao/projects/Travle_Agent/backend/app/prompts/generate_itinerary.py)。

当前通过：

- `build_planner_messages(request)`

生成给 provider 的消息数组，结构为：

- `system prompt`
  - 定义角色、输出规则和 JSON 约束
- `user prompt`
  - 注入出发地、目的地、天数、预算、风格、补充需求

核心要求：

- 只输出 JSON
- 围绕用户给定目的地规划
- 输出必须能被后端组装为 `TravelResponse`

## 8. 配置与运行

### 8.1 环境变量

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

### 8.3 测试

后端测试：

```bash
cd backend
uv run pytest
```

当前测试覆盖：

- `/api/v1/generate`
- `/api/v1/agent/plan`
- `PlanAgent`
- `AgentRegistry`
- `ToolRegistry`
- `ProviderRegistry`
- `SiliconFlow` provider 错误映射

## 9. 日志与可观测性

当前日志主要输出到启动后端的终端。

关键日志包括：

- `agent_run`
  - 包含 `request_id`、`agent`、`provider`、`attempts`、`fallback`、`latency_ms`、`tools`、`steps`
- `agent_observe_failed`
  - 表示结果解析或校验失败
- `agent_fallback`
  - 表示进入模板兜底

## 10. 当前边界

当前已实现：

- 单 Agent 旅行规划
- BaseAgent 通用执行框架
- Agent Registry
- Provider 抽象与 SiliconFlow 实现
- ToolSpec / ToolRegistry
- LLM 输出规范化与 fallback
- 兼容旧产品接口和 agent 接口

当前未实现：

- 多 agent 协作
- 按请求切换 provider
- 真实地图工具
- 数据库存储
- 登录与历史记录
- 流式规划结果
