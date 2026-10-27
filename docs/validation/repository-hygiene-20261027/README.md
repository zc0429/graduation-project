# 仓库整理审计证据（2026-10-27）

基准为 `origin/dev@d328adb9b6c48c1d580a0f2a40fe9d20fa2d9521`，记录的是新整理分支发布前的 14 个远程分支快照。没有复用上轮应用测试结果作为本轮检查，也没有运行会重写截图、论文或图示的命令。

| 文件 | 内容 |
|---|---|
| branches.json | 每个远程分支的完整 SHA、相对 dev 的落后/独有数，未合并分支日志与差异 |
| branch-only-files.md | 两个未合并分支头中当前 dev 不具备的 95 个路径（论文 94、文献 1） |
| inventory.json | 522 文件大小、重复 blob、各分支可疑路径、忽略与 Windows 路径检查、限定范围的凭据形状扫描 |
| baseline-manifest.json | 整理前全部 522 个文件的 Git blob、大小及 SHA-256，用于证明原成果未覆盖 |
| checks.json | 本轮实际执行的定向检查、通过数量与范围限制 |

实际使用的主要 Git 命令：

```text
git status --short --branch
git branch -vv
git worktree list
git fetch origin
git ls-remote --heads origin
git for-each-ref refs/remotes/origin
git rev-list --left-right --count origin/dev...origin/分支
git merge-base --is-ancestor origin/分支 origin/dev
git diff --name-status origin/dev...origin/分支
git ls-tree -r -l -z origin/dev
git ls-files -ci --exclude-standard
git log --all --format= --name-only -- .env **/.env *.pem *.key *.p12 *.pfx
git check-ignore --no-index 路径
git diff --check
git diff --cached --check
```

敏感文件名查询由 Python subprocess 按字面参数调用，避免 Shell 展开 glob。Git tree 与 blob 由 Python 汇总；凭据扫描只输出规则名与路径，不输出匹配内容。扫描范围为 14 个远程分支头的 670 个 UTF-8 文本 blob（≤2 MB），不含完整历史与二进制材料取证。额外对当前可达历史查询了列出的敏感文件名，未发现命中。

忽略规则以虚拟路径作正反例查询，不创建密钥文件；同时检查所有 522 个基准路径没有被新规则隐藏。对允许修改的 `.gitignore`、根 README、进度记录之外的 519 个原文件逐项校验字节与 Git blob，覆盖应用、配置、数据库、论文、开题、图示、截图和原验证记录。

manifest 的 `bytes` 为 Git blob 大小，`sha256` 为整理前工作区文件字节哈希。`server/.gitattributes` 对 Wrapper 的既有 LF/CRLF 规则保持原样；工作区 SHA-256 校验之外，使用遵循该属性的 `git hash-object` 比较 blob，不用裸字节 SHA-1 误判 Windows 启动脚本变化。

完整处置建议见 [仓库整理报告](../../notes/仓库整理报告-20261027.md)。这是审计证据目录，不是可清除缓存。
