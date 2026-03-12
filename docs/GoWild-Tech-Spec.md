# GoWild MVP 技术方案

## 1. 目标

GoWild 第一版采用前后端分离架构。

目标是用尽量简单的方式跑通这条最小闭环：

1. 用户输入需求
2. 系统生成行程
3. 用户查看结果

技术原则：

- Less is more
- 前后端职责清晰
- 先跑通核心链路，再补能力
- 不做过度工程化

## 2. 技术栈

### 前端

- Vue 3
- TypeScript
- Vite
- Vue Router
- Tailwind CSS

选择原因：

- 轻量，适合快速搭建 MVP
- 组件开发效率高
- 适合纯前端应用，边界清晰

### 后端

- FastAPI
- Pydantic
- Uvicorn

选择原因：

- 适合快速搭建 API 服务
- 类型清晰，数据校验简单
- 非常适合承接 AI 调用和业务编排

### AI 能力

- OpenAI 兼容 API

选择原因：

- 第一版优先验证效果和体验
- 模型调用、Prompt、密钥统一放后端管理
- 通过环境变量切换不同服务商，避免绑定单一平台

### 数据存储

- MVP 第一版先不强制接数据库
- 当前会话以内的数据可由前端保存
- 后端保持无状态

后续如需要保存历史记录，再引入数据库。

### 部署

- 前端：Vercel 或 Netlify
- 后端：Render、Railway 或自托管

## 3. 整体架构

采用标准前后端分离：

- 前端负责页面、交互、状态展示
- 后端负责接口、AI 调用、结果组装
- 前端只通过 HTTP 请求后端 API

基础结构：

1. 用户在前端输入旅行需求
2. 前端调用后端生成接口
3. 后端拼装 prompt 并调用模型
4. 后端返回结构化行程结果
5. 前端渲染行程结果

## 4. 职责划分

### 前端职责

- 输入旅行需求
- 展示行程结果
- 管理当前会话状态
- 发起生成请求
- 处理 loading 和错误提示

### 后端职责

- 校验请求参数
- 调用模型生成行程
- 统一处理 Prompt、解析和错误兜底
- 返回稳定 JSON 给前端

## 5. 页面设计

### 5.1 首页 `/`

目标：快速开始

模块：

- 品牌区
- 出发地输入（必填）
- 目的地输入（必填）
- 天数输入（必填）
- 预算输入（可选）
- 风格选择（可选）
- 自由输入框（可选）
- 开始生成按钮

### 5.2 结果页 `/plan`

目标：展示生成的行程

模块：

- 当前需求摘要
- 行程区
- 预算摘要
- 注意事项
- 复制结果按钮

## 6. 前端结构建议

建议结构：

- `src/pages`：页面
- `src/components`：通用组件
- `src/modules/travel`：旅行相关业务组件和类型
- `src/services`：API 请求封装
- `src/router`：路由配置
- `src/styles`：全局样式和设计变量

建议页面：

- `HomePage`
- `PlanPage`

建议核心组件：

- `TripForm`
- `ItineraryCard`
- `PlanSummary`
- `BudgetSummary`
- `TipsList`

## 7. 后端结构建议

建议结构：

- `app/main.py`：服务入口
- `app/api`：路由层
- `app/schemas`：请求响应模型
- `app/services`：业务逻辑
- `app/integrations`：LLM 调用封装
- `app/prompts`：Prompt 模板
- `app/core`：配置、日志、常量

建议 API 模块：

- `generate.py`

建议服务模块：

- `travel_service.py`
- `llm_service.py`

建议补充：

- `app/core/config.py`：环境变量读取
- `app/integrations/llm_client.py`：统一模型客户端

## 8. API 设计

第一版只做 1 个核心接口。

接口前缀建议统一为：

- `/api/v1`

### 8.1 `POST /api/v1/generate`

用途：

- 根据用户输入生成行程规划

请求示例：

```json
{
  "origin": "Shanghai",
  "destination": "Hangzhou",
  "days": 2,
  "budget": "1000-1500",
  "style": ["relaxed", "photogenic"],
  "prompt": "周末想出去透透气，不想太累"
}
```

返回示例：

```json
{
  "mode": "itinerary",
  "summary": "杭州2天1晚轻松游",
  "plan": {
    "days": [
      {
        "day": 1,
        "title": "西湖漫步",
        "morning": "抵达杭州，前往西湖",
        "afternoon": "环湖骑行，游览苏堤",
        "evening": "河坊街逛吃"
      },
      {
        "day": 2,
        "title": "灵隐祈福",
        "morning": "灵隐寺祈福",
        "afternoon": "返回上海"
      }
    ],
    "budgetSummary": "预算约1200元/人",
    "budgetBreakdown": {
      "交通": "300元",
      "餐饮": "400元",
      "门票": "200元",
      "住宿": "300元"
    }
  },
  "tips": ["建议避开周末高峰期", "记得带伞"]
}
```

规则：

- 出发地、目的地、天数为必填
- 后端始终返回单一行程规划结果
- 第一版不返回目的地推荐
- 第一版不支持微调

## 9. AI 输出策略

后端必须要求模型输出结构化 JSON，避免前端直接消费自由文本。

核心字段建议固定为：

- `mode`
- `summary`
- `plan`
- `tips`

### 行程模式

输出：

- 行程摘要
- 按天安排
- 预算摘要（包含分项）
- 注意事项

约束：

- 第一版只支持 `itinerary` 一种结果类型
- 输出围绕用户已填写的目的地展开
- 不生成候选目的地
- 不生成后续追问

## 10. AI Provider 配置

第一版 AI 能力应支持通过环境变量切换服务商，而不是把代码写死到某一家。

建议后端统一采用一层 LLM Client 封装，前面业务只关心：

- 用哪个模型
- 传什么 prompt
- 拿回什么结构化结果

底层 provider 通过环境变量决定。

建议环境变量：

```env
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
LLM_TIMEOUT=60
```

说明：

- `LLM_PROVIDER`：当前使用的服务商标识，如 `openai`、`openrouter`、`siliconflow`
- `LLM_API_KEY`：对应服务商的密钥
- `LLM_BASE_URL`：服务商接口地址
- `LLM_MODEL`：当前默认模型
- `LLM_TIMEOUT`：请求超时时间

设计要求：

- 业务层不得直接依赖某个固定 provider SDK
- 所有模型调用统一走 `llm_client.py`
- 默认支持 OpenAI 兼容接口
- 后续如有必要，再增加 provider 特殊适配

推荐实现方式：

1. 在 `config.py` 中读取环境变量
2. 在 `llm_client.py` 中初始化统一客户端
3. 在 `llm_service.py` 中提供生成文本或结构化结果的方法
4. `travel_service.py` 只调用 `llm_service.py`

## 11. 状态设计

### 前端状态

第一版由前端维护当前会话状态：

- 表单输入
- 当前请求参数
- 当前返回结果

建议使用：

- `ref`
- `reactive`
- `computed`

第一版不建议引入复杂状态库，也不需要维护多轮对话上下文。

### 后端状态

- 第一版保持无状态

## 12. 数据结构建议

### 12.1 前端类型

```ts
export type TravelRequest = {
  origin: string;
  destination: string;
  days: number;
  budget?: string;
  style?: string[];
  prompt?: string;
};
```

```ts
export type ItineraryDay = {
  day: number;
  title: string;
  morning?: string;
  afternoon?: string;
  evening?: string;
};
```

```ts
export type TravelResult = {
  mode: "itinerary";
  summary: string;
  plan: {
    days: ItineraryDay[];
    budgetSummary?: string;
    budgetBreakdown?: Record<string, string>;
  };
  tips?: string[];
};
```

### 12.2 后端模型

建议在 FastAPI 中使用 Pydantic 定义：

- `TravelRequest`
- `GenerateResponse`
- `TravelResult`

## 13. Prompt 设计

第一版建议一套 Prompt：

- `generate_prompt`

要求：

- 输出 JSON
- 行程节奏合理
- 包含预算分项
- 不要输出冗余内容
- 严格围绕表单输入生成结果

Prompt 模板统一放在后端管理。

## 14. 错误处理

至少处理这些情况：

- 用户输入缺失
- 模型超时
- 模型输出格式错误
- 后端接口异常

前端表现：

- 展示简洁错误提示
- 支持重试
- 不暴露内部错误细节

后端表现：

- 记录错误日志
- 统一返回标准错误结构

## 15. 开发顺序建议

### Phase 1

- 初始化 Vue 3 + Vite 前端
- 初始化 FastAPI 后端
- 建立基础目录结构
- 接入环境变量配置

### Phase 2

- 完成首页和结果页静态结构
- 定义前后端类型
- 用假数据跑通页面展示

### Phase 3

- 接入 `/api/v1/generate`
- 跑通行程生成
- 跑通可配置 provider 的 LLM 调用

### Phase 4

- 补 loading、错误提示、复制结果
- 部署测试版

## 16. 第一版明确不做

- 目的地推荐
- 微调
- 登录
- 历史记录
- 收藏
- 分享
- 地图路线
- 实时天气
- 酒店机票接入
- 数据库持久化

## 17. 当前推荐结论

GoWild 第一版推荐采用：

- 前端：`Vue 3 + TypeScript + Vite + Vue Router + Tailwind CSS`
- 后端：`FastAPI + Pydantic`
- AI：`OpenAI 兼容 API + 环境变量切换 provider`
- 架构：`前后端分离`
- 状态：`前端持有单次表单和结果，后端无状态`

这套方案足够轻，边界清晰，也适合后续继续扩展。
