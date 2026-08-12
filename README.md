# 开发笔记 Skill

面向 Codex 与 Obsidian 的开发笔记工作流源码仓库。

## Skills

- `developer-notes`：通过 Obsidian MCP 搜索、查重、创建和更新开发笔记，并区分需求架构设计、Bug 修复和简单需求处理。

## 本地安装

仓库源码位于：

```text
skills/developer-notes/
```

全局安装使用符号链接指向仓库源码：

```text
~/.codex/skills/developer-notes -> <repo>/skills/developer-notes
```

显式调用：

```text
$developer-notes 把刚才的开发工作整理成 Obsidian 笔记。
```

不要在仓库中保存 API Key、Token、证书、私钥、`.env` 或 `~/.codex/config.toml`。
