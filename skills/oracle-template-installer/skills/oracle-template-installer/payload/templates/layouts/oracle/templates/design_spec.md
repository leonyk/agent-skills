---
layout_id: oracle
kind: layout
category: general
summary: 16:9 结构模板，支持图文解释、双栏比较、数据图表与说明，适合现场演讲及会后阅读。
keywords:
- 图文解释
- 双栏比较
- 数据图表
- 表格
- 深色预览
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: 0 0 1280 720
source_canvas_width: 1280
source_canvas_height: 720
source_viewbox: 0 0 1280 720
replication_mode: standard
native_structure_mode: structured
page_count: 23
page_types:
- cover
- toc
- chapter
- chapter_image
- content_single
- content_dual
- content_three_columns
- content_comparison
- content_row_comparison
- content_table
- content_chart
- content_chart_four_notes
- content_single_metric
- content_image_right
- content_image_left
- content_grouped_image
- content_two_images
- content_screenshot
- content_three_icons
- content_four_icons
- content_left_rail
- content_three_points
- ending
placeholders:
  01_cover:
  - '{{TITLE}}'
  - '{{SUBTITLE}}'
  - '{{AUTHOR}}'
  - '{{DATE}}'
  02_toc:
  - '{{PAGE_TITLE}}'
  - '{{ITEM_1}}'
  - '{{DETAIL_1}}'
  - '{{ITEM_2}}'
  - '{{DETAIL_2}}'
  - '{{ITEM_3}}'
  - '{{DETAIL_3}}'
  - '{{ITEM_4}}'
  - '{{DETAIL_4}}'
  - '{{ITEM_5}}'
  - '{{DETAIL_5}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  03a_chapter:
  - '{{CHAPTER_NUM}}'
  - '{{CHAPTER_TITLE}}'
  - '{{CHAPTER_DESC}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  03b_chapter_image:
  - '{{CH_TITLE}}'
  - '{{SUBTITLE}}'
  04a_content_single:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{CONTENT_AREA}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04b_content_dual:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{LEFT_HEADING}}'
  - '{{LEFT_CONTENT}}'
  - '{{RIGHT_HEADING}}'
  - '{{RIGHT_CONTENT}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04c_content_three_columns:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{COL_1_BODY}}'
  - '{{COL_2_BODY}}'
  - '{{COL_3_BODY}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04d_content_comparison:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{LEFT_HEADING}}'
  - '{{LEFT_CONTENT}}'
  - '{{RIGHT_HEADING}}'
  - '{{RIGHT_CONTENT}}'
  - '{{KEY_MESSAGE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04e_content_row_comparison:
  - '{{PAGE_TITLE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  - '{{LEFT_HEADING}}'
  - '{{RIGHT_HEADING}}'
  - '{{LEFT_ITEM_1}}'
  - '{{RIGHT_ITEM_1}}'
  - '{{LEFT_ITEM_2}}'
  - '{{RIGHT_ITEM_2}}'
  - '{{LEFT_ITEM_3}}'
  - '{{RIGHT_ITEM_3}}'
  - '{{LEFT_ITEM_4}}'
  - '{{RIGHT_ITEM_4}}'
  - '{{LEFT_ITEM_5}}'
  - '{{RIGHT_ITEM_5}}'
  04f_content_table:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{KEY_MESSAGE}}'
  - '{{SOURCE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04g_content_chart:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{INSIGHT_HEADING}}'
  - '{{CONTENT_AREA}}'
  - '{{SOURCE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04h_content_chart_four_notes:
  - '{{PAGE_TITLE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  - '{{A_TITLE}}'
  - '{{A_BODY}}'
  - '{{B_TITLE}}'
  - '{{B_BODY}}'
  - '{{C_TITLE}}'
  - '{{C_BODY}}'
  - '{{D_TITLE}}'
  - '{{D_BODY}}'
  - '{{SOURCE}}'
  04i_content_single_metric:
  - '{{PAGE_TITLE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  - '{{VALUE}}'
  - '{{METRIC_DESCRIPTION}}'
  - '{{SOURCE}}'
  04j_content_image_right:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{CONTENT_AREA}}'
  - '{{IMAGE_CAPTION}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04k_content_image_left:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{IMAGE_CAPTION}}'
  - '{{CONTENT_AREA}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04l_content_grouped_image:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  - '{{SECTION_1_TITLE}}'
  - '{{SECTION_1_BODY}}'
  - '{{SECTION_2_TITLE}}'
  - '{{SECTION_2_BODY}}'
  - '{{SECTION_3_TITLE}}'
  - '{{SECTION_3_BODY}}'
  - '{{IMAGE_CAPTION}}'
  04m_content_two_images:
  - '{{PAGE_TITLE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  - '{{LEFT_CAPTION}}'
  - '{{LEFT_DESCRIPTION}}'
  - '{{RIGHT_CAPTION}}'
  - '{{RIGHT_DESCRIPTION}}'
  04n_content_screenshot:
  - '{{PAGE_TITLE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  - '{{DESCRIPTION}}'
  - '{{IMAGE_CAPTION}}'
  04o_content_three_icons:
  - '{{PAGE_TITLE}}'
  - '{{COL_1_HEAD}}'
  - '{{COL_1_BODY}}'
  - '{{COL_2_HEAD}}'
  - '{{COL_2_BODY}}'
  - '{{COL_3_HEAD}}'
  - '{{COL_3_BODY}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04p_content_four_icons:
  - '{{PAGE_TITLE}}'
  - '{{COL_1_HEAD}}'
  - '{{COL_1_BODY}}'
  - '{{COL_2_HEAD}}'
  - '{{COL_2_BODY}}'
  - '{{COL_3_HEAD}}'
  - '{{COL_3_BODY}}'
  - '{{COL_4_HEAD}}'
  - '{{COL_4_BODY}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  04q_content_left_rail:
  - '{{PAGE_TITLE}}'
  - '{{SUBTITLE}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  - '{{RAIL_CONTENT}}'
  - '{{CONTENT_AREA}}'
  04r_content_three_points:
  - '{{PAGE_TITLE}}'
  - '{{INTRO}}'
  - '{{POINT_1_BODY}}'
  - '{{POINT_2_BODY}}'
  - '{{POINT_3_BODY}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
  05_ending:
  - '{{THANK_YOU}}'
  - '{{ENDING_SUBTITLE}}'
  - '{{CONTACT_INFO}}'
  - '{{PAGE_NUM}}'
  - '{{SECTION_NAME}}'
---

# Oracle — Design Specification

## IV. Signature Design Elements

### Canvas and source geometry

画布为 1280 × 720，viewBox 为 `0 0 1280 720`。原始 PPTX 为 12192000 × 6858000 EMU，即 13⅓ × 7.5 英寸。源文件 `template-dark.pptx` 的 1 个母版、113 个版式及 57 张示例页用于结构分析，本模板独立重建为 1 个母版和 23 个版式。

### Master and layout ownership

`master_defaults.json` 和 `master-defaults/` 是本模板的原生默认值与稀疏继承契约。母版包含标题、正文、日期、页脚、页码五种真实占位符，以及中性标识图像。通用标题、正文和系统字段的默认值只保留在所属层，页面通常仅保存内容和显式局部覆写。各版式的几何例外由配置逐项列明，不根据“坐标刚好相等”推断继承。

普通标题和页脚/页码的通用几何来自母版；单栏正文采用原稿的母版正文框 `80.72 168 1120.32 474`。封面、章节、窄标题、图片组合、分栏和半幅页脚保留版式几何。母版正文一级至九级默认使用原稿的16 pt，恢复原稿的缩进、符号、95%/90%行距、6/4/5 pt段前及96 px制表位。具体文稿显式指定正文大小时可以覆盖该默认值，各层级仍使用相同正文大小。普通标题在版式保留原稿的100%行距与粗体，但字号和通用几何继续继承母版。

母版默认浅底，内容版式覆盖为深底；具体颜色、字体和标识由 Brand 提供。Layout 的颜色是中性预览值。使用 Oracle Brand 时，完整 Flat 主题、原颜色槽顺序及50个命名颜色由 Brand 主题文件提供，并保留用户确认的字体和金色覆盖值。

标识通用框为 `1197.44 678.72 41.28 41.28`，普通页继承母版的单个图片。分组图文的满幅照片会覆盖该区域，保留一个同位置的页面前景图片，替换品牌时与母版引用同一资源。页脚不画横线。页码为自动字段；日期恢复母版/版式编辑能力，但默认不在内容页实例化，原有封面日期仍可填写。

页码通用框为 `80 674.4 38.4 38.4`，页脚通用框为 `118.4 674.43 921.6 38.33`。分组图文页脚仅保留左半幅，右边界 x=580。提示文案不替代实际页脚，版权及保密等级由创建提示词和项目内容决定。

### Cover artwork and placement

封面恢复参考 `Dark - Title_Pillar` 的空间关系。背景是原生 Layout 背景，整页铺放且不裁切；禁止用普通整页图片遮住母版标识。`cover-background` 与 `wordmark-on-dark` 由选中 Brand 的 `brand_assets.json` 提供，未选择 Brand 时使用中性预览资源。右下角及图片前景标识使用 `corner-mark` 角色。

强调标记是无描边实心矩形 `83.34 437.39 38.4 3.84`。其 `cover-accent` 颜色由 Brand 提供，不用细长描边线替代。左上字标框为 `76.71 118.88 160.09 33.60`。主标题框 `83.21 225.60 672 134.40`，副标题框 `83.21 369.51 672 35.83`，作者框 `83.21 477.12 533.12 27.96`，日期框 `83.21 512.64 533.12 93.98`。标题最多两行，副标题单行；这些左侧文本框避免覆盖右侧品牌图案。坐标保留到0.01 px。

这些是 Layout 几何与资源角色，不是品牌颜色、字体或图片副本。原有17个版式保持，v13另补充6个版式；普通内容页不套用封面图案。完整主题文件不替代品牌资源文件。使用安装后的原型创建新页面时保留角色标记及已绑定的 href。

### Grid and text roles

| 区域 | 几何与行为 |
|---|---|
| 内容页横向范围 | x=80 至 1200，宽 1120，左右边距均为 80。 |
| 标题 | `80.72 19.15 1120.32 86.4`，左对齐，文字靠近框底部，支持一至两行并固定最后一行的位置。右侧图片版式宽度为 712.88。 |
| 副标题 | `80.5 106.03 1120.32 34.7`，单行，紧接主标题区；与正文保持独立框。右侧图片版式宽度为 712.88。 |
| 正文 | 单栏正文从 y=168 开始，其他版式按各自内容框起排。单栏、双栏分别使用自己的完整占位框。 |
| 双栏 | x=80、667，每栏宽533，中间留白54。两栏标题和正文上沿一致。 |
| 页脚 | 不添加页脚横线；页码 `80 674.4 38.4 38.4`；说明 `118.4 674.43 921.6 38.33`。 |
| 文字入口 | 正文从占位框左上方开始，左对齐，自然换行。标题按语义断行；不使用两端对齐。 |
| 段落节奏 | 正文使用真实段落；组内换行保留在同一段落。段间在基准行距之外增加留白，双栏的同级内容使用相同节奏。审阅稿第 3、5 页段前额外留白为 9 pt，属于可替换预览值。 |

### Vertical alignment contract

解释正文和文本型通用对象固定从框顶起排，短文与接近容量的长文使用相同入口。原型中的 `data-pptx-vertical-align` 明确记录例外；文字长度不决定垂直对齐。

常规内容页主标题底部对齐；封面、章节和结束页主标题垂直居中。副标题、页码、页脚以及紧凑行框中的小标题、单行图注、来源和结论沿用各自原型的显式位置。第 13 页的对应行单元格垂直居中；第 15 页大数值底部对齐。多行解释正文不因这些例外改为居中。各槽的精确值见下表。

### Capacity and density

默认母版字号对齐原稿：标题24 pt、正文一级至九级16 pt、其他文字18 pt、页码/页脚/日期8 pt。正文预览锚点为单栏正文框的21.33 px，导出后为16 pt；禁止用文稿演示用的21 pt覆盖默认模板。内容页副标题仍为独立版式值20 pt，其他版式的专用字级按各自占位框保留。所有这些默认值都允许具体文稿显式覆盖，不属于Brand字级锁定。主标题最后一行靠标题区下缘，副标题独立成行，单栏正文从 y=168 开始。这些容量对应审阅稿的临时字级，是常用内容量，不是自动缩字规则。更换语言、字体或字号后，需要重新测量文本。

| 页面 | 典型内容容量 |
|---|---|
| 封面与章节 | 主标题最多两行；副标题或章节说明一至两行；封面作者、日期各一行。 |
| 单栏 | 四至六个短要点，每项一至两行；约 180–300 个汉字，或四个短段落。 |
| 双栏 | 每栏三至四个短要点，每项一至两行；约 90–150 个汉字。 |
| 比较 | 每栏三个对齐比较项，底部共同结论一行。比较维度顺序一致。 |
| 图表与说明 | 左侧一个图表；右侧一条小标题、两至三个解释段；约 70–110 个汉字。 |
| 表格 | 审阅示例为四列、表头加六行；常用三至五列、五至七行；格内优先一行短语。表下结论一至两行。 |
| 图文 | 文字约 100–180 个汉字，照片保留主体识别区域；图注一至两行，且不混入页脚。 |
| 结束 | 一至两行结束语，一至两行补充信息及联系方式。 |

### Image and data behavior

左文右图使用 `854 0 426 608` 的竖向图片框，按比例填满并裁切，主体落在中部。图片下方 `854 622 346 30` 放置图注。裁切不得挤压人物主体；替换图片后需要检查主体位置。

左图右文使用 `80 184 660 414` 图片框，按比例完整显示，适合横向图片、截图和已经排版的图；比例不匹配时保留空白。图注位于 `80 620 660 32`。两种方式均不拉伸图片。

图表版式声明真实 chart 占位符，表格版式声明真实 table 占位符。SVG 中的图表及表格 JSON 为模板示例数据，审阅 PPTX 将其编译为原生对象，数值可编辑。图表页的来源独立于图表数据对象，位于底部。

图片框使用从参考文件提取的两张带有“Placeholder image”字样的示意照片。`images/preview-portrait.jpeg` 来自 `image96.jpeg`，`images/preview-landscape.jpeg` 来自 `image104.jpeg`。这些文件仅帮助识别占位与裁切，不承担品牌身份，也不声明额外素材许可。实际演示文稿在图片槽中替换它们。

### Title and subtitle source mapping

原稿常规内容标题使用母版的底部对齐框，副标题在原文件中虽然登记为 `body` 占位符，但名称和内容为 `Subtitle`。本模板依据其作用将它标为原生 `subTitle`，保留独立标题区、位置与相对层级。识别依据同时包括占位符名称、文本、父级位置与字级，不能只依赖 OOXML 的 `body` 类型。

### Added source-aligned structures

新增七个原型对应源文件第 32、36、38、49、50、52、54 页。分组图文保留三组独立小标题和说明，右侧半幅图片；双图页保留两个独立图片槽及图注，通常每侧不超过三行说明。窄侧栏的左侧正文约 80–120 个汉字，右侧通用对象区可承载图表、图示或文字。

逐行比较提供五组对应内容，每格约一至两行。截图说明使用居中的左侧标题，截图完整显示，图注位于图片下方。单项指标突出一个值，单位包含在值中，含义和口径使用独立文字框。环形图与四周说明提供四组小标题和正文，每组通常两至四行；图表数值在原生图表中编辑。

新增两张示意照片来自原文件的 `image97.jpeg`、`image103.jpeg`，均保留占位说明。截图示例来自本模板表格原型的渲染并去掉页脚，只用于展示完整图片的适配方式。品牌图形和品牌背景的资源由 Brand 提供；本 Layout 通过语义角色记录放置与继承方式。

### Prototype scope

下列原型描述可用的页面结构，不规定未来演示文稿的页数、顺序、主题或叙事。每个原型对应一个独立版式。

### v13 ownership and source behavior

六个增补来自原稿第30、34、44、24、22、35页，分别对应原生Layout72、84、60、46、16、86。原有17个原型保持。新原型不是固定的未来页数或顺序。

Layout拥有槽位、原稿几何、图片裁切、列分隔与卡片形状；Brand提供agenda-decoration、agenda-card-fill、agenda-card-accent、content-divider及已有cover-accent和corner-mark。Brand不存这些元素的画布坐标。图标与章节照片是可替换示例内容，不是品牌身份资产。

议程原稿的五个组合对象没有原生占位符。本次保持五个卡片的几何，将每卡标题与说明拆成独立可编辑槽。卡片横向坐标为83.20、314.51、545.82、777.14、1008.45，宽192，高211.20，顶端色条高9.60。新增的槽位语义属于本次设计，不冒称源文件已有结构。议程纹样的可见窗口为719.80 0 560.20 288，保留源左裁切5.687%及下裁切27.270%。

图片章节保留原照片的底部标识缺口。右侧图片框归一为640 0 640 720，源框右侧超出画布0.32 px已裁齐。标识为Layout前景资产绑定，沿用母版标识位置及尺寸。原稿页脚和页码在画幅外，本原型不实例化这两类字段，母版定义继续可编辑，日期定义默认关闭。源画外编辑说明不进入模板。

三栏正文、图标小标题和正文、三要点说明的默认值为16 pt。三要点主标题32 pt，图片章节主标题40 pt与副标题20 pt。默认字级只用于复现源稿并提供可覆盖起点，字体身份由Brand提供，整体字号仍可由具体文稿设定。换语言或字号后重新核对容量。

| 原型 | 典型容量 |
|---|---|
| `05_content_three_columns` | 一行16–26字；一行18–35字；每栏4–6条短要点；每栏约80–130字。源16pt，约15字/行。 |
| `06_content_three_icons` | 一行16–26字；每项4–10字，单行；每项3–5行，约30–50字。源16pt，约10字/行。 |
| `07_content_three_points` | 左侧2–5行，约18–32字。源32pt。；2–3行，约35–55字。源16pt。；每个要点不超过2行，约20–40字。源16pt。 |
| `08_toc` | 一行12–20字；每卡4–7字，单行；每卡2–4行，约12–28字。标题与正文源16pt。 |
| `09_chapter_image` | 左侧2行优先，约10–16字。源40pt，底部对齐。；1–2行，约14–26字。源20pt。；右半幅图片，640×720；替换后检查人物/主体和右下角凹口。 |
| `10_content_four_icons` | 一行16–26字；每项4–8字，单行；每项3–5行，约25–45字。源16pt，约9字/行。 |

## V. Page Roster

本页序用于模板目录和审阅导航：封面、目录、章节变体、内容变体、结束页。内容变体按信息形态分组，23个原型均保留一次。该顺序不是未来文稿的规定叙事；原有17个与增补6个都是可选版式示例。文件名控制默认预览顺序，稳定Layout key保持不变。

| SVG | Master | Layout key | PowerPoint picker name | Content shape |
|---|---|---|---|---|
| `01_cover.svg` | `oracle-master` | `01_cover` | 01 封面 | 左侧两行主标题与单行副标题，短矩形强调标记、作者与日期分层；整页背景及左上字标通过 Brand 角色绑定。 |
| `02_toc.svg` | `oracle-master` | `08_toc` | 02 五项目录 | 原稿第 24 页。五个横向议程卡片，每卡独立标题和说明；原稿组合对象重构为原生占位区域。 |
| `03a_chapter.svg` | `oracle-master` | `02_chapter` | 03 章节 | 独立章节编号，左对齐章节标题和两行说明。 |
| `03b_chapter_image.svg` | `oracle-master` | `09_chapter_image` | 04 图片章节 | 原稿第 22 页。左侧章节标题、副标题及短矩形强调，右侧可替换图片带标识缺口，不显示页码及页脚。 |
| `04a_content_single.svg` | `oracle-master` | `03a_content_single` | 05 单栏内容 | 一个宽正文区，可容纳解释段落或四至六个简短要点。 |
| `04b_content_dual.svg` | `oracle-master` | `03b_content_dual` | 06 双栏内容 | 等宽双栏，每栏独立标题与正文，间距约54 px。 |
| `04c_content_three_columns.svg` | `oracle-master` | `05_content_three_columns` | 07 三栏内容 | 原稿第 30 页。标题、副标题与三栏独立正文，三栏保留原稿轻微的纵向偏移。 |
| `04d_content_comparison.svg` | `oracle-master` | `03c_content_comparison` | 08 双栏比较 | 两组标题和比较文字对齐，底部留一个共同结论区。 |
| `04e_content_row_comparison.svg` | `oracle-master` | `03k_content_row_comparison` | 09 逐行对应比较 | 原稿第 49 页：五组左右对应内容，固定行对齐与方向箭头。 |
| `04f_content_table.svg` | `oracle-master` | `03e_content_table` | 10 表格 | 原生四列表格示例，表头加六行数据，表下结论和来源。 |
| `04g_content_chart.svg` | `oracle-master` | `03d_content_chart` | 11 图表与说明 | 左侧原生数据图表，右侧解释，底部独立来源。 |
| `04h_content_chart_four_notes.svg` | `oracle-master` | `03n_content_chart_four_notes` | 12 图表与四周说明 | 原稿第 54 页：中心原生环形图，四周四组独立小标题和说明。 |
| `04i_content_single_metric.svg` | `oracle-master` | `03m_content_single_metric` | 13 单项指标 | 原稿第 52 页：单个大数字配指标含义与统计口径，保留大块留白。 |
| `04j_content_image_right.svg` | `oracle-master` | `03f_content_image_right` | 14 左文右图 | 右侧三分之一竖向图片直达上沿和右沿，左侧为正文。 |
| `04k_content_image_left.svg` | `oracle-master` | `03g_content_image_left` | 15 左图右文 | 完整横向图片或截图位于左侧，右侧解释，图片下方图注。 |
| `04l_content_grouped_image.svg` | `oracle-master` | `03h_content_grouped_image` | 16 分组图文 | 原稿第 32 页：左侧三组独立小标题及正文，右侧半幅图片。 |
| `04m_content_two_images.svg` | `oracle-master` | `03i_content_two_images` | 17 双图比较 | 原稿第 36 页：两个等宽图片区，各自拥有图注标题与说明。 |
| `04n_content_screenshot.svg` | `oracle-master` | `03l_content_screenshot` | 18 截图说明 | 原稿第 50 页：左侧居中标题及说明，右侧完整显示截图，图注在下。 |
| `04o_content_three_icons.svg` | `oracle-master` | `06_content_three_icons` | 19 三图标内容 | 原稿第 34 页。三组可替换图标、小标题及正文，列分隔线由版式定义。 |
| `04p_content_four_icons.svg` | `oracle-master` | `10_content_four_icons` | 20 四图标内容 | 原稿第 35 页。四组可替换图标、小标题及正文，适合更短的并列说明。 |
| `04q_content_left_rail.svg` | `oracle-master` | `03j_content_left_rail` | 21 窄侧栏 | 原稿第 38 页：左侧窄栏承载标题和概述，右侧完整区域承载主内容对象。 |
| `04r_content_three_points.svg` | `oracle-master` | `07_content_three_points` | 22 三要点内容 | 原稿第 44 页。左侧大标题，右侧独立导语及三组图标与短说明。 |
| `05_ending.svg` | `oracle-master` | `04_ending` | 23 结束 | 大字号结束语、补充信息和联系方式分层排列。 |

### Slot geometry

下表是192个可填内容槽的有效框，单位为画布px。原生文件的局部xfrm可以省略，由父层解析得到这些框。除封面已有日期外，22个默认关闭的日期定义只存在于版式层，不计入可填内容槽。

| Prototype | Slot | Role | Effective frame |
|---|---|---|---|
| `01_cover` | `title-slot` | `title` | `83.21 225.6 672 134.4` |
| `01_cover` | `subtitle-slot` | `subtitle` | `83.21 369.51 672 35.83` |
| `01_cover` | `author-slot` | `body` | `83.21 477.12 533.12 27.96` |
| `01_cover` | `date-slot` | `date` | `83.21 512.64 533.12 93.98` |
| `08_toc` | `title-slot` | `title` | `80.72 19.15 565.18 86.4` |
| `08_toc` | `item-1-title-slot` | `body` | `92.8 268.8 172.8 100.8` |
| `08_toc` | `item-1-body-slot` | `body` | `92.8 369.6 172.8 100.8` |
| `08_toc` | `item-2-title-slot` | `body` | `324.11 268.8 172.8 100.8` |
| `08_toc` | `item-2-body-slot` | `body` | `324.11 369.6 172.8 100.8` |
| `08_toc` | `item-3-title-slot` | `body` | `555.42 268.8 172.8 100.8` |
| `08_toc` | `item-3-body-slot` | `body` | `555.42 369.6 172.8 100.8` |
| `08_toc` | `item-4-title-slot` | `body` | `786.74 268.8 172.8 100.8` |
| `08_toc` | `item-4-body-slot` | `body` | `786.74 369.6 172.8 100.8` |
| `08_toc` | `item-5-title-slot` | `body` | `1018.05 268.8 172.8 100.8` |
| `08_toc` | `item-5-body-slot` | `body` | `1018.05 369.6 172.8 100.8` |
| `08_toc` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `08_toc` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `02_chapter` | `number-slot` | `body` | `80 202 144 112` |
| `02_chapter` | `title-slot` | `title` | `280 214 920 144` |
| `02_chapter` | `description-slot` | `body` | `280 414 840 120` |
| `02_chapter` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `02_chapter` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `09_chapter_image` | `title-slot` | `title` | `80.72 245.37 460.8 134.4` |
| `09_chapter_image` | `subtitle-slot` | `subtitle` | `81.54 434.14 460.8 71.52` |
| `09_chapter_image` | `picture-slot` | `picture` | `640 0 640 720` |
| `03a_content_single` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03a_content_single` | `subtitle-slot` | `subtitle` | `80.5 106.03 1120.32 34.7` |
| `03a_content_single` | `body-slot` | `body` | `80.7217847769 168 1120.32 474` |
| `03a_content_single` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03a_content_single` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03b_content_dual` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03b_content_dual` | `subtitle-slot` | `subtitle` | `80.5 106.03 1120.32 34.7` |
| `03b_content_dual` | `left-heading-slot` | `body` | `80 180 533 42` |
| `03b_content_dual` | `left-body-slot` | `body` | `80 244 533 396` |
| `03b_content_dual` | `right-heading-slot` | `body` | `667 180 533 42` |
| `03b_content_dual` | `right-body-slot` | `body` | `667 244 533 396` |
| `03b_content_dual` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03b_content_dual` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `05_content_three_columns` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `05_content_three_columns` | `subtitle-slot` | `subtitle` | `80.5 106.03 1120.32 34.7` |
| `05_content_three_columns` | `column-1-body-slot` | `body` | `80.5 168.0 345.6 473.28` |
| `05_content_three_columns` | `column-2-body-slot` | `body` | `467.2 168.72 345.6 473.28` |
| `05_content_three_columns` | `column-3-body-slot` | `body` | `853.9 169.44 345.6 473.28` |
| `05_content_three_columns` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `05_content_three_columns` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03c_content_comparison` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03c_content_comparison` | `subtitle-slot` | `subtitle` | `80.5 106.03 1120.32 34.7` |
| `03c_content_comparison` | `left-heading-slot` | `body` | `80 180 533 48` |
| `03c_content_comparison` | `left-body-slot` | `body` | `80 248 533 302` |
| `03c_content_comparison` | `right-heading-slot` | `body` | `667 180 533 48` |
| `03c_content_comparison` | `right-body-slot` | `body` | `667 248 533 302` |
| `03c_content_comparison` | `takeaway-slot` | `body` | `80 598 1120 42` |
| `03c_content_comparison` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03c_content_comparison` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03k_content_row_comparison` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03k_content_row_comparison` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03k_content_row_comparison` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03k_content_row_comparison` | `left-heading-slot` | `body` | `80 146 500 38` |
| `03k_content_row_comparison` | `right-heading-slot` | `body` | `700 146 500 38` |
| `03k_content_row_comparison` | `left-row-1-slot` | `body` | `80 208 500 64` |
| `03k_content_row_comparison` | `right-row-1-slot` | `body` | `700 208 500 64` |
| `03k_content_row_comparison` | `left-row-2-slot` | `body` | `80 290 500 64` |
| `03k_content_row_comparison` | `right-row-2-slot` | `body` | `700 290 500 64` |
| `03k_content_row_comparison` | `left-row-3-slot` | `body` | `80 372 500 64` |
| `03k_content_row_comparison` | `right-row-3-slot` | `body` | `700 372 500 64` |
| `03k_content_row_comparison` | `left-row-4-slot` | `body` | `80 454 500 64` |
| `03k_content_row_comparison` | `right-row-4-slot` | `body` | `700 454 500 64` |
| `03k_content_row_comparison` | `left-row-5-slot` | `body` | `80 536 500 64` |
| `03k_content_row_comparison` | `right-row-5-slot` | `body` | `700 536 500 64` |
| `03e_content_table` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03e_content_table` | `subtitle-slot` | `subtitle` | `80.5 106.03 1120.32 34.7` |
| `03e_content_table` | `table-slot` | `table` | `80 184 1120 350` |
| `03e_content_table` | `takeaway-slot` | `body` | `80 558 1120 56` |
| `03e_content_table` | `source-slot` | `body` | `80 628 1120 24` |
| `03e_content_table` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03e_content_table` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03d_content_chart` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03d_content_chart` | `subtitle-slot` | `subtitle` | `80.5 106.03 1120.32 34.7` |
| `03d_content_chart` | `chart-slot` | `chart` | `80 184 720 414` |
| `03d_content_chart` | `insight-title-slot` | `body` | `856 184 344 42` |
| `03d_content_chart` | `insight-body-slot` | `body` | `856 252 344 340` |
| `03d_content_chart` | `source-slot` | `body` | `80 624 1120 28` |
| `03d_content_chart` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03d_content_chart` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03n_content_chart_four_notes` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03n_content_chart_four_notes` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03n_content_chart_four_notes` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03n_content_chart_four_notes` | `chart-slot` | `chart` | `384 184 512 430` |
| `03n_content_chart_four_notes` | `a-heading-slot` | `body` | `80 200 280 40` |
| `03n_content_chart_four_notes` | `a-body-slot` | `body` | `80 256 280 138` |
| `03n_content_chart_four_notes` | `b-heading-slot` | `body` | `920 200 280 40` |
| `03n_content_chart_four_notes` | `b-body-slot` | `body` | `920 256 280 138` |
| `03n_content_chart_four_notes` | `c-heading-slot` | `body` | `80 428 280 40` |
| `03n_content_chart_four_notes` | `c-body-slot` | `body` | `80 484 280 138` |
| `03n_content_chart_four_notes` | `d-heading-slot` | `body` | `920 428 280 40` |
| `03n_content_chart_four_notes` | `d-body-slot` | `body` | `920 484 280 138` |
| `03n_content_chart_four_notes` | `source-slot` | `body` | `80 628 1120 24` |
| `03m_content_single_metric` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03m_content_single_metric` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03m_content_single_metric` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03m_content_single_metric` | `value-slot` | `body` | `80 168 700 274` |
| `03m_content_single_metric` | `metric-description-slot` | `body` | `80 488 840 92` |
| `03m_content_single_metric` | `source-slot` | `body` | `80 606 1120 38` |
| `03f_content_image_right` | `title-slot` | `title` | `80.72 19.15 712.88 86.4` |
| `03f_content_image_right` | `subtitle-slot` | `subtitle` | `80.5 106.03 712.88 34.7` |
| `03f_content_image_right` | `body-slot` | `body` | `80 180 713 428` |
| `03f_content_image_right` | `picture-slot` | `picture` | `854 0 426 608` |
| `03f_content_image_right` | `caption-slot` | `body` | `854 622 346 30` |
| `03f_content_image_right` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03f_content_image_right` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03g_content_image_left` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03g_content_image_left` | `subtitle-slot` | `subtitle` | `80.5 106.03 1120.32 34.7` |
| `03g_content_image_left` | `picture-slot` | `picture` | `80 184 660 414` |
| `03g_content_image_left` | `caption-slot` | `body` | `80 620 660 32` |
| `03g_content_image_left` | `body-slot` | `body` | `800 184 400 454` |
| `03g_content_image_left` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03g_content_image_left` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03h_content_grouped_image` | `title-slot` | `title` | `80.72 19.15 499.2 86.4` |
| `03h_content_grouped_image` | `subtitle-slot` | `subtitle` | `80.5 106.03 499.2 34.7` |
| `03h_content_grouped_image` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03h_content_grouped_image` | `footer-slot` | `footer` | `118.4 674.43 461.6 38.33` |
| `03h_content_grouped_image` | `group-1-heading-slot` | `body` | `80 196 500 36` |
| `03h_content_grouped_image` | `group-1-body-slot` | `body` | `80 240 500 80` |
| `03h_content_grouped_image` | `group-2-heading-slot` | `body` | `80 338 500 36` |
| `03h_content_grouped_image` | `group-2-body-slot` | `body` | `80 382 500 80` |
| `03h_content_grouped_image` | `group-3-heading-slot` | `body` | `80 480 500 36` |
| `03h_content_grouped_image` | `group-3-body-slot` | `body` | `80 524 500 80` |
| `03h_content_grouped_image` | `picture-slot` | `picture` | `640 0 640 720` |
| `03h_content_grouped_image` | `caption-slot` | `body` | `80 610 500 32` |
| `03i_content_two_images` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `03i_content_two_images` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03i_content_two_images` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03i_content_two_images` | `left-picture-slot` | `picture` | `80 168 520 280` |
| `03i_content_two_images` | `right-picture-slot` | `picture` | `680 168 520 280` |
| `03i_content_two_images` | `left-caption-slot` | `body` | `80 466 520 38` |
| `03i_content_two_images` | `left-description-slot` | `body` | `80 518 520 110` |
| `03i_content_two_images` | `right-caption-slot` | `body` | `680 466 520 38` |
| `03i_content_two_images` | `right-description-slot` | `body` | `680 518 520 110` |
| `03l_content_screenshot` | `title-slot` | `title` | `80 259.43 395.01 86.4` |
| `03l_content_screenshot` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03l_content_screenshot` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03l_content_screenshot` | `description-slot` | `body` | `80 374.17 395.01 170` |
| `03l_content_screenshot` | `screenshot-slot` | `picture` | `563.2 177.19 656.13 395.09` |
| `03l_content_screenshot` | `caption-slot` | `body` | `563.2 594 636.8 46` |
| `06_content_three_icons` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `06_content_three_icons` | `icon-1-slot` | `picture` | `94.26 199.89 198.83 178.28` |
| `06_content_three_icons` | `column-1-heading-slot` | `body` | `95.66 418.24 239.05 34.0` |
| `06_content_three_icons` | `column-1-body-slot` | `body` | `95.66 459.57 239.05 130.7` |
| `06_content_three_icons` | `icon-2-slot` | `picture` | `499.45 199.88 198.83 178.28` |
| `06_content_three_icons` | `column-2-heading-slot` | `body` | `503.66 418.24 239.05 34.0` |
| `06_content_three_icons` | `column-2-body-slot` | `body` | `503.66 459.57 239.05 130.7` |
| `06_content_three_icons` | `icon-3-slot` | `picture` | `904.65 202.5 198.83 178.28` |
| `06_content_three_icons` | `column-3-heading-slot` | `body` | `907.96 418.24 239.05 34.0` |
| `06_content_three_icons` | `column-3-body-slot` | `body` | `907.96 459.57 239.05 130.7` |
| `06_content_three_icons` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `06_content_three_icons` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `10_content_four_icons` | `title-slot` | `title` | `80.72 19.15 1120.32 86.4` |
| `10_content_four_icons` | `icon-1-slot` | `picture` | `80.0 198.98 170.25 160.12` |
| `10_content_four_icons` | `column-1-heading-slot` | `body` | `80.0 418.24 225.41 34.0` |
| `10_content_four_icons` | `column-1-body-slot` | `body` | `80.0 459.57 225.41 130.7` |
| `10_content_four_icons` | `icon-2-slot` | `picture` | `373.6 199.88 170.25 160.12` |
| `10_content_four_icons` | `column-2-heading-slot` | `body` | `373.33 418.24 225.41 34.0` |
| `10_content_four_icons` | `column-2-body-slot` | `body` | `373.33 459.57 225.41 130.7` |
| `10_content_four_icons` | `icon-3-slot` | `picture` | `671.63 200.44 170.25 160.12` |
| `10_content_four_icons` | `column-3-heading-slot` | `body` | `672.0 418.24 225.41 34.0` |
| `10_content_four_icons` | `column-3-body-slot` | `body` | `672.0 459.57 225.41 130.7` |
| `10_content_four_icons` | `icon-4-slot` | `picture` | `969.6 198.98 170.25 160.12` |
| `10_content_four_icons` | `column-4-heading-slot` | `body` | `969.6 418.24 225.41 34.0` |
| `10_content_four_icons` | `column-4-body-slot` | `body` | `969.6 459.57 225.41 130.7` |
| `10_content_four_icons` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `10_content_four_icons` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03j_content_left_rail` | `title-slot` | `title` | `80.72 19.15 319.28 86.4` |
| `03j_content_left_rail` | `subtitle-slot` | `subtitle` | `80.5 106.03 319.28 34.7` |
| `03j_content_left_rail` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `03j_content_left_rail` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `03j_content_left_rail` | `rail-body-slot` | `body` | `80 182 319.5 458` |
| `03j_content_left_rail` | `main-content-slot` | `object` | `456 168 744 472` |
| `07_content_three_points` | `title-slot` | `title` | `81.72 118.0 518.82 484.0` |
| `07_content_three_points` | `intro-slot` | `body` | `639.96 137.38 554.12 105.0` |
| `07_content_three_points` | `point-1-icon-slot` | `picture` | `639.96 250.0 70.09 70.08` |
| `07_content_three_points` | `point-1-body-slot` | `body` | `736.05 265.53 502.03 70.08` |
| `07_content_three_points` | `point-2-icon-slot` | `picture` | `639.96 360.0 70.09 70.08` |
| `07_content_three_points` | `point-2-body-slot` | `body` | `736.05 375.53 502.03 70.08` |
| `07_content_three_points` | `point-3-icon-slot` | `picture` | `639.96 470.0 70.09 70.08` |
| `07_content_three_points` | `point-3-body-slot` | `body` | `736.05 485.53 502.03 70.08` |
| `07_content_three_points` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `07_content_three_points` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |
| `04_ending` | `title-slot` | `title` | `80 240 1120 156` |
| `04_ending` | `subtitle-slot` | `subtitle` | `80 422 1040 76` |
| `04_ending` | `contact-slot` | `body` | `80 552 1040 70` |
| `04_ending` | `page-number-slot` | `slide-number` | `80 674.4 38.4 38.4` |
| `04_ending` | `footer-slot` | `footer` | `118.4 674.43 921.6 38.33` |

## VII. Placeholder Overrides

每个原型的实际文本标记已在 frontmatter 中列出。双栏使用独立的左右标题和正文标记；图表、表格及图片通过各自类型的原生占位符替换。

