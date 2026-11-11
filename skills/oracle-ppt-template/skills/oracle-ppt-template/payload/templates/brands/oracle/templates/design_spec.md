---
brand_id: oracle
kind: brand
summary: Oracle 品牌身份预设，适用于公司汇报、客户方案和内部培训，可跨项目复用
primary_color: "#C74634"
---

# Oracle Brand Specification

> 品牌身份预设。仅约束颜色、字体、标识、页脚、语气和图标，不提供固定页面原型。

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Oracle |
| Use Cases | 公司汇报、客户方案、内部培训。用户指定，可跨项目复用 |
| Tone | 正式、直接、以内容和事实为主。源材料的表达观察及本预设建议，不属于已核验的官方语气规范 |
| Sources | 用户提供的 `template-dark.pptx` 第 3–10 页说明，以及这些页面直接继承的字体、主题和标识。2026-11-03 提取并由用户确认 |
| Source File | `/Users/kyin/MyData/Oracle/Template/template-dark.pptx`，仅为来源记录，使用本预设无需访问该路径 |
| Source SHA-256 | `df408eac1dc3bdd9330d1d9e132546f6600101160d585933b527b3ccfafc0be5` |
| User Confirmation | 2026-11-03。确认思源黑体、简洁线性图标、说明页金色、Oracle Sans Tab 标题和正文，以及右下角原始 OTag |

来源分类须在后续使用和修改中保留：

- 材料明文：提供的 Oracle 模板中明确写出的要求。这里只记录该文件的规定，未声称已核验 Oracle 最新完整品牌手册。
- 模板观察：从源文件的样式、主题或资产中读出的事实。观察到的实现不自动等于全品牌官方规范。
- 用户指定：用户明确要求或确认的选择。
- 建议：为跨项目使用补充的默认值。不得改称官方规定。
- 颜色表的 `fact` 表示源材料明确数值，`user` 表示用户选择，`approx` 表示观察或建议。

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | #C74634 | fact | Oracle Red，第 5 页明文。本预设将其用作品牌主色，未规定必须占据大面积 |
| background-light | #FBF9F8 | fact | Neutral 10，第 5 页的浅色背景 |
| background-dark | #2A2F2F | fact | Slate 170，第 5 页的深色背景 |
| accent-light-sky | #04536F | fact | Sky 140，第 5 页指定的浅底文字强调色 |
| accent-light-rose | #6C3F49 | fact | Rose 140，第 5 页指定的浅底文字强调色 |
| accent-dark-brand | #F0CC72 | user | Brand 170，第 5 页说明和第 6 页自定义链接色。用户明确采用此数值 |
| accent-dark-teal | #89B2B0 | fact | Teal 70，第 5 页指定的深底文字强调色 |
| accent-dark-pine | #86B596 | fact | Pine 70，第 5 页指定的深底文字强调色 |
| link-light | #00688C | fact | Sky 120，第 6 页的浅底默认链接色，对应自定义颜色 27 |
| link-dark | #F0CC72 | user | Brand 170，第 6 页的深底链接色，对应自定义颜色 2 |
| footer-light | #514C47 | fact | Neutral 140，第 8 页的浅底页脚文字色 |
| footer-dark | #AEA8A2 | fact | Neutral 70，第 8 页的深底页脚文字色 |

- 材料明文，第 5 页：使用规定的主题和自定义颜色，不使用 PowerPoint 自动生成的色阶及“标准颜色”。Oracle Red 同时是浅底文字可用的强调色。
- 来源冲突：第 5 页说明写 Brand 170 为 `#F0CC72`，源文件主题 `accent4` 和 `folHlink` 实际存储 `#F0CC71`。依用户确认，本预设统一采用 `#F0CC72`，保留此差异记录。
- 未规定主色与辅助色的面积比例。不得补造官方比例或固定的成功、警告、错误语义色。
- 生成器颜色角色使用 `colors.footer_light=#514C47` 与 `colors.footer_dark=#AEA8A2`，分别绑定浅底与深底页脚。它们对应上表的 `footer-light` / `footer-dark`，不改变原主题槽位顺序。

### Portable PowerPoint Theme

- `brand_theme.xml` 保存源文件 `ppt/theme/theme1.xml` 的完整主题，包括 `Flat` 格式矩阵、对象默认样式、50 个命名自定义颜色和主题家族信息。它是本 Brand 的身份资源；不包含页面原型、母版或版式的结构、坐标，也不改变 Layout 的中性身份。
- 保留源 `clrScheme` 的槽位顺序与数值对应：`dk1=#2A2F2F`、`lt1=#FFFFFF`、`dk2=#2A2F2F`、`lt2=#FBF9F8`、`accent1=#04536F`、`accent2=#6C3F49`、`accent3=#C74634`、`accent4=#F0CC72`、`accent5=#89B2B0`、`accent6=#86B596`、`hlink=#00688C`、`folHlink=#F0CC72`。深浅页面的文字/背景映射由所选 Layout 决定，不通过交换这些槽位实现。
- 相对源主题仅有已确认的字体与金色覆盖：major/minor Latin 使用 Oracle Sans Tab，major/minor East Asian 使用 Source Han Sans SC，`#F0CC71` 统一为 `#F0CC72`。保留全部自定义颜色原名、顺序和数值，包括源名称中的拼写与空格。
- 应用模板时复制此文件并纳入安装回执。新建演示文稿须在颜色引用生成前按真实 RGB 重新绑定主题槽位；主题中不存在的项目色保持直接 RGB。最终打包保留完整主题，不以默认 Office 效果或仅有改名的主题替代。保留源文件的 round-trip / mirror 导出不自动套用此 Brand 主题。
- 此 XML 不引用外部关系或额外文件；使用本 Brand 无需原始 PPTX。上述内容是所提供模板的实现与用户确认结果，不构成独立核验的最新官方品牌规范。

## III. Typography

| Role | Family | Weight | Provenance |
|---|---|---|---|
| title | Oracle Sans Tab | Bold / 700 | 第 3–10 页及直接继承版式的实际观察；用户明确确认 |
| body | Oracle Sans Tab | Regular / 400 | 模板实际观察；用户明确确认 |
| emphasis | Oracle Sans Tab | Bold / 700 | 用户明确确认正文局部强调使用 Bold |
| title-zh | Source Han Sans SC（思源黑体） | Bold / 700 | 用户指定，不是源模板明文规定 |
| body-zh | Source Han Sans SC（思源黑体） | Regular / 400 | 用户指定，不是源模板明文规定 |
| emphasis-zh | Source Han Sans SC（思源黑体） | Bold / 700 | 用户指定的中文家族及局部加粗规则 |

- 英文使用 Oracle Sans Tab；简体中文使用思源黑体。不自行替换为相似字体。目标环境缺少字体时，在具体项目中处理字体安装或替代选择。
- 主题虽然登记 `majorLatin=Georgia`，第 3–10 页的标题被版式覆盖为 Oracle Sans Tab Bold。本预设不将 Georgia 设为统一标题字体。
- 源文件未明确指定中文字体。不得把思源黑体标记为 Oracle 官方要求。
- 材料明文，第 9 页：沿用模板的标题和文字格式，不任意改变文字间距。具体字号和排版留给使用本预设的项目决定。
- 不打包字体文件，也不根据本预设推断字体的再分发许可。
- 应用到实际 PPT 时，主题的 major/minor Latin 字体采用 Oracle Sans Tab，East Asian 字体采用 Source Han Sans SC，与页面可见文字保持一致；不能只改文字对象而保留 Calibri 或 Microsoft YaHei 的主题回退。

## IV. Logo

- Default Presenting Entity: Oracle。
- File: `../images/oracle-otag.emf`。
- Form: 红底白色 OTag 方形标识。
- Usage: 在采用本品牌页脚标识的页面右下角使用 OTag，保留原素材比例和颜色。此为用户确认的使用方式，不应扩大解释为 Oracle 规定所有页面必须出现标识。
- Source: `ppt/media/image1.emf`，由源文件的 `ppt/slideMasters/slideMaster1.xml` 以名称 `OTag` 引用。采用源文件内嵌资产，未重新绘制或转换。
- Asset SHA-256: `51d67140624a137b6d086735f045f70ddbf32d8017e544af675f82c156666e2d`。
- 标识内嵌颜色与主题 Oracle Red 的数值并不完全相同。保持原文件，不按主色表重新染色。
- 第 3–10 页继承此未隐藏的母版标识。这是源文件结构观察。2026-11-03 的 v10 审阅 PPTX 已通过 PowerPoint 原生 PDF 渲染核验，包含普通页的母版标识与图片遮挡页的同位前景标识。EMF 在浏览器预览中可能不显示，不能据此删除或替换原素材。
- 来源未给出标识最小尺寸、安全留白或完整字标的用法。本预设不补造这些官方规定，也不从商标出现推断额外授权。

- 采用提供固定标识区域的 Layout 时，将本 Brand 的原始标识放入最终 PPT 的母版，位置和显示尺寸遵循 Layout。普通页面继承母版；仅在 Layout 明确声明的图片遮挡例外中添加同位前景标识。Brand 不重复定义画布坐标，不把源稿某次摆放尺寸当作官方最小尺寸，也不逐页重复添加标识。

### Footer

以下为第 8 页的材料明文规则，按具体演示文稿的实际用途应用：

- 版权文本为 `Copyright © {year}, Oracle and/or its affiliates`。仅将 `{year}` 替换为演示文稿使用当年的年份，其余版权文字不变。
- 除标题页和结束页外，版权信息置于各页底部相同位置。此例外只针对版权页脚，不能直接推导出标识必须隐藏。
- 浅底版权文字使用 `footer-light`，深底使用 `footer-dark`。
- 公开活动可只保留版权文字，删除分隔符 `|` 及右侧保密内容。
- 保密材料保留保密部分，并依据该材料的实际分类选择等级。例如 `Copyright © {year}, Oracle and/or its affiliates | Confidential: Internal`。
- 可用等级为 `Internal`、`Restricted`、`Highly Restricted`。不得把三个备选等级并列当作最终页脚，也不在全局预设中替所有项目决定保密等级。

- 创建提示词已明确“公开”或某个保密等级时，直接作为该项目选择，不重复询问；未明确时在生成前确认一次，不根据受众自行定级，也不默认按公开活动省略。将选定的唯一等级写入项目规范并据此检查最终页脚。

## V. Voice & Tone

- Formality: formal。
- Person: none。默认中性叙述，按需要明确写出 Oracle、客户或具体责任主体。
- Emoji: forbidden。正文不使用装饰性 emoji。
- Abbreviations: spell-out-first。缩写首次出现时给出全称或解释。
- 以上为本预设的表达建议，来源是说明材料的直接、内容优先表达方式，并非材料明确规定的完整官方语气政策。
- 材料明文，第 4 页：内容页以内容为主。不要让装饰取代信息。

## VI. Icon Style

- Preference: linear。
- 用户指定：使用简洁线性图标，并使用已经确认的品牌配色。
- 在同一份演示文稿中保持线条和图标家族一致。不得将这个建议标记为 Oracle 官方图标库标准。
- 第 3–10 页没有指定官方图标库或固定线宽。本预设不虚构这些要求，不附带第三方图标文件。

## VII. Visual Assets

| File | Role | Provenance |
|---|---|---|
| `../images/oracle-otag.emf` | 默认 Oracle OTag 标识 | 源 PPTX 内嵌文件的逐字节副本；用户确认采用 |
| `brand_theme.xml` | 完整可移植 PowerPoint 主题 | 源主题及本规范列出的用户确认覆盖 |
| `../images/oracle-title-pillar-dark.jpg` | 主品牌深色封面背景 | 源 `ppt/media/image2.jpg` 逐字节副本 |
| `../images/oracle-wordmark-white.svg` | 深底白色 Oracle 字标 | 源 `ppt/media/image3.svg` 逐字节副本 |
| `brand_assets.json` | 图片与强调颜色的语义角色绑定 | 不包含位置、大小或版式清单 |

- 收录上述身份资源及源模板主品牌封面的背景与字标；示例人物照片、产品截图和其他行业封面未作为通用品牌资产收录。
- 材料明文，第 10 页：使用经过许可核验的获准来源图片；摄影应反映真实世界；避免叠加虚构界面、明显摆拍或偏离品牌的 AI 图形。使用 AI 图片和视频时遵守材料所指向的相关指南。
- 此文件记录了上述图片原则，未访问或核验源材料链接中的完整摄影与 AI 指南，不能视为这些指南的替代品。

### Cover assets

`cover-background` 提供源主品牌深色封面的1920×1080 JPEG，已包含深色底及右侧纹样。`wordmark-on-dark` 提供源白色字标 SVG。`corner-mark` 提供原始 OTag EMF。资源按原始字节保存，位置、尺寸、裁切与继承层由 Layout 定义，不在 Brand 重复规定。

`cover-accent` 使用用户已确认的 `#F0CC72`，对应源短矩形强调标记的颜色；源对象原值 `#F0CC71` 保留在差异记录中。安装 Brand 与带有对应角色的 Layout 时绑定图片 href 和强调填充。只有明确声明对应角色的页面才使用封面资源，普通内容页不自动添加封面装饰。

### Agenda and content-divider assets

源第24页、Layout46的固定右上纹样`ppt/media/image30.svg`逐字节保存为`../images/oracle-agenda-decoration.svg`，角色为`agenda-decoration`。这是固定品牌装饰，不是需要填写的图片内容。位置、可视窗口、裁切比例和是否使用由Layout声明，Brand不存画布坐标。

`agenda-card-fill=#464F4F`和`agenda-card-accent=#99ADAE`来自第24页的卡片及顶部色条。`content-divider=#8B8580`来自第30、34、35页的列分隔线。它们是本参考模板的颜色观察值，非新增的官方品牌规则；分隔线粗细、长度及可视透明度留给Layout。

第34、35、44页中的图标和第22页中的照片是可替换内容，且包含示意用途标识。它们不登记为Brand身份资产。图片槽与图标槽的几何和裁切归Layout，实际文稿可替换为自己的合规素材。
