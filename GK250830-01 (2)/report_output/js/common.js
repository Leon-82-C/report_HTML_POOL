// 切换图片分组
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
    var pagination = document.getElementById(tableId + '_pagination');
    if (!pagination) return;
    var infoSpan = pagination.querySelector('.pagination-info');
    if (infoSpan) {
        var totalRows = window.tableFilteredData[tableId] ? window.tableFilteredData[tableId].length : (window.tableData[tableId] ? window.tableData[tableId].length : 0);
        if (window.tableFilteredData[tableId]) { infoSpan.textContent = `共 ${totalRows} 行，筛选出 ${visibleCount} 行`; }
        else { infoSpan.textContent = `共 ${totalRows} 行，显示 ${visibleCount} 行`; }
    }
}

function goToPage(tableId, pageNum) {
    var data = window.tableData[tableId];
    if (!data) return;
    var filteredData = window.tableFilteredData[tableId];
    var displayData = filteredData || data;
    var maxRows = window.tableMaxRows[tableId] || 10;
    var totalPages = Math.ceil(displayData.length / maxRows);
    if (pageNum > totalPages) { pageNum = totalPages; }
    if (pageNum < 1) { pageNum = 1; }
    var tbody = document.getElementById(tableId + '_body');
    if (!tbody) return;
    var start = (pageNum - 1) * maxRows;
    var end = Math.min(start + maxRows, displayData.length);
    tbody.innerHTML = displayData.slice(start, end).join('');
    window.tablePage[tableId] = pageNum;
    var currentSpan = document.getElementById(tableId + '_current');
    if (currentSpan) { currentSpan.textContent = pageNum; }
    var pageInfo = document.querySelector('#' + tableId + '_pagination .page-info');
    if (pageInfo) { pageInfo.innerHTML = '<span id="' + tableId + '_current">' + pageNum + '</span> / ' + totalPages; }
    updatePaginationButtons(tableId, totalPages);
    if (event) { event.preventDefault(); event.stopPropagation(); }
}

function prevPage(tableId) { var current = window.tablePage[tableId] || 1; goToPage(tableId, current - 1); }
function nextPage(tableId) { var current = window.tablePage[tableId] || 1; goToPage(tableId, current + 1); }

function updatePaginationButtons(tableId, totalPages) {
    var current = window.tablePage[tableId] || 1;
    var pagination = document.getElementById(tableId + '_pagination');
    if (!pagination) return;
    var buttons = pagination.querySelectorAll('.pagination-controls .btn');
    if (buttons.length >= 4) {
        buttons[0].disabled = (current === 1);
        buttons[1].disabled = (current === 1);
        buttons[2].disabled = (current === totalPages);
        buttons[3].disabled = (current === totalPages);
    }
    var infoSpan = pagination.querySelector('.pagination-info');
    if (infoSpan) {
        var filteredData = window.tableFilteredData[tableId];
        var data = window.tableData[tableId];
        var totalRows = filteredData ? filteredData.length : (data ? data.length : 0);
        var maxRows = window.tableMaxRows[tableId] || 10;
        var start = (current - 1) * maxRows + 1;
        var end = Math.min(current * maxRows, totalRows);
        if (filteredData) { infoSpan.textContent = `共 ${totalRows} 行，筛选出 ${filteredData.length} 行，显示 ${start}-${Math.min(end, filteredData.length)} 行`; }
        else { infoSpan.textContent = `共 ${totalRows} 行，显示 ${start}-${end} 行`; }
    }
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
        '<select class="field-select" onchange="updateOperatorOptions(\'' + tableId + '\', \'' + conditionId + '\')">' + fieldOptions + '</select>' +
        '<select class="operator-select"><option value=">">></option><option value=">=">>=</option><option value="<"><</option><option value="<="><=</option><option value="=">=</option></select>' +
        '<input type="text" class="value-input" placeholder="数值">' +
        '<button class="remove-condition" onclick="removeFilterCondition(\'' + tableId + '\', \'' + conditionId + '\')">&times;</button></div>';
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
        operatorSelect.innerHTML = '<option value=">">></option><option value=">=">>=</option><option value="<"><</option><option value="<="><=</option><option value="=">=</option>';
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
