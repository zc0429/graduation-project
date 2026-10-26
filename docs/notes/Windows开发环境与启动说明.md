# Windows 开发环境与启动说明

> 适用仓库：`D:\Documents\GitHub\graduation-project`。以下命令均为 Windows PowerShell 命令，不使用 Linux 的 `./mvnw` 或 `/tmp`。

## 1 Git 本地身份配置

在仓库根目录执行：

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project'
git config --local user.name 'zc0429'
git config --local user.email '17268890681@163.com'
git config --local --get user.name
git config --local --get user.email
git branch --show-current
```

本次验证结果：本地身份为 `zc0429 <17268890681@163.com>`，当前分支为 `dev`。

## 2 环境校验与修正

### 2.1 一次性校验命令

```powershell
where.exe java
java -version
$env:JAVA_HOME

where.exe mvn
mvn -version
Set-Location 'D:\Documents\GitHub\graduation-project\server'
.\mvnw.cmd -version

where.exe node
node --version
npm --version

where.exe mysql
mysql --version
Get-Service -Name 'MySQL80' -ErrorAction SilentlyContinue
```

本次 Windows 实测：

| 工具 | 检测结果 | 处理结论 |
|---|---|---|
| JDK | PATH 默认命中 Java 8.0.481；`D:\Dev\jdk21` 为 Temurin 21.0.11 | PATH 不匹配；本次会话切换到 JDK 21 后启动及测试通过 |
| Maven | 全局 Maven 3.8.1 且绑定 Java 8；仓库 Wrapper 为 Maven 3.9.16 | 项目统一使用 `mvnw.cmd`，无需依赖全局 Maven |
| Node.js | Node 25.5.0、npm 11.8.0 | 本次构建和 Playwright 通过；项目基线建议切换为 Node 22.23.1 LTS |
| MySQL | MySQL 8.0.40 已安装 | `MySQL80` 服务需要管理员权限；本次使用独立用户数据目录启动并完成建库导入 |

### 2.2 JDK 21 下载、安装与环境变量

若 `D:\Dev\jdk21` 不存在，从 [Eclipse Temurin Windows 安装说明](https://adoptium.net/installation/windows/) 下载 Temurin 21 x64 MSI。安装时勾选“Set JAVA_HOME variable”和“Add to PATH”；也可安装到 `D:\Dev\jdk21`。

当前终端立即切换：

```powershell
$env:JAVA_HOME = 'D:\Dev\jdk21'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
java -version
$env:JAVA_HOME
```

永久配置步骤：

1. 打开“系统属性 → 高级 → 环境变量”。
2. 将 `JAVA_HOME` 设置为 `D:\Dev\jdk21`。
3. 在 Path 中加入 `%JAVA_HOME%\bin`，并将其移动到旧 JDK 路径之前。
4. 删除或下移 `D:\Dev\jdk\bin` 及 Oracle Java 8 的 `C:\Program Files (x86)\Common Files\Oracle\Java\java8path`。
5. 关闭并重新打开 PowerShell，执行 `where.exe java` 与 `java -version`；第一条路径必须是 JDK 21，版本必须为 21.x。

### 2.3 Maven 下载、安装与环境变量

项目优先使用仓库自带的 Maven Wrapper：

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project\server'
$env:JAVA_HOME = 'D:\Dev\jdk21'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
.\mvnw.cmd -version
```

若确实需要全局 Maven，从 [Apache Maven 官方下载页](https://maven.apache.org/download.cgi) 下载 Maven 3.9.16 binary zip，解压到 `D:\Dev\apache-maven-3.9.16`，再按以下步骤配置：

1. 新建 `MAVEN_HOME=D:\Dev\apache-maven-3.9.16`。
2. 在 Path 中加入 `%MAVEN_HOME%\bin`，并置于 `D:\Dev\apache-maven-3.8.1\bin` 之前。
3. 重新打开 PowerShell，执行 `mvn -version`。
4. 输出应同时显示 Maven 3.9.16 与 Java 21；若仍显示 Java 8，先按 2.2 节修正 `JAVA_HOME` 和 Path。

### 2.4 Node.js 22.23.1 下载与切换

本机 Node 25.5.0 已完成本次构建与自动化测试，但项目既定基线为 Node 22.23.1 LTS。建议从 [Node.js 官方下载页](https://nodejs.org/en/download) 下载 22.23.1 x64 MSI，或下载官方 `node-v22.23.1-win-x64.zip` 后解压到 `D:\Dev\nodejs-22.23.1`。

使用 ZIP 版本时：

1. 在正在运行前端的终端按 `Ctrl+C`。
2. 解压后，在“环境变量 → Path”中将 `D:\Dev\nodejs-22.23.1` 放到 `D:\Dev\nodejs` 之前。
3. 关闭并重新打开 PowerShell。
4. 校验：

```powershell
where.exe node
node --version
npm --version
```

`node --version` 应输出 `v22.23.1`。随后在 `web` 目录重新执行 `npm install`、`npm run build` 与 `npm run e2e:screenshots`，用项目基线版本补做一次回归。

### 2.5 MySQL 8 安装、服务与数据库初始化

若未安装，从 [MySQL Installer for Windows](https://dev.mysql.com/downloads/windows/installer/8.html) 下载 MySQL 8 Installer，选择 Server only 或 Developer Default，配置 TCP 端口 3306、服务名 `MySQL80`、启动类型 Automatic，并为 root 设置仅保存在本机 `.env` 中的独立密码。将 MySQL 的 `bin` 目录（本机为 `D:\Dev\mysql\bin`）加入 Path。

启动 Windows 服务必须使用“以管理员身份运行”的 PowerShell：

```powershell
Start-Service -Name 'MySQL80'
Get-Service -Name 'MySQL80'
```

若提示“拒绝访问”或“无法打开 MySQL80 服务”，说明当前终端不是管理员权限。若 3306 已被当前用户启动的临时 MySQL 实例占用，先在普通 PowerShell 中正常关闭该实例，再启动服务：

```powershell
& 'D:\Dev\mysql\bin\mysqladmin.exe' --protocol=TCP --host=127.0.0.1 --port=3306 --user=root -p shutdown
```

按提示输入本机 root 密码后，重新以管理员身份执行 `Start-Service MySQL80`。

登录 MySQL 并执行仓库 SQL：

```powershell
& 'D:\Dev\mysql\bin\mysql.exe' --protocol=TCP --host=127.0.0.1 --port=3306 --user=root -p
```

在 MySQL 提示符内输入：

```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY '<your-local-root-password>';
CREATE DATABASE IF NOT EXISTS wrongbook
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE wrongbook;
SOURCE D:/Documents/GitHub/graduation-project/server/src/main/resources/db/schema.sql;
SHOW TABLES;
```

应看到 10 张表：`user`、`subject`、`knowledge_point`、`question`、`ai_analysis`、`variant_question`、`review_plan`、`practice_record`、`message`、`announcement`。

## 3 后端配置与启动

`server/.env` 已创建且被 `.gitignore` 排除，数据库配置为：

```dotenv
DB_URL=jdbc:mysql://127.0.0.1:3306/wrongbook?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&useSSL=false
DB_USERNAME=<your-local-db-user>
DB_PASSWORD=<your-local-db-password>
```

正常运行默认 `glm`，文本默认 `glm-5.3-flash`，图片识题默认开启；缺少密钥时手工录入可用，AI 请求明确失败。离线开发需显式设置 `LLM_PROVIDER=mock` 与 `IMAGE_RECOGNITION_ENABLED=false`。模型配置统一从 `server/.env` 或进程环境变量读取，真实密钥不得写入 Git、文档、日志或截图。完整占位配置见 `server/.env.example`。

智谱 GLM 正式配置（获得并轮换为可用的新密钥后填写）：

```dotenv
LLM_PROVIDER=glm
LLM_API_KEY=replace-with-your-glm-api-key
LLM_CHAT_MODEL=glm-5.3-flash
LLM_EMBEDDING_MODEL=embedding-3
LLM_EMBEDDING_DIMENSIONS=1024
```

DeepSeek 临时联调配置：

```dotenv
LLM_PROVIDER=deepseek
LLM_API_KEY=replace-with-your-deepseek-api-key
LLM_CHAT_MODEL=deepseek-v4-flash
```

DeepSeek 官方未提供 Embedding 接口，因此该模式仅验证真实文本生成，向量检索明确降级为本地 256 维字符 n-gram 哈希；论文终稿和最终截图应在智谱 `embedding-3` 配置后重新验证。不得修改 `pom.xml` 中固定的 Spring Boot 3.5.16。

启动命令：

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project\server'
$env:JAVA_HOME = 'D:\Dev\jdk21'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
.\mvnw.cmd spring-boot:run
```

看到 `Started WrongbookServerApplication`、Tomcat 端口 8080、Hikari 连接成功即表示后端启动完成。若出现数据库连接失败，依次执行：

```powershell
Get-NetTCPConnection -LocalPort 3306 -State Listen -ErrorAction SilentlyContinue
Test-NetConnection 127.0.0.1 -Port 3306
Test-Path -LiteralPath '.env'
```

最后一条命令只确认 `.env` 是否存在；不要在终端、日志或对话中打印其内容。

## 4 前端安装与启动

新开一个 PowerShell 终端：

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project\web'
npm install
npm run dev
```

浏览器打开 `http://localhost:5173/`。本机 Vite 监听 IPv6 回环地址时，`http://127.0.0.1:5173/` 可能不可用，应使用 `localhost`。

构建校验：

```powershell
npm run build
```

## 5 Playwright 安装与截图

首次安装：

```powershell
Set-Location 'D:\Documents\GitHub\graduation-project\web'
npm install --save-dev @playwright/test
npx playwright install chromium
npx playwright --version
```

保持前后端运行，执行：

```powershell
npm run e2e:screenshots
```

脚本位置为 `web/e2e/walkthrough.spec.ts`，配置为 `web/playwright.config.ts`，截图直接保存到 `docs/thesis/screenshots/`，不使用 `/tmp`。更详细的复跑说明见 `web/e2e/README.md`。
