# 毕业设计

**题目（待定）**：基于 Spring Boot + Vue 的 AI ××× 系统设计与实现

## 仓库结构

```
paper/
├── docs/                  # 论文与文档（本阶段重点）
│   ├── materials/         # 导师提供的参考文件（任务书、模板、往届论文等）
│   ├── thesis/            # 毕业论文 Word 文档（.docx）
│   ├── notes/             # 开题报告、周报、需求分析等过程文档
│   └── references/        # 参考文献管理（详见其 README）
│       ├── references.bib     # BibTeX 条目库
│       ├── gb7714-list.md     # GB/T 7714 国标格式清单
│       └── pdfs/              # 文献原文 PDF（默认不入库）
├── server/                # 【待建】Spring Boot 3 后端（Windows 端开发时添加）
└── web/                   # 【待建】Vue 3 + Vite 前端（Windows 端开发时添加）
```

## 快速指引

- **导师给的参考文件** → 放入 `docs/materials/`
- **下载的文献 PDF** → 放入 `docs/references/pdfs/`，并按 `docs/references/README.md` 的流程登记
- **论文写作** → Word 文档放 `docs/thesis/`，参考文献格式从 `gb7714-list.md` 复制

## 系统开发（Windows 端）

本仓库通过 GitHub 在双系统间同步，实际编码在 Windows 上进行：

- 后端：JDK 17+、IntelliJ IDEA、Maven、MySQL
- 前端：Node.js 18+、Vue 3 + Vite
- 开发时先创建 `server/` 与 `web/` 骨架，`.gitignore` 已覆盖两者的构建产物

## Git 使用

### 分支策略

- `main`：稳定分支，阶段性成果合并到这里
- `dev`：日常开发分支，平时在此提交

```bash
git switch dev          # 切到日常开发分支
git add -A && git commit -m "docs: 更新周报"
git switch main && git merge dev   # 阶段完成后合并回 main
```

### 推送到 GitHub（首次）

> ⚠️ 本机（Linux）当前无法连通 github.com，推送前请确保网络/代理正常。

**第一步：创建远程仓库**（在能访问 GitHub 的网络下，用浏览器操作）

1. 登录 https://github.com → 右上角 `+` → `New repository`
2. 仓库名如 `graduation-project`，勾选 **Private**
3. **不要勾选** "Add a README file" 等初始化选项（避免与本仓库冲突）
4. 点击 `Create repository`

**第二步：配置 SSH 密钥**（本机尚未配置过，两台系统各需配一次）

```bash
ssh-keygen -t ed25519 -C "17268890681@163.com"   # 一路回车即可
cat ~/.ssh/id_ed25519.pub                         # 复制输出的全部内容
```

打开 GitHub → 头像 → `Settings` → `SSH and GPG keys` → `New SSH key`，粘贴公钥保存。
验证：`ssh -T git@github.com`，看到 "Hi zc0429!" 即成功。

**第三步：关联并推送**

```bash
git remote add origin git@github.com:zc0429/graduation-project.git
git push -u origin main
git push -u origin dev
```

此后日常使用 `git push` / `git pull` 即可在 Linux 与 Windows 间同步。

### 提交信息规范（建议）

`类型: 简述`，类型如：`docs`（文档）、`feat`（新功能）、`fix`（修复）、`chore`（杂项）、`ref`（参考文献）
