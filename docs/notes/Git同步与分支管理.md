# Git 同步与分支管理

以远程 `dev` 作为日常集成基准，`main` 保存既有稳定快照。当前 `main` 停在 8 月的旧版本，不代表最新可运行系统；稳定发布应另行验收后正常合并，不在整理中自动更新。

## 每次开始：先看状态，再更新

以下步骤在仓库根目录逐条执行，每条确认成功后再继续。Git 命令在 Bash、PowerShell 均可用；无需重新 `git init`、替换 `.git` 或重复添加 `origin`。

```text
git status --short --branch
git branch --show-current
git worktree list
git fetch origin
git log -1 --oneline origin/dev
```

工作区有修改时先在原任务分支检查、保存并提交有价值的文件；未跟踪文件也要检查。不要为切换分支执行 `reset --hard`、`clean -fdx` 或强制覆盖。`stash -u` 也不会备份被忽略的密钥、上传图片、数据库和本地交接包，应单独安全备份这些本地数据。

更新本地 `dev`：

```text
git switch dev
git pull --ff-only origin dev
git status --short --branch
```

如果 `dev` 已在另一个 worktree 中检出，进入那个目录更新。若没有本地 `dev`，首次使用 `git switch --track -c dev origin/dev`。如果 `--ff-only` 失败，停下来用 `git log --graph --oneline --left-right dev...origin/dev` 检查双方提交，在任务分支解决分歧；不要改用强制推送、重置或盲目 rebase。

## 云端 Codex：独立分支交付

从刷新后的远程 `dev` 开始，分支名用任务和日期区分，例如：

```text
git switch --no-track -c codex/task-YYYYMMDD origin/dev
```

会话先读 `AGENTS.md` 与进度记录。只暂存本任务文件，检查 `git diff --cached`，按实际改动执行必要验证，再提交与推送：

```text
git diff --check
git commit -m "docs: 说明本次任务成果"
git push -u origin HEAD
```

`commit` 前须已用 `git add -- 文件路径` 显式暂存审核过的文件；命令示例不代替检查。推送新分支后由 PR 或单独授权的集成任务正常合并到 `dev`；未经集成不要让任务分支追踪 `origin/dev`，以免误推主开发分支。跨端继续同一任务时避免两端同时修改同一分支；先在一端提交推送，另一端再拉取。

## Windows：接收成果或继续任务

在 PowerShell 中进入自己的真实仓库路径。建议使用短路径如 `D:\src\graduation-project`；已有长路径可先保持，遇到工具路径限制再单独迁移。

```powershell
Set-Location 'D:\src\graduation-project'
git status --short --branch
git fetch origin
git switch dev
git pull --ff-only origin dev
```

需要审阅某个 Codex 分支时，先确保工作区干净；首次检出使用：

```text
git switch --track -c codex/repository-hygiene-20261027 origin/codex/repository-hygiene-20261027
```

本地已存在该分支时改为 `git switch 分支名`，再 `git pull --ff-only`。若云端尚未推送，相应 `origin/codex/...` 不存在，先完成云端分支推送，不能用复制整个工作目录来替代 Git 同步。

Windows 本地继续开发同样从最新 `origin/dev` 新建独立任务分支，完成后提交、推送、审核再集成。依赖目录不随 Git 同步，在 `web/` 执行 `npm ci`；后端使用 JDK 21 与 `server/mvnw.cmd`。数据库、账号、密钥和图片上传数据需在本地分别准备，不能期待 `git pull` 取得。

自动化测试只使用隔离数据库与 Mock 配置，真实联网测试开关保持关闭。不要将 `.env.example` 的占位值当作可用凭据，也不要把 `.env` 强制加入 Git。运行说明见 [Windows 环境说明](Windows开发环境与启动说明.md)及[当前模型与富文本说明](默认GLM与富文本运行说明.md)。

## 换行、中文路径与本地配置

以下是可选的仓库级本地设置，不写全局配置，不自动在本轮执行：

```text
git config --local pull.ff only
git config --local push.default simple
git config --local core.autocrlf false
git config --local core.safecrlf warn
```

Windows 需要时另设 `git config --local core.longpaths true`；IDE 与 Office 也可能有各自路径限制。当前审计未发现大小写冲突、Windows 禁用文件名或在示例 Windows 根路径下达到 260 字符的已跟踪路径。中文全角冒号与括号属于合法文件名，不需要为了同步重命名学校材料。

保持现有文件字节与换行，编辑器将新建脚本保存为 UTF-8/LF；不要执行全仓 `git add --renormalize .`。独立论文分支有针对 XSD 与证据字节保护的 `.gitattributes`，未来接入时需随对应文件评估，不能用统一换行转换破坏证据哈希。

现有 `server/.gitattributes` 已将 `mvnw` 设为 LF、`*.cmd` 设为 CRLF。Windows Wrapper 的工作区字节与 Git 中规范化 blob 可以不同；跨端校验应分别检查原文件 SHA-256 与遵循属性规则的 `git hash-object`，不要为了让原始字节一致而改写脚本。

## 查看历史成果与清理分支

正文当前以 `dev:docs/thesis/毕业论文.md` 为准。需要查看尚未接入的论文审阅版、答辩材料，可独立检出只读工作树：

```text
git worktree add --detach ../graduation-project-thesis-archive origin/codex/thesis-finalization-20260920
```

如目标目录已存在，先核对其中成果，不覆盖。该命令只是检出已有成果，不代表已合并到 `dev`。旧工作树上的本地 ZIP/bundle、未跟踪文件也不会因分支存在而自动同步。

远程分支删除必须先取得用户对具体清单的确认；删除前重新 fetch，并用 `git merge-base --is-ancestor origin/分支 origin/dev` 与独有提交差异核对。已合并分支即使可删，也应检查两端 worktree 和未提交工作；未合并论文、文献分支先保留，按需选取成果或经授权归档。

本轮不执行远程分支删除、已跟踪文件删除、历史重写或强制推送。具体建议与文件清单见 [仓库整理报告](仓库整理报告-20261027.md)。

上述“本轮不执行”指删除前审计阶段。后续用户已确认按清单删除，执行结果见 [删除执行记录](仓库整理删除执行记录-20261027.md)。Windows 接收本次整理时用 `git fetch origin --prune` 清除已不存在的远程跟踪引用，再对干净的 `dev` 执行 `git pull --ff-only origin dev`；该操作不会删除本地任务分支。本地旧分支有工作树或独有提交时先保留，只有确认已合并且无待保存工作后，才使用 `git branch -d 分支名`，不用 `-D` 强删。
