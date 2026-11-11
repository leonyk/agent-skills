# 固定版本与支持范围

发布清单位于 [`runtime-release/runtime-lock.json`](../runtime-release/runtime-lock.json)，来源与补丁说明位于 [ORIGIN.md](../runtime-release/ORIGIN.md)。

- 官方基线为 PPT Master `v6.8.0`，提交 `5e8856be0da8e6bc85c4aa28acc614478f7b7137`，使用官方仓库中的 `skills/ppt-master/`。新安装从该来源和固定兼容补丁重建。
- Oracle 载荷固定为 2026-11-10 分享包。原 manifest SHA-256 为 `92fc5d711795490b77814970c81827d0bf6f110ddbb2ea14b5749d72681a9a0a`，包含 Brand 7 个文件、Layout 131 个文件和 23 个页面 SVG。更新这些字节需要新的明确发布。
- 支持目标为 macOS，Python 最低为 3.11。解释器和固定依赖要求见发布清单及 `requirements.lock`。运行时重建曾在 macOS arm64、CPython 3.14.0 上验证；最低版本声明不表示已逐一实测其他 Python 版本或 Intel macOS。
- 依赖限定为 `python-pptx`、`PyYAML`、`Pillow`、`XlsxWriter`、`lxml`、`typing-extensions`。新装环境按锁定版本与哈希创建。可选 AI、网页、PDF、音频服务以及上游的全部资源和功能不在本次承诺内。

完整 23 页 Oracle 预览和独立的 23 页中文正式内容导出已经过运行时结构验证。检查范围包含完整 Brand theme、四类品牌资产、内部关系、可编辑文字、原生母版及占位符。该结果不等于客户端安装验收或 PowerPoint 视觉保真。

原始 `master_defaults.json` 要求完整的 23 个 layout 定义。较小的 Quick 页面集合需要显式收窄项目 profile，或采用保留 layout 定义的普通 locked 导出流程。该小页数流程尚未完成资格验证，不能把完整 roster 的通过结果套用到任意小页数导出。接口约束见 [Runtime API](../runtime-release/API.md)。

字体不随包分发，也不由安装器安装。主题声明 Oracle Sans Tab 和 Source Han Sans SC；接收者需要自行具备合适字体及许可。缺字体时应报告视觉检查限制，不改写固定 Brand 来掩盖差异。预览示例及正式导出的原生图表仍有 Arial 和 Microsoft YaHei 声明。正式中文导出的幻灯片、表格、版式及母版文字使用主题字体引用。验收报告按 XML 部件列出字体，不能把完整主题声明等同于所有图表文字均使用主题字体。

官方 MIT 许可证、归属检查及赞助文件保持不变。Oracle 资产遵循原分享包说明与品牌使用限制；本插件不授予新的公开再分发许可。插件卸载与 runtime、依赖环境、模板库及事务备份的清理是不同操作。
