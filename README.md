# CRISPR文库测序数据报告生成器

用于自动生成 CRISPR 文库测序数据分析报告的脚本工具。

## 功能特点

- **自动数据扫描**：自动识别数据目录中的 CSV 和 PNG 文件
- **数据可视化**：将 CSV 数据转换为可交互的 HTML 表格
- **图片展示**：支持多种图片展示方式（单图居中、多图网格）
- **交互功能**：表格支持排序、搜索、分页
- **响应式设计**：适配不同屏幕尺寸

## 支持的数据格式

### CSV 数据文件

| 文件 | 说明 |
|------|------|
| `*clean*.csv` | 测序数据质控统计（total_reads, clean_reads, Q20, Q30, GC等） |
| `result.csv` | 比对结果统计（Mapped, NotMapped, Coverage, Depth等） |
| `output.csv` | sgRNA 计数数据（gene, uid, seq, counts） |

### PNG 图片文件

自动识别并分类展示以下类型的图片：

- `*quality*` - 碱基质量分布图
- `*raw*` - 原始Reads分类图
- `*depth*` - 测序深度分布图
- `*uniformity*` - 均一性分析图
- `*volcano*` - 火山图
- `*scatter*` - 散点图
- `*rank*` - 排名图
- `*kegg*` - KEGG通路富集图
- `*go*` - GO功能富集图
- `*correlation*` - 相关性热图
- `*density*` - 密度分布图

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 方式一：运行批处理文件

双击 `run_report.bat` 即可在当前目录生成报告

### 方式二：命令行运行

```bash
python report_generator.py <数据目录> <输出目录> [选项]
```

#### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `data_dir` | 否 | `.` | 数据文件夹路径 |
| `output_dir` | 否 | `./report_output` | 报告输出目录 |
| `--name` | 否 | CRISPR文库分析报告 | 项目名称 |
| `--project-id` | 否 | 自动检测 | 项目编号 |

#### 示例

```bash
# 基本用法
python report_generator.py . ./report_output

# 指定项目名称
python report_generator.py . ./report --name "GK250830-01-LHJ2573"

# 指定项目ID
python report_generator.py . ./report --project-id "PRJ-001"
```

## 输出文件

生成的报告包含以下结构：

```
output_dir/
├── report.html          # 主报告文件（用浏览器打开）
├── css/
│   └── style.css        # 样式文件
├── js/
│   ├── common.js        # 交互脚本
│   └── scrolltop.js     # 返回顶部脚本
├── data/                # 数据文件副本
│   ├── 1. Clean_data/
│   │   └── clean_summary.csv
│   └── 2. Mapping/
│       ├── result.csv
│       └── output.csv
└── images/              # 图片文件副本
    ├── base_quality_and_error_rate.png
    ├── sgRNA_sequencing_depth.png
    └── ...
```

## 报告章节

生成的报告包含以下章节：

1. **封面页** - 报告标题、项目信息
2. **数据概览** - 关键统计指标的卡片展示
3. **数据质控** - Clean Summary 数据表格和字段说明
4. **比对分析** - Mapping Result 数据表格和字段说明
5. **sgRNA分析** - sgRNA 计数数据预览和统计
6. **图表展示** - 按类型分组展示各种分析图表

## 自定义封面

如需自定义报告封面，请在脚本同级目录放置以下图片文件：

| 文件名 | 说明 |
|--------|------|
| `logo.png` / `logo.jpg` | 公司Logo（显示在封面左上角） |
| `background.png` / `background.jpg` | 封面背景图 |

## 注意事项

1. 确保 Python 版本 >= 3.7
2. 建议安装 pandas 库以获得完整的数据处理功能
3. 图片文件支持 PNG、JPG、GIF、SVG 格式
4. 报告使用浏览器打开，建议使用 Chrome、Firefox 或 Edge

## 技术栈

- **Python 3.7+** - 核心脚本
- **Pandas** - CSV 数据处理
- **HTML5** - 报告结构
- **CSS3** - 样式设计
- **jQuery 3.3.1** - 前端交互
- **Bootstrap 4.3.1** - UI框架

## 许可证

MIT License
