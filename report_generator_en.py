# -*- coding: utf-8 -*-
"""
CRISPR Library Sequencing Data Report Generator (English)
Integrated advanced features from reference scripts: multi-condition filtering, search, sort, etc.
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
    print("Warning: pandas not installed. Will use simplified mode for CSV processing.")
    pd = None


class CRISPRReportGeneratorEN:
    """CRISPR Library Sequencing Data Report Generator (English)"""

    def __init__(self, data_dir, output_dir, project_name="sgRNA Library Analysis Report",
                 project_id=None, protocol_number="", sample_name=""):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.project_name = project_name if project_name else "sgRNA Library Analysis Report"
        self.report_title = ""
        self.project_id = project_id or self._detect_project_id()
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        self.protocol_number = protocol_number
        self.sample_name = sample_name

        self.clean_summary = None
        self.mapping_result = None
        self.sgrna_counts = None
        self.data_files = {}
        self.image_files = {}
        self.all_images = []

        self._load_cover_resources()

    def _detect_project_id(self):
        """Auto-detect project ID from data filenames"""
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
        """Load cover resources (logo, background)"""
        self.logo_base64 = ''
        self.bg_base64 = ''
        self.bg_mime = 'image/png'

        script_dir = Path(__file__).parent if '__file__' in globals() else self.data_dir

        for logo_name in ['logo_en.png', 'logo.png', 'logo.jpg', 'logo.jpeg']:
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
        """Convert image file to base64 encoding"""
        try:
            with open(filepath, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Warning: Failed to read image {filepath}: {e}")
            return ''

    def scan_files(self):
        """Scan data directory and collect all files"""
        print(f"Scanning directory: {self.data_dir}")

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
        print(f"Found {csv_count} CSV file(s)")
        print(f"Found {img_count} image file(s)")

        self._load_main_data()

    def _load_main_data(self):
        """Load main data files"""
        for rel_path, files in self.data_files.items():
            for f in files:
                if 'clean' in f['name'].lower() and f['name'].endswith('.csv'):
                    self.clean_summary = self._read_csv(f['path'])
                    if self.clean_summary is not None:
                        print(f"  Loaded: {f['name']}")
                    break

        for rel_path, files in self.data_files.items():
            for f in files:
                if f['name'] == 'result.csv':
                    self.mapping_result = self._read_csv(f['path'])
                    if self.mapping_result is not None:
                        print(f"  Loaded: {f['name']}")
                    break

        for rel_path, files in self.data_files.items():
            for f in files:
                if f['name'] == 'output.csv':
                    self.sgrna_counts = self._read_csv(f['path'])
                    if self.sgrna_counts is not None:
                        print(f"  Loaded: {f['name']}")
                    break

    def _read_csv(self, filepath):
        """Read CSV file"""
        if pd is None:
            return None
        try:
            return pd.read_csv(filepath)
        except Exception as e:
            print(f"Failed to read CSV {filepath}: {e}")
            return None

    def get_csv_relative_path(self, csv_path):
        """Get the relative path of a copied CSV file in the output directory"""
        csv_path = str(csv_path)
        for rel_path, files in self.data_files.items():
            for f in files:
                if f['path'] == csv_path and 'output_path' in f:
                    return f['output_path']
        return None

    def copy_resources(self):
        """Copy data files and images to output directory"""
        print("\nCopying resource files...")

        data_dir = self.output_dir / 'data'
        images_dir = self.output_dir / 'images'
        css_dir = self.output_dir / 'css'
        js_dir = self.output_dir / 'js'

        for d in [data_dir, images_dir, css_dir, js_dir]:
            d.mkdir(parents=True, exist_ok=True)

        for rel_path, files in self.data_files.items():
            target_dir = data_dir / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                src = Path(f['path'])
                dst = target_dir / src.name
                try:
                    shutil.copy2(src, dst)
                    f['output_path'] = str(Path('data') / rel_path / src.name)
                    print(f"  Copied: {src.name}")
                except Exception as e:
                    print(f"  Copy failed {src}: {e}")

        for rel_path, images in self.image_files.items():
            target_dir = images_dir / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            for img in images:
                src = Path(img['path'])
                dst = target_dir / src.name
                try:
                    shutil.copy2(src, dst)
                    img['output_path'] = str(Path('images') / rel_path / src.name)
                    print(f"  Copied: {src.name}")
                except Exception as e:
                    print(f"  Copy failed {src}: {e}")

        self._copy_static_images()
        self._write_css(css_dir)
        self._write_js(js_dir)
        self._copy_library_files(js_dir, css_dir)

        print("Resource files copied successfully.")

    def _copy_library_files(self, js_dir, css_dir):
        """Copy front-end library files (bootstrap-4.3.1.min.css renamed to bootstrap.min.css)"""
        script_dir = Path(__file__).parent if '__file__' in globals() else self.data_dir
        resources_dir = script_dir / 'resources'

        if not resources_dir.exists():
            print("Warning: resources folder not found.")
            return

        for css_file in resources_dir.glob('css/*.css'):
            if css_file.name in ('style.css', 'base.css', 'gallery.css'):
                continue
            dst_name = 'bootstrap.min.css' if css_file.name == 'bootstrap-4.3.1.min.css' else css_file.name
            shutil.copy2(css_file, css_dir / dst_name)

        for js_file in resources_dir.glob('js/*.js'):
            if js_file.name in ('common.js', 'scrolltop.js'):
                continue
            dst_name = 'bootstrap.min.js' if js_file.name == 'bootstrap-4.3.1.min.js' else js_file.name
            shutil.copy2(js_file, js_dir / dst_name)

        fancybox_src = resources_dir / 'js' / 'fancybox'
        if fancybox_src.exists():
            fancybox_dst = js_dir / 'fancybox'
            fancybox_dst.mkdir(exist_ok=True)
            for fb_file in fancybox_src.glob('*'):
                if fb_file.is_file():
                    shutil.copy2(fb_file, fancybox_dst / fb_file.name)

    def _copy_static_images(self):
        """Copy static report images (flute.png, fastq.png)"""
        static_images = ['flute.png', 'fastq.png']
        script_dir = Path(__file__).parent if '__file__' in globals() else self.data_dir

        for img_name in static_images:
            src = script_dir / img_name
            if src.exists():
                dst = self.output_dir / 'images' / img_name
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(src, dst)
                    print(f"  Copied: {img_name}")
                except Exception as e:
                    print(f"  Failed to copy static image {img_name}: {e}")

    def _write_css(self, css_dir):
        """Generate CSS style files"""
        with open(css_dir / 'style.css', 'w', encoding='utf-8') as f:
            f.write(self._get_style_css())

        with open(css_dir / 'base.css', 'w', encoding='utf-8') as f:
            f.write(self._get_base_css())

        with open(css_dir / 'gallery.css', 'w', encoding='utf-8') as f:
            f.write(self._get_gallery_css())

    def _write_js(self, js_dir):
        """Generate JavaScript files"""
        with open(js_dir / 'common.js', 'w', encoding='utf-8') as f:
            f.write(self._get_common_js())

        with open(js_dir / 'scrolltop.js', 'w', encoding='utf-8') as f:
            f.write(self._get_scrolltop_js())

    def generate_report(self):
        """Generate the complete HTML report"""
        print("\nGenerating HTML report...")
        html = self._generate_html()
        output_file = self.output_dir / 'report.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Report generated: {output_file}")
        return output_file

    def generate_table_html(self, df, caption="Data Table", max_rows=10, relative_path=None,
                           enable_search=False, enable_filter=False, fixed_column_width=False):
        """Generate table HTML with pagination and multi-condition filter modal"""
        if df is None or df.empty:
            return '<p>No data available.</p>'

        table_id = f"table_{hash(caption) % 100000}"
        total_rows = len(df)
        total_pages = (total_rows + max_rows - 1) // max_rows
        columns = list(df.columns)

        first_col_width = '40ch'
        remaining_cols = len(columns) - 1
        other_col_width = f'calc((100% - {first_col_width}) / {remaining_cols})' if remaining_cols > 0 else 'auto'

        headers = ''.join([
            f'<th onclick="sortTableByColumn(\'{table_id}\', {i})" style="cursor:pointer">{col}<span class="sort-indicator"></span></th>'
            for i, col in enumerate(columns)
        ])
        table_classes = 'gy table table-striped table-bordered'

        rows = ''
        for idx, row in df.head(max_rows).iterrows():
            cells = ''.join([f'<td>{val}</td>' for val in row])
            rows += f'<tr>{cells}</tr>'

        search_svg = '<svg viewBox="0 0 1024 1024"><path d="M909.6 854.5L649.9 594.8C690.2 542.7 712 479 712 412c0-80.2-31.3-155.6-87.9-212.1-56.6-56.7-132-87.9-212.1-87.9s-155.5 31.3-212.1 87.9C143.2 256.5 112 331.8 112 412c0 80.1 31.3 155.5 87.9 212.1C256.5 680.8 331.8 712 412 712c67 0 130.6-21.8 182.7-62l259.7 259.6a8.2 8.2 0 0011.6 0l43.6-43.5a8.2 8.2 0 000-11.6zM412 640c-125.9 0-228-102.1-228-228S286.1 184 412 184s228 102.1 228 228-102.1 228-228 228z"/></svg>'
        filter_svg = '<svg viewBox="0 0 1024 1024"><path d="M924.8 625.7l-65.5-56c3.1-19 4.7-38.4 4.7-57.7s-1.6-38.8-4.7-57.7l65.5-56a32.03 32.03 0 009.3-35.2l-54.7-110.6a32.12 32.12 0 00-29.2-18l-1.3.1-85.3 15.6c-24.3-19.1-51.2-35.1-80-47.3L669 116.6A32 32 0 00640.4 96H531c-14.3 0-26.8 9.5-31 23.3L485.4 206c-28.8 12.2-55.7 28.2-80 47.3l-85.3-15.6-1.3-.1a32.09 32.09 0 00-29.2 18L235 366.2a32.03 32.03 0 009.3 35.2l65.5 56c-3.1 19-4.7 38.4-4.7 57.7s1.6 38.8 4.7 57.7l-65.5 56a32.03 32.03 0 00-9.3 35.2l54.7 110.6c7.3 14.8 24.3 21.6 40 15.9l80.2-15c24.3 19.1 51.2 35.1 80 47.3l14.6 86.6c4.2 13.8 16.7 23.3 31 23.3h109.4c14.3 0 26.8-9.5 31-23.3l14.6-86.6c28.8-12.2 55.7-28.2 80-47.3l80.2 15.1c15.6 5.6 32.7-1 40-15.9l54.7-110.6a32.03 32.03 0 00-9.3-35.2zM585.6 631c-65.8 65.8-172.5 65.8-238.3 0-65.8-65.8-65.8-172.5 0-238.3 65.8-65.8 172.5-65.8 238.3 0 65.8 65.8 65.8 172.5 0 238.3z"/></svg>'

        search_html = ''
        if enable_search:
            search_html = f'''
            <div class="modern-search">
                {search_svg}
                <input type="text" id="{table_id}_search" placeholder="Search keywords..." onkeyup="searchTableByColumn('{table_id}')">
            </div>'''

        toolbar_html = ''
        if enable_search or enable_filter:
            toolbar_html = '<div class="modern-table-toolbar">'
            if enable_search:
                toolbar_html += search_html
            if enable_filter:
                toolbar_html += f'''
            <button type="button" class="modern-filter-btn" onclick="openFilterModal('{table_id}')">
                {filter_svg} Multi-condition Filter
                <span id="{table_id}_filter_count" class="filter-count-badge"></span>
            </button>'''
            toolbar_html += '</div>'

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
                        <div class="subtitle-red">Multi-condition Filter</div>
                        <span class="filter-modal-close" onclick="closeFilterModal('{table_id}')">&times;</span>
                    </div>
                    <div class="filter-modal-body">
                        <div class="filter-logic-section">
                            <label>Condition Logic:</label>
                            <div class="filter-logic-buttons">
                                <label class="filter-radio">
                                    <input type="radio" name="{table_id}_logic" value="AND" checked>
                                    <span>AND - All conditions must be met</span>
                                </label>
                                <label class="filter-radio">
                                    <input type="radio" name="{table_id}_logic" value="OR">
                                    <span>OR - Any condition met</span>
                                </label>
                            </div>
                        </div>
                        <div id="{table_id}_filter_conditions" class="filter-conditions"></div>
                        <div class="filter-actions">
                            <button type="button" class="btn btn-secondary btn-sm" onclick="addFilterCondition('{table_id}')">+ Add Filter</button>
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="clearAllFilters('{table_id}')">Clear All</button>
                        </div>
                    </div>
                    <div class="filter-modal-footer">
                        <span id="{table_id}_filter_result_count" class="filter-result-count"></span>
                        <div class="filter-modal-buttons">
                            <button type="button" class="btn btn-secondary" onclick="closeFilterModal('{table_id}')">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="applyFilters('{table_id}')">Apply</button>
                        </div>
                    </div>
                </div>
            </div>
            <select id="{table_id}_field_template" style="display:none;">{field_options}</select>'''

        download_svg = '''<span class="download-icon"><svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M512 666.286l226.286-226.286-60.343-60.343-123.429 123.429V128H469.714v375.086L346.286 379.657l-60.343 60.343L512 666.286zM853.714 853.714H170.286V725.714H85.143v170.857c0 23.429 18.857 42.857 42.857 42.857h768c23.429 0 42.857-19.429 42.857-42.857V725.714h-85.143v128z"/></svg></span>'''

        if relative_path:
            href = relative_path.replace('%2F', '/')
            dl_name = html_module.escape(Path(href).name, quote=True)
            caption_html = f'<a href="{href}" class="table-caption-link" download="{dl_name}">{download_svg}<span class="download-text">{caption}</span></a>'
        else:
            caption_html = caption

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

        init_start = 1
        init_end = min(max_rows, total_rows)
        page_nums_html = ''
        if total_pages > 1:
            visible_end = min(total_pages, 5)
            for p in range(1, visible_end + 1):
                cls = 'page-num active' if p == 1 else 'page-num'
                page_nums_html += f'<span class="{cls}" onclick="goToPage(\'{table_id}\', {p})">{p}</span>'
        pagination = f'''<div class="table-pagination" id="{table_id}_pagination">
            <span class="pagination-info">Total {total_rows} rows, showing {init_start}-{init_end}</span>
            <div class="pagination-controls">
                <span class="page-nav prev-nav disabled" onclick="prevPage('{table_id}')">Prev</span>
                <span class="page-arrow page-arrow-prev disabled" onclick="prevPage('{table_id}')">&lt;</span>
                <span class="page-nums" id="{table_id}_pageNums">{page_nums_html}</span>
                <span class="page-arrow page-arrow-next" onclick="nextPage('{table_id}')">&gt;</span>
                <span class="page-nav next-nav" onclick="nextPage('{table_id}')">Next</span>
            </div>
        </div>'''

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
        """Classify images by filename"""
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
        """Generate image selector"""
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
        """Group images by type"""
        groups = {}
        for img in images:
            name = img['name']
            if 'base_quality' in name.lower() or 'quality' in name.lower():
                group_name = 'base_quality'
                display_name = 'Base Quality & Error Rate'
            elif 'raw reads' in name.lower() or 'reads_classification' in name.lower():
                group_name = 'raw_reads'
                display_name = 'Raw Reads Classification'
            elif 'volcano' in name.lower():
                group_name = 'volcano'
                display_name = 'Volcano Plot'
            elif 'scatter' in name.lower():
                group_name = 'scatter'
                display_name = 'Scatter Plot'
            elif 'rank' in name.lower():
                group_name = 'rank'
                display_name = 'Rank Plot'
            elif 'kegg' in name.lower():
                group_name = 'kegg'
                display_name = 'KEGG Pathway'
            elif 'go' in name.lower():
                group_name = 'go'
                display_name = 'GO Enrichment'
            elif 'correlation' in name.lower():
                group_name = 'correlation'
                display_name = 'Correlation Heatmap'
            elif 'density' in name.lower():
                group_name = 'density'
                display_name = 'Density Distribution'
            elif 'depth' in name.lower():
                group_name = 'depth'
                display_name = 'sgRNA Sequencing Depth'
            elif 'uniformity' in name.lower() or 'slope' in name.lower():
                group_name = 'uniformity'
                display_name = 'Uniformity Slope'
            else:
                group_name = 'other'
                display_name = 'Other Images'

            if group_name not in groups:
                groups[group_name] = {'display_name': display_name, 'images': []}
            groups[group_name]['images'].append(img)
        return groups

    def _generate_side_by_side_layout(self, images, category, group_key, display_name, description=None):
        """Generate side-by-side image layout"""
        desc_html = f'<p class="modern-img-desc">{description}</p>' if description else ''
        html = f'''
            <div class="modern-img-group">
                <div class="modern-img-header">
                    <span>{display_name}</span>
                    <span class="badge">{len(images)} image(s)</span>
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
        """Generate stacked image layout"""
        img_count = len(images)
        group_id = f"{category}_{group_key}"

        if img_count == 1:
            img = images[0]
            img_path = img.get('output_path', img['path']).replace('\\', '/')
            html = f'''
            <div class="modern-img-group">
                <div class="modern-img-header">
                    <span>{display_name}</span>
                    <span class="badge">1 image</span>
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
                    <span class="badge">{img_count} images</span>
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
        """Generate the full HTML content"""
        self.all_images = []
        for rel_path, images in self.image_files.items():
            for img in images:
                img_copy = img.copy()
                img_copy['rel_path'] = rel_path
                img_copy['type'] = self._classify_image(img['name'])
                self.all_images.append(img_copy)

        images_by_type = {}
        for img in self.all_images:
            img_type = img['type']
            if img_type not in images_by_type:
                images_by_type[img_type] = []
            images_by_type[img_type].append(img)

        logo_src = f"data:image/png;base64,{self.logo_base64}" if self.logo_base64 else ""
        bg_mime = getattr(self, 'bg_mime', 'image/png')
        bg_src = f"data:{bg_mime};base64,{self.bg_base64}" if self.bg_base64 else ""
        logo_display = 'block' if self.logo_base64 else 'none'
        bg_display = 'block' if self.bg_base64 else 'none'

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.project_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Source+Sans+3:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="css/bootstrap.min.css">
    <link rel="stylesheet" href="css/jquery-ui.css">
    <link rel="stylesheet" href="css/jquery.tocify.css">
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/base.css">
    <link rel="stylesheet" href="css/gallery.css">
</head>
<body>

    <!-- TOC Sidebar -->
    <nav class="toc-sidebar" aria-label="Quick Navigation">
        <div class="toc-sidebar-header">
            <span class="toc-sidebar-title">Quick Navigation</span>
            <span class="toc-sidebar-header-icon">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M11 21h-1l1-7H7.5c-.58 0-.57-.32-.38-.66.19-.34.05-.08.07-.12C8.48 10.94 10.42 7.54 13.01 3h1l-1 7h3.5c.49 0 .56.33.47.51l-.07.15C17.52 13.06 15.58 16.4 13 21z"/></svg>
            </span>
        </div>
        <div class="toc-sidebar-body">
            <div id="toc"></div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="main-content">
    <div class="report-container">

'''
        protocol_text = f"Protocol No.: {self.protocol_number}" if self.protocol_number else ""
        html += f'''
        <div class="report-cover">
            <div class="report-cover-inner">
            <div class="cover-header">
                <div class="cover-logo">
                    <img src="{logo_src}" alt="Logo" style="display: {logo_display};">
                </div>
            </div>

            <div class="cover-body">
                <div class="cover-body-upper">
                    <div class="cover-center-block">
                        <h1 class="cover-main-title">sgRNA Library</h1>
                        <div class="cover-title-badge">Analysis Report</div>
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

        html += f'''
<br>
            <header class="report-header">
                <h1 class="report-title">{self.report_title}</h1>
                <div class="report-header-box">
                    <div class="report-meta-grid">
                        <div class="report-meta-row">
                            <span class="report-meta-label">Project ID</span>
                            <span class="report-meta-value">{self.project_id}</span>
                        </div>
                                                <div class="report-meta-row">
                            <span class="report-meta-label">Data Type</span>
                            <span class="report-meta-value">sgRNA Library Sequencing Analysis</span>
                        </div>
                        <div class="report-meta-row">
                            <span class="report-meta-label">Report Type</span>
                            <span class="report-meta-value">{self.project_name}</span>
                        </div>
                                                <div class="report-meta-row">
                            <span class="report-meta-label">Report Date</span>
                            <span class="report-meta-value">{self.report_date}</span>
                        </div>
                    </div>
                </div>
            </header>
            <br><br>

'''
        html += self._generate_section('overview', '1 Project Summary', self._generate_overview_section())
        html += self._generate_section('quality-control', '2 Quality Control', self._generate_qc_section())
        html += self._generate_section('mapping', '3 Statistical Analysis', self._generate_mapping_section())
        if images_by_type:
            html += self._generate_section('figures', '4 Figures', self._generate_figures_section(images_by_type))

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
        """Generate a section HTML block"""
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
    <h2 class="section-title-modern">{num_html}&nbsp;{text_html}</h2>
                {content}
            </section>
</div>
'''

    def _generate_overview_section(self):
        """Generate the Project Summary section (Section 1)"""
        return '''
        <h3>Technical Overview</h3>
        <p class="para-no-indent">
            The basic principle of gRNA library construction is to utilize a gRNA that is identical to the target DNA to guide Cas9 nuclease to modify the DNA of the target gene, so as to cause the functional mutation or loss of the gene. On this basis, CRISPR/Cas9 technology is used to establish mammalian genome-wide mutation libraries or gene mutant libraries related to a certain category of function. Through functional screening and enrichment, as well as subsequent PCR amplification and deep sequencing analysis, genes related to the phenotype are discovered and screened. This process is called <strong>CRISPR/Cas9 gRNA library screening</strong>.
        </p>

        <h3>gRNA Library Applications</h3>
        <p class="para-no-indent">
            gRNA library is an ideal tool for drug screening or targeted screening of specific pathways. The establishment of gRNA libraries plays an important role in functional gene screening, disease mechanism research, and drug development. gRNA libraries include genome-wide libraries, lncRNA libraries, pathway-specific libraries (e.g., signaling pathways, cell apoptosis, cell proliferation, ion channels, nuclear receptor, and various diseases). The construction of genome-wide gRNA libraries can target any type of genomic DNA, including ORF cDNA, lncRNA cDNA, and cDNA fragments of specific regions. An efficient gRNA library constructed to target full-length cDNA or genomic DNA is highly suitable for high-throughput functional gene and related drug target screening.
        </p>

        <h3>Experimental Workflow</h3>

        <h4 class="subtitle-red">1.1 Library Preparation</h4>
        <p class="para-no-indent">
            DNA samples are processed through DNA fragmentation (Shear), end repair, 3\' end A-tailing (Add 3\'A Tail), adapter ligation (Ligate Adapters), size selection (Clean), PCR enrichment (Enrich with PCR), size selection (Clean), and PCR product QC to construct an Illumina high-throughput sequencing library.
        </p>
        <div style="margin: 20px 0; text-align: center;">
            <img src="images/flute.png" alt="Library Preparation Workflow" style="max-height: 500px;">
        </div>

        <h4 class="subtitle-red">1.2 Sequencing</h4>
        <p class="para-no-indent">
            Sequencing is performed on the Illumina platform. FASTQ is the output format of the sequencing platforms. It contains the sequence information of reads and their corresponding sequencing quality information. Each read in a FASTQ format file is described in four lines as follows:
        </p>

        <div class="rounded-info-box">
            <div style="margin: 15px 0; text-align: center;">
                <img src="images/fastq.png" alt="Sequencing Data" style="max-height: 380px;">
            </div>
            <p class="para-no-indent" style="margin-top: 10px;">
            <strong>Line 1</strong> starts with "@" and is followed by the basic identifier information of the read (divided into a unique ID and optional description fields separated by a space). The ID part is the unique identifier for each read, containing multiple fields separated by colons. The description area is optional and can store custom information such as primer sequences used during sequencing.
            </p>
            <p class="para-no-indent" style="margin-top: 8px;">
            <strong>Line 2</strong> is the base sequence (comprising A, T, C, G, N where N represents an uncertain base type).
            </p>
            <p class="para-no-indent" style="margin-top: 8px;">
            <strong>Line 3</strong> starts with "+" and is used to separate the sequencing sequence from the quality value content. Optionally, the description from Line 1 can be appended.
            </p>
            <p class="para-no-indent" style="margin-top: 8px;">
            <strong>Line 4</strong> contains the sequencing quality scores for the corresponding base sequence (stored in ASCII code, corresponding one-to-one with the base sequence in Line 2).
            </p>
        </div>

        <h4 class="subtitle-red">1.3 Data Analysis</h4>

        <div class="sub-content-block">
        <h4 class="subtitle-black">1.3.1 Sequencing Data QC</h4>
        <p class="para-no-indent">Quality control (QC) is performed on raw sequencing data. Low-quality reads and adapter contamination are removed to obtain clean reads for downstream analysis.</p>

        <h4 class="subtitle-black">1.3.2 Reads Alignment</h4>
        <p class="para-no-indent">Clean reads are aligned to the sgRNA library reference sequence. The read count for each sgRNA is extracted and tallied.</p>

        <h4 class="subtitle-black">1.3.3 Statistical Analysis</h4>
        <p class="para-no-indent">Statistical analysis is performed on the alignment results, including the number of mapped reads, number of covered sgRNAs and genes, coverage rate, and read uniformity.</p>
        </div>

'''

    def _generate_qc_section(self):
        """Generate the Quality Control section (Section 2)"""
        html = '''
        <h3>Sequencing Quality and Error Rate Distribution</h3>
        <p class="para-no-indent">
            Sequencing error rate is related to base quality and is jointly affected by factors including the sequencer itself, sequencing reagents, and samples. For Illumina high-throughput sequencing platforms, sequencing quality and error rate distribution exhibit two characteristics:
        </p>
        <ul class="overview-list">
            <li>The quality of the first few bases in each read is typically lower, due to slower focusing of the sequencer's fluorescence-sensitive element during the initial stage of sequencing-by-synthesis, resulting in lower-quality fluorescence images and higher base-calling error rates.</li>
            <li>As sequencing progresses, the error rate increases and quality decreases due to incomplete fluorophore cleavage and de-phasing, which cause signal attenuation.</li>
        </ul>

        <h4 style="color: #222; text-indent: 0;">Quality Score and Error Rate Conversion</h4>
        <p class="para-no-indent">
            If the base quality score is denoted as Q and the error probability as P, the relationship between quality score and error rate is given by the following formulas:
        </p>
        <div class="gray-formula-box">
            <p style="margin: 5px 0;"><strong>Q = -10 &times; log&#8321;&#8320;P</strong></p>
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

        <h3 style="color: #222; border-left: 4px solid #da1e33; padding-left: 10px; font-size: 18px; margin: 20px 0 15px 0; font-weight: bold;">Raw Data Filtering</h3>
        <p class="para-no-indent">
            Raw sequencing data may contain adapter sequences and low-quality reads. To ensure data quality, raw reads are filtered to obtain clean reads, upon which all downstream analyses are based.
        </p>

        <h3 style="color: #222; border-left: 4px solid #da1e33; padding-left: 10px; font-size: 18px; margin: 20px 0 15px 0; font-weight: bold;">Data Processing Steps:</h3>
        <ol style="list-style-type: decimal; margin: 10px 0 10px 0; padding-left: 1.8em; line-height: 1.9; color: #3E3A39;">
            <li style="margin-bottom: 6px;">Remove read pairs with length less than 50 bp.</li>
            <li style="margin-bottom: 6px;">Remove read pairs if the proportion of N bases exceeds 10%.</li>
            <li style="margin-bottom: 6px;">Remove read pairs with Q20 less than 80% (Q20 refers to base quality score &ge; 20).</li>
        </ol>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">

'''
        if self.clean_summary is not None:
            html += '<h3>QC Statistics</h3>'

            for col in self.clean_summary.columns:
                col_lower = col.lower()
                if any(k in col_lower for k in ('reads',)):
                    try:
                        self.clean_summary[col] = pd.to_numeric(self.clean_summary[col], errors='coerce').astype('Int64')
                    except Exception:
                        pass

            if 'total_reads' in self.clean_summary.columns and 'clean_reads' in self.clean_summary.columns:
                total = pd.to_numeric(self.clean_summary['total_reads'], errors='coerce')
                clean = pd.to_numeric(self.clean_summary['clean_reads'], errors='coerce')
                self.clean_summary['Effective_Rate(%)'] = (clean / total * 100).round(2)
                cols = list(self.clean_summary.columns)
                cols.remove('Effective_Rate(%)')
                pos = cols.index('discard_reads')
                cols.insert(pos + 1, 'Effective_Rate(%)')
                self.clean_summary = self.clean_summary[cols]

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

            if self.sample_name and 'Sample' in self.clean_summary.columns:
                self.clean_summary['Sample'] = self.sample_name

            rel_path = None
            for rel_path_key, files in self.data_files.items():
                for f in files:
                    if 'clean' in f['name'].lower() and f['name'].endswith('.csv'):
                        rel_path = self.get_csv_relative_path(f['path'])
                        break
                if rel_path:
                    break

            html += self.generate_table_html(self.clean_summary.head(1), "Clean Summary Overview",
                                            relative_path=rel_path)

            html += '''
            <div class="plain-field-desc">
                <strong>Field Descriptions:</strong><br>
                Sample: Sample name;<br>
                total_reads: Total number of raw reads;<br>
                clean_reads: Number of effective reads after filtering;<br>
                discard_reads: Number of discarded reads after filtering;<br>
                Effective_Rate(%): Percentage of clean reads relative to raw reads;<br>
                Q20(%): Percentage of bases with quality score &ge; 20;<br>
                Q30(%): Percentage of bases with quality score &ge; 30;<br>
                GC(%): Percentage of GC bases among total bases
            </div>
'''

        quality_imgs = [img for img in self.all_images if img['type'] in ['base_quality', 'raw_reads']]
        if quality_imgs:
            html += '<h3>Raw Data Quality Distribution</h3>'
            html += '''
            <p class="para-no-indent">
                Displays the quality distribution of raw sequencing data for each sample, including base quality distribution, GC content distribution, etc., used to evaluate the reliability of sequencing data.
            </p>
            '''
            html += self.generate_image_selector(quality_imgs[:2], "qc_images", "QC Charts", side_by_side=True)

        return html

    def _generate_mapping_section(self):
        """Generate the Statistical Analysis section (Section 3)"""
        html = ''

        if self.mapping_result is not None:
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

            for col in self.mapping_result.columns:
                col_lower = col.lower()
                if col_lower in ('mean_depth', 'median_depth', 'max_depth', 'skew_ratio'):
                    try:
                        self.mapping_result[col] = pd.to_numeric(self.mapping_result[col], errors='coerce').round(2)
                    except Exception:
                        pass

            rename_map = {}
            for old_col, new_col in [('Percentage1', 'Mapping_Rate(%)')]:
                if old_col in self.mapping_result.columns:
                    try:
                        raw = self.mapping_result[old_col].astype(str).str.replace('%', '', regex=False)
                        self.mapping_result[old_col] = pd.to_numeric(raw, errors='coerce').round(2)
                        rename_map[old_col] = new_col
                    except Exception:
                        pass
            if 'Percentage2' in self.mapping_result.columns:
                try:
                    raw = self.mapping_result['Percentage2'].astype(str).str.replace('%', '', regex=False)
                    p2 = pd.to_numeric(raw, errors='coerce')
                    if p2.max() > 1:
                        self.mapping_result['Coverage Rate (%)'] = (100 - p2).round(2)
                    else:
                        self.mapping_result['Coverage Rate (%)'] = ((1 - p2) * 100).round(2)
                    self.mapping_result = self.mapping_result.drop(columns=['Percentage2'])
                except Exception:
                    pass
            if rename_map:
                self.mapping_result = self.mapping_result.rename(columns=rename_map)

            if 'Coverage Rate (%)' in self.mapping_result.columns and 'Zero_sgrnas' in self.mapping_result.columns:
                cols = list(self.mapping_result.columns)
                cols.remove('Coverage Rate (%)')
                pos = cols.index('Zero_sgrnas')
                cols.insert(pos + 1, 'Coverage Rate (%)')
                self.mapping_result = self.mapping_result[cols]

            rel_path = None
            for rel_path_key, files in self.data_files.items():
                for f in files:
                    if f['name'] == 'result.csv':
                        rel_path = self.get_csv_relative_path(f['path'])
                        break
                if rel_path:
                    break

            html += '''
        <h3>Sample Reads Statistics</h3>
        <p class="para-no-indent">
            sgRNA sequences are extracted from reads and aligned to the sgRNA library reference sequence. Statistical analysis is performed on the alignment results, including the number of perfectly matched reads, the number of matched sgRNAs and genes, coverage, and uniformity. These metrics reflect the reliability and accuracy of the data.
        </p>
'''
            html += self.generate_table_html(self.mapping_result, "Alignment Statistics",
                                            relative_path=rel_path)

            html += '''
            <div class="plain-field-desc">
                <strong>Field Descriptions:</strong><br>
                Reads: Total number of gRNA reads;<br>
                Mapped: Number of reads perfectly matching the gRNA library;<br>
                NotMapped: Number of reads not aligned to the reference sequence;<br>
                NotFound: Number of reads not found in the library;<br>
                Mapping_Rate(%): Mapping rate (proportion of mapped reads to total reads);<br>
                Total_sgrnas: Number of gRNAs in the gRNA library;<br>
                Zero_sgrnas: Number of missing/undetected gRNAs in the library;<br>
                Coverage Rate (%): Library coverage, the percentage of detected gRNAs among total gRNAs;<br>
                Mean_depth: Average sequencing depth per gRNA;<br>
                Median_depth: Median sequencing depth of gRNAs;<br>
                Max_depth: Maximum sequencing depth observed for a single gRNA;<br>
                Total_genes: Total number of targeted genes in the library;<br>
                Zero_genes: Number of undetected genes;<br>
                skew_ratio: Library uniformity ratio (ratio of gRNA count at 90% cumulative distribution to 10% cumulative distribution)
        </div>
'''

        if self.sgrna_counts is not None and not self.sgrna_counts.empty:
            sgrna_rel_path = None
            for rel_path_key, files in self.data_files.items():
                for f in files:
                    if f['name'] == 'output.csv':
                        sgrna_rel_path = self.get_csv_relative_path(f['path'])
                        break
                if sgrna_rel_path:
                    break

            html += '''
        <h3>sgRNA Counts Detail</h3>
        <p class="para-no-indent">
            The following table shows the complete count data for each individual sgRNA.
        </p>
'''
            html += self.generate_table_html(self.sgrna_counts, "sgRNA Counts Detail",
                                            max_rows=10, relative_path=sgrna_rel_path,
                                            enable_search=True, enable_filter=True)

            html += '''
        <div class="plain-field-desc">
            <strong>Field Descriptions:</strong><br>
            gene: Target gene corresponding to the sgRNA;<br>
            uid: Unique identifier of the sgRNA;<br>
            seq: Nucleic acid sequence of the sgRNA;<br>
            counts: Number of reads aligned to this sgRNA
        </div>
'''

        return html

    def _generate_figures_section(self, images_by_type):
        """Generate the Figures section (Section 4)"""
        html = '<p class="para-no-indent">Charts and figures generated from the analysis are shown below.</p>'

        display_names = {
            'depth': 'Sequencing Depth Distribution',
            'uniformity': 'Uniformity Analysis'
        }
        depth_desc = 'Inductive statistics on the alignment counts show the sequencing depth distribution of sgRNAs across the library, providing an intuitive visualization of how reads are distributed among individual sgRNAs.'
        uniformity_desc = 'Library uniformity is described by the skew ratio, calculated as the ratio of gRNA depth at the 90th percentile to the gRNA depth at the 10th percentile of the cumulative distribution. Evaluating library uniformity is critical for downstream functional screening, as it effectively prevents false-negative results from missing sgRNAs and false-positive artifacts caused by biased sgRNA representation.'
        for img_type in ['depth', 'uniformity']:
            if img_type in images_by_type:
                images = images_by_type[img_type]
                html += f'<h3>{display_names.get(img_type, img_type)}</h3>'
                desc = depth_desc if img_type == 'depth' else uniformity_desc
                html += self.generate_image_selector(images, f"img_{img_type}", side_by_side=True, description=desc)

        return html

    def _get_style_css(self):
        """Get full style.css content"""
        return '''/* ========== Cover: wide landscape, left-text-right-image layout ========== */
.report-cover {
    width: 100%;
    background-color: #fff;
    margin-bottom: 40px;
    page-break-after: always;
    box-sizing: border-box;
}
.report-cover-inner {
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
    box-sizing: border-box;
    padding: 0 24px;
}

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

html, body, div, ul, ol {
    margin: 0;
    padding: 0;
}
html, body, div, ul, ol { margin: 0; padding: 0; }
body {
    font-family: 'Source Sans 3', 'Inter', 'Segoe UI', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #3E3A39;
    background: #FFFFFF;
}
a { color: #da1e33; text-decoration: none; }
a:hover { text-decoration: underline; }

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
.overview-list li::before { content: "\\00B7"; position: absolute; left: 0; color: #3E3A39; font-weight: bold; }

.title-bar-red {
    border-left: 4px solid #da1e33;
    padding-left: 10px;
    font-size: 20px;
    font-weight: bold;
    color: #333;
    margin: 25px 0 15px 0;
}
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
.subtitle-black { color: #000; font-size: 15px; font-weight: bold; margin: 15px 0 10px 0; text-indent: 0; }
.sub-content-block { padding-left: 2em; }

.rounded-info-box {
    border: 1px solid #ccc;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
    background: #fff;
}

.gray-formula-box {
    background: #f4f5f7;
    padding: 15px 20px;
    border-radius: 4px;
    margin: 15px 0;
    font-family: Arial, sans-serif;
    color: #333;
    line-height: 2;
}

.workflow-diagram {
    display: flex; align-items: center; justify-content: center; flex-wrap: wrap;
    gap: 10px; margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;
}
.workflow-step { display: flex; flex-direction: column; align-items: center; padding: 15px 20px; background: #036eb8; color: #fff; border-radius: 6px; text-align: center; }
.workflow-step span { font-weight: 600; font-size: 14px; }
.workflow-step small { font-size: 11px; opacity: 0.8; margin-top: 4px; }
.workflow-step.final { background: #539A34; }
.workflow-arrow { font-size: 24px; color: #999; }

.analysis-steps { margin: 20px 0; }
.analysis-step { display: flex; align-items: flex-start; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }
.step-number { width: 40px; height: 40px; background: #da1e33; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; flex-shrink: 0; margin-right: 15px; }
.step-content h4 { margin: 0 0 8px 0; color: #333; }
.step-content p { margin: 0; color: #666; }

.formula-box { background: #f0f0f0; padding: 15px 25px; border-radius: 6px; margin: 15px 0; text-align: center; }
.formula-box p { margin: 8px 0; font-size: 16px; }

.table-container { margin: 15px 0; }
.table-responsive { overflow-x: auto; margin: 15px 0; }
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

.gy { font-family: 'Source Sans 3', 'Inter', 'Segoe UI', sans-serif; width: 100%; border-collapse: collapse; margin: 15px auto; }
.gy.fixed-first-col { table-layout: fixed; width: 100%; }
.gy.fixed-first-col th:first-child, .gy.fixed-first-col td:first-child { width: 40ch; min-width: 40ch; max-width: 40ch; overflow: hidden; text-overflow: ellipsis; }
.gy th { position: relative; font-size: 1em; border: 2px solid #ffffff; padding: 12px 15px; text-align: center; word-break: keep-all; white-space: nowrap; background-color: #da1e33; color: #ffffff; font-weight: 500; }
.gy td { font-size: 1em; border: 2px solid #ffffff; padding: 10px 15px; text-align: center; word-break: keep-all; white-space: nowrap; color: #333333; }
.gy tr:nth-child(odd) { background: #f8f9fa; }
.gy tr:nth-child(even) { background: #e2e6ea; }
.gy tr:hover td { background: #d4d9df; transition: background 0.3s ease; }

.field-description { background: #f8f9fa; padding: 15px 20px; border-radius: 6px; margin-top: 15px; font-size: 13px; }
.field-description ul { margin: 10px 0 0 20px; }
.field-description li { margin-bottom: 5px; }
.plain-field-desc { font-size: 13px; color: #555; line-height: 1.8; margin-top: 15px; }

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

.modern-table-toolbar { display: flex; justify-content: flex-end; align-items: center; gap: 15px; margin-bottom: 15px; margin-top: -40px; }
.modern-search { position: relative; display: inline-flex; align-items: center; }
.modern-search svg { position: absolute; left: 14px; width: 16px; height: 16px; fill: #333; }
.modern-search input { background: #e6e9ec; border: none; border-radius: 20px; padding: 8px 15px 8px 36px; font-size: 14px; color: #333; width: 260px; outline: none; transition: all 0.3s; }
.modern-search input:focus { background: #dce0e5; box-shadow: 0 0 0 2px rgba(218,30,51,0.15); }
.modern-filter-btn { display: inline-flex; align-items: center; background: #f0f2f5; border: none; border-radius: 20px; padding: 8px 18px; font-size: 14px; color: #555; cursor: pointer; transition: all 0.3s; }
.modern-filter-btn svg { width: 16px; height: 16px; margin-right: 6px; fill: #666; }
.modern-filter-btn:hover { background: #e6e9ec; color: #333; }
.filter-count-badge { background: #da1e33; color: white; border-radius: 10px; padding: 1px 6px; font-size: 12px; margin-left: 6px; display: none; }

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
.page-nav {
    font-size: 13px; color: #555; cursor: pointer; user-select: none; padding: 2px 4px;
}
.page-nav:hover { color: #222; }
.page-nav.disabled { color: #bbb; cursor: default; pointer-events: none; }
.page-arrow {
    font-size: 14px; color: #555; cursor: pointer; user-select: none; padding: 2px 4px; font-family: monospace;
}
.page-arrow:hover { color: #222; }
.page-arrow.disabled { color: #bbb; cursor: default; pointer-events: none; }
.page-nums { display: flex; align-items: center; gap: 4px; }
.page-num {
    display: inline-flex; justify-content: center; align-items: center;
    min-width: 28px; height: 28px; font-size: 13px; color: #555;
    cursor: pointer; user-select: none; border-radius: 4px; transition: all 0.15s ease;
}
.page-num:hover { color: #222; background: #e8e8e8; }
.page-num.active { background: #e3edf5; color: #da1e33; font-weight: 600; cursor: default; }
.page-info { color: #333; font-size: 13px; margin: 0 10px; }

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

#goTopBtn {
    position: fixed; text-align: center; line-height: 30px;
    width: 40px; height: 40px; bottom: 35px; right: 20px;
    cursor: pointer; background: #F7F7F7; border: 1px solid #D1D1D1;
    border-radius: 50%; transition: all 0.3s ease; z-index: 1000;
}
#goTopBtn:hover { background: #da1e33; transform: translateY(-3px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
#goTopBtn:hover svg path { fill: #ffffff; }
@media (max-width: 768px) { #goTopBtn { right: 15px; bottom: 15px; } }

th .sort-indicator { position: absolute; margin-left: 3px; opacity: 0.3; }
th .sort-indicator::before { content: "\\2195"; }
th.sorted-asc .sort-indicator::before { content: "\\2191"; opacity: 1; color: #da1e33; }
th.sorted-desc .sort-indicator::before { content: "\\2193"; opacity: 1; color: #da1e33; }

@media print {
    .toc-sidebar, #goTopBtn { display: none !important; }
    .main-content { margin: 0 !important; padding: 20px !important; }
    .image-viewer img { max-width: 100% !important; max-height: none !important; page-break-inside: avoid; }
}
'''

    def _get_base_css(self):
        """Get base.css content"""
        return '''a, img { border-style: none; outline: none !important }
body { font-size: 14px; padding: 12px; font-family: 'Source Sans 3', 'Inter', 'Segoe UI', sans-serif; }
h1 { font-size: 30px; text-align: center; }
h2 { font-size: 24px; }
h3 { font-size: 18px; text-indent: 0.5em; }
h4 { font-size: 16px; text-indent: 1em; }
p.head { text-align: right; color: grey; font-family: 'Source Sans 3', 'Segoe UI', sans-serif; }
p.paragraph { text-indent: 2em; line-height: 1.5; }
p.center { text-align: center; }
img.normal { height: auto; width: 100%; margin: auto; }
table { font-family: 'Source Sans 3', 'Segoe UI', sans-serif; font-size: 14px; width: 100%; border-collapse: collapse; text-align: center; padding: 3px 10px 2px 10px; }
#goTopBtn { position: fixed; text-align: center; line-height: 30px; width: 30px; height: 33px; font-size: 12px; cursor: pointer; right: 0px; }
.bs-docs-qa { position: relative; margin: 15px 0; padding: 19px 19px 14px; background-color: #fff; border: 1px solid #ddd; border-radius: 4px; }
.alert-qa { background-color: #eeeeee; border-color: #dddddd; }
'''

    def _get_gallery_css(self):
        """Get gallery.css content"""
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
        """Get common.js content"""
        return '''// Switch image group
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

// Switch image
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

// Side-by-side image switch
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

// Toggle fullscreen
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

// ========== Table search and sort ==========
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
        if (filteredData) { infoSpan.textContent = 'Filtered ' + totalRows + ' rows'; }
        else { infoSpan.textContent = 'Total ' + totalRows + ' rows'; }
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
            if (filteredData) { infoSpan.textContent = 'Filtered ' + totalRows + ' rows, showing ' + s + '-' + e; }
            else { infoSpan.textContent = 'Total ' + totalRows + ' rows, showing ' + s + '-' + e; }
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

// ========== Multi-condition filter ==========
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
    if (conditionsContainer.children.length >= 6) { alert('Maximum 6 filter conditions allowed.'); return; }
    var conditionId = Date.now();
    var fieldOptions = templateSelect ? templateSelect.innerHTML : '';
    var conditionHtml = '<div class="filter-condition" id="' + tableId + '_condition_' + conditionId + '">' +
        '<select class="field-select" onchange="updateOperatorOptions(\\'' + tableId + '\\', \\'' + conditionId + '\\')">' + fieldOptions + '</select>' +
        '<select class="operator-select"><option value=">">></option><option value=">=">>=</option><option value="<"><</option><option value="<="><=</option><option value="=">=</option><option value="|x|>">|x|></option></select>' +
        '<input type="text" class="value-input" placeholder="Value">' +
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

// Modern tab switch
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
        """Get scrolltop.js content"""
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
    """Main function"""
    parser = argparse.ArgumentParser(
        description='CRISPR Library Sequencing Data Report Generator (English)',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('data_dir', nargs='?', default='.', help='Data folder path')
    parser.add_argument('output_dir', nargs='?', default='./report_output_en', help='Output directory')
    parser.add_argument('--name', default=None, help='Project name')
    parser.add_argument('--project-id', default=None, help='Project ID')
    parser.add_argument('--protocol', default='', help='Protocol number')
    parser.add_argument('--sample', default='', help='Sample name (overrides Sample column in QC stats)')

    args = parser.parse_args()

    generator = CRISPRReportGeneratorEN(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        project_name=args.name,
        project_id=args.project_id,
        protocol_number=args.protocol,
        sample_name=args.sample
    )

    print("=" * 60)
    print("CRISPR Library Sequencing Data Report Generator (English)")
    print("=" * 60)

    generator.scan_files()
    generator.copy_resources()
    output_file = generator.generate_report()

    print("\n" + "=" * 60)
    print("Report generation complete!")
    print(f"Output file: {output_file}")
    print("=" * 60)


if __name__ == '__main__':
    main()
