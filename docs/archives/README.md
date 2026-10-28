# 历史成果归档索引

归档保留原分支的完整提交与文件树，通过带说明的 Git 标签固定版本，不将历史正文、旧代码或导出件混入当前工作目录。当前完整论文继续使用 [dev 中的源稿](../thesis/毕业论文.md)。两个仍有独有成果的原分支继续保留。

| 固定标签 | 原提交 | 内容与状态 |
|---|---|---|
| [archive/thesis-finalization-20260920-20261028](https://github.com/zc0429/graduation-project/tree/archive/thesis-finalization-20260920-20261028) | 29ae335c98d9944a50360ed8ffa9a1b07f70cd15 | 完整历史论文审阅版、答辩材料、文档工具与验证；7 个未整体合并提交 |
| [archive/reference-freeze-20261028](https://github.com/zc0429/graduation-project/tree/archive/reference-freeze-20261028) | 7698cadd9a448b3e4b78ce7f934ea6cc922446db | 早期文献/引用冻结及后续 Word 锁文件删除；3 个未合并提交 |

[详细成果清单](20261028-historical-branches.md)列出重点文件、独有提交和相对当前 dev 的路径差异；[机器清单](../validation/repository-maintenance-20261028/archives.json)包含标签对象、原提交、树、文件数与分支独有文件的 SHA-256。

## 跨端取得历史成果

在已有仓库根目录执行，确认目标目录尚不存在：

```text
git fetch origin --tags
git rev-parse archive/thesis-finalization-20260920-20261028^{}
git worktree add --detach ../graduation-project-thesis-archive archive/thesis-finalization-20260920-20261028
```

Windows PowerShell 中可将带 `^{}` 的参数用单引号括起，例如 `git rev-parse 'archive/thesis-finalization-20260920-20261028^{}'`。完整提交应为表中 SHA；旧 Word/PDF/PPT 从这个独立目录查看。文献快照同理使用 `archive/reference-freeze-20261028`。标签已推送并验证；今后不覆盖或移动这些标签。

归档不是最新论文重新导出，也不是学校正式提交。源分支内的旧模型、旧开题表述和当时待办只代表该阶段，当前功能以 dev 为准。原图、截图、实验记录和校验哈希保持原样，不重新生成。
