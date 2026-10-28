# 后续仓库维护证据（2026-10-28）

本轮基准 `dev@2d5a135`。只更新当前文档入口、归档引用及清理已确认分支/重复缓存，没有重跑应用或真实模型测试。

| 文件 | 内容 |
|---|---|
| preflight.json | 5 个原远程分支、仓库权限与默认分支、主树 533/导师树 505 文件的基准 SHA-256 |
| default-branch.json | 默认分支设置请求的 403 失败及回读结果，默认仍为 main |
| branch-cleanup.json | 已合并 repository-hygiene 分支的原头、祖先保留、远程/本地删除结果 |
| advisor-cache-cleanup.json | 6 个重复缓存删除统计及 44 份保留报告/状态哈希 |
| archives.json | 两个固定归档的标签对象、原提交、树、独有日志、路径差异、独有路径 blob/SHA-256 |
| checks.json | 本轮定向校验与默认分支设置受阻的独立状态 |

主要实际命令：`git fetch origin`、`git ls-remote --heads origin`、`git merge-base --is-ancestor`、`git push origin --delete codex/repository-hygiene-20261027`、`git branch -d`、`git tag -a`、逐标签普通推送、`git ls-remote --tags`、`git rev-parse 标签^{}`、`git rev-parse 标签^{tree}`、`git diff --check` 和 `git diff --cached --check`。文件与索引由 Python subprocess 和 SHA-256 核对。

仅包含 `default_branch=dev` 的 `gh api --method PATCH` 返回 403；`gh api` 再次 GET 返回 main。没有把仓库权限元数据的 admin=true 当作设置写入成功，也没有读取或输出凭据值。当前没有可用浏览器控制工具作为已登录备用入口。

保护范围：主工作树除 6 份说明/记忆更新外的 527 个既有文件字节不变；导师工作树 505 个既有跟踪文件及 44 份报告/状态字节不变。Git blob 比较遵循原有属性与换行规则。两个历史分支头保持原 SHA，归档标签远程剥离后均等于原头，完整树一致，未覆盖已有标签。

完整执行结果见 [后续整理记录](../../notes/仓库后续整理-20261028.md)，跨端历史成果入口见 [归档索引](../../archives/README.md)。旧报告中的分支数量继续作为当时快照保留。
