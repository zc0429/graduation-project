# Windows Playwright 截图走查

## 前置条件

1. MySQL 8 已启动，`wrongbook` 数据库已执行 `server/src/main/resources/db/schema.sql`。
2. `server/.env` 的数据库地址、账号和密码与本机 MySQL 一致。
3. 后端在独立 PowerShell 终端运行：

   ```powershell
   Set-Location 'D:\Documents\GitHub\graduation-project\server'
   .\mvnw.cmd spring-boot:run
   ```

4. 前端在独立 PowerShell 终端运行：

   ```powershell
   Set-Location 'D:\Documents\GitHub\graduation-project\web'
   npm install
   npm run dev
   ```

## 首次安装 Playwright

在 `web` 目录执行：

```powershell
npm install --save-dev @playwright/test
npx playwright install chromium
npx playwright --version
```

浏览器默认下载到 `%USERPROFILE%\AppData\Local\ms-playwright`。若更新了 Playwright 版本，应再次执行 `npx playwright install chromium`。

## 生成截图

保持前后端运行，在 `web` 目录执行：

```powershell
npm run e2e:screenshots
```

脚本使用 `admin/123456`、`teacher/123456`、`student/123456` 依次走查 14 个页面，并将 PNG 直接写入 `docs/thesis/screenshots/`，不使用系统临时目录。

为使空数据库也能展示 AI 解析、RAG 参考和相似题推荐，脚本先走查并截图真实错题录入页，再在学生登录会话中通过系统自身的 REST API 准备两条带有“自动化测试数据”前缀的演示错题。变式题和周报消息也只在缺失时生成，因此重复执行不会持续追加同名错题或重复变式题。复习计划按业务规则从录入次日开始，脚本不会篡改计划日期；首次当天截图出现空状态是正常、真实的结果。
