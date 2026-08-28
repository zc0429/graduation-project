# 知错前端

“知错”是 AI 错题分析与学习推荐系统的 Vue 3 前端。界面采用纸张、批注与校勘符号组成的学习工作台视觉语言，正式运行不内置演示业务数据；Mock API 业务数据仅用于 `e2e/smoke` 与设计证据截图，单元测试替身也只存在于测试运行时。

## 技术栈与目录

- Vue 3.5、TypeScript、Vite 8
- Pinia、Vue Router、Axios
- Element Plus、ECharts
- Vitest、Vue Test Utils、Playwright、axe-core、Lighthouse

```text
src/
├── api/             # 按 auth/user/catalog/question/ai/learning/communication 拆分的接口
├── components/      # 品牌、导航、页面头、纸张面板、异步状态、掌握度等共享组件
├── composables/     # 有时限、可清理的 AI 解析轮询
├── layout/          # 桌面侧栏、顶部栏和移动底栏外壳
├── router/          # 懒加载路由、会话校验和角色守卫
├── store/           # JWT 与用户会话状态
├── styles/          # 设计变量、Element Plus 覆盖、焦点与减弱动效规则
├── types/           # 后端响应和领域类型
├── utils/           # Axios 解包、错误归一化、带认证文件下载
└── views/           # 学生、教师、管理员及通用页面
tests/               # Vitest 组件与单元测试
e2e/smoke/           # 路由级 Mock API 的 UI、响应式、浏览器与无障碍测试
e2e/integration/     # 连接 wrongbook_e2e 真实后端的关键流程测试
e2e/evidence/        # 明确标注 Mock 的桌面、平板和手机设计截图
```

完整组件、设计变量、路由和后端边界见 [前端架构说明](../docs/design/frontend-architecture.md)。

## 角色能力边界

| 角色 | 当前真实能力 | 不展示的能力 |
|---|---|---|
| 学生 | 错题增删改查、图片、JWT Excel 导出、AI 解析、同账号相似题、变式练习、到期/逾期复习、练习历史、个人周报 | 未来复习日历 |
| 教师 | 全站聚合周报、通用消息/公告/资料 | 班级/课程筛选、学生名单与学生钻取 |
| 管理员 | 用户查询与逻辑注销、科目新增/编辑、两级知识点增删、公告查看/发布 | 角色分配、账号恢复、科目删除、公告编辑/下线 |

`message`、`announcement`、`profile` 为登录后通用页面。前端角色路由只改善交互，服务端仍必须执行最终鉴权。

## 安装与启动

要求 Node.js 22；依赖版本以 `package-lock.json` 为准。

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project\web'
npm ci
npm run dev
```

前端默认运行在 `http://localhost:5173`，仅将 `/api` 代理到 `http://localhost:8080`。错题图片不提供匿名静态目录，已认证的题目详情接口会将本人图片转换为 Data URI 返回。除真实后端联调外，前端静态构建和 Mock UI 测试不需要启动 MySQL 或 Spring Boot。

## 构建与自动化检查

```powershell
npm run typecheck        # vue-tsc 类型检查
npm run test:unit        # Vitest 单元与共享组件测试
npm run build            # 类型检查后生成 dist/
npm run e2e:smoke        # Chromium，1600/1280/820/390 四档视口，API 路由模拟
npm run e2e:real-ai      # 默认跳过；仅显式开关后调用真实 GLM 并生成论文证据
npm run verify           # typecheck + unit + build + e2e:smoke
```

首次运行 Playwright，或 Playwright 版本更新后安装所需浏览器：

```powershell
npx playwright install chromium firefox
```

Chrome Stable 与 Microsoft Edge Stable 使用本机已安装渠道并运行完整桌面套件；Firefox 使用 Playwright 管理的浏览器并运行关键流程烟测：

```powershell
npm run e2e:browsers
```

生成与论文证据分离、带 Mock 标识的多端设计截图：

```powershell
npm run e2e:screenshots
```

单独执行 axe-core 无障碍检查：

```powershell
npm run e2e:a11y
```

失败时的 trace 和截图写入 `test-results/`。上述 UI 测试会拦截 `/api`，验证的是前端交互与状态，不可作为真实数据库或服务端权限已通过的证据。

真实 GLM 浏览器证据与上述 Mock 测试严格分离。启动真实 GLM 后端、注入临时密码、
显式 opt-in 以及证据数据保留规则见 [E2E 验收说明](e2e/README.md)，本轮结果见
[真实 GLM 浏览器业务 E2E 记录](../docs/validation/real-ai-e2e.md)。

## `wrongbook_e2e` 真实后端验收

`npm run e2e:integration` **只自动启动 4175 端口的前端**。运行它之前，必须在另一个终端把后端固定启动在 8080，并人工核对以下两项：

1. `DB_URL` 的数据库名精确为 `wrongbook_e2e`，不能是 `wrongbook` 或其他开发库。
2. `LLM_PROVIDER` 精确为 `mock`，真实 GLM/DeepSeek 密钥不得用于此验收。

测试会创建、编辑、练习、导出并删除一条带唯一时间戳的错题，也会登录教师和管理员种子账号。不要对日常开发库或生产库运行。

### 1. 创建或重置隔离库

以下 PowerShell 命令只允许作用于字面量 `wrongbook_e2e`。它会删除该测试库中的旧数据；如需保留数据，去掉 `DROP DATABASE`，只执行 `CREATE DATABASE IF NOT EXISTS`。

```powershell
$e2eDatabase = 'wrongbook_e2e'
if ($e2eDatabase -cne 'wrongbook_e2e') { throw '拒绝操作：数据库名必须精确为 wrongbook_e2e' }
$mysqlUser = Read-Host 'MySQL 测试账号'
mysql --protocol=TCP --host=127.0.0.1 --port=3306 "--user=$mysqlUser" --password --execute='DROP DATABASE IF EXISTS `wrongbook_e2e`; CREATE DATABASE `wrongbook_e2e` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
```

MySQL 客户端会交互式询问密码，密码不应写入命令、文档或仓库。

### 2. 用 Mock AI 启动后端

Windows 当前要求 `JAVA_HOME` 指向 JDK 21。下面通过当前终端环境变量覆盖全部验收配置，无需查看、修改或依赖 `.env`；启动前仍须保留数据库名与 Mock 提供方的显式校验：

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project\server'
if (-not $env:JAVA_HOME) { throw '请先让 JAVA_HOME 指向 JDK 21' }
& "$env:JAVA_HOME\bin\java.exe" --version

$dbCredential = Get-Credential -Message '输入 wrongbook_e2e 的 MySQL 凭据'
$env:DB_URL = 'jdbc:mysql://127.0.0.1:3306/wrongbook_e2e?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&useSSL=false'
$env:DB_USERNAME = $dbCredential.UserName
$env:DB_PASSWORD = $dbCredential.GetNetworkCredential().Password
$env:LLM_PROVIDER = 'mock'

if ($env:DB_URL -notmatch '/wrongbook_e2e(?:\?|$)') { throw '拒绝启动：DB_URL 未指向 wrongbook_e2e' }
if ($env:LLM_PROVIDER -cne 'mock') { throw '拒绝启动：LLM_PROVIDER 必须为 mock' }
.\mvnw.cmd spring-boot:run
```

Linux 使用同一组变量并保持 JDK 21：

```bash
cd server
export DB_URL='jdbc:mysql://127.0.0.1:3306/wrongbook_e2e?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&useSSL=false'
export DB_USERNAME='<测试账号>'
read -rsp 'MySQL 测试库密码: ' DB_PASSWORD && export DB_PASSWORD
export LLM_PROVIDER='mock'
test "$LLM_PROVIDER" = mock && printf '%s' "$DB_URL" | grep -q '/wrongbook_e2e?' || exit 1
./mvnw spring-boot:run
```

后端启动时会在隔离库内执行幂等的 `schema.sql` 和 `data.sql`。不要输出环境变量，也不要把凭据写进测试报告。

### 3. 执行真实联调

确认 `http://127.0.0.1:8080` 已由上述后端占用后，在新终端执行：

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project\web'
npm run e2e:integration
```

关键断言包括学生错题创建/编辑/练习/删除、Excel 下载请求携带 `Bearer` JWT、教师接口角色边界、私有图片访问边界和管理员真实管理入口。停用账号旧 JWT 的即时失效由后端自动化测试覆盖。

## Lighthouse 性能与可访问性复测

先构建并在独立终端启动预览：

```powershell
npm run build
npm run preview -- --host 127.0.0.1 --port 4176 --strictPort
```

再执行本地 Lighthouse（默认审计未登录的登录页）：

```powershell
npx lighthouse http://127.0.0.1:4176/login --only-categories=performance,accessibility,best-practices,seo --chrome-flags="--headless=new" --output=html --output-path=./test-results/lighthouse-login.html
```

认证后的学生首页使用临时测试凭据复测，不把密码、令牌写入脚本或报告：

```powershell
$lighthouseCredential = Get-Credential -Message '输入本地 Lighthouse 测试账号'
$env:LIGHTHOUSE_USERNAME = $lighthouseCredential.UserName
$env:LIGHTHOUSE_PASSWORD = $lighthouseCredential.GetNetworkCredential().Password
$env:LIGHTHOUSE_BASE_URL = 'http://127.0.0.1:4176'
npm run audit:lighthouse:auth
Remove-Item Env:LIGHTHOUSE_USERNAME, Env:LIGHTHOUSE_PASSWORD, Env:LIGHTHOUSE_BASE_URL
```

路由按页懒加载，ECharts 仅进入报告页后动态载入；仍应以当次构建和 Lighthouse 报告判断性能，不把旧分数当作永久结论。

## 状态与安全说明

- REST 响应统一解包 `{ code, message, data }`；HTTP/业务 401 会清理本地会话并返回登录页，网络失败不会误当成空数据。
- Excel 导出使用带 `Authorization: Bearer …` 的 Blob 请求，能识别 JSON 错误响应、清理文件名并及时释放临时 URL。
- AI 解析以非重叠轮询查询，默认最长 90 秒，并区分等待、成功、失败、超时和网络错误。
- 相似题与 RAG 候选已在查询层绑定原题所属学生，并保留结果层归属校验；正式前端按需请求同账号相似题。RAG 仍只显示参考 ID，不展开其他题目内容。
- 教师报告只有全站聚合范围，报告没有历史归档；练习历史接口也不返回完整题干。
- 服务端在每次认证请求中复核账号状态和数据库当前角色；账号停用后旧 JWT 即时失效，旧令牌中的角色声明不能覆盖数据库角色。
- 错题图片不暴露匿名静态地址；详情接口仅为题目所属学生返回内联 Data URI，替换和删除题目时会清理旧文件。

## 验收记录

以下为 2026-08-28 当前 `dev` 在 Windows 本机的验收快照；分数和数量不是永久保证，代码变化后必须重跑。浏览器兼容、axe-core、设计截图和 Lighthouse 行沿用 2026-08-25 的专项验收结果，未在本轮重复执行：

| 项目 | 当次结果 |
|---|---|
| `npm run typecheck` / `test:unit` / `build` | 类型检查与生产构建通过；Vitest 8 文件、23/23。Vite 仍提示主入口压缩后超过 500 kB |
| 四档响应式 Mock UI | 44/44；覆盖 1600×1200、1280×800、820×1180、390×844 |
| Chrome / Edge / Firefox | 59/59；Chrome 29、Edge 29 为完整桌面套件，Firefox 1 为关键烟测 |
| axe-core | 独立套件 3/3；登录、学生核心页、教师与管理员核心页无 serious/critical WCAG A/AA 问题 |
| `wrongbook_e2e` 真实联调 | 4/4；Spring Boot + MySQL + `LLM_PROVIDER=mock`，含 JWT Axios Blob 下载、教师直调 403 与私有图片边界 |
| 设计证据截图 | 10/10；桌面 5、平板 2、手机 3，全部带 Mock 标识并存于 `docs/design/vue-rebuild-screenshots/` |
| Lighthouse | 登录页 Performance 99 / Accessibility 100（FCP 693 ms，LCP 769 ms）；学生首页 99 / 100（FCP 744 ms，LCP 926 ms）；两页 TBT 0、CLS 0 |
