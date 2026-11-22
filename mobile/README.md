# 学生端微信小程序交付报告

交付日期为 2026-11-22。开发分支为 `codex/mobile-miniapp-20261122`，起点为 `claude/thesis-voice-cleanup-20261117` 的 `a52dc36eaff4ca3c001e689667cc8cd00485365e`。完整分支头提交号见交付消息和 GitHub 提交记录。检出交付分支后可执行 `git rev-parse HEAD` 复核。[GitHub 分支头与提交记录](https://github.com/zc0429/graduation-project/commits/codex/mobile-miniapp-20261122/)

## 运行说明

1. 准备 Node.js 22.12 或以上、JDK 21、MySQL 8 和微信开发者工具。开发使用已有后端的 `dev` profile。先创建 MySQL 开发数据库，再设置 `DB_URL`、`DB_USERNAME`、`DB_PASSWORD`，进入仓库根目录下的 `server/` 执行 `./mvnw spring-boot:run`。Windows 执行 `mvnw.cmd spring-boot:run`。后端在启动时执行 `server/src/main/resources/db/schema.sql` 和 `data.sql`。建议后端进程使用 `Asia/Shanghai` 时区，以对齐页面的中国时区日期和后端每日统计。
2. 小程序默认后端地址为 `http://127.0.0.1:8080/api`，定义在 `mobile/src/config.js`。可从 `mobile/.env.example` 复制得到 `mobile/.env.local`，将 `VITE_API_BASE_URL` 改为含 `/api` 的后端地址。地址在构建时注入，修改后重新构建。
3. 进入 `mobile/` 执行 `npm ci` 和 `npm run build:mp-weixin`。在微信开发者工具选择「导入项目」，项目目录选 `mobile/dist/build/mp-weixin/`。需要监听源码时执行 `npm run dev:mp-weixin`，开发产物在 `mobile/dist/dev/mp-weixin/`。
4. 微信 AppID 的测试占位为 `touristappid`。若使用微信分配的测试号或正式 AppID，在 `mobile/src/manifest.json` 替换 `mp-weixin.appid` 后重新构建，也可在开发者工具导入时选择对应 AppID。顶层 `appid` 是 uni-app 项目标识。开发者工具使用本机 HTTP 后端时，在项目本地设置勾选「不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书」。真机和发布环境应配置手机可达的 HTTPS 后端，并将域名加入微信小程序的 request 合法域名。
5. 测试学生账号 `student`、密码 `123456` 来自 `server/src/main/resources/db/data.sql`，仅用于本机隔离库。图片识题需在后端提供 `IMAGE_RECOGNITION_API_KEY` 或 `LLM_API_KEY`。AI 解析、知识生成和题池耗尽后的新变式题生成使用后端的 `LLM_API_KEY`。密钥留在服务端环境变量或 `server/.env`。

## 页面与现有接口

所有业务请求复用已有响应结构。鉴权请求携带 `Authorization: Bearer <JWT>`，收到 HTTP 401 或业务码 401 后清理本地会话并回到登录页。登录成功后仅学生进入小程序。退出登录清除本地 JWT。

| 页面 | 方法与路径 | 用途 |
|---|---|---|
| 登录 `pages/login/index` | `POST /api/auth/login` | 账号密码登录并保存学生 JWT |
| 首页 `pages/home/index` | `GET /api/user/profile`、`GET /api/report/weekly`、`GET /api/review-plan/today` | 校验恢复的学生会话，显示错题总数、今日练习次数和到期或逾期待复习数 |
| 错题列表 `pages/questions/index` | `GET /api/subject/list`、`GET /api/question/page` | 通过 `subjectId` 筛选，通过 `pageNum` 和 `pageSize` 分页加载 |
| 错题详情 `pages/detail/index` | `GET /api/question/{id}`、`GET /api/subject/list`、`GET /api/ai/analysis/{questionId}`、`POST /api/ai/analyze/{questionId}` | 查看原题、题图、录入答案和 AI 解析。支持发起、轮询和重试解析 |
| 错题录入 `pages/create/index` | `GET /api/subject/list`、`POST /api/question-recognition/recognize`、`POST /api/question` | 手录或从相册识别。识别返回候选，用户可采纳、修改或忽略，仅在确认保存时创建错题 |
| 知识学习 `pages/knowledge/index` | `POST /api/learning/knowledge/{questionId}` | 读取原题关联的讲解，后端负责缓存复用和按需生成 |
| 练习作答 `pages/practice/index` | `POST /api/learning/practice/next/{questionId}`、`GET /api/question/{id}`、`POST /api/practice`、`GET /api/ai/analysis/{questionId}` | 取得未练原题或变式题，核对答案、提交自评、查看记录和原题解析。练习原题时读取题图 |
| 复习计划 `pages/review/index` | `GET /api/review-plan/today`、`GET /api/subject/list` | 显示今日到期和逾期未完成的计划 |
| 复习作答，复用 `pages/practice/index?reviewId=…` | `GET /api/review-plan/today`、`GET /api/question/{id}`、`POST /api/practice`、`PUT /api/review-plan/{id}/finish`、`GET /api/ai/analysis/{questionId}` | 核对待复习计划并重做原题，保存作答后回写任务状态。当前页可单独重试完成回写 |
| 我的 `pages/profile/index` | `GET /api/user/profile` | 查看个人资料并本地退出登录 |

练习结果由学生对照答案自评，后端记录 `isCorrect` 并更新掌握度。推荐顺序由原有后端接口决定，依次查找未练原题、未练已有变式题，题池耗尽时再生成。变式题接口提供参考答案。页面同时提供标明来源的原题 AI 解析，现有接口无变式题独立解析字段。

## 端侧功能对照（论文第 5 章）

| 角色与功能 | PC 网页端 | 微信小程序端 |
|---|---|---|
| 学生账号与资料 | 注册、登录、查看和编辑个人资料、退出登录 | 登录、查看个人资料、退出登录 |
| 学生学情 | 首页概览、学情周报 | 首页展示错题总数、待复习数和今日练习次数 |
| 学生错题 | 手工与图片识别录入、错题筛选分页、详情、AI 解析、编辑、删除、导出 | 手工与相册图片识别录入、按科目筛选分页、详情、AI 解析 |
| 学生知识学习与练习 | 知识讲解、未练题优先推荐、变式练习、显式重做、相似题与练习历史 | 知识讲解、未练题优先推荐、变式练习与自评结果。复习入口可重做计划对应原题 |
| 学生复习 | 到期及逾期清单、原题重做、自评与计划完成 | 到期及逾期清单，重做并保存自评后更新完成状态 |
| 公告和消息 | 学生查看公告与站内消息 | — |
| 教师 | PC 端查看全站聚合学情周报 | — |
| 管理员 | PC 端查询及注销用户、维护科目与知识点、查看及发布公告 | — |

## 构建与本地联调记录

联调环境为 Linux、Node.js `24.22.3`、npm `11.19.1`、JDK `21.0.2`、MySQL `8.4.13` 和 Spring Boot `3.5.16`。后端使用 `dev` profile、`LLM_PROVIDER=glm` 和 `IMAGE_RECOGNITION_ENABLED=true`。通过微信构建产物执行真实 HTTP 请求，验证脚本适配了 Node.js 中的微信网络接口、存储和导航调用。变式题和复习日期由脚本在隔离 MySQL 中准备，用于检验既有接口对持久化数据的推荐与状态更新。全部 API 响应来自启动后的 Spring Boot。

| 实际执行 | 结果 |
|---|---|
| `cd mobile && npm ci --no-audit --no-fund --cache /workspace/work/npm-cache` | 退出 0，安装 530 个包。npm 输出传递依赖 `phin` 的弃用提示及 3 个安装脚本提示 |
| `cd mobile && npm run build:mp-weixin` | 退出 0，编译器 `5.34（vue3）` 输出 `DONE  Build complete.`，产物位于 `dist/build/mp-weixin` |
| `cd mobile && VITE_API_BASE_URL=https://miniapp.example.invalid/api/ npm run build:mp-weixin` | 退出 0，在生成的配置中断言地址已替换并去除尾部斜线。随后重建默认本地地址的产物 |
| 校验产物 `app.json`、`project.config.json` 和所有页面、组件的 JS、JSON、WXML | 9 个页面、4 个共享组件、4 个 tab 和 `touristappid` 校验通过 |
| `docker run -d --name wrongbook-mobile-20261122 … -p 127.0.0.1:33306:3306 mysql:8.4` | 临时 MySQL 启动，连接库为 `wrongbook_mobile` |
| `cd server && JAVA_HOME=/workspace/work/jdk-21.0.2 MAVEN_OPTS=-Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts ./mvnw -s /workspace/work/maven-settings.xml -U -Dmaven.repo.local=/workspace/work/m2 -B -ntp -Dmaven.test.skip=true package` | `BUILD SUCCESS`，产出 `target/wrongbook-server-0.0.1-SNAPSHOT.jar` |
| `cd server && TZ=Asia/Shanghai … /workspace/work/jdk-21.0.2/bin/java -jar target/wrongbook-server-0.0.1-SNAPSHOT.jar --server.address=127.0.0.1` | Tomcat 监听 8080，`GET /api/health` 返回 `{"code":0,"message":"success","data":{"status":"ok"}}`，隔离库包含 11 张表 |
| `TMPDIR=/workspace/work MOBILE_TEST_DB_CONTAINER=wrongbook-mobile-20261122 node mobile/scripts/verify-local.cjs` | 退出 0，输出 `PASS real HTTP and MySQL core flows` |

末次联调在同一个隔离库重跑，统计包含两轮测试留下的记录。摘录如下。

```text
MYSQL 8.4.13 tables=11
POST /api/auth/login HTTP 401 code=401
POST /api/auth/login HTTP 200 code=0
GET /api/user/profile HTTP 200 code=0
POST /api/question HTTP 200 code=0
GET /api/question/page?pageNum=1&pageSize=1&subjectId=1 HTTP 200 code=0
GET /api/question/page?pageNum=2&pageSize=1&subjectId=1 HTTP 200 code=0
QUESTIONS saved=3,4 mathTotal=4 pagesChecked=2 authenticatedImage=exact
POST /api/learning/practice/next/3 HTTP 200 code=0
POST /api/practice HTTP 200 code=0
PRACTICE originalRecord=4 variantRecord=5 variant=3 next=4
GET /api/review-plan/today HTTP 200 code=0
PUT /api/review-plan/11/finish HTTP 200 code=0
PUT /api/review-plan/11/finish HTTP 400 code=400
REVIEW plan=11 practiceRecord=6 completed=1 pendingList=false repeatedFinish=400
REPORT total=4 todayPractice=6
GET /api/user/profile HTTP 401 code=401
SESSION invalid JWT cleared; one login navigation
PASS real HTTP and MySQL core flows
```

登录另验证了教师账号虽可在后端登录，小程序拒绝建立学生会话。错题验证涵盖手录、带题图错题保存、题图逐字节回读、按科目过滤和两页读取。练习验证涵盖原题优先、练习提交后掌握度增至 15，以及已练变式题 3 被下一道未练题 4 取代。复习验证涵盖录入后自动建立五轮计划、到期任务出现、作答入库、完成时间写入及待复习列表移除。

| 失败项或未覆盖项 | 实际结果与原因 |
|---|---|
| 相册识别成功回填 | 向 `POST /api/question-recognition/recognize` 发送有效 PNG Data URI，后端返回 HTTP 400，提示未配置 `IMAGE_RECOGNITION_API_KEY` 或 `LLM_API_KEY`。识别候选成功回填仍待真机或模拟器接入真实 GLM 后验证 |
| AI 解析和知识生成 | 读取新错题的 AI 解析返回 HTTP 200、`data: null`。发起解析和获取知识讲解均返回 HTTP 400，提示缺少 `LLM_API_KEY`。真实生成的解析、知识讲解、题池耗尽后生成新题仍待配置真实服务后验证 |
| 微信开发者工具与真机 | 本次 Linux 环境未安装微信开发者工具。界面渲染、实际导入、相册授权、原生相册选取、真机域名校验和真机交互未验证 |
| 初始构建和依赖拉取 | 小程序首次编译提示 `App.vue` 需要脚本或模板，补齐应用入口后构建通过。后端首次 Maven 直连失败，改用环境代理。系统仅有 Java 21 运行时，缺少 `javac`，改用工作目录中的完整 JDK 21，并指定系统信任库后打包成功 |

复跑联调可使用隔离容器。运行前在终端提供本地数据库密码 `DB_PASSWORD` 和容器初始化密码 `MYSQL_ROOT_PASSWORD`。

```bash
docker run -d --name wrongbook-mobile-20261122 \
  -e MYSQL_ROOT_PASSWORD -e MYSQL_DATABASE=wrongbook_mobile \
  -e MYSQL_USER=wrongbook_mobile -e MYSQL_PASSWORD="$DB_PASSWORD" \
  -p 127.0.0.1:33306:3306 mysql:8.4
```

在 `server/` 中启动后端，由 `dev` profile 执行原有数据库脚本。

```bash
export DB_URL='jdbc:mysql://127.0.0.1:33306/wrongbook_mobile?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&useSSL=false'
export DB_USERNAME=wrongbook_mobile
export DB_PASSWORD
TZ=Asia/Shanghai LLM_PROVIDER=glm IMAGE_RECOGNITION_ENABLED=true \
  ./mvnw spring-boot:run -Dspring-boot.run.arguments=--server.address=127.0.0.1
```

构建默认本地地址的产物后，从仓库根目录运行 `MOBILE_TEST_DB_CONTAINER=wrongbook-mobile-20261122 node mobile/scripts/verify-local.cjs`。脚本会创建联调错题、练习及复习操作记录，请使用专用测试库。

## 新增与修改文件

新增 30 个文件，修改 1 个进度记录。构建产物和依赖目录由本地命令生成。

| 路径 | 用途 |
|---|---|
| `mobile/.env.example`、`mobile/.gitignore` | 本地后端地址模板、生成目录及本地配置的忽略规则 |
| `mobile/package.json`、`mobile/package-lock.json`、`mobile/vite.config.js` | 构建命令、锁定依赖和 uni-app 编译配置 |
| `mobile/README.md`、`mobile/scripts/verify-local.cjs` | 交付报告及可复跑的真实后端联调脚本 |
| `mobile/src/main.js`、`mobile/src/App.vue`、`mobile/src/manifest.json`、`mobile/src/pages.json` | 应用入口、全局样式、微信配置、页面与 tab 注册 |
| `mobile/src/config.js`、`mobile/src/api/request.js`、`mobile/src/api/student.js` | 后端地址、JWT 请求层、学生接口定义 |
| `mobile/src/components/AnalysisPanel.vue`、`mobile/src/components/LoadState.vue`、`mobile/src/components/QuestionImage.vue`、`mobile/src/components/QuestionText.vue` | 解析面板、异步状态、题图预览和题干渲染 |
| `mobile/src/composables/use-load.js`、`mobile/src/utils/date.js`、`mobile/src/utils/images.js` | 页面加载、统计日期、图片读写处理 |
| `mobile/src/pages/login/index.vue`、`mobile/src/pages/home/index.vue`、`mobile/src/pages/questions/index.vue`、`mobile/src/pages/detail/index.vue`、`mobile/src/pages/create/index.vue`、`mobile/src/pages/knowledge/index.vue`、`mobile/src/pages/practice/index.vue`、`mobile/src/pages/review/index.vue`、`mobile/src/pages/profile/index.vue` | 九个微信小程序页面 |
| `docs/notes/进度记录.md` | 记录本次交付入口及联调验收情况 |

`server/` 和 `web/` 的分支差异均为 0。后端跨域补充 0 项、部署配置补充 0 项、业务逻辑改动 0 项。联调使用现有的数据库、GLM 和绑定地址运行参数，微信开发者工具的本地 HTTP 连接设置由客户端控制。现有 39 个控制器映射、JWT 和 Bearer 约定继续共用。此次交付未创建或合并 PR。
