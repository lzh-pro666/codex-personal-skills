# Codex Personal Skills

面向 Codex 的个人开发工作流、iOS 专项能力与知识沉淀 Skill 源码仓库。

## Skills

- `development-workflow`：对齐需求，路由专项 Skill，完成实现、验证、质量门禁和笔记询问。
- `developer-notes`：通过 Obsidian MCP 查重并安全沉淀架构、Bug、简单需求三类笔记。
- `pr-review-to-notion`：生成证据优先的单 PR 中文复盘，按需写入本地配置的 Notion 数据源。
- `ios-accessibility`、`swift-concurrency`、`swift-testing`、`swiftui-uikit-interop`：iOS 专项实现与审查规则。

## 本地安装

每个 Skill 都从仓库源码符号链接到 Codex 的用户级目录：

```text
~/.agents/skills/<skill> -> <repo>/skills/<skill>
```

日常开发可以直接说：

```text
请实现这个需求。
修复这个 Bug，并补回归测试。
```

复杂任务或需要指定流程时显式调用：

```text
$development-workflow 实现这个需求并完成质量验收。
$developer-notes 把刚才验证完成的工作整理成开发笔记。
```

`development-workflow` 是 Codex 的个人策略与路由层，不复制 Superpowers 本体。需求确实存在重大歧义时才调用 `$brainstorming`；精确任务和已批准规格直接执行。不要为启停 Skill 中断任务或重启 Codex，也不要并装两套同名 Superpowers Skill。代码、测试、PR 和已接受的 OpenSpec 是事实来源，Obsidian 是可复用知识层，Notion 是单 PR 复盘层。

## 维护

仓库保留运行 Skill 所需的 `SKILL.md`、按需加载的 references、确定性功能脚本、
UI 元数据，以及后续优化 Skill 可复用的评估源码：

```text
evals/
├── cases/      # 行为、生成和真实项目案例定义
├── fixtures/   # 可重复执行的最小测试输入
└── scripts/    # 准备、验证、聚合和安全门禁脚本
```

运行产生的 `evals/.runs/`、Swift `.build/`、日志、渲染文件、盲评结果和临时
worktree 不进入 Git；它们可以删除并由评估脚本重新生成。

修改 Skill 后，使用 Codex 自带的 `skill-creator` 校验其目录结构，并针对实际改动
先运行基础静态门禁：

```bash
python3 evals/scripts/run_static_checks.py
```

需要高强度回归时，再使用 `run_behavior_eval.py`、`run_generative_eval.py` 和
`validate_real_project_report.py`。涉及项目代码时，在独立分支或 worktree 中执行
项目自身的测试和构建，并只把可复用案例定义留在本仓库。

不要在仓库中保存 API Key、Token、证书、私钥、`.env` 或 `~/.codex/config.toml`。
