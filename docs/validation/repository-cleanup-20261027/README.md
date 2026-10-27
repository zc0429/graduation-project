# 授权删除执行证据（2026-10-27）

本目录记录用户确认删除后的实际操作，区别于 [删除前审计快照](../repository-hygiene-20261027/README.md)。没有修改或替换历史测试证据。

| 文件 | 内容 |
|---|---|
| preflight.json | 操作前远程 15 分支、候选原头、dev/整理分支基准、532 文件工作区 SHA-256；另附 Word 锁文件普通提交的前后头 |
| branch-deletions.json | 10 个分支逐项重新检查、普通删除及远程不存在的验证结果，含可恢复原 SHA |
| local-cache-cleanup.json | 6 个已忽略缓存目录的删除数量/逻辑字节数，以及 44 份保留的测试报告/状态文件哈希 |
| checks.json | 本轮 Git、文件保护、链接、忽略与暂存差异定向检查结果；未将业务测试计为新通过 |

实际主要操作：

```text
git fetch origin
git ls-remote --heads origin
git merge-base --is-ancestor 原分支SHA devSHA
git push origin --delete 单个已确认分支
git ls-remote --heads origin refs/heads/该分支
git rm -- 五个明确的空占位文件路径
git diff --cached --check
```

Word 锁文件在临时独立工作树内用字面路径参数 `git rm -- 路径`、普通 commit、`git push origin HEAD:refs/heads/codex/reference-freeze` 处理，提交 `7698cad` 的完整树差异只包含该删除。所有操作由 Python subprocess 传参，Word 文件名中的 `$` 没有交给 Shell 展开。

删除远程分支逐项进行，不是一次性多引用推送；候选头如变化则中止，祖先校验失败也中止。没有使用强推或改写历史。删除后的 `fetch --prune` 清理本地远程跟踪引用；导师工作树原目录保留为 detached HEAD，本地旧分支用 `-d` 删除。

文件级验证基准是操作前 `727796a`：除 5 个空占位文件和 3 份追加说明/进度外，524 个既有文件的 SHA-256 保持一致。Git 索引检查确保源代码、配置、数据库、正文、学校材料、开题、图源与历史证据均没有变化。文献分支除 Word 锁文件外的所有 Git blob 与原头逐项一致。

缓存清理仅作用于当前主工作树、未跟踪且已忽略的指定目录。测试报告与运行状态保留；不会执行 `git clean -fdx`、删除整个 output/docs 或清理唯一证据。

通过检查后整理分支正常提交/推送，再快进 dev 并正常推送。提交号及最终远程状态可通过 `git log`、`git ls-remote` 核查；[执行记录](../../notes/仓库整理删除执行记录-20261027.md)同时提供 Windows 接收流程。
