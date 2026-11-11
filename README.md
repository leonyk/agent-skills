# Agent Skills

公开的 agent 技能集合。每个 `skills/<插件名>/` 目录是一个独立插件，内部的 `skills/` 提供技能入口。

| 插件 | 用途 | 运行依赖 |
| --- | --- | --- |
| [oracle-ppt-template](skills/oracle-ppt-template/README.md) | 按范围安装或复用 PPT Master，并安装固定 Oracle Brand 与 Layout | macOS、Python 3.11+、Git |

## 在 Codex 中安装

```sh
codex plugin marketplace add leonyk/agent-skills
codex plugin add oracle-ppt-template@agent-skills
```

开启新会话后选择 `oracle-ppt-template`。插件安装只获取技能文件；后续交互分别选择 PPT Master 与 Oracle 模板的安装范围。

如果已安装旧名 `oracle-template-installer`，移除对应来源的旧入口，再安装 `oracle-ppt-template`，避免重复发现。移除客户端插件不会删除 PPT Master、模板库或备份。按旧版本的来源执行对应命令：

```sh
codex plugin remove oracle-template-installer@agent-tools
codex plugin remove oracle-template-installer@agent-skills
```

## 在 Cursor 中使用

克隆本仓库到持久目录，按[插件说明](skills/oracle-ppt-template/README.md#在-cursor-中加载)将完整技能目录链接到项目的 `.agents/skills/`。

Codex 已完成真实会话验收。Cursor 的共享目录分发依据官方文档，尚未完成本机客户端实测。

## 运行验证

从技能目录运行检查。`--work` 使用新的隔离目录，验收不会操作日常模板库。

```sh
cd skills/oracle-ppt-template/skills/oracle-ppt-template
python3 -B scripts/test_installer.py --work /absolute/new-unit-work
python3 -B scripts/verify_runtime.py qualify --work /absolute/new-runtime-work --report /absolute/runtime-report.json
```

运行时来源、固定依赖、Oracle 素材说明和授权边界见[版本与限制](skills/oracle-ppt-template/skills/oracle-ppt-template/references/release.md)。上游许可证与署名保留在 `runtime-release/`。本仓库不为 Oracle 素材授予新的使用或再分发许可。
