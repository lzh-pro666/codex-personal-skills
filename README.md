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

复杂需求优先显式调用 Superpowers 的 `$brainstorming`；不要为了启停插件中断当前任务。若当前任务尚未加载该能力，直接使用 `development-workflow` 的需求对齐步骤继续工作。代码、测试、PR 和已接受的 OpenSpec 是事实来源，Obsidian 是可复用知识层，Notion 是单 PR 复盘层。

## 验证

```bash
python3 evals/scripts/run_static_checks.py
python3 evals/scripts/validate_scorecard.py --suite \
  evals/fixtures/pass-code.json \
  evals/fixtures/pass-note.json \
  evals/fixtures/pass-workflow.json
```

最终图表门禁还要用固定版本的官方 Mermaid CLI 真正渲染每个 Mermaid 块，而不只做文本检查：

```bash
python3 evals/scripts/run_generative_eval.py verify <run-id> \
  --mermaid-cli /path/to/node_modules/.bin/mmdc
```

除独立 Swift fixture 外，`evals/cases/real-project-cases.jsonl` 还定义了两个
`siuper-ios` 真实回归案例。它们必须从项目当前已提交 HEAD 创建独立
`codex/skill-eval-*` 分支与 worktree，记录 red-green-regression 证据，并用：

```bash
python3 evals/scripts/validate_real_project_report.py \
  evals/.runs/<run-id>/real-project-report.jsonl \
  --source-worktree "/path/to/siuper-ios" \
  --worktree "siuper-ios-lru-capacity=/path/to/lru-worktree" \
  --worktree "siuper-ios-retry-fractional-delay=/path/to/retry-worktree"
```

以 live 模式直接核对来源工作区指纹、worktree 来源、分支/基准提交、实际变更
文件与 `git diff --check`，并校验已记录命令证据和质量阈值。命令结果仍是评测
运行留下的证据，不应把结构校验冒充重新执行测试；发布结论前要保留并人工抽查
原始日志。评测分支不自动提交、推送或合并，避免影响正在开发的分支。

不要在仓库中保存 API Key、Token、证书、私钥、`.env` 或 `~/.codex/config.toml`。
