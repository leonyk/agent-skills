# 安装器命令

执行前读取该安装包的 `--help`；入口缺失或参数不符时停止并报告版本不完整，不能自行拼接另一套安装流程。

从技能根目录运行以下命令，使用 macOS 上的 Python 3.11+：

```sh
python3 -B scripts/install.py --help
python3 -B scripts/install.py inspect --help
python3 -B scripts/install.py plan --help
python3 -B scripts/install.py apply --help
python3 -B scripts/install.py recover --help
```

`inspect` 每次枚举一个范围。以下命令在隔离 home 中分别检查全局和项目，所选目录必须已经存在：

```sh
python3 -B scripts/install.py inspect --ppt-scope global --home /absolute/isolated-home
python3 -B scripts/install.py inspect --ppt-scope project \
  --project /absolute/project --home /absolute/isolated-home
```

这些只读检查的范围参数不代表用户的安装选择。普通检查返回 `probe: not_run`；候选的 `unprobed` 不能作为兼容证据。需要实际探测时，增加 `--probe --work /absolute/private/work`，并为非托管运行时提供 `--python`。多个候选先用 `--runtime` 指定真实目录。探测只写隔离工作目录；`plan` 也会检查兼容性。

## 生成计划

以下项目新安装示例假设用户已分别选择两个 `project` 范围，并给出项目根。把所有占位路径替换为实际绝对路径；`--python` 是本次选定的解释器。

```sh
python3 -B scripts/install.py plan \
  --ppt-scope project \
  --oracle-scope project \
  --project /absolute/project \
  --python /absolute/python3 \
  --work /absolute/private/work \
  --out /absolute/private/work/plan.json
```

两个全局选择对应 `--ppt-scope global --oracle-scope global`。复用已选候选时增加 `--runtime /absolute/ppt-master`，使用该候选的持久解释器绑定。`--runtime` 不构成改变范围的许可。

测试时增加 `--home /absolute/isolated-home`。工作目录必须独立于运行时及其状态目录，初次使用时为空或不存在。`--out` 必须位于 `--work` 内且尚不存在。后续计划可复用同一私有工作目录，但必须使用新的输出文件；`apply` 和 `recover` 始终使用原计划的工作目录。保留工作目录中的密钥、计划和回执，不能只移动一个 JSON 文件。新安装的依赖环境位于所选范围的持久路径，不搬移已创建的 venv。

命令返回 `status: planned`、`digest`、`changes`、`backups` 及计划路径。计划文件的 `value` 保存两个范围、真实路径、`bound_python`、动作和后置条件。读取这些字段并展示给用户，保留外层摘要与 seal 原样。`keep` 跳过注册及目标改写；`register` 只补齐合法缺失的注册；`blocked` 不执行。孤立索引、损坏 JSON、路径逃逸和不明确身份不能通过重建整库绕过。

## 执行已审阅计划

无冲突且范围已明确时执行：

```sh
python3 -B scripts/install.py apply \
  --plan /absolute/private/work/plan.json \
  --work /absolute/private/work
```

冲突时先向用户展示计划中的完整差异和备份安排。用户明确批准该计划后，在同一命令增加 `--confirm <plan-digest>`。仅持有摘要、过去批准了另一份计划或一般性安装请求，均不能代替这次冲突批准。

`plan` 和 `apply` 都可用 `--archive /absolute/official-archive.tar.gz` 提供预下载的固定官方归档；入口仍校验归档哈希。未提供时由 `runtime.py` 下载固定版本。新安装的 `plan` 可在工作目录重建参考运行时，但不写目标。连接失败或超时后，用 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`、`http_proxy`、`https_proxy`、`all_proxy` 全部等于 `http://127.0.0.1:8080` 重试。

修改成功返回 `status: committed` 和 `verified: true`。相同安装返回 `status: kept`、`registrar_invoked: false` 及 `backups_created: false`；还需读取回执 `value.verification` 中的验证记录。结合计划和回执报告实际目标、解释器及备份。过期计划必须重新生成；有冲突的新计划重新取得批准。不要为使计划通过而手动改写摘要或回执。

## 恢复中断事务

保留失败时返回的事务回执、原计划、工作目录及备份。`recover` 从原计划找到对应回执：

```sh
python3 -B scripts/install.py recover \
  --plan /absolute/private/work/plan.json \
  --work /absolute/private/work
```

读取恢复结果中的 `status`、`verified` 和回执。保留返回的备份与环境信息。已有回执的计划不能直接再次 `apply`；先恢复，或在确认现场后生成新计划。

恢复依据回执中的前像和后像核对现场。出现第三种内容时停止覆盖，保留第三方修改并报告具体对象。不要重新执行安装来代替恢复，也不要删除稳定锁文件来绕过写入者。两个模板目录和两份索引分别发布；这是可恢复事务，不保证其他进程始终看到四个对象同时切换。

## 读取失败结果

失败 JSON 提供 `status` 和 `message`，可能附带候选、差异或回执。保留原始信息并按状态处理：

| 退出码 | status | 处理 |
| --- | --- | --- |
| 2 | `usage` | 核对参数和当前帮助。 |
| 3 | `blocked` | 报告具体前提或边界错误。 |
| 4 | `stale` | 现场已变，重新计划。 |
| 5 | `busy` | 已有写入者，保留锁文件。 |
| 6 | `confirmation_required` | 展示冲突计划，等待明确批准。 |
| 7 | `recovery_conflict` | 保留第三方内容，报告需协调的对象。 |
| 8 | `rolled_back` | 原操作失败，读取回执核对恢复结果。 |
| 9 | `invalid_plan` | 保留现场，核对原计划及其工作目录。 |
| 10 | `interrupted` | 恢复被中断，保留现场并使用原计划与工作目录再次恢复。 |
