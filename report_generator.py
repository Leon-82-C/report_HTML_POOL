# -*- coding: utf-8 -*-
"""
CRISPR文库测序数据报告生成器
集成自参考脚本的高级功能，支持多条件筛选、搜索排序等交互功能
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime
import re
import base64
import html as html_module

try:
    import pandas as pd
except ImportError:
    print("警告: 未安装pandas库，将使用简化模式处理CSV文件")
    pd = None


class CRISPRReportGenerator:
    """CRISPR文库测序数据报告生成器"""

    def __init__(self, data_dir, output_dir, project_name="sgRNA文库分析报告", project_id=None, protocol_number="", sample_name=""):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.project_name = project_name if project_name else "sgRNA文库分析报告"
        # 报告主标题（与项目名称区分：名称可为样本编号等）
        self.report_title = ""
        self.project_id = project_id or self._detect_project_id()
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        self.protocol_number = protocol_number
        self.sample_name = sample_name

        # 数据存储
        self.clean_summary = None
        self.mapping_result = None
        self.sgrna_counts = None
        self.data_files = {}
        self.image_files = {}
        self.all_images = []

        # 加载封面资源
        self._load_cover_resources()

    def _detect_project_id(self):
        """从数据文件名中自动检测项目ID"""
        clean_files = list(self.data_dir.glob('**/*clean*.csv'))
        for f in clean_files:
            try:
                df = pd.read_csv(f, nrows=1)
                if 'Sample' in df.columns:
                    sample = str(df['Sample'].iloc[0])
                    if '_' in sample:
                        return sample.split('_')[0]
            except:
                pass

        result_files = list(self.data_dir.glob('**/result.csv'))
        if result_files:
            try:
                df = pd.read_csv(result_files[0], nrows=1)
                sample_cols = [c for c in df.columns if 'sample' in c.lower() or 'label' in c.lower()]
                if sample_cols:
                    return str(df[sample_cols[0]].iloc[0])
            except:
                pass

        return self.data_dir.name

    def _load_cover_resources(self):
        """加载封面资源（logo、背景图）"""
        self.logo_base64 = ''
        self.bg_base64 = ''
        self.bg_mime = 'image/png'

        script_dir = Path(__file__).parent if '__file__' in globals() else self.data_dir

        for logo_name in ['logo.png', 'logo.jpg', 'logo.jpeg']:
            logo_path = script_dir / logo_name
            if logo_path.exists():
                self.logo_base64 = self._get_base64(logo_path)
                break

        for bg_name in ['background.jpg', 'background.png', 'bg.jpg', 'bg.png']:
            bg_path = script_dir / bg_name
            if bg_path.exists():
                self.bg_base64 = self._get_base64(bg_path)
                if bg_name.endswith('.jpg') or bg_name.endswith('.jpeg'):
                    self.bg_mime = 'image/jpeg'
                break

    def _get_base64(self, filepath):
        """将图片文件转换为base64编码"""
        try:
            with open(filepath, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"警告: 读取图片失败 {filepath}: {e}")
            return ''

    def scan_files(self):
        """扫描数据目录，收集所有文件"""
        print(f"正在扫描目录: {self.data_dir}")
        
        exclude_dirs = ['参考报告形式', 'reference', 'ref', 'report_output', '__pycache__']
        
        for root, dirs, files in os.walk(self.data_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            rel_path = Path(root).relative_to(self.data_dir)
            
            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                if ext == '.csv':
                    if str(rel_path) not in self.data_files:
                        self.data_files[str(rel_path)] = []
                    self.data_files[str(rel_path)].append({
                        'name': file,
                        'path': str(file_path),
                        'rel_path': str(rel_path)
                    })
                elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                    if str(rel_path) not in self.image_files:
                        self.image_files[str(rel_path)] = []
                    self.image_files[str(rel_path)].append({
                        'name': file,
                        'path': str(file_path)
                    })
        
        csv_count = len(sum(self.data_files.values(), []))
        img_count = len(sum(self.image_files.values(), []))
        print(f"找到 {csv_count} 个CSV文件")
        print(f"找到 {img_count} 个图片文件")
        
        # 加载主要数据
        self._load_main_data()

    def _load_main_data(self):
        """加载主要数据文件"""
        # 读取clean_summary.csv
        for rel_path, files in self.data_files.items():
            for f in files:
                if 'clean' in f['name'].lower() and f['name'].endswith('.csv'):
                    self.clean_summary = self._read_csv(f['path'])
                    if self.clean_summary is not None:
                        print(f"  已加载: {f['name']}")
                    break
        
        # 读取result.csv
        for rel_path, files in self.data_files.items():
            for f in files:
                if f['name'] == 'result.csv':
                    self.mapping_result = self._read_csv(f['path'])
                    if self.mapping_result is not None:
                        print(f"  已加载: {f['name']}")
                    break
        
        # 读取output.csv
        for rel_path, files in self.data_files.items():
            for f in files:
                if f['name'] == 'output.csv':
                    self.sgrna_counts = self._read_csv(f['path'])
                    if self.sgrna_counts is not None:
                        print(f"  已加载: {f['name']}")
                    break

    def _read_csv(self, filepath):
        """读取CSV文件"""
        if pd is None:
            return None
        try:
            return pd.read_csv(filepath)
        except Exception as e:
            print(f"读取CSV失败 {filepath}: {e}")
            return None

    def get_csv_relative_path(self, csv_path):
        """获取CSV文件复制到输出目录后的相对路径"""
        csv_path = str(csv_path)
        for rel_path, files in self.data_files.items():
            for f in files:
                if f['path'] == csv_path and 'output_path' in f:
                    return f['output_path']
        return None

    def copy_resources(self):
        """复制数据文件和图片到输出目录"""
        print("\n正在复制资源文件...")

        data_dir = self.output_dir / 'data'
        images_dir = self.output_dir / 'images'
        css_dir = self.output_dir / 'css'
        js_dir = self.output_dir / 'js'

        for d in [data_dir, images_dir, css_dir, js_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 复制CSV文件
        for rel_path, files in self.data_files.items():
            target_dir = data_dir / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                src = Path(f['path'])
                dst = target_dir / src.name
                try:
                    shutil.copy2(src, dst)
                    f['output_path'] = str(Path('data') / rel_path / src.name)
                    print(f"  复制: {src.name}")
                except Exception as e:
                    print(f"  复制失败 {src}: {e}")

        # 复制图片文件
        for rel_path, images in self.image_files.items():
            target_dir = images_dir / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            for img in images:
                src = Path(img['path'])
                dst = target_dir / src.name
                try:
                    shutil.copy2(src, dst)
                    img['output_path'] = str(Path('images') / rel_path / src.name)
                    print(f"  复制: {src.name}")
                except Exception as e:
                    print(f"  复制失败 {src}: {e}")
        
        # 复制固定的报告图片 (flute.png, fastq.png)
        self._copy_static_images()

        # 生成CSS和JS文件
        self._write_css(css_dir)
        self._write_js(js_dir)

        # 复制库文件
        self._copy_library_files(js_dir, css_dir)

        print("资源文件复制完成")

    def _copy_library_files(self, js_dir, css_dir):
        """复制前端库文件（对齐参考脚本：bootstrap-4.3.1.min.css 重命名为 bootstrap.min.css）"""
        script_dir = Path(__file__).parent if '__file__' in globals() else self.data_dir
        resources_dir = script_dir / 'resources'

        if not resources_dir.exists():
            print("警告: 未找到resources文件夹")
            return

        # CSS: bootstrap-4.3.1.min.css → bootstrap.min.css，其余保持原名
        # 排除 style.css / base.css / gallery.css（由 _write_css 生成，resources 中为旧版）
        for css_file in resources_dir.glob('css/*.css'):
            if css_file.name in ('style.css', 'base.css', 'gallery.css'):
                continue
            dst_name = 'bootstrap.min.css' if css_file.name == 'bootstrap-4.3.1.min.css' else css_file.name
            shutil.copy2(css_file, css_dir / dst_name)

        # JS: bootstrap-4.3.1.min.js → bootstrap.min.js，其余保持原名
        for js_file in resources_dir.glob('js/*.js'):
            if js_file.name in ('common.js', 'scrolltop.js'):
                continue
            dst_name = 'bootstrap.min.js' if js_file.name == 'bootstrap-4.3.1.min.js' else js_file.name
            shutil.copy2(js_file, js_dir / dst_name)

        # fancybox 资源目录
        fancybox_src = resources_dir / 'js' / 'fancybox'
        if fancybox_src.exists():
            fancybox_dst = js_dir / 'fancybox'
            fancybox_dst.mkdir(exist_ok=True)
            for fb_file in fancybox_src.glob('*'):
                if fb_file.is_file():
                    shutil.copy2(fb_file, fancybox_dst / fb_file.name)
    
    def _copy_static_images(self):
        """复制固定的报告图片 (flute.png, fastq.png)"""
        static_images = ['flute.png', 'fastq.png']
        script_dir = Path(__file__).parent if '__file__' in globals() else self.data_dir
        
        for img_name in static_images:
            src = script_dir / img_name
            if src.exists():
                dst = self.output_dir / 'images' / img_name
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(src, dst)
                    print(f"  复制: {img_name}")
                except Exception as e:
                    print(f"  复制静态图片失败 {img_name}: {e}")

    def _write_css(self, css_dir):
        """生成CSS样式文件"""
        with open(css_dir / 'style.css', 'w', encoding='utf-8') as f:
            f.write(self._get_style_css())
        
        with open(css_dir / 'base.css', 'w', encoding='utf-8') as f:
            f.write(self._get_base_css())
        
        with open(css_dir / 'gallery.css', 'w', encoding='utf-8') as f:
            f.write(self._get_gallery_css())

    def _write_js(self, js_dir):
        """生成JavaScript文件"""
        with open(js_dir / 'common.js', 'w', encoding='utf-8') as f:
            f.write(self._get_common_js())

        with open(js_dir / 'scrolltop.js', 'w', encoding='utf-8') as f:
            f.write(self._get_scrolltop_js())

    def generate_report(self):
        """生成完整HTML报告"""
        print("\n正在生成HTML报告...")
        html = self._generate_html()
        output_file = self.output_dir / 'report.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"报告生成完成: {output_file}")
        return output_file

    def generate_table_html(self, df, caption="数据表格", max_rows=10, relative_path=None, 
                           enable_search=False, enable_filter=False, fixed_column_width=False):
        """生成表格HTML（带分页和多条件组合筛选弹窗）"""
        if df is None or df.empty:
            return '<p>暂无数据</p>'
        
        table_id = f"table_{hash(caption) % 100000}"
        total_rows = len(df)
        total_pages = (total_rows + max_rows - 1) // max_rows
        columns = list(df.columns)
        
        # 生成表头
        first_col_width = '40ch'
        remaining_cols = len(columns) - 1
        other_col_width = f'calc((100% - {first_col_width}) / {remaining_cols})' if remaining_cols > 0 else 'auto'
        
        # 生成表头（始终带排序功能，视觉统一用 gy 样式对齐参考脚本）
        headers = ''.join([
            f'<th onclick="sortTableByColumn(\'{table_id}\', {i})" style="cursor:pointer">{col}<span class="sort-indicator"></span></th>'
            for i, col in enumerate(columns)
        ])
        table_classes = 'gy table table-striped table-bordered'
        
        # 生成数据行
        rows = ''
        for idx, row in df.head(max_rows).iterrows():
            cells = ''.join([f'<td>{val}</td>' for val in row])
            rows += f'<tr>{cells}</tr>'
        
        # SVG图标
        search_svg = '<svg viewBox="0 0 1024 1024"><path d="M909.6 854.5L649.9 594.8C690.2 542.7 712 479 712 412c0-80.2-31.3-155.6-87.9-212.1-56.6-56.7-132-87.9-212.1-87.9s-155.5 31.3-212.1 87.9C143.2 256.5 112 331.8 112 412c0 80.1 31.3 155.5 87.9 212.1C256.5 680.8 331.8 712 412 712c67 0 130.6-21.8 182.7-62l259.7 259.6a8.2 8.2 0 0011.6 0l43.6-43.5a8.2 8.2 0 000-11.6zM412 640c-125.9 0-228-102.1-228-228S286.1 184 412 184s228 102.1 228 228-102.1 228-228 228z"/></svg>'
        filter_svg = '<svg viewBox="0 0 1024 1024"><path d="M924.8 625.7l-65.5-56c3.1-19 4.7-38.4 4.7-57.7s-1.6-38.8-4.7-57.7l65.5-56a32.03 32.03 0 009.3-35.2l-54.7-110.6a32.12 32.12 0 00-29.2-18l-1.3.1-85.3 15.6c-24.3-19.1-51.2-35.1-80-47.3L669 116.6A32 32 0 00640.4 96H531c-14.3 0-26.8 9.5-31 23.3L485.4 206c-28.8 12.2-55.7 28.2-80 47.3l-85.3-15.6-1.3-.1a32.09 32.09 0 00-29.2 18L235 366.2a32.03 32.03 0 009.3 35.2l65.5 56c-3.1 19-4.7 38.4-4.7 57.7s1.6 38.8 4.7 57.7l-65.5 56a32.03 32.03 0 00-9.3 35.2l54.7 110.6c7.3 14.8 24.3 21.6 40 15.9l80.2-15c24.3 19.1 51.2 35.1 80 47.3l14.6 86.6c4.2 13.8 16.7 23.3 31 23.3h109.4c14.3 0 26.8-9.5 31-23.3l14.6-86.6c28.8-12.2 55.7-28.2 80-47.3l80.2 15.1c15.6 5.6 32.7-1 40-15.9l54.7-110.6a32.03 32.03 0 00-9.3-35.2zM585.6 631c-65.8 65.8-172.5 65.8-238.3 0-65.8-65.8-65.8-172.5 0-238.3 65.8-65.8 172.5-65.8 238.3 0 65.8 65.8 65.8 172.5 0 238.3z"/></svg>'
        
        # 搜索框
        search_html = ''
        if enable_search:
            search_html = f'''
            <div class="modern-search">
                {search_svg}
                <input type="text" id="{table_id}_search" placeholder="输入关键字搜索..." onkeyup="searchTableByColumn('{table_id}')">
            </div>'''
        
        # 工具栏（只有启用搜索或筛选时才显示）
        toolbar_html = ''
        if enable_search or enable_filter:
            toolbar_html = '<div class="modern-table-toolbar">'
            if enable_search:
                toolbar_html += search_html
            if enable_filter:
                toolbar_html += f'''
            <button type="button" class="modern-filter-btn" onclick="openFilterModal('{table_id}')">
                {filter_svg} 多条件筛选
                <span id="{table_id}_filter_count" class="filter-count-badge"></span>
            </button>'''
            toolbar_html += '</div>'
        
        # 多条件筛选弹窗
        filter_modal_html = ''
        if enable_filter:
            numeric_cols = []
            for i, col in enumerate(columns):
                is_numeric = False
                if not df.empty:
                    try:
                        float(df[col].iloc[0])
                        is_numeric = True
                    except:
                        is_numeric = False
                if is_numeric:
                    numeric_cols.append((i, col))
            
            field_options = ''
            for i, col in enumerate(columns):
                if col.lower() not in ['gene', 'id', 'sgrna', 'sgrna', 'seq', 'uid']:
                    is_numeric = any(idx == i for idx, _ in numeric_cols)
                    field_options += f'<option value="{i}" data-type="{"numeric" if is_numeric else "text"}">{col}</option>'
            
            filter_modal_html = f'''
            <div id="{table_id}_filter_modal" class="filter-modal">
                <div class="filter-modal-content">
                    <div class="filter-modal-header">
                        <div class="subtitle-red">多条件组合筛选</div>
                        <span class="filter-modal-close" onclick="closeFilterModal('{table_id}')">&times;</span>
                    </div>
                    <div class="filter-modal-body">
                        <div class="filter-logic-section">
                            <label>条件组合逻辑：</label>
                            <div class="filter-logic-buttons">
                                <label class="filter-radio">
                                    <input type="radio" name="{table_id}_logic" value="AND" checked>
                                    <span>且 (AND) - 所有条件同时满足</span>
                                </label>
                                <label class="filter-radio">
                                    <input type="radio" name="{table_id}_logic" value="OR">
                                    <span>或 (OR) - 满足任一条件即可</span>
                                </label>
                            </div>
                        </div>
                        <div id="{table_id}_filter_conditions" class="filter-conditions"></div>
                        <div class="filter-actions">
                            <button type="button" class="btn btn-secondary btn-sm" onclick="addFilterCondition('{table_id}')">+ 添加筛选条件</button>
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="clearAllFilters('{table_id}')">一键清除</button>
                        </div>
                    </div>
                    <div class="filter-modal-footer">
                        <span id="{table_id}_filter_result_count" class="filter-result-count"></span>
                        <div class="filter-modal-buttons">
                            <button type="button" class="btn btn-secondary" onclick="closeFilterModal('{table_id}')">取消</button>
                            <button type="button" class="btn btn-primary" onclick="applyFilters('{table_id}')">筛选</button>
                        </div>
                    </div>
                </div>
            </div>
            <select id="{table_id}_field_template" style="display:none;">{field_options}</select>'''
        
        # 下载图标
        download_svg = '''<span class="download-icon"><svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M512 666.286l226.286-226.286-60.343-60.343-123.429 123.429V128H469.714v375.086L346.286 379.657l-60.343 60.343L512 666.286zM853.714 853.714H170.286V725.714H85.143v170.857c0 23.429 18.857 42.857 42.857 42.857h768c23.429 0 42.857-19.429 42.857-42.857V725.714h-85.143v128z"/></svg></span>'''
        
        # 标题链接
        if relative_path:
            href = relative_path.replace('%2F', '/')
            dl_name = html_module.escape(Path(href).name, quote=True)
            caption_html = f'<a href="{href}" class="table-caption-link" download="{dl_name}">{download_svg}<span class="download-text">{caption}</span></a>'
        else:
            caption_html = caption
        
        # 无需分页
        if total_rows <= max_rows:
            return f'''{toolbar_html}
{filter_modal_html}
<div class="table-responsive">
    <table class="{table_classes}" id="{table_id}">
        <thead><tr>{headers}</tr></thead>
        <tbody id="{table_id}_body">{rows}</tbody>
    </table>
</div>
<p class="name_table">{caption_html}</p>'''
        
        # 分页控件（精简风格：Prev/Next + 页码方块）
        init_start = 1
        init_end = min(max_rows, total_rows)
        page_nums_html = ''
        if total_pages > 1:
            visible_end = min(total_pages, 5)
            for p in range(1, visible_end + 1):
                cls = 'page-num active' if p == 1 else 'page-num'
                page_nums_html += f'<span class="{cls}" onclick="goToPage(\'{table_id}\', {p})">{p}</span>'
        pagination = f'''<div class="table-pagination" id="{table_id}_pagination">
            <span class="pagination-info">共 {total_rows} 行，显示 {init_start}-{init_end} 行</span>
            <div class="pagination-controls">
                <span class="page-nav prev-nav disabled" onclick="prevPage('{table_id}')">Prev</span>
                <span class="page-arrow page-arrow-prev disabled" onclick="prevPage('{table_id}')">&lt;</span>
                <span class="page-nums" id="{table_id}_pageNums">{page_nums_html}</span>
                <span class="page-arrow page-arrow-next" onclick="nextPage('{table_id}')">&gt;</span>
                <span class="page-nav next-nav" onclick="nextPage('{table_id}')">Next</span>
            </div>
        </div>'''
        
        # 存储所有数据
        all_rows_data = []
        for idx, row in df.iterrows():
            cells = ''.join([f'<td>{val}</td>' for val in row])
            all_rows_data.append(f'<tr>{cells}</tr>')
        rows_data_json = '|||'.join(all_rows_data)
        rows_data_json = rows_data_json.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
        
        numeric_cols_info = [i for i, col in enumerate(columns)]
        column_names_json = '|||'.join([c.replace('\\', '\\\\').replace("'", "\\'") for c in columns])
        
        return f'''{toolbar_html}
{filter_modal_html}
<div class="table-responsive">
    <table class="{table_classes}" id="{table_id}">
        <thead><tr>{headers}</tr></thead>
        <tbody id="{table_id}_body">{rows}</tbody>
    </table>
</div>
<p class="name_table">{caption_html}</p>
{pagination}
<script>
    window.tableData = window.tableData || {{}};
    window.tableData['{table_id}'] = '{rows_data_json}'.split('|||');
    window.tablePage = window.tablePage || {{}};
    window.tablePage['{table_id}'] = 1;
    window.tableFilteredData = window.tableFilteredData || {{}};
    window.tableFilteredData['{table_id}'] = null;
    window.tableSortCol = window.tableSortCol || {{}};
    window.tableSortCol['{table_id}'] = -1;
    window.tableSortDir = window.tableSortDir || {{}};
    window.tableSortDir['{table_id}'] = 'asc';
    window.tableMaxRows = window.tableMaxRows || {{}};
    window.tableMaxRows['{table_id}'] = {max_rows};
    window.tableNumericCols = window.tableNumericCols || {{}};
    window.tableNumericCols['{table_id}'] = {numeric_cols_info};
    window.tableColumnNames = window.tableColumnNames || {{}};
    window.tableColumnNames['{table_id}'] = '{column_names_json}'.split('|||');
    window.tableSearchTerm = window.tableSearchTerm || {{}};
    window.tableSearchTerm['{table_id}'] = '';
    window.activeFilters = window.activeFilters || {{}};
    window.activeFilters['{table_id}'] = [];
    window._tableMeta = window._tableMeta || {{}};
    window._tableMeta['{table_id}'] = {{ totalRows: {total_rows}, maxRows: {max_rows} }};
</script>'''

    def _classify_image(self, filename):
        """根据文件名分类图片"""
        name_lower = filename.lower()
        if 'quality' in name_lower or 'base_quality' in name_lower:
            return 'base_quality'
        elif 'raw' in name_lower or 'reads_classification' in name_lower:
            return 'raw_reads'
        elif 'depth' in name_lower or 'sequencing_depth' in name_lower:
            return 'depth'
        elif 'uniformity' in name_lower or 'slope' in name_lower:
            return 'uniformity'
        elif 'volcano' in name_lower:
            return 'volcano'
        elif 'scatter' in name_lower:
            return 'scatter'
        elif 'rank' in name_lower:
            return 'rank'
        elif 'kegg' in name_lower:
            return 'kegg'
        elif 'go' in name_lower:
            return 'go'
        elif 'correlation' in name_lower:
            return 'correlation'
        elif 'density' in name_lower:
            return 'density'
        else:
            return 'other'

    def generate_image_selector(self, images, category, title_prefix="", side_by_side=False, description=None):
        """生成图片选择器"""
        if not images:
            return ''
        
        groups = self._group_images_by_type(images)
        html = '<div class="image-selector-container">'
        
        for group_key, group_data in groups.items():
            group_images = group_data['images']
            display_name = group_data['display_name']
            
            if not group_images:
                continue
            
            if side_by_side:
                html += self._generate_side_by_side_layout(group_images, category, group_key, display_name, description)
            else:
                html += self._generate_stacked_layout(group_images, category, group_key, display_name)
        
        html += '</div>'
        return html

    def _group_images_by_type(self, images):
        """将图片按类型分组"""
        groups = {}
        for img in images:
            name = img['name']
            if 'base_quality' in name.lower() or 'quality' in name.lower():
                group_name = 'base_quality'
                display_name = '碱基质量与错误率'
            elif 'raw reads' in name.lower() or 'reads_classification' in name.lower():
                group_name = 'raw_reads'
                display_name = '原始 Reads 分类'
            elif 'volcano' in name.lower():
                group_name = 'volcano'
                display_name = '火山图'
            elif 'scatter' in name.lower():
                group_name = 'scatter'
                display_name = '散点图'
            elif 'rank' in name.lower():
                group_name = 'rank'
                display_name = '排名图'
            elif 'kegg' in name.lower():
                group_name = 'kegg'
                display_name = 'KEGG通路'
            elif 'go' in name.lower():
                group_name = 'go'
                display_name = 'GO富集分析'
            elif 'correlation' in name.lower():
                group_name = 'correlation'
                display_name = '相关性热图'
            elif 'density' in name.lower():
                group_name = 'density'
                display_name = '密度分布图'
            elif 'depth' in name.lower():
                group_name = 'depth'
                display_name = 'sgRNA Sequencing Depth'
            elif 'uniformity' in name.lower() or 'slope' in name.lower():
                group_name = 'uniformity'
                display_name = 'Uniformity Slope'
            else:
                group_name = 'other'
                display_name = '其他图片'

            if group_name not in groups:
                groups[group_name] = {'display_name': display_name, 'images': []}
            groups[group_name]['images'].append(img)
        return groups

    def _generate_side_by_side_layout(self, images, category, group_key, display_name, description=None):
        """生成左右布局"""
        desc_html = f'<p class="modern-img-desc">{description}</p>' if description else ''
        html = f'''
            <div class="modern-img-group">
                <div class="modern-img-header">
                    <span>{display_name}</span>
                    <span class="badge">{len(images)}张</span>
                </div>
                <div class="modern-img-body">
                    <div class="modern-img-view">
                        <div class="tab-content" id="{category}_{group_key}Content">'''
        
        for idx, img in enumerate(images):
            img_path = img.get('output_path', img['path']).replace('\\', '/')
            show_class = 'show active' if idx == 0 else ''
            html += f'''
                            <div class="tab-pane fade {show_class}" id="{category}_{group_key}-{idx}">
                                <img src="{img_path}" alt="{img['name']}">
                            </div>'''
        
        # 只有一张图时不显示右侧选择器，说明文字放在图片下方
        if len(images) == 1:
            html += f'''
                        </div>
                        {desc_html}
                    </div>
                </div>
            </div>'''
        else:
            html += f'''
                        </div>
                    </div>
                    <div class="modern-img-list">'''
            
            for idx, img in enumerate(images):
                img_name = img['name'].replace('_', ' ').replace('.png', '').replace('.jpg', '')
                active_class = 'active' if idx == 0 else ''
                html += f'''
                        <div class="modern-img-btn {active_class}" onclick="switchImageSideBySide(this, '{category}_{group_key}', {idx})">
                            {img_name}
                        </div>'''
            
            html += '''
                    </div>
                </div>
            </div>'''
        return html

    def _generate_stacked_layout(self, images, category, group_key, display_name):
        """生成上下布局"""
        img_count = len(images)
        group_id = f"{category}_{group_key}"
        
        if img_count == 1:
            img = images[0]
            img_path = img.get('output_path', img['path']).replace('\\', '/')
            html = f'''
            <div class="modern-img-group">
                <div class="modern-img-header">
                    <span>{display_name}</span>
                    <span class="badge">1 张</span>
                </div>
                <div class="modern-img-body-stacked">
                    <div class="image-container" ondblclick="toggleFullscreen(this)">
                        <img src="{img_path}" style="max-width: 100%; max-height: 550px; object-fit: contain;" alt="{img['name']}">
                    </div>
                </div>
            </div>'''
            return html
        
        html = f'''
            <div class="modern-img-group">
                <div class="modern-img-header">
                    <span>{display_name}</span>
                    <span class="badge">{img_count} 张</span>
                </div>
                <div class="modern-img-body-stacked">
                    <div class="image-tabs-wrapper">
                        <ul class="image-tab-list" id="{group_id}Tabs">'''
        
        for idx, img in enumerate(images):
            img_name = img['name'].replace('_', ' ').replace('.png', '').replace('.jpg', '')
            img_path = img.get('output_path', img['path']).replace('\\', '/')
            active_class = 'active' if idx == 0 else ''
            html += f'''
                            <li class="image-tab-item {active_class}" data-target="{group_id}-{idx}" onclick="switchImage(this, '{group_id}', {idx})">
                                <img src="{img_path}" alt="{img_name}" class="image-thumbnail">
                                <span class="image-tab-label">{img_name}</span>
                            </li>'''
        
        html += f'''
                        </ul>
                    </div>
                    <div class="tab-content" id="{group_id}Content">'''
        
        for idx, img in enumerate(images):
            img_name = img['name'].replace('_', ' ').replace('.png', '').replace('.jpg', '')
            img_path = img.get('output_path', img['path']).replace('\\', '/')
            show_class = 'show active' if idx == 0 else ''
            html += f'''
                        <div class="tab-pane fade {show_class}" id="{group_id}-{idx}">
                            <div class="image-viewer">
                                <div class="image-container" ondblclick="toggleFullscreen(this)">
                                    <img src="{img_path}" class="img-fluid" alt="{img['name']}">
                                </div>
                            </div>
                        </div>'''
        
        html += '''
                    </div>
                </div>
            </div>'''
        return html

    def _generate_html(self):
        """生成HTML内容"""
        # 收集所有图片到实例变量
        self.all_images = []
        for rel_path, images in self.image_files.items():
            for img in images:
                img_copy = img.copy()
                img_copy['rel_path'] = rel_path
                img_copy['type'] = self._classify_image(img['name'])
                self.all_images.append(img_copy)
        
        # 按类型分组图片
        images_by_type = {}
        for img in self.all_images:
            img_type = img['type']
            if img_type not in images_by_type:
                images_by_type[img_type] = []
            images_by_type[img_type].append(img)

        # 封面资源
        logo_src = f"data:image/png;base64,{self.logo_base64}" if self.logo_base64 else ""
        bg_mime = getattr(self, 'bg_mime', 'image/png')
        bg_src = f"data:{bg_mime};base64,{self.bg_base64}" if self.bg_base64 else ""
        logo_display = 'block' if self.logo_base64 else 'none'
        bg_display = 'block' if self.bg_base64 else 'none'

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.project_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Source+Sans+3:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="css/bootstrap.min.css">
    <link rel="stylesheet" href="css/jquery-ui.css">
    <link rel="stylesheet" href="css/jquery.tocify.css">
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/base.css">
    <link rel="stylesheet" href="css/gallery.css">
</head>
<body>

    <!-- 目录导航 -->
    <nav class="toc-sidebar" aria-label="快速通道">
        <div class="toc-sidebar-header">
            <span class="toc-sidebar-title">快速通道</span>
            <span class="toc-sidebar-header-icon">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M11 21h-1l1-7H7.5c-.58 0-.57-.32-.38-.66.19-.34.05-.08.07-.12C8.48 10.94 10.42 7.54 13.01 3h1l-1 7h3.5c.49 0 .56.33.47.51l-.07.15C17.52 13.06 15.58 16.4 13 21z"/></svg>
            </span>
        </div>
        <div class="toc-sidebar-body">
            <div id="toc"></div>
        </div>
    </nav>

    <!-- 主内容区 -->
    <div class="main-content">
    <div class="report-container">

'''
        # 封面页 — 横版左文右图布局（对齐参考脚本结构）
        protocol_text = f"协议编号：{self.protocol_number}" if self.protocol_number else ""
        html += f'''
        <div class="report-cover">
            <div class="report-cover-inner">
            <div class="cover-header">
                <div class="cover-logo">
                    <img src="{logo_src}" alt="源井生物" style="display: {logo_display};">
                </div>
            </div>

            <div class="cover-body">
                <div class="cover-body-upper">
                    <div class="cover-center-block">
                        <h1 class="cover-main-title">sgRNA文库</h1>
                        <div class="cover-title-badge">分析报告</div>
                    </div>
                </div>
                <img src="{bg_src}" alt="" class="cover-artwork" style="display: {bg_display};">
            </div>

            <div class="cover-footer">
                <span class="cover-protocol">{protocol_text}</span>
            </div>
            </div>
        </div>
'''
        
        # 报告头部
        html += f'''
<br>
            <header class="report-header">
                <h1 class="report-title">{self.report_title}</h1>
                <div class="report-header-box">
                    <div class="report-meta-grid">
                        <div class="report-meta-row">
                            <span class="report-meta-label">项目编号</span>
                            <span class="report-meta-value">{self.project_id}</span>
                        </div>
                                                <div class="report-meta-row">
                            <span class="report-meta-label">数据类型</span>
                            <span class="report-meta-value">sgRNA文库测序分析</span>
                        </div>
                        <div class="report-meta-row">
                            <span class="report-meta-label">报告类型</span>
                            <span class="report-meta-value">{self.project_name}</span>
                        </div>
                                                <div class="report-meta-row">
                            <span class="report-meta-label">报告时间</span>
                            <span class="report-meta-value">{self.report_date}</span>
                        </div>
                    </div>
                </div>
            </header>
            <br><br>

'''
        # 1. 项目摘要
        html += self._generate_section('overview', '1 项目摘要', self._generate_overview_section())

        # 2. 数据质控
        html += self._generate_section('quality-control', '2 数据质控', self._generate_qc_section())

        # 3. Reads比对
        html += self._generate_section('mapping', '3 统计分析', self._generate_mapping_section())

        # 4. 图表展示
        if images_by_type:
            html += self._generate_section('figures', '4 图表展示', self._generate_figures_section(images_by_type))

        # 页脚
        html += '''
    </div>

    <div id="goTopBtn" onclick="goTop()">
        <svg viewBox="0 0 24 24" width="30" height="30">
            <path fill="#da1e33" d="M12 4l-8 8h5v8h6v-8h5z"/>
        </svg>
    </div>

    <script src="js/jquery-3.3.1.min.js"></script>
    <script src="js/jquery-ui.min.js"></script>
    <script src="js/jquery.tocify.min.js"></script>
    <script src="js/bootstrap.min.js"></script>
    <script src="js/common.js"></script>
    <script src="js/scrolltop.js"></script>

    <script>
    $(function () {
        var options = {
            context: ".main-content",
            selectors: "h2,h3",
            theme: "bootstrap",
            scrollTo: 60,
            highlightSelector: "h2,h3",
            showAndHide: true,
            extendPage: false
        };
        var toc = $("#toc").tocify(options).data("toc-tocify");
    });
    </script>
</body>
</html>'''
        return html

    def _generate_section(self, section_id, title, content):
        """生成章节HTML"""
        parts = title.split(' ', 1)
        if len(parts) == 2 and parts[0].isdigit():
            num_html = f'<span class="num-box">{parts[0]}</span>'
            text_html = parts[1]
        else:
            num_html = ''
            text_html = title
        
        return f'''
<div class="report-section-wrap">
<hr />
<section id="{section_id}" class="report-section">
    <h2 class="section-title-modern">{num_html}{text_html}</h2>
                {content}
            </section>
</div>
'''

    def _generate_overview_section(self):
        """生成项目摘要章节"""
        return '''
        <h3>技术概述</h3>
        <p class="para-no-indent">
            gRNA文库构建基本原理是通过一段与靶标DNA相同的gRNA指导Cas9核酸酶对靶向基因进行DNA修饰，以此造成基因的功能突变或缺失。在此基础上，利用CRISPR/Cas9技术建立哺乳动物全基因组突变库或者与某类功能相关的基因突变体库，通过功能性筛选和富集以及随后的PCR扩增和深度测序分析，发掘与筛选表型相关的基因，称为 CRISPR/Cas9 gRNA文库筛选。
        </p>

        <h3>gRNA文库应用</h3>
        <p class="para-no-indent">
            gRNA文库是药物筛选或靶向筛选特定通路的理想工具，gRNA文库的建立将在功能基因筛选、疾病机制研究及药物研发等方面发挥重要的功能。gRNA文库包括全基因组文库、IncRNA文库、信号通路、细胞凋亡、细胞增殖、离子通道、核受体相关、各种疾病相关等文库。全基因组gRNA文库的构建可以针对任何类型的基因组DNA，包括ORF cDNA，IncRNA cDNA以及特定区域的cDNA片段等。能够针对全长cDNA乃至基因组DNA构建高效的RNA文库，适用于高通量功能基因及相关药物靶点筛选。
        </p>

        <h3>实验流程</h3>

        <h4 class="subtitle-red">1.1 文库制备</h4>
        <p class="para-no-indent">
            DNA样品经DNA片段化(Shear)、末端补平(End repair)、片段3端加A尾(Add 3\'A Tail)、连接接头(Ligate Adapters)、片段筛选(Clean)、PCR扩增(Enrich with PCR)、片段筛选(Clean)、PCR产物质检(QC)等步骤构建形成Illumina平台高通量测序文库。
        </p>
        <div style="margin: 20px 0; text-align: center;">
            <img src="images/flute.png" alt="文库制备流程图" style="max-height: 500px;">
        </div>

        <h4 class="subtitle-red">1.2 测序</h4>
        <p class="para-no-indent">
            Illumina平台上机测序。fastq是测序数据下机格式，其中包含测序序列(reads)的序列信息，及其对应的测序质量信息。fastq格式文件中每个read由四行描述，如下：
        </p>

        <div class="rounded-info-box">
            <div style="margin: 15px 0; text-align: center;">
                <img src="images/fastq.png" alt="测序数据图" style="max-height: 380px;">
            </div>
            <p class="para-no-indent" style="margin-top: 10px;">
            <strong>第一行</strong>以"@"开头，后面是这个read的基本信息，分为两部分：ID部分和可选的描述部分，中间用空格分开，ID部分是每条read的唯一标识，它包含多个字段，每个字段之间用冒号分隔；描述区域是可选的，用来保存一些自定义的信息，如测序时用到的引物序列信息等。
            </p>
            <p class="para-no-indent" style="margin-top: 8px;">
            <strong>第二行</strong>是碱基序列(分ATCGN5种情况，N代表不确定碱基类型)。
            </p>
            <p class="para-no-indent" style="margin-top: 8px;">
            <strong>第三行</strong>用于将测序序列和质量值内容分离开来，以'+'开头，后面可添加第一行的描述信息。
            </p>
            <p class="para-no-indent" style="margin-top: 8px;">
            <strong>第四行</strong>为对应碱基序列的测序质量(以ASCII码形式储存，与第二行的碱基序列一一对应)。
            </p>
        </div>

        <h4 class="subtitle-red">1.3 数据分析</h4>

        <div class="sub-content-block">
        <h4 class="subtitle-black">1.3.1 测序数据质控</h4>
        <p class="para-no-indent">对原始测序数据进行质量控制（QC），去除低质量 Reads 和接头污染序列，获得 Clean Reads 用于后续分析。</p>

        <h4 class="subtitle-black">1.3.2 Reads 比对</h4>
        <p class="para-no-indent">将 Clean Reads 与 sgRNA 文库参考序列进行比对，提取并统计各 sgRNA 的 Reads 数目。</p>

        <h4 class="subtitle-black">1.3.3 统计分析</h4>
        <p class="para-no-indent">对比对结果进行统计分析，包括比对上的 Reads 数量、覆盖的 sgRNA 和基因数目、覆盖率及Reads 均一性等质控指标。</p>
        </div>

'''

    def _generate_qc_section(self):
        """生成数据质控章节"""
        html = '''
        <h3>测序质量与错误率分布统计</h3>
        <p class="para-no-indent">
            测序错误率与碱基质量有关，受测序仪本身、测序试剂、样品等多个因素共同影响。对于Illumina高通量测序平台，测序质量和错误率分布具有两个特点：
        </p>
        <ul class="overview-list">
            <li>每个read的前几个碱基的测序质量一般较低，这是由于边合成边测序过程初始阶段，测序仪荧光感光元件对焦速度较慢。获取的荧光图像质量较低，导致碱基识别错误率较高。</li>
            <li>随着测序的进行，错误率会升高，测序质量降低，这是由于测试过程中荧光基团的不完全切割和de-phasing引起荧光信号衰减。</li>
        </ul>

        <h4 style="color: #222; text-indent: 0;">质量分数与错误率换算关系</h4>
        <p class="para-no-indent">
            如果碱基的质量分数用Q表示，识别错误率用P表示，则碱基的质量分数和错误率能用以下公式表示：
        </p>
        <div class="gray-formula-box">
            <p style="margin: 5px 0;"><strong>Q = -10 × log₁₀P</strong></p>
            <p style="margin: 5px 0;"><strong>P = 10^(-Q/10)</strong></p>
        </div>

        <table style="width: 100%; margin: 15px 0; border-collapse: collapse;">
                <thead style="background: #da1e33; color: white;">
                    <tr>
                        <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Phred Quality Score</th>
                    <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Probability of Error</th>
                    <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Base Call Accuracy</th>
                    </tr>
                </thead>
                <tbody style="background: #fff5f5;">
                    <tr><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">10</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">1/10</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">90%</td></tr>
                    <tr><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">20</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">1/100</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">99%</td></tr>
                    <tr><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">30</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">1/1000</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">99.9%</td></tr>
                    <tr><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">40</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">1/10000</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">99.99%</td></tr>
                    <tr><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">50</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">1/100000</td><td style="padding: 8px; text-align: center; border: 1px solid #ddd;">99.999%</td></tr>
                </tbody>
            </table>

        <h3 style="color: #222; border-left: 4px solid #da1e33; padding-left: 10px; font-size: 18px; margin: 20px 0 15px 0; font-weight: bold;">原始数据过滤说明</h3>
        <p class="para-no-indent">
            测序得到的原始测序序列，里面含有带接头的、低质量的reads。为了保证信息分析质量，需要对raw reads进行精细过滤，得到clean reads，后续分析都基于clean reads进行。
        </p>

        <h3 style="color: #222; border-left: 4px solid #da1e33; padding-left: 10px; font-size: 18px; margin: 20px 0 15px 0; font-weight: bold;">数据处理步骤：</h3>
        <ol style="list-style-type: decimal; margin: 10px 0 10px 0; padding-left: 1.8em; line-height: 1.9; color: #3E3A39;">
            <li style="margin-bottom: 6px;">去除长度小于50的reads对；</li>
            <li style="margin-bottom: 6px;">reads中N碱基的比例大于10%时，需要去除此对reads；</li>
            <li style="margin-bottom: 6px;">去除Q20小于80%的reads对（Q20指reads的碱基质量分数大于等于20）。</li>
        </ol>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">

'''
        # Clean Summary数据
        if self.clean_summary is not None:
            html += '<h3>数据质控统计</h3>'

            # 整数列转为 int（total_reads、clean_reads、discard_reads 等）
            for col in self.clean_summary.columns:
                col_lower = col.lower()
                if any(k in col_lower for k in ('reads',)):
                    try:
                        self.clean_summary[col] = pd.to_numeric(self.clean_summary[col], errors='coerce').astype('Int64')
                    except Exception:
                        pass

            # 计算 Effective_Rate(%) = clean_reads / total_reads * 100，放在 discard_reads 右边
            if 'total_reads' in self.clean_summary.columns and 'clean_reads' in self.clean_summary.columns:
                total = pd.to_numeric(self.clean_summary['total_reads'], errors='coerce')
                clean = pd.to_numeric(self.clean_summary['clean_reads'], errors='coerce')
                self.clean_summary['Effective_Rate(%)'] = (clean / total * 100).round(2)
                cols = list(self.clean_summary.columns)
                cols.remove('Effective_Rate(%)')
                pos = cols.index('discard_reads')
                cols.insert(pos + 1, 'Effective_Rate(%)')
                self.clean_summary = self.clean_summary[cols]

            # Q20/Q30/GC 数值列：去掉%后转数值并×100转为百分比，列名加(%)后缀
            pct_rename = {}
            for col in self.clean_summary.columns:
                col_lower = col.lower()
                if any(k in col_lower for k in ('q20', 'q30', 'gc')):
                    try:
                        raw = self.clean_summary[col].astype(str).str.replace('%', '', regex=False)
                        self.clean_summary[col] = (pd.to_numeric(raw, errors='coerce') * 100).round(2)
                        pct_rename[col] = f'{col}(%)'
                    except Exception:
                        pass
                elif any(k in col_lower for k in ('rate', 'effective')):
                    try:
                        self.clean_summary[col] = pd.to_numeric(self.clean_summary[col], errors='coerce').round(2)
                    except Exception:
                        pass
            if pct_rename:
                self.clean_summary = self.clean_summary.rename(columns=pct_rename)

            # 如果用户指定了样本名称，覆盖 Sample 列
            if self.sample_name and 'Sample' in self.clean_summary.columns:
                self.clean_summary['Sample'] = self.sample_name

            # 获取CSV相对路径
            rel_path = None
            for rel_path_key, files in self.data_files.items():
                for f in files:
                    if 'clean' in f['name'].lower() and f['name'].endswith('.csv'):
                        rel_path = self.get_csv_relative_path(f['path'])
                        break
                if rel_path:
                    break

            html += self.generate_table_html(self.clean_summary.head(1), "Clean Summary 数据概览",
                                            relative_path=rel_path)

            html += '''
            <div class="plain-field-desc">
                <strong>字段说明：</strong><br>
                Sample：样本名称；<br>
                total_reads：原始reads数；<br>
                clean_reads：经过滤后的有效reads数；<br>
                discard_reads：过滤丢弃的reads数；<br>
                Effective_Rate(%)：过滤得到的clean reads数占raw reads数的比例；<br>
                Q20(%)：测序质量值大于20的碱基占总碱基的百分比；<br>
                Q30(%)：测序质量值大于30的碱基占总碱基的百分比；<br>
                GC(%)：GC碱基占总碱基的百分比
            </div>
'''
        
        # 添加原始数据质量分布图（如果有）
        quality_imgs = [img for img in self.all_images if img['type'] in ['base_quality', 'raw_reads']]
        if quality_imgs:
            html += '<h3>原始数据质量分布图</h3>'
            html += '''
            <p class="para-no-indent">
                展示各样本原始测序数据的质量分布情况，包括碱基质量分布、GC含量分布等，用于评估测序数据的可靠性。
            </p>
            '''
            html += self.generate_image_selector(quality_imgs[:2], "qc_images", "质控图", side_by_side=True)
        
        return html

    def _generate_mapping_section(self):
        """生成比对分析章节"""
        html = ''
        
        if self.mapping_result is not None:
            # 整数列转为 int（Reads、Mapped、NotMapped、NotFound、Total/Zero sgrnas/genes 等）
            int_like_cols = []
            for col in self.mapping_result.columns:
                col_lower = col.lower()
                if any(k in col_lower for k in ('reads', 'mapped', 'notmapped', 'notfound',
                                                  'total_sgrnas', 'zero_sgrnas',
                                                  'total_genes', 'zero_genes')):
                    int_like_cols.append(col)
            for col in int_like_cols:
                try:
                    self.mapping_result[col] = pd.to_numeric(self.mapping_result[col], errors='coerce').astype('Int64')
                except Exception:
                    pass

            # Mean_depth / Median_depth / Max_depth / skew_ratio 保留两位小数
            for col in self.mapping_result.columns:
                col_lower = col.lower()
                if col_lower in ('mean_depth', 'median_depth', 'max_depth', 'skew_ratio'):
                    try:
                        self.mapping_result[col] = pd.to_numeric(self.mapping_result[col], errors='coerce').round(2)
                    except Exception:
                        pass

            # 重命名 Percentage1；Percentage2 计算为 Coverage Rate (%)
            rename_map = {}
            for old_col, new_col in [('Percentage1', 'Mapping_Rate(%)')]:
                if old_col in self.mapping_result.columns:
                    try:
                        raw = self.mapping_result[old_col].astype(str).str.replace('%', '', regex=False)
                        self.mapping_result[old_col] = pd.to_numeric(raw, errors='coerce').round(2)
                        rename_map[old_col] = new_col
                    except Exception:
                        pass
            # Coverage Rate (%) = 1 - Percentage2
            if 'Percentage2' in self.mapping_result.columns:
                try:
                    raw = self.mapping_result['Percentage2'].astype(str).str.replace('%', '', regex=False)
                    p2 = pd.to_numeric(raw, errors='coerce')
                    # 如果值 > 1 则视为百分数，否则视为小数比例
                    if p2.max() > 1:
                        self.mapping_result['Coverage Rate (%)'] = (100 - p2).round(2)
                    else:
                        self.mapping_result['Coverage Rate (%)'] = ((1 - p2) * 100).round(2)
                    self.mapping_result = self.mapping_result.drop(columns=['Percentage2'])
                except Exception:
                    pass
            if rename_map:
                self.mapping_result = self.mapping_result.rename(columns=rename_map)

            # Coverage Rate (%) 放到 Zero_sgrnas 右边
            if 'Coverage Rate (%)' in self.mapping_result.columns and 'Zero_sgrnas' in self.mapping_result.columns:
                cols = list(self.mapping_result.columns)
                cols.remove('Coverage Rate (%)')
                pos = cols.index('Zero_sgrnas')
                cols.insert(pos + 1, 'Coverage Rate (%)')
                self.mapping_result = self.mapping_result[cols]

            # 获取CSV相对路径
            rel_path = None
            for rel_path_key, files in self.data_files.items():
                for f in files:
                    if f['name'] == 'result.csv':
                        rel_path = self.get_csv_relative_path(f['path'])
                        break
                if rel_path:
                    break

            html += '''
        <h3>样本 Reads 统计</h3>
        <p class="para-no-indent">
            从reads中提取sgRNA序列，比对到sgRNA文库的参考序列，并对比对结果进行统计，包括完全匹配的reads数量，匹配到的sgRNA、基因数量和覆盖率、均一性等指标。根据这些指标可反映数据的可靠性和准确性。
        </p>
'''
            html += self.generate_table_html(self.mapping_result, "比对信息统计表", 
                                            relative_path=rel_path)

            html += '''
            <div class="plain-field-desc">
                <strong>字段说明：</strong><br>
                Reads：gRNA reads总数；<br>
                Mapped：完全比对上gRNA Library的reads数目；<br>
                NotMapped：未能比对上参考序列的reads数目；<br>
                NotFound：在文库中未找到的reads数目；<br>
                Mapping_Rate(%)：比对率（Mapped reads占总reads的比例）；<br>
                Total_sgrnas：gRNA Library中的gRNA数目；<br>
                Zero_sgrnas：gRNA文库中丢失的gRNA数目；<br>
                Coverage Rate (%)：文库覆盖度，即检测到的 gRNA 占总 gRNA 的百分比；<br>
                Mean_depth：gRNA平均测序深度，即比对上参考序列的gRNA reads的总数目除以gRNA Library中被比对的gRNA数目；<br>
                Median_depth：gRNA测序深度的中位数；<br>
                Max_depth：gRNA最高测序深度，即gRNA Library中所有gRNA中比对上最多reads的gRNA的比对数目；<br>
                Total_genes：gRNA library对应基因总数；<br>
                Zero_genes：未能检测到的基因数目；<br>
                skew_ratio：文库均一性比例，累积分布达90%与10%时对应gRNA数目的比值
        </div>
'''

        # sgRNA counts 详细表格
        if self.sgrna_counts is not None and not self.sgrna_counts.empty:
            # 获取CSV相对路径
            sgrna_rel_path = None
            for rel_path_key, files in self.data_files.items():
                for f in files:
                    if f['name'] == 'output.csv':
                        sgrna_rel_path = self.get_csv_relative_path(f['path'])
                        break
                if sgrna_rel_path:
                    break

            html += '''
        <h3>sgRNA Counts 详细数据</h3>
        <p class="para-no-indent">
            以下展示每条sgRNA的详细计数的完整数据。
        </p>
'''
            html += self.generate_table_html(self.sgrna_counts, "sgRNA Counts 详细数据",
                                            max_rows=10, relative_path=sgrna_rel_path,
                                            enable_search=True, enable_filter=True)

            html += '''
        <div class="plain-field-desc">
            <strong>字段说明：</strong><br>
            gene：sgRNA对应的目标基因；<br>
            uid：sgRNA的唯一标识符；<br>
            seq：sgRNA的核酸序列；<br>
            counts：比对到该sgRNA的reads数目
        </div>
'''

        return html

    def _generate_figures_section(self, images_by_type):
        """生成图表展示章节"""
        html = '<p class="para-no-indent">以下展示本次分析生成的各种图表。</p>'

        # 深度和均一性图片（排除 base_quality 和 raw_reads）
        display_names = {
            'depth': '测序深度分布',
            'uniformity': '均一性分析'
        }
        depth_desc = '根据sgRNA文库中每条sgRNA比对到的reads数目，进行归纳统计，并将统计结果可视化，直观展示sgRNA的测序深度分布情况。'
        uniformity_desc = '文库均一性用skew ratio表示，是累积分布达到90%时对应的gRNA数目与累积分布达到10%时对应的gRNA数目的比值。文库的均一性评估在功能筛选上是非常重要的，可以有效避免sgRNA的缺失导致的筛选阳性靶点的遗漏以及假阳性结果。'
        for img_type in ['depth', 'uniformity']:
            if img_type in images_by_type:
                images = images_by_type[img_type]
                html += f'<h3>{display_names.get(img_type, img_type)}</h3>'
                desc = depth_desc if img_type == 'depth' else uniformity_desc
                html += self.generate_image_selector(images, f"img_{img_type}", side_by_side=True, description=desc)

        return html

    def _get_style_css(self):
        """获取style.css完整内容"""
        return '''/* ========== 封面页：宽屏横版，左文右图布局 ========== */
.report-cover {
    width: 100%;
    background-color: #fff;
    margin-bottom: 40px;
    page-break-after: always;
    box-sizing: border-box;
}
/* 封面专用内容宽：与正文容器一致 1200px，适配宽屏横版 */
.report-cover-inner {
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
    box-sizing: border-box;
    padding: 0 24px;
}

/* 顶部：左侧 logo.png */
.cover-header {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    padding: 20px 0 12px;
    background: #ffffff;
}
.cover-logo img {
    height: auto;
    max-height: 64px;
    width: auto;
    max-width: 100%;
    display: block;
    object-fit: contain;
}
/* 主体：横版左右布局，左文右图 */
.cover-body {
    background-color: #ffffff;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 8px;
    gap: 40px;
    min-height: 420px;
}
/* 左侧：标题+红标，统一左对齐 */
.cover-body-upper {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: center;
    flex: 0 0 auto;
    padding: 0;
    margin-bottom: 0;
    box-sizing: border-box;
}
.cover-center-block {
    text-align: left;
    width: auto;
    max-width: 100%;
    margin-top: 0;
    margin-bottom: 0;
    padding-top: 0;
    padding-bottom: 0;
}
.cover-main-title {
    margin: 0 0 0.14em 0;
    font-size: clamp(56px, 7vw, 100px);
    font-weight: 800;
    color: #111111;
    letter-spacing: 0.04em;
    line-height: 1.02;
}
.cover-title-badge {
    display: inline-block;
    position: relative;
    z-index: 1;
    margin-bottom: 0;
    padding: 0.6em 1.8em;
    min-width: 0;
    font-size: clamp(18px, 2.5vw, 28px);
    font-weight: 700;
    color: #ffffff;
    background: #d81e31;
    border-radius: 999px;
    letter-spacing: 0.35em;
    text-indent: 0.35em;
}
/* 右侧：背景插画，整体位于画面右半部分 */
.cover-artwork {
    flex: 1 1 auto;
    min-width: 0;
    max-width: 55%;
    height: auto;
    display: block;
    margin-top: 0;
    margin-bottom: 0;
    object-fit: contain;
    object-position: center center;
}
/* 左下角：协议编号 */
.cover-footer {
    padding: 0 0 16px;
    background: #ffffff;
}
.cover-protocol {
    font-size: 18px;
    font-weight: 700;
    color: #000000;
    letter-spacing: 0.02em;
}

@media (max-width: 768px) {
    .report-cover-inner {
        padding: 0 16px;
        max-width: 100%;
    }
    .cover-header {
        padding: 16px 0 10px;
    }
    /* 小屏回退为纵向堆叠 */
    .cover-body {
        flex-direction: column;
        align-items: flex-start;
        gap: 20px;
        min-height: auto;
    }
    .cover-body-upper {
        align-items: flex-start;
    }
    .cover-center-block {
        text-align: left;
        margin-top: 16px;
    }
    .cover-main-title {
        font-size: clamp(42px, 10vw, 72px);
    }
    .cover-artwork {
        max-width: 100%;
        width: 100%;
    }
    .cover-protocol {
        font-size: 15px;
    }
}

/* 基础样式重置 */
html, body, div, ul, ol {
    margin: 0;
    padding: 0;
}
html, body, div, ul, ol { margin: 0; padding: 0; }
body {
    font-family: 'Source Sans 3', 'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #3E3A39;
    background: #FFFFFF;
}
a { color: #da1e33; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ========== 侧边目录 ========== */
.toc-sidebar {
    position: fixed;
    left: 16px;
    top: 16px;
    width: 240px;
    max-height: calc(100vh - 72px);
    z-index: 100;
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border-radius: 10px;
    box-shadow: 0 4px 24px rgba(15, 23, 42, 0.08), 0 2px 10px rgba(15, 23, 42, 0.06);
    overflow: hidden;
}
.toc-sidebar-header {
    position: relative;
    flex-shrink: 0;
    padding: 14px 18px;
    background: #475569;
    color: #ffffff;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.02em;
    overflow: hidden;
}
.toc-sidebar-title { position: relative; z-index: 1; }
.toc-sidebar-header-icon {
    position: absolute;
    right: -6px;
    top: 50%;
    transform: translateY(-50%);
    width: 64px;
    height: 64px;
    opacity: 0.14;
    color: #ffffff;
    pointer-events: none;
}
.toc-sidebar-header-icon svg { width: 100%; height: 100%; display: block; }
.toc-sidebar-body {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 8px 0 14px;
}
.toc-sidebar .tocify {
    position: relative !important;
    left: auto !important;
    top: auto !important;
    width: 100% !important;
    max-height: none !important;
    height: auto !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    border-radius: 0 !important;
    box-shadow: none !important;
}
.toc-sidebar .tocify ul,
.toc-sidebar .tocify li { line-height: 1.45; font-size: 14px; }
.toc-sidebar .tocify ul a { text-decoration: none; display: block; padding: 0; border: none; }
.toc-sidebar .tocify-header > .tocify-item > a { color: #5c6b7a; font-weight: 400; }
.toc-sidebar .tocify-header > .tocify-item { padding: 10px 18px; margin: 2px 0; }
.toc-sidebar .tocify-header > .tocify-item.active {
    background: #DFE7F0;
    font-weight: 700;
}
.toc-sidebar .tocify-header > .tocify-item.active > a { color: #000000; font-weight: 700; }
.toc-sidebar .tocify-header:has(.tocify-subheader li.active) > li.tocify-item:first-of-type {
    background: #DFE7F0;
}
.toc-sidebar .tocify-header:has(.tocify-subheader li.active) > li.tocify-item:first-of-type > a {
    color: #000000;
    font-weight: 700;
}
.toc-sidebar .tocify-subheader .tocify-item { padding: 8px 18px 8px 32px; margin: 0; }
.toc-sidebar .tocify-subheader .tocify-item > a { color: #3e3a39; font-weight: 400; font-size: 13px; }
.toc-sidebar .tocify-subheader .tocify-item.active > a { color: #da1e33; font-weight: 600; }

/* ========== 主内容区 ========== */
.main-content {
    margin-left: 280px;
    margin-right: 280px;
    padding-top: 30px;
    min-height: 100vh;
}
.report-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}
@media (max-width: 1600px) { .main-content { margin-right: 30px; } }
@media (max-width: 768px) {
    .toc-sidebar { display: none !important; }
    .main-content { margin-left: 15px; margin-right: 15px; }
    .report-container { padding: 0; }
}

/* ========== 报告头部 ========== */
.report-header { margin-bottom: 2rem; }
.report-title {
    text-align: center;
    color: #000000;
    font-size: 30px;
    font-weight: bold;
    margin: 30px 0 20px 0;
}
.report-header-box {
    padding: 28px 40px;
    background: linear-gradient(to top, #DFE7F0 0%, #ffffff 100%);
    border-radius: 8px;
    box-sizing: border-box;
}
.report-meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto;
    gap: 18px 40px;
}
.report-meta-row { display: flex; align-items: baseline; gap: 8px; white-space: nowrap; }
.report-meta-label { font-size: 14px; color: #000000; line-height: 1.5; flex-shrink: 0; }
.report-meta-value { font-size: 14px; color: #000000; font-weight: 500; line-height: 1.5; word-break: break-word; }
@media (max-width: 768px) {
    .report-meta-grid { grid-template-columns: 1fr; gap: 20px; }
    .report-header-box { padding: 20px 24px; }
}

/* ========== 章节样式 ========== */
.report-section { margin-bottom: 40px; }
h2.section-title-modern {
    display: flex;
    align-items: center;
    font-size: 24px;
    font-weight: bold;
    color: #333;
    margin: 30px 0 20px 0;
    border-bottom: none !important;
    padding-bottom: 0;
}
h2.section-title-modern .num-box {
    background-color: #da1e33;
    color: white;
    width: 32px;
    height: 32px;
    display: inline-flex;
    justify-content: center;
    align-items: center;
    margin-right: 15px;
    font-size: 20px;
    flex-shrink: 0;
}
.report-section h3 {
    color: #222;
    font-size: 18px;
    margin: 20px 0 15px 0;
    padding-left: 10px;
    border-left: 4px solid #da1e33;
    font-weight: bold;
}
.report-section h4 { color: #000; font-size: 15px; margin: 15px 0 10px 0; font-weight: bold; }
.report-section h5 { color: #333; font-size: 14px; margin: 12px 0 8px 0; font-weight: bold; }
.report-section .section-sub-indent { margin-left: 20px; }

/* ========== 段落样式 ========== */
.paragraph { text-indent: 2em; line-height: 1.8; margin: 10px 0; }
.para-no-indent { font-size: 14px; text-indent: 0; line-height: 1.8; color: #3E3A39; margin: 10px 0; }
.overview-list { list-style: none; margin: 10px 0 10px 0; padding: 0; }
.overview-list li {
    position: relative;
    padding-left: 18px;
    font-size: 14px;
    line-height: 1.9;
    color: #3E3A39;
    margin-bottom: 6px;
}
.overview-list li::before { content: "·"; position: absolute; left: 0; color: #3E3A39; font-weight: bold; }

/* 红条标题 */
.title-bar-red {
    border-left: 4px solid #da1e33;
    padding-left: 10px;
    font-size: 20px;
    font-weight: bold;
    color: #333;
    margin: 25px 0 15px 0;
}
/* 红色副标题 */
.subtitle-red,
h4.subtitle-red {
    color: #da1e33;
    font-size: 16px;
    margin: 20px 0 10px 0;
    padding-left: 10px;
    border-left: 3px solid #da1e33;
    font-weight: bold;
    text-indent: 0;
}
/* 黑色副标题 */
.subtitle-black { color: #000; font-size: 15px; font-weight: bold; margin: 15px 0 10px 0; text-indent: 0; }
/* 缩进内容块 */
.sub-content-block { padding-left: 2em; }

/* 圆角信息框 */
.rounded-info-box {
    border: 1px solid #ccc;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
    background: #fff;
}

/* 浅灰公式框 */
.gray-formula-box {
    background: #f4f5f7;
    padding: 15px 20px;
    border-radius: 4px;
    margin: 15px 0;
    font-family: Arial, sans-serif;
    color: #333;
    line-height: 2;
}

/* ========== 流程图样式 ========== */
.workflow-diagram {
    display: flex; align-items: center; justify-content: center; flex-wrap: wrap;
    gap: 10px; margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;
}
.workflow-step { display: flex; flex-direction: column; align-items: center; padding: 15px 20px; background: #036eb8; color: #fff; border-radius: 6px; text-align: center; }
.workflow-step span { font-weight: 600; font-size: 14px; }
.workflow-step small { font-size: 11px; opacity: 0.8; margin-top: 4px; }
.workflow-step.final { background: #539A34; }
.workflow-arrow { font-size: 24px; color: #999; }

/* ========== 分析步骤 ========== */
.analysis-steps { margin: 20px 0; }
.analysis-step { display: flex; align-items: flex-start; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }
.step-number { width: 40px; height: 40px; background: #da1e33; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; flex-shrink: 0; margin-right: 15px; }
.step-content h4 { margin: 0 0 8px 0; color: #333; }
.step-content p { margin: 0; color: #666; }

/* ========== 公式框 ========== */
.formula-box { background: #f0f0f0; padding: 15px 25px; border-radius: 6px; margin: 15px 0; text-align: center; }
.formula-box p { margin: 8px 0; font-size: 16px; }

/* ========== 表格样式 ========== */
.table-container { margin: 15px 0; }
.table-responsive { overflow-x: auto; margin: 15px 0; }
/* 单元格间留白隙（与参考脚本块状表头/斑马行一致） */
.data-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 2px;
    font-size: 13px;
    background: #fff;
}
.data-table th {
    background: #da1e33;
    color: #fff;
    padding: 10px 12px;
    text-align: center;
    font-weight: 500;
    white-space: nowrap;
    cursor: pointer;
    border: none;
}
.data-table th:hover { background: #c4172c; }
.data-table td {
    padding: 8px 12px;
    text-align: center;
    border: none;
}
.data-table tbody tr:nth-child(odd) td { background: #f8f9fa; }
.data-table tbody tr:nth-child(even) td { background: #e2e6ea; }
.data-table tbody tr:hover td { background: #d4d9df; transition: background 0.3s ease; }
.data-table-static th { cursor: default; }
.data-table-static th:hover { background: #da1e33; }
/* 排序指示器实例样式继承上方 th .sort-indicator 规则 */

/* ========== gy表格样式 ========== */
.gy { font-family: 'Source Sans 3', 'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', sans-serif; width: 100%; border-collapse: collapse; margin: 15px auto; }
.gy.fixed-first-col { table-layout: fixed; width: 100%; }
.gy.fixed-first-col th:first-child, .gy.fixed-first-col td:first-child { width: 40ch; min-width: 40ch; max-width: 40ch; overflow: hidden; text-overflow: ellipsis; }
.gy th { position: relative; font-size: 1em; border: 2px solid #ffffff; padding: 12px 15px; text-align: center; word-break: keep-all; white-space: nowrap; background-color: #da1e33; color: #ffffff; font-weight: 500; }
.gy td { font-size: 1em; border: 2px solid #ffffff; padding: 10px 15px; text-align: center; word-break: keep-all; white-space: nowrap; color: #333333; }
.gy tr:nth-child(odd) { background: #f8f9fa; }
.gy tr:nth-child(even) { background: #e2e6ea; }
.gy tr:hover td { background: #d4d9df; transition: background 0.3s ease; }

/* ========== 字段说明 ========== */
.field-description { background: #f8f9fa; padding: 15px 20px; border-radius: 6px; margin-top: 15px; font-size: 13px; }
.field-description ul { margin: 10px 0 0 20px; }
.field-description li { margin-bottom: 5px; }
.plain-field-desc { font-size: 13px; color: #555; line-height: 1.8; margin-top: 15px; }

/* ========== 图片样式 ========== */
.image-selector-container { margin: 20px 0; }
.modern-img-group { border: 2px solid #858d98; border-radius: 16px; margin-bottom: 30px; overflow: hidden; background: #fff; }
.modern-img-header { background: #858d98; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; font-size: 16px; }
.modern-img-header .badge { background: rgba(0,0,0,0.2); padding: 2px 12px; border-radius: 12px; font-size: 13px; }
.modern-img-body { display: flex; padding: 20px; gap: 20px; background: #fff; }
.modern-img-view { flex: 1; text-align: center; }
.modern-img-view img { max-width: 100%; max-height: 450px; object-fit: contain; }
.modern-img-desc { font-size: 13px; color: #555; line-height: 1.8; text-align: left; padding: 10px 15px; background: #f8f9fa; border-radius: 8px; margin: 0 0 12px 0; }
.modern-img-list { width: 300px; display: flex; flex-direction: column; gap: 10px; flex-shrink: 0; max-height: 450px; overflow-y: auto; }
.modern-img-btn { padding: 12px 20px; background: #f4f5f7; border-radius: 12px; cursor: pointer; text-align: center; color: #555; transition: all 0.3s; font-size: 14px; }
.modern-img-btn:hover { background: #e8e9ea; }
.modern-img-btn.active { background: #da1e33; color: #fff; font-weight: bold; }
.modern-img-body-stacked { padding: 20px; background: #fff; text-align: center; }
.image-tabs-wrapper { margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; }
.image-tab-list { display: flex; flex-wrap: wrap; gap: 10px; list-style: none; padding: 0; margin: 0; }
.image-tab-item { display: flex; flex-direction: column; align-items: center; padding: 8px 12px; background: #fff; border: 2px solid #e0e0e0; border-radius: 8px; cursor: pointer; transition: all 0.3s; min-width: 100px; max-width: 120px; }
.image-tab-item:hover { border-color: #da1e33; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
.image-tab-item.active { border-color: #da1e33; background: #fceaea; box-shadow: 0 2px 8px rgba(218,30,51,0.3); }
.image-thumbnail { width: 80px; height: 50px; object-fit: contain; border-radius: 4px; margin-bottom: 5px; background: #f0f0f0; }
.image-tab-label { font-size: 11px; color: #666; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100px; }
.image-tab-item.active .image-tab-label { color: #da1e33; font-weight: 600; }
.image-viewer { text-align: center; background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }
.image-viewer img { max-width: 100%; max-height: 450px; cursor: pointer; transition: transform 0.3s; border-radius: 4px; }
.image-container { display: block; text-align: center; width: 100%; }
.image-container img { max-width: 100%; max-height: 450px; cursor: zoom-in; object-fit: contain; }
.image-container.fullscreen-div { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; background: #ffffff; display: flex; align-items: center; justify-content: center; cursor: zoom-out; }
.image-container.fullscreen-div img { width: auto; height: auto; max-width: 90vw; max-height: 90vh; cursor: zoom-out; }

/* ========== 现代Tab选项卡样式 ========== */
.modern-tab-header {
    background: #858d98;
    border-radius: 16px 16px 0 0;
    display: flex;
    padding: 0 20px;
    align-items: flex-end;
    overflow-x: auto;
}
.modern-tab-item {
    color: #d1d4d7;
    padding: 15px 20px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s;
    white-space: nowrap;
}
.modern-tab-item:hover { color: #fff; }
.modern-tab-item.active { color: #fff; font-weight: bold; }
.modern-tab-content {
    display: none;
    padding: 20px;
    background: #fff;
    border-radius: 0 0 16px 16px;
    text-align: center;
}
.modern-tab-content.active { display: block; }

/* ========== 筛选弹窗样式 ========== */
.filter-modal { display: none; position: fixed; z-index: 9999; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); animation: fadeIn 0.3s; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.filter-modal-content { background-color: #fff; margin: 5% auto; padding: 0; border-radius: 8px; width: 90%; max-width: 700px; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.filter-modal-header { background: linear-gradient(135deg, #da1e33 0%, #b01828 100%); color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }
.filter-modal-close { color: white; font-size: 28px; font-weight: bold; cursor: pointer; line-height: 1; }
.filter-modal-close:hover { color: #ff6b6b; }
.filter-modal-body { padding: 20px; overflow-y: auto; flex: 1; }
.filter-logic-section { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 6px; }
.filter-logic-section label { font-weight: 600; color: #333; margin-bottom: 10px; display: block; }
.filter-logic-buttons { display: flex; gap: 20px; }
.filter-radio { display: flex; align-items: center; cursor: pointer; font-weight: normal !important; }
.filter-radio input { margin-right: 8px; width: 16px; height: 16px; accent-color: #da1e33; }
.filter-condition { display: flex; align-items: center; gap: 10px; padding: 12px; background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 10px; flex-wrap: wrap; }
.filter-condition select, .filter-condition input { padding: 6px 10px; border: 1px solid #ced4da; border-radius: 4px; font-size: 13px; }
.filter-condition select { min-width: 120px; }
.filter-condition input[type="number"] { width: 100px; }
.filter-condition input[type="text"] { width: 120px; }
.filter-condition .remove-condition { background: none; border: none; color: #dc3545; font-size: 20px; cursor: pointer; padding: 0 5px; margin-left: auto; }
.filter-actions { display: flex; gap: 10px; margin-top: 15px; }
.filter-modal-footer { padding: 15px 20px; background: #f8f9fa; border-top: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
.filter-result-count { color: #da1e33; font-weight: 600; }
.filter-modal-buttons { display: flex; gap: 10px; }
.filter-modal-buttons .btn-primary { background: linear-gradient(135deg, #da1e33 0%, #b01828 100%); border: none; }
.filter-modal-buttons .btn-primary:hover { background: linear-gradient(135deg, #b01828 0%, #8a1220 100%); }

/* ========== 表格工具栏 ========== */
.modern-table-toolbar { display: flex; justify-content: flex-end; align-items: center; gap: 15px; margin-bottom: 15px; margin-top: -40px; }
.modern-search { position: relative; display: inline-flex; align-items: center; }
.modern-search svg { position: absolute; left: 14px; width: 16px; height: 16px; fill: #333; }
.modern-search input { background: #e6e9ec; border: none; border-radius: 20px; padding: 8px 15px 8px 36px; font-size: 14px; color: #333; width: 260px; outline: none; transition: all 0.3s; }
.modern-search input:focus { background: #dce0e5; box-shadow: 0 0 0 2px rgba(218,30,51,0.15); }
.modern-filter-btn { display: inline-flex; align-items: center; background: #f0f2f5; border: none; border-radius: 20px; padding: 8px 18px; font-size: 14px; color: #555; cursor: pointer; transition: all 0.3s; }
.modern-filter-btn svg { width: 16px; height: 16px; margin-right: 6px; fill: #666; }
.modern-filter-btn:hover { background: #e6e9ec; color: #333; }
.filter-count-badge { background: #da1e33; color: white; border-radius: 10px; padding: 1px 6px; font-size: 12px; margin-left: 6px; display: none; }

/* ========== 分页样式（精简风格：Prev/Next + 页码方块）========== */
.table-pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    background: #f5f5f5;
    border-radius: 4px;
    margin-top: 10px;
}
.pagination-info { color: #888; font-size: 13px; }
.pagination-controls { display: flex; align-items: center; gap: 6px; }
/* Prev / Next 文本 */
.page-nav {
    font-size: 13px; color: #555; cursor: pointer; user-select: none; padding: 2px 4px;
}
.page-nav:hover { color: #222; }
.page-nav.disabled { color: #bbb; cursor: default; pointer-events: none; }
/* < > 箭头 */
.page-arrow {
    font-size: 14px; color: #555; cursor: pointer; user-select: none; padding: 2px 4px; font-family: monospace;
}
.page-arrow:hover { color: #222; }
.page-arrow.disabled { color: #bbb; cursor: default; pointer-events: none; }
/* 页码数字容器 */
.page-nums { display: flex; align-items: center; gap: 4px; }
/* 单个页码方块 */
.page-num {
    display: inline-flex; justify-content: center; align-items: center;
    min-width: 28px; height: 28px; font-size: 13px; color: #555;
    cursor: pointer; user-select: none; border-radius: 4px; transition: all 0.15s ease;
}
.page-num:hover { color: #222; background: #e8e8e8; }
.page-num.active { background: #e3edf5; color: #da1e33; font-weight: 600; cursor: default; }
.page-info { color: #333; font-size: 13px; margin: 0 10px; }

/* ========== 下载链接 ========== */
.name_table { margin: 10px 0 2px 0; text-align: left; }
.table-caption-link {
    display: inline-flex; align-items: center; color: #333333;
    text-decoration: none; font-size: 16px; font-weight: 500; transition: all 0.3s ease;
}
.table-caption-link .download-text {
    text-decoration: underline; text-decoration-color: #cccccc;
    text-underline-offset: 3px; text-decoration-thickness: 1px;
}
.table-caption-link:hover .download-text { color: #da1e33; text-decoration-color: #da1e33; }
.table-caption-link .download-icon { margin-right: 8px; display: inline-flex; align-items: center; justify-content: center; }
.table-caption-link .download-icon svg { fill: #da1e33; width: 20px; height: 20px; }

/* ========== 返回顶部 ========== */
#goTopBtn {
    position: fixed; text-align: center; line-height: 30px;
    width: 40px; height: 40px; bottom: 35px; right: 20px;
    cursor: pointer; background: #F7F7F7; border: 1px solid #D1D1D1;
    border-radius: 50%; transition: all 0.3s ease; z-index: 1000;
}
#goTopBtn:hover { background: #da1e33; transform: translateY(-3px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
#goTopBtn:hover svg path { fill: #ffffff; }
@media (max-width: 768px) { #goTopBtn { right: 15px; bottom: 15px; } }

/* ========== 列排序指示器 ========== */
th .sort-indicator { position: absolute; margin-left: 3px; opacity: 0.3; }
th .sort-indicator::before { content: "↕"; }
th.sorted-asc .sort-indicator::before { content: "↑"; opacity: 1; color: #da1e33; }
th.sorted-desc .sort-indicator::before { content: "↓"; opacity: 1; color: #da1e33; }

/* ========== 打印样式 ========== */
@media print {
    .toc-sidebar, #goTopBtn { display: none !important; }
    .main-content { margin: 0 !important; padding: 20px !important; }
    .image-viewer img { max-width: 100% !important; max-height: none !important; page-break-inside: avoid; }
}
'''

    def _get_base_css(self):
        """获取base.css内容"""
        return '''a, img { border-style: none; outline: none !important }
body { font-size: 14px; padding: 12px; font-family: 'Source Sans 3', 'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', sans-serif; }
h1 { font-size: 30px; text-align: center; }
h2 { font-size: 24px; }
h3 { font-size: 18px; text-indent: 0.5em; }
h4 { font-size: 16px; text-indent: 1em; }
p.head { text-align: right; color: grey; font-family: 'Noto Sans SC', 'Source Han Sans SC', 'Microsoft YaHei', 'PingFang SC', sans-serif; }
p.paragraph { text-indent: 2em; line-height: 1.5; }
p.center { text-align: center; }
img.normal { height: auto; width: 100%; margin: auto; }
table { font-family: 'Noto Sans SC', 'Source Han Sans SC', 'Microsoft YaHei', 'PingFang SC', sans-serif; font-size: 14px; width: 100%; border-collapse: collapse; text-align: center; padding: 3px 10px 2px 10px; }
#goTopBtn { position: fixed; text-align: center; line-height: 30px; width: 30px; height: 33px; font-size: 12px; cursor: pointer; right: 0px; }
.bs-docs-qa { position: relative; margin: 15px 0; padding: 19px 19px 14px; background-color: #fff; border: 1px solid #ddd; border-radius: 4px; }
.alert-qa { background-color: #eeeeee; border-color: #dddddd; }
'''

    def _get_gallery_css(self):
        """获取gallery.css内容"""
        return '''.button_prev { display: block; position: absolute; opacity: .8; cursor: pointer; width: 50px; height: 50px; top: 200px; left: 20px; z-index: 99; }
.button_prev:hover { opacity: 1; }
.button_next { display: block; position: absolute; opacity: .8; cursor: pointer; width: 50px; height: 50px; top: 200px; right: 20px; z-index: 99; }
.button_next:hover { opacity: 1; }
.list-group { height: 400px; overflow-y: auto; }
.list-group-item { height: 40px; line-height: 1; margin-bottom: 0; }
.img-gallery { height: 450px; display: block; margin: auto; user-select: none; border: none; }
.fullscreen-div { z-index: 9999; position: fixed; top: 0; bottom: 0; left: 0; right: 0; margin: auto; background: rgba(0,0,0,0.8); }
.fullscreen-img { z-index: 9999; height: 100%; }
.gallery-row { height: 500px; }
'''

    def _get_common_js(self):
        """获取common.js内容"""
        return '''// 切换图片分组
function toggleImageGroup(groupId) {
    var content = document.getElementById('group_' + groupId);
    var toggle = document.getElementById('toggle_' + groupId);
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        toggle.classList.remove('collapsed');
    } else {
        content.classList.add('collapsed');
        toggle.classList.add('collapsed');
    }
}

// 切换图片
function switchImage(element, category, index) {
    var tabList = element.parentElement.querySelectorAll('.image-tab-item');
    tabList.forEach(function(item) { item.classList.remove('active'); });
    element.classList.add('active');
    var contentContainer = document.getElementById(category + 'Content');
    if (contentContainer) {
        var panes = contentContainer.querySelectorAll('.tab-pane');
        panes.forEach(function(pane) { pane.classList.remove('show', 'active'); });
        var targetPane = document.getElementById(category + '-' + index);
        if (targetPane) { targetPane.classList.add('show', 'active'); }
    }
    if (event) { event.preventDefault(); event.stopPropagation(); }
}

// 左右布局切换图片
function switchImageSideBySide(element, category, index) {
    var listItems = element.parentElement.querySelectorAll('.modern-img-btn');
    listItems.forEach(function(item) { item.classList.remove('active'); });
    element.classList.add('active');
    var viewer = element.closest('.modern-img-body').querySelector('.modern-img-view');
    var panes = viewer.querySelectorAll('.tab-pane');
    panes.forEach(function(pane) { pane.classList.remove('show', 'active'); });
    var targetPane = document.getElementById(category + '-' + index);
    if (targetPane) { targetPane.classList.add('show', 'active'); }
    if (event) { event.preventDefault(); event.stopPropagation(); }
}

// 全屏图片
function toggleFullscreen(container) {
    if (container.classList.contains('fullscreen-div')) {
        container.classList.remove('fullscreen-div');
    } else {
        container.classList.add('fullscreen-div');
    }
}

$(document).on('click', '.fullscreen-div', function(e) {
    if (e.target === this || e.target.tagName === 'IMG') {
        $(this).removeClass('fullscreen-div');
    }
});

// ========== 表格搜索和排序 ==========
function searchTableByColumn(tableId) {
    var input = document.getElementById(tableId + '_search');
    var filter = input.value.toUpperCase();
    var tbody = document.getElementById(tableId + '_body');
    if (!tbody) return;
    var tr = tbody.getElementsByTagName('tr');
    var filteredData = [];
    for (var i = 0; i < tr.length; i++) {
        var display = 'none';
        var td = tr[i].getElementsByTagName('td');
        for (var j = 0; j < td.length; j++) {
            if (td[j]) {
                var txtValue = td[j].textContent || td[j].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) { display = ''; break; }
            }
        }
        tr[i].style.display = display;
        if (display === '') { filteredData.push(tr[i].outerHTML); }
    }
    window.tableFilteredData[tableId] = filter ? filteredData : null;
    window.tablePage[tableId] = 1;
    updatePaginationDisplay(tableId);
    if (window.tableSortCol[tableId] !== undefined && window.tableSortCol[tableId] >= 0) {
        sortTableByColumn(tableId, window.tableSortCol[tableId]);
    }
}

function sortTableByColumn(tableId, colIndex) {
    var data = window.tableData[tableId];
    var filteredData = window.tableFilteredData[tableId];
    var allData = filteredData || data;
    if (!allData || allData.length === 0) return;
    
    if (typeof window.tableSortCol[tableId] === 'undefined') { window.tableSortCol[tableId] = -1; }
    if (typeof window.tableSortDir[tableId] === 'undefined') { window.tableSortDir[tableId] = 'asc'; }
    
    var currentSortCol = window.tableSortCol[tableId];
    var currentSortDir = window.tableSortDir[tableId];
    
    if (currentSortCol === colIndex) {
        window.tableSortDir[tableId] = currentSortDir === 'asc' ? 'desc' : 'asc';
    } else {
        window.tableSortCol[tableId] = colIndex;
        window.tableSortDir[tableId] = 'asc';
    }
    var sortDir = window.tableSortDir[tableId];
    updateSortIndicators(tableId, colIndex, sortDir);
    
    var rows = [];
    for (var i = 0; i < allData.length; i++) {
        var tempDiv = document.createElement('div');
        tempDiv.innerHTML = '<table><tbody>' + allData[i] + '</tbody></table>';
        var tr = tempDiv.querySelector('tr');
        if (tr) {
            var tdList = tr.getElementsByTagName('td');
            if (tdList.length > colIndex) {
                rows.push({ html: allData[i], colValue: tdList[colIndex].textContent.trim() });
            }
        }
    }
    if (rows.length === 0) return;
    
    rows.sort(function(a, b) {
        var aVal = a.colValue;
        var bVal = b.colValue;
        var aNum = parseFloat(aVal);
        var bNum = parseFloat(bVal);
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return sortDir === 'asc' ? aNum - bNum : bNum - aNum;
        }
        aVal = aVal.toLowerCase(); bVal = bVal.toLowerCase();
        return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    
    var sortedData = rows.map(function(row) { return row.html; });
    if (filteredData) { window.tableFilteredData[tableId] = sortedData; }
    else { window.tableData[tableId] = sortedData; }
    goToPage(tableId, 1);
}

function updateSortIndicators(tableId, colIndex, sortDir) {
    var table = document.getElementById(tableId);
    if (!table) return;
    var headers = table.querySelectorAll('th');
    headers.forEach(function(th, index) {
        th.classList.remove('sorted-asc', 'sorted-desc');
        if (index === colIndex) { th.classList.add(sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc'); }
    });
}

function updatePaginationDisplay(tableId) {
    var tbody = document.getElementById(tableId + '_body');
    if (!tbody) return;
    var tr = tbody.getElementsByTagName('tr');
    var visibleCount = 0;
    for (var i = 0; i < tr.length; i++) {
        if (tr[i].style.display !== 'none') { visibleCount++; }
    }
    var data = window.tableData[tableId];
    var filteredData = window.tableFilteredData[tableId];
    var displayData = filteredData || data;
    var totalRows = displayData ? displayData.length : 0;
    var meta = window._tableMeta && window._tableMeta[tableId];
    var maxRows = (meta ? meta.maxRows : null) || window.tableMaxRows[tableId] || 10;
    var totalPages = Math.ceil(totalRows / maxRows) || 1;
    var current = window.tablePage[tableId] || 1;
    if (current > totalPages) current = totalPages;
    if (current < 1) current = 1;
    var pagination = document.getElementById(tableId + '_pagination');
    if (!pagination) return;
    var infoSpan = pagination.querySelector('.pagination-info');
    if (infoSpan) {
        if (filteredData) { infoSpan.textContent = '筛选 ' + totalRows + ' 行'; }
        else { infoSpan.textContent = '共 ' + totalRows + ' 行'; }
    }
    if (typeof renderPageNumbers === 'function') { renderPageNumbers(tableId, totalPages, current); }
    var prevNav = pagination.querySelector('.prev-nav');
    var prevArrow = pagination.querySelector('.page-arrow-prev');
    var nextArrow = pagination.querySelector('.page-arrow-next');
    var nextNav = pagination.querySelector('.next-nav');
    if (prevNav) prevNav.classList.toggle('disabled', current <= 1);
    if (prevArrow) prevArrow.classList.toggle('disabled', current <= 1);
    if (nextArrow) nextArrow.classList.toggle('disabled', current >= totalPages);
    if (nextNav) nextNav.classList.toggle('disabled', current >= totalPages);
}

function renderPageNumbers(tableId, totalPages, current) {
    var container = document.getElementById(tableId + '_pageNums');
    if (!container) return;
    if (totalPages <= 1) { container.innerHTML = ''; return; }
    var start = Math.max(1, current - 2);
    var end = Math.min(totalPages, current + 2);
    if (end - start < 4) {
        if (start === 1) { end = Math.min(totalPages, start + 4); }
        else { start = Math.max(1, end - 4); }
    }
    var html = '';
    for (var i = start; i <= end; i++) {
        var cls = (i === current) ? 'page-num active' : 'page-num';
        html += '<span class="' + cls + '" onclick="goToPage(\\'' + tableId + '\\', ' + i + ')">' + i + '</span>';
    }
    container.innerHTML = html;
}

function goToPage(tableId, pageNum) {
    var data = window.tableData[tableId];
    if (!data) return;
    var filteredData = window.tableFilteredData[tableId];
    var displayData = filteredData || data;
    var meta = window._tableMeta && window._tableMeta[tableId];
    var maxRows = (meta ? meta.maxRows : null) || window.tableMaxRows[tableId] || 10;
    var totalPages = Math.ceil(displayData.length / maxRows) || 1;
    if (pageNum > totalPages) { pageNum = totalPages; }
    if (pageNum < 1) { pageNum = 1; }
    var tbody = document.getElementById(tableId + '_body');
    if (!tbody) return;
    var start = (pageNum - 1) * maxRows;
    var end = Math.min(start + maxRows, displayData.length);
    tbody.innerHTML = displayData.slice(start, end).join('');
    window.tablePage[tableId] = pageNum;
    if (typeof renderPageNumbers === 'function') { renderPageNumbers(tableId, totalPages, pageNum); }
    var pagination = document.getElementById(tableId + '_pagination');
    if (pagination) {
        var prevNav = pagination.querySelector('.prev-nav');
        var prevArrow = pagination.querySelector('.page-arrow-prev');
        var nextArrow = pagination.querySelector('.page-arrow-next');
        var nextNav = pagination.querySelector('.next-nav');
        if (prevNav) prevNav.classList.toggle('disabled', pageNum === 1);
        if (prevArrow) prevArrow.classList.toggle('disabled', pageNum === 1);
        if (nextArrow) nextArrow.classList.toggle('disabled', pageNum >= totalPages);
        if (nextNav) nextNav.classList.toggle('disabled', pageNum >= totalPages);
        var infoSpan = pagination.querySelector('.pagination-info');
        if (infoSpan) {
            var totalRows = filteredData ? filteredData.length : (data ? data.length : 0);
            var s = (pageNum - 1) * maxRows + 1;
            var e = Math.min(pageNum * maxRows, totalRows);
            if (filteredData) { infoSpan.textContent = '筛选 ' + totalRows + ' 行，显示 ' + s + '-' + e + ' 行'; }
            else { infoSpan.textContent = '共 ' + totalRows + ' 行，显示 ' + s + '-' + e + ' 行'; }
        }
    }
    if (event) { event.preventDefault(); event.stopPropagation(); }
}

function prevPage(tableId) {
    var current = window.tablePage[tableId] || 1;
    if (current > 1) goToPage(tableId, current - 1);
}
function nextPage(tableId) {
    var data = window.tableData[tableId];
    var filteredData = window.tableFilteredData[tableId];
    var displayData = filteredData || data;
    if (!displayData) return;
    var meta = window._tableMeta && window._tableMeta[tableId];
    var maxRows = (meta ? meta.maxRows : null) || window.tableMaxRows[tableId] || 10;
    var totalPages = Math.ceil(displayData.length / maxRows) || 1;
    var current = window.tablePage[tableId] || 1;
    if (current < totalPages) goToPage(tableId, current + 1);
}

// ========== 多条件筛选 ==========
function openFilterModal(tableId) {
    var modal = document.getElementById(tableId + '_filter_modal');
    if (modal) { modal.style.display = 'block'; }
}

function closeFilterModal(tableId) {
    var modal = document.getElementById(tableId + '_filter_modal');
    if (modal) { modal.style.display = 'none'; }
}

function addFilterCondition(tableId) {
    var conditionsContainer = document.getElementById(tableId + '_filter_conditions');
    var templateSelect = document.getElementById(tableId + '_field_template');
    if (conditionsContainer.children.length >= 6) { alert('最多只能添加6个筛选条件'); return; }
    var conditionId = Date.now();
    var fieldOptions = templateSelect ? templateSelect.innerHTML : '';
    var conditionHtml = '<div class="filter-condition" id="' + tableId + '_condition_' + conditionId + '">' +
        '<select class="field-select" onchange="updateOperatorOptions(\\'' + tableId + '\\', \\'' + conditionId + '\\')">' + fieldOptions + '</select>' +
        '<select class="operator-select"><option value=">">></option><option value=">=">>=</option><option value="<"><</option><option value="<="><=</option><option value="=">=</option><option value="|x|>">|x|></option></select>' +
        '<input type="text" class="value-input" placeholder="数值">' +
        '<button class="remove-condition" onclick="removeFilterCondition(\\'' + tableId + '\\', \\'' + conditionId + '\\')">&times;</button></div>';
    conditionsContainer.insertAdjacentHTML('beforeend', conditionHtml);
}

function removeFilterCondition(tableId, conditionId) {
    var condition = document.getElementById(tableId + '_condition_' + conditionId);
    if (condition) { condition.remove(); }
}

function updateOperatorOptions(tableId, conditionId) {
    var condition = document.getElementById(tableId + '_condition_' + conditionId);
    if (!condition) return;
    var fieldSelect = condition.querySelector('.field-select');
    var operatorSelect = condition.querySelector('.operator-select');
    var valueInput = condition.querySelector('.value-input');
    if (!fieldSelect || !operatorSelect || !valueInput) return;
    var selectedOption = fieldSelect.options[fieldSelect.selectedIndex];
    var fieldType = selectedOption ? selectedOption.getAttribute('data-type') : 'text';
    operatorSelect.innerHTML = '';
    if (fieldType === 'numeric') {
        operatorSelect.innerHTML = '<option value=">">></option><option value=">=">>=</option><option value="<"><</option><option value="<="><=</option><option value="=">=</option><option value="|x|>">|x|></option>';
    } else {
        operatorSelect.innerHTML = '<option value="=">=</option>';
    }
}

function clearAllFilters(tableId) {
    var conditionsContainer = document.getElementById(tableId + '_filter_conditions');
    if (conditionsContainer) { conditionsContainer.innerHTML = ''; }
    var searchInput = document.getElementById(tableId + '_search');
    if (searchInput) { searchInput.value = ''; }
    window.tableFilteredData[tableId] = null;
    window.tableSearchTerm[tableId] = '';
    window.activeFilters[tableId] = [];
    window.tablePage[tableId] = 1;
    updatePaginationDisplay(tableId);
    goToPage(tableId, 1);
}

function applyFilters(tableId) {
    var conditionsContainer = document.getElementById(tableId + '_filter_conditions');
    var searchInput = document.getElementById(tableId + '_search');
    var searchTerm = searchInput ? searchInput.value.trim().toUpperCase() : '';
    var conditions = [];
    if (conditionsContainer) {
        var conditionDivs = conditionsContainer.querySelectorAll('.filter-condition');
        conditionDivs.forEach(function(cond) {
            var fieldSelect = cond.querySelector('.field-select');
            var operatorSelect = cond.querySelector('.operator-select');
            var valueInput = cond.querySelector('.value-input');
            if (fieldSelect && operatorSelect && valueInput) {
                var fieldIndex = parseInt(fieldSelect.value);
                var operator = operatorSelect.value;
                var value = valueInput.value.trim();
                if (value !== '') { conditions.push({ fieldIndex: fieldIndex, operator: operator, value: value }); }
            }
        });
    }
    window.activeFilters[tableId] = conditions;
    var data = window.tableData[tableId];
    var allRowsData = data || [];
    var filteredData = [];
    for (var i = 0; i < allRowsData.length; i++) {
        var rowHtml = allRowsData[i];
        var tempDiv = document.createElement('div');
        tempDiv.innerHTML = '<table><tbody>' + rowHtml + '</tbody></table>';
        var tr = tempDiv.querySelector('tr');
        if (!tr) continue;
        var tdList = tr.getElementsByTagName('td');
        var searchMatch = true;
        if (searchTerm !== '') {
            searchMatch = false;
            if (rowHtml.toUpperCase().indexOf(searchTerm) > -1) { searchMatch = true; }
        }
        var filterMatch = true;
        if (conditions.length > 0) {
            filterMatch = conditions.every(function(cond) { return checkCondition(tdList, cond); });
        }
        if (searchMatch && filterMatch) { filteredData.push(rowHtml); }
    }
    window.tableFilteredData[tableId] = filteredData;
    closeFilterModal(tableId);
    window.tablePage[tableId] = 1;
    updatePaginationDisplay(tableId);
    goToPage(tableId, 1);
}

function checkCondition(tdList, condition) {
    var fieldIndex = condition.fieldIndex;
    var operator = condition.operator;
    var value = condition.value;
    if (fieldIndex >= tdList.length) return true;
    var cellValue = tdList[fieldIndex].textContent.trim();
    var numValue = parseFloat(cellValue);
    var numTarget = parseFloat(value);
    if (!isNaN(numValue) && !isNaN(numTarget)) {
        switch (operator) {
            case '>': return numValue > numTarget;
            case '>=': return numValue >= numTarget;
            case '<': return numValue < numTarget;
            case '<=': return numValue <= numTarget;
            case '=': return numValue === numTarget;
            case '|x|>': return Math.abs(numValue) > Math.abs(numTarget);
            default: return true;
        }
    } else {
        if (operator === '=') { return cellValue.toUpperCase() === value.toUpperCase(); }
        return true;
    }
}

window.onclick = function(event) {
    var modals = document.querySelectorAll('.filter-modal');
    modals.forEach(function(modal) { if (event.target === modal) { modal.style.display = 'none'; } });
}

// 现代版 Tab 切换
function switchModernTab(element, targetId, groupPrefix) {
    var tabs = element.parentElement.querySelectorAll('.modern-tab-item');
    tabs.forEach(function(tab) { tab.classList.remove('active'); });
    element.classList.add('active');
    var container = element.closest('.modern-img-group');
    var contents = container.querySelectorAll('.modern-tab-content');
    contents.forEach(function(content) { content.classList.remove('active'); });
    var target = document.getElementById(targetId);
    if (target) { target.classList.add('active'); }
}
'''

    def _get_scrolltop_js(self):
        """获取scrolltop.js内容"""
        return '''function goTop() { $('html, body').animate({ scrollTop: 0 }, 300); }
$(window).scroll(function() {
    if ($(this).scrollTop() > 300) { $('#goTopBtn').fadeIn(); } else { $('#goTopBtn').fadeOut(); }
});
$(document).on('click', 'a[href^="#"]', function(event) {
    event.preventDefault();
    var target = $(this.getAttribute('href'));
    if (target.length) {
        $('html, body').stop().animate({ scrollTop: target.offset().top - 70 }, 500);
    }
});
'''


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CRISPR文库测序数据报告生成器', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('data_dir', nargs='?', default='.', help='数据文件夹路径')
    parser.add_argument('output_dir', nargs='?', default='./report_output', help='输出目录')
    parser.add_argument('--name', default=None, help='项目名称')
    parser.add_argument('--project-id', default=None, help='项目编号')
    parser.add_argument('--protocol', default='', help='协议编号')
    parser.add_argument('--sample', default='', help='样本名称（覆盖数据质控统计中Sample列）')

    args = parser.parse_args()

    generator = CRISPRReportGenerator(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        project_name=args.name,
        project_id=args.project_id,
        protocol_number=args.protocol,
        sample_name=args.sample
    )

    print("=" * 60)
    print("CRISPR文库测序数据报告生成器")
    print("=" * 60)

    generator.scan_files()
    generator.copy_resources()
    output_file = generator.generate_report()

    print("\n" + "=" * 60)
    print("报告生成完成!")
    print(f"输出文件: {output_file}")
    print("=" * 60)


if __name__ == '__main__':
    main()
