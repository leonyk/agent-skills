# 安装 Oracle 模板

本插件在 macOS 上安装固定 Oracle Brand 与 Layout，并复用兼容的 PPT Master，或按用户选择创建独立运行时。Codex 和 Cursor 使用同一份技能及 Python 安装器。需要 Python 3.11+、Git，以及下载固定来源和依赖的网络连接。

## 在 Codex 中加载

从公开的 agent-skills marketplace 安装：

```sh
codex plugin marketplace add leonyk/agent-skills
codex plugin add oracle-ppt-template@agent-skills
```

开启新的 Codex 会话，选择 `oracle-ppt-template`。安装插件只取得技能文件；PPT Master 和 Oracle 模板在后续安装交互中才会写入。

开发时可在隔离的 `CODEX_HOME` 注册本地仓库。将下面路径替换为实际值：

```sh
CODEX_HOME=/absolute/test/codex-home codex plugin marketplace add /absolute/agent-skills --json
CODEX_HOME=/absolute/test/codex-home codex plugin add oracle-ppt-template@agent-skills --json
CODEX_HOME=/absolute/test/codex-home codex plugin list --marketplace agent-skills --json
```

插件列表只证明安装登记。验收还需要在该隔离配置下启动新会话，确认发现技能，并使用隔离 home、项目和模板库完成实际交互。

## 在 Cursor 中加载

把完整插件保存在持久目录中，将唯一技能目录链接到项目的 `.agents/skills/`。以下目标路径必须尚不存在；若已有同名技能，先核对来源，不强制覆盖。

```sh
mkdir -p /absolute/project/.agents/skills
ln -s /absolute/agent-skills/skills/oracle-ppt-template/skills/oracle-ppt-template \
  /absolute/project/.agents/skills/oracle-ppt-template
```

开启新的 Cursor 会话，在技能列表中确认 `oracle-ppt-template`，再运行安装交互。个人本地使用可将链接位置改为 `~/.agents/skills/oracle-ppt-template`。保留链接指向的完整目录，脚本、payload 和 runtime-release 都必须可读。

Cursor 官方文档列出 `.agents/skills/`、`.cursor/skills/` 及其用户级目录；本插件采用共享目录，不要求 Cursor 读取 Codex marketplace。链接能否在所用 Cursor 版本中被发现仍须实测。全局本地技能不会自动分发到远程 worker；本说明不承诺 Cloud Agents 分发。

## 选择安装范围

向 agent 提供两个独立选择及项目根，例如：

> 使用 oracle-ppt-template。PPT Master 选择项目范围，Oracle 模板也选择项目范围。项目根是 `/absolute/project`。先检查候选，再计划安装。

两个范围必须一致。两个都选项目时，允许与现有全局安装共存，但项目运行时、依赖环境和模板库必须真正独立。多份真实候选需要选择具体目标；相同真实目录的别名只算一个候选。

相同模板且索引正确时完整跳过。缺少合法注册条目时补注册。发生冲突时，agent 展示全部差异、完整备份安排和计划摘要，取得你对该计划的明确批准后才更新。摘要用于检测计划是否过期，本身不是批准。

具体执行顺序见[安装技能](skills/oracle-ppt-template/SKILL.md)，手动命令与恢复步骤见[命令说明](skills/oracle-ppt-template/references/cli.md)。安装结束后核对 JSON 验证结果中的实际目标、解释器、备份和事务回执。中断后保留回执，使用 `recover` 协调现场；第三方改动会阻止覆盖。

## 核对支持范围

固定官方基线为 PPT Master `v6.8.0` 提交 `5e8856be0da8e6bc85c4aa28acc614478f7b7137`，Oracle 载荷保持原分享包字节。完整 23 页的运行时结构验证不等于 PowerPoint 视觉保真或任意小页数 Quick 导出资格。字体不随包分发。精确依赖、来源、许可及导出限制见[版本与限制](skills/oracle-ppt-template/references/release.md)。

更新插件后，重新检查与计划目标；不会自动把未知运行时原地打补丁。卸载 Codex 插件只移除客户端插件安装，不代表已删除 PPT Master、模板库或备份。

分发方式依据 [OpenAI 插件文档](https://developers.openai.com/plugins/build/plugins)、[Codex 技能文档](https://learn.chatgpt.com/docs/build-skills)及 [Cursor 技能文档](https://cursor.com/docs/skills)。
