# 图片错题识别录入验证记录

> 验证日期：2026-08-28
> 分支：`codex/image-question-recognition`
> 基线：`origin/dev@5d1180933a9d8f665bc056ba097b0c22022300ee`

## 1. 范围与结论

本分支新增“图片错题识别录入”旁路：用户上传单题图片后，系统调用智谱
`glm-5.3-flash` 提取科目、题干、学生实际作答和来源，再回填现有
`QuestionCreateView`。识别不会自动创建 `Question`，最终保存仍走原
`POST /api/question`，创建后仍由原前端调用 `POST /api/ai/analyze/{id}`。

本轮没有修改数据库结构，没有新增 `student_answer`，没有修改现有
`LlmClient`、`OpenAiCompatibleLlmClient`、`glm-4.7-flash`、`embedding-3`、
RAG、Variant、ReviewPlan、Practice、Mastery 或 Gate4/Gate5 文件。

## 2. 真实 API Spike

### 2.1 实际调用方式

- 地址：`POST https://open.bigmodel.cn/api/paas/v4/chat/completions`
- 模型：`glm-5.3-flash`
- 图片：用户消息 `content` 中的 `image_url.url`，值为
  `data:image/png;base64,...`
- 输出：`response_format={"type":"json_object"}`
- 非流式：`stream=false`
- 思考：`thinking={"type":"enabled"}`、`reasoning_effort="low"`
- 鉴权：`Authorization: Bearer <API Key>`；Key 仅来自环境变量或未跟踪的
  `server/.env`，未写入代码、文档、日志或截图

### 2.2 参数验证过程

第一次真实请求沿用现有主链的 `thinking={"type":"disabled"}`，智谱返回
HTTP 400、错误码 `1210`：该模型始终思考，不支持关闭思考，并要求使用
`low/high/max`。这证明现有文本模型参数不能直接复用，也进一步支持使用独立
Client 的设计。

改为 `thinking.type=enabled + reasoning_effort=low` 后，同一张 19,326 字节的
PNG 单题图片连续三次成功，返回模型均为 `glm-5.3-flash`，三次结果均通过严格
四字段 JSON 校验：

```json
{
  "subjectName": "数学",
  "stem": "已知函数 f(x) = x² - 5x + 6。求方程 f(x) = 0 的解。",
  "studentAnswer": "x = 3",
  "source": "高一数学课堂练习"
}
```

三次成功请求 ID：

- `20260828095632b99f92bc3d054e82`
- `20260828095658c6232900f4c24248`
- `2026082809570020fdd58a1eb843ab`

对应延迟约 1,289 ms、1,425 ms、950 ms。图片中的学生答案是 `x = 3`，模型
没有把方程的另一个根或完整正确答案补入 `studentAnswer`。

## 3. 后端约束

- 新接口：`POST /api/question-recognition/recognize`
- 必须携带现有 JWT；真实未登录调用返回统一业务码 `401`
- 默认 `IMAGE_RECOGNITION_ENABLED=false`
- 仅接受单张 JPG/JPEG、PNG 或 WebP Data URI
- 服务端校验 Base64、5 MB 上限与 JPG/PNG/WebP 文件签名
- Prompt 中动态加入当前启用的 Subject 名称；返回科目仅做精确归一化匹配
- 非候选科目统一返回 `subjectId=null, subjectName=null`，不创建新科目
- 模型响应必须且只能包含 `subjectName/stem/studentAnswer/source` 四字段
- `stem` 为空、缺字段、非 JSON、字段类型或长度非法时拒绝结果
- 超时/网络、429、5xx 和其他上游错误均映射为不含上游敏感信息的统一业务错误
- 识别过程不保存图片，不调用 Question、ReviewPlan、AiAnalysis、Variant、
  Embedding、RAG 或 Practice 写入链

## 4. 8 图真实接口 QA

本轮在系统临时目录生成 8 张小型工程 QA 图片，未写入 Gate5 数据集或仓库。
它们是合成输入，只用于验证格式和边界，不替代后续真实手机照片/真实手写样本验收。

| 样本 | 格式 | 场景 | 首轮结果 | 延迟 |
|---|---|---|---|---:|
| 01 | PNG | 清晰数学单题 | 通过，数学，题干/作答/来源正确 | 2699 ms |
| 02 | PNG | 数学公式 | 通过，数学，`x = 3` 仅作为学生作答 | 1148 ms |
| 03 | PNG | 物理题 | 通过，物理，保留图片中的错误作答 `F = 5 N` | 1132 ms |
| 04 | PNG | 纯文本英语选择题 | 通过，英语，学生作答 `B` | 1438 ms |
| 05 | JPG | 手机照片风格 | 通过，数学，题干/作答/来源正确 | 1059 ms |
| 06 | PNG | 手写字体风格作答 | 通过，数学，保留错误作答 `54` | 1896 ms |
| 07 | PNG | 无学生答案 | 首轮业务码 400；立即单独重试成功，`studentAnswer=null` | 首轮 264 ms |
| 08 | JPG | 轻微模糊低分辨率 | 通过，数学，题干/作答/来源正确 | 1362 ms |

首轮为 7/8；样本 07 的立即重试成功。首轮失败响应在批处理输出中未保留具体
message，因此不能武断归因为 429、瞬时平台拒绝或结构波动。该失败被如实保留，
前端在此类情况下显示“识别失败”，用户仍可手工录入。

## 5. 数据副作用核验

使用真实学生 JWT 调用新增接口前后，五类业务记录计数完全一致：

| 表 | 调用前 | 调用后（含样本 07 重试） |
|---|---:|---:|
| `question` | 32 | 32 |
| `review_plan` | 25 | 25 |
| `ai_analysis` | 32 | 32 |
| `variant_question` | 6 | 6 |
| `practice_record` | 1 | 1 |

识别阶段也没有写入 `server/uploads/`。测试后端与用户态 MySQL 均在验证后停止。

## 6. 自动化回归

### 后端

- 全量 Maven：61 项，57 passed，0 failures，0 errors，4 skipped
- skipped 均为默认关闭的真实入口，其中新增
  `LiveQuestionRecognitionTests` 仅在
  `RUN_LIVE_IMAGE_RECOGNITION_TESTS=true` 时联网
- 新增离线测试覆盖：合法结构化响应、缺字段、非法 JSON、非法科目、空题干、
  disabled、非法/伪造/过大图片、网络超时、429、5xx、JWT 和无业务写入

### 前端

- `npm run typecheck`：通过
- Vitest：8 files、23/23 passed
- production build：通过
- Playwright Mock smoke：44/44 passed
- 新增浏览器覆盖：无图片禁用、loading 防重复、成功回填科目/题干/来源、
  `studentAnswer` 不污染 `answer`、不自动提交、失败后手工保存，以及桌面/笔记本/
  平板/手机四档无横向溢出

## 7. 已知风险与后续人工验收

1. 合成样本不能代表真实拍照中的透视、阴影、反光、复杂手写和公式排版；独立 Review
   前建议由用户补 3–5 张不含隐私的真实单题照片复测。
2. 首轮 8 图 QA 有 1 次未分类的瞬时失败，不能宣称接口 100% 稳定；产品行为已保证
   失败可见且手工录入不受影响。
3. 第一阶段不持久化学生原作答；如后续确需 `student_answer`，应作为另一个独立决策，
   不能接入现有分析 Prompt、Embedding、RAG 或 Gate5。
4. 本分支等待独立 Review，不自行合并 `dev`。
