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

## 维护

仓库只保留运行 Skill 所需的 `SKILL.md`、按需加载的 references、确定性功能脚本
和 UI 元数据。一次性的评测案例、fixture、盲评结果与构建缓存不进入源码仓库。

修改 Skill 后，使用 Codex 自带的 `skill-creator` 校验其目录结构，并针对实际改动
执行最小的真实场景验证。涉及项目代码时，在独立分支或 worktree 中执行项目自身
的测试和构建，不把通用测试夹具长期复制到本仓库。

不要在仓库中保存 API Key、Token、证书、私钥、`.env` 或 `~/.codex/config.toml`。
