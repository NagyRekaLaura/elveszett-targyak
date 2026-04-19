
function switchAdminPage(event, page) {
    event.preventDefault();
    
    document.querySelectorAll('.admin-page').forEach(el => {
        el.classList.remove('active');
    });
    
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('active');
    });
    
    const pageEl = document.getElementById(page + '-page');
    if (pageEl) {
        pageEl.classList.add('active');
    }
    
    event.target.closest('.nav-item').classList.add('active');
    
    // Load data when switching to a page
    if (page === 'users') {
        loadUsersData();
    } else if (page === 'posts') {
        loadPostsData();
    } else if (page === 'reports') {
        loadReportsData();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initializeCheckboxes();
    initializeFilters();
    initializeTableRows();
    initializeButtons();
    initializeSearch();
    initializeDashboardCharts();
});

function initializeCheckboxes() {
    const masterCheckboxes = document.querySelectorAll('thead input[type="checkbox"]');
    
    masterCheckboxes.forEach(masterCheckbox => {
        masterCheckbox.addEventListener('change', function() {
            const tableBody = this.closest('table').querySelector('tbody');
            const rowCheckboxes = tableBody.querySelectorAll('input[type="checkbox"]');
            rowCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateSelectedCount();
        });
    });

    const allRowCheckboxes = document.querySelectorAll('tbody input[type="checkbox"]');
    allRowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectedCount();
            updateMasterCheckbox();
        });
    });

    function updateSelectedCount() {
        const countElements = document.querySelectorAll('#selected-count');
        countElements.forEach(el => {
            const checkedCount = el.parentElement.parentElement.querySelector('tbody') 
                ? el.parentElement.parentElement.querySelector('tbody').querySelectorAll('input[type="checkbox"]:checked').length
                : 0;
            el.textContent = checkedCount;
        });
    }

    function updateMasterCheckbox() {
        masterCheckboxes.forEach(masterCheckbox => {
            const tableBody = masterCheckbox.closest('table').querySelector('tbody');
            const rowCheckboxes = tableBody.querySelectorAll('input[type="checkbox"]');
            const allChecked = rowCheckboxes.length === 
                              Array.from(rowCheckboxes).filter(cb => cb.checked).length;
            masterCheckbox.checked = allChecked;
        });
    }
}

function initializeFilters() {
    const filterSelects = document.querySelectorAll('.filter-group select, .filter-group input');
    const resetButtons = document.querySelectorAll('.btn-secondary');

    filterSelects.forEach(filter => {
        filter.addEventListener('change', function() {
            const pageId = this.closest('.admin-page').id;
            if (pageId === 'users-page') loadUsersData();
            else if (pageId === 'posts-page') loadPostsData();
            else if (pageId === 'reports-page') loadReportsData();
        });
    });

    resetButtons.forEach(btn => {
        if (btn.innerHTML.includes('Apply') || btn.innerHTML.includes('Check')) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const pageId = this.closest('.admin-page').id;
                if (pageId === 'users-page') loadUsersData();
                else if (pageId === 'posts-page') loadPostsData();
                else if (pageId === 'reports-page') loadReportsData();
            });
        }
        if (btn.innerHTML.includes('Reset')) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const filterBar = this.closest('.filter-bar');
                if (filterBar) {
                    const selects = filterBar.querySelectorAll('select');
                    const inputs = filterBar.querySelectorAll('input');
                    selects.forEach(select => select.selectedIndex = 0);
                    inputs.forEach(input => input.value = '');
                    console.log('Filters reset');
                }
            });
        }
    });
}

function initializeTableRows() {
}

function initializeButtons() {
    const actionBtns = document.querySelectorAll('.action-btn, .btn-icon, .bulk-buttons button');
    
    actionBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!this.getAttribute('href') && this.tagName !== 'A') {
                e.preventDefault();
                const actionText = this.textContent.trim() || this.title;
                if (actionText) {
                    console.log('Action clicked: ' + actionText);
                }
            }
        });
    });
}

function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-bar input');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const pageId = this.closest('.admin-page').id;
            if (pageId === 'users-page') loadUsersData();
            else if (pageId === 'posts-page') loadPostsData();
            else if (pageId === 'reports-page') loadReportsData();
        });
    });

    const searchButtons = document.querySelectorAll('.search-bar button');
    searchButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const input = this.previousElementSibling;
            if (input && input.value) {
                const pageId = this.closest('.admin-page').id;
                if (pageId === 'users-page') loadUsersData();
                else if (pageId === 'posts-page') loadPostsData();
                else if (pageId === 'reports-page') loadReportsData();
            }
        });
    });
}

function initializeDashboardCharts() {
    const dashboardPage = document.getElementById('dashboard-page');
    if (!dashboardPage) {
        return;
    }

    const ramCtx = document.getElementById('ramChart');
    const cpuCtx = document.getElementById('cpuChart');
    const canRenderCharts = typeof Chart !== 'undefined' && ramCtx && cpuCtx;

    function createDoughnutChart(ctx, backgroundColor, borderColor) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Available'],
                datasets: [{
                    data: [0, 100],
                    backgroundColor: backgroundColor,
                    borderColor: borderColor,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    function updateLegend(chartCanvas, usedColor, availableColor, usedPercent, availablePercent) {
        const chartBox = chartCanvas.closest('.chart-box');
        if (!chartBox) {
            return;
        }

        let legendContainer = chartBox.querySelector('.custom-legend');
        if (!legendContainer) {
            legendContainer = document.createElement('div');
            legendContainer.className = 'custom-legend';
            chartBox.appendChild(legendContainer);
        }

        legendContainer.innerHTML = `
            <div class="legend-item"><span style="display:inline-block;width:12px;height:12px;background:${usedColor};border-radius:2px;margin-right:6px;"></span>Used (${usedPercent.toFixed(1)}%)</div>
            <div class="legend-item"><span style="display:inline-block;width:12px;height:12px;background:${availableColor};border-radius:2px;margin-right:6px;"></span>Available (${availablePercent.toFixed(1)}%)</div>
        `;
    }

    function clampPercent(value) {
        return Math.max(0, Math.min(100, Number(value) || 0));
    }

    function updateDoughnutChart(chart, usedPercent) {
        const safeUsed = clampPercent(usedPercent);
        const safeAvailable = 100 - safeUsed;
        chart.data.datasets[0].data = [safeUsed, safeAvailable];
        chart.update();
        return { safeUsed, safeAvailable };
    }

    const ramChart = canRenderCharts
        ? createDoughnutChart(ramCtx, ['#3498db', '#ecf0f1'], ['#2980b9', '#bdc3c7'])
        : null;
    const cpuChart = canRenderCharts
        ? createDoughnutChart(cpuCtx, ['#e74c3c', '#ecf0f1'], ['#c0392b', '#bdc3c7'])
        : null;

    const ramDisplay = document.getElementById('ramUsageDisplay');
    const cpuDisplay = document.getElementById('cpuUsageDisplay');
    const totalUsersDisplay = document.getElementById('totalUsersDisplay');
    const totalPostsDisplay = document.getElementById('totalPostsDisplay');
    const pendingReportsDisplay = document.getElementById('pendingReportsDisplay');

    function formatWholeNumber(value) {
        return Number(value || 0).toLocaleString();
    }

    async function refreshDashboardMetrics() {
        try {
            const response = await fetch('/admin/metrics', {
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Request failed with status ${response.status}`);
            }

            const metrics = await response.json();

            if (ramChart && ramCtx) {
                const ramStats = updateDoughnutChart(ramChart, metrics?.ram?.percent_used);
                updateLegend(ramCtx, '#3498db', '#ecf0f1', ramStats.safeUsed, ramStats.safeAvailable);
            }
            if (ramDisplay) {
                const ramUsed = Number(metrics?.ram?.used_gb || 0).toFixed(2);
                const ramTotal = Number(metrics?.ram?.total_gb || 0).toFixed(2);
                ramDisplay.textContent = `${ramUsed} GB / ${ramTotal} GB`;
            }

            const cpuUsagePercent = clampPercent(metrics?.cpu?.usage_percent);
            if (cpuChart && cpuCtx) {
                const cpuStats = updateDoughnutChart(cpuChart, cpuUsagePercent);
                updateLegend(cpuCtx, '#e74c3c', '#ecf0f1', cpuStats.safeUsed, cpuStats.safeAvailable);
            }
            if (cpuDisplay) {
                const usagePercent = cpuUsagePercent.toFixed(1);
                const currentGHz = metrics?.cpu?.current_frequency_ghz;
                const maxGHz = metrics?.cpu?.max_frequency_ghz;
                const logicalCores = metrics?.cpu?.logical_cores || 0;

                if (typeof currentGHz === 'number' && typeof maxGHz === 'number') {
                    cpuDisplay.textContent = `${usagePercent}% (${currentGHz.toFixed(2)} GHz / ${maxGHz.toFixed(2)} GHz)`;
                } else if (typeof currentGHz === 'number') {
                    cpuDisplay.textContent = `${usagePercent}% (${currentGHz.toFixed(2)} GHz, ${logicalCores} cores)`;
                } else {
                    cpuDisplay.textContent = `${usagePercent}% (${logicalCores} cores)`;
                }
            }

            if (totalUsersDisplay) {
                totalUsersDisplay.textContent = formatWholeNumber(metrics?.stats?.total_users);
            }
            if (totalPostsDisplay) {
                totalPostsDisplay.textContent = formatWholeNumber(metrics?.stats?.total_posts);
            }
            if (pendingReportsDisplay) {
                pendingReportsDisplay.textContent = formatWholeNumber(metrics?.stats?.pending_reports);
            }
        } catch (error) {
            console.error('Failed to load dashboard metrics:', error);
        }
    }

    refreshDashboardMetrics();
    setInterval(refreshDashboardMetrics, 5000);
}

// ============== USERS DATA LOADING ==============
async function loadUsersData(page = 1) {
    try {
        const role = document.querySelector('[data-page="users"] ~ .filter-bar select[value]')?.value || 'all';
        const search = document.querySelector('#users-page .search-bar input')?.value || '';
        
        const url = `/admin/api/users?page=${page}&role=${role}&search=${search}`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error('Failed to load users');
        
        const data = await response.json();
        populateUsersTable(data.users);
        updatePagination('users-page', data.pages, page);
    } catch (error) {
        console.error('Error loading users:', error);
        showToast('Failed to load users', 'error');
    }
}

function populateUsersTable(users) {
    const tbody = document.querySelector('#users-page tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="checkbox"></td>
            <td><strong>${escapeHtml(user.name)}</strong><br><small>@${escapeHtml(user.username)}</small></td>
            <td>${escapeHtml(user.email)}</td>
            <td><span class="status-badge active">Active</span></td>
            <td><span class="badge" style="background: ${user.role === 'admin' ? '#e74c3c' : '#3498db'}">${user.role}</span></td>
            <td>${user.posts}</td>
            <td>${user.joined}</td>
            <td class="action-cell">
                <button class="btn-icon" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="btn-icon" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ============== POSTS DATA LOADING ==============
async function loadPostsData(page = 1) {
    try {
        const status = document.querySelector('#posts-page .filter-group select')?.value || 'all';
        const search = document.querySelector('#posts-page .search-bar input')?.value || '';
        
        const url = `/admin/api/posts?page=${page}&status=${status}&search=${search}`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error('Failed to load posts');
        
        const data = await response.json();
        populatePostsTable(data.posts);
        updatePagination('posts-page', data.pages, page);
    } catch (error) {
        console.error('Error loading posts:', error);
        showToast('Failed to load posts', 'error');
    }
}

function populatePostsTable(posts) {
    const tbody = document.querySelector('#posts-page tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    posts.forEach(post => {
        const row = document.createElement('tr');
        row.className = post.has_reports ? 'reported' : '';
        row.innerHTML = `
            <td><input type="checkbox"></td>
            <td><strong>${escapeHtml(post.name)}</strong></td>
            <td>${escapeHtml(post.uploader)}</td>
            <td>${post.type}</td>
            <td><span class="status-badge ${post.status.toLowerCase()}">${post.status}</span></td>
            <td>${post.category}</td>
            <td>${post.reports > 0 ? `<span style="color: #e74c3c; font-weight: bold;">${post.reports}</span>` : '0'}</td>
            <td>${post.posted}</td>
            <td class="action-cell">
                <button class="btn-icon" title="View"><i class="fas fa-eye"></i></button>
                <button class="btn-icon" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ============== REPORTS DATA LOADING ==============
async function loadReportsData(page = 1) {
    try {
        const status = document.querySelector('#reports-page .filter-group select')?.value || 'all';
        const search = document.querySelector('#reports-page .search-bar input')?.value || '';
        
        const url = `/admin/api/reports?page=${page}&status=${status}&search=${search}`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error('Failed to load reports');
        
        const data = await response.json();
        populateReportsTable(data.reports);
        updatePagination('reports-page', data.pages, page);
    } catch (error) {
        console.error('Error loading reports:', error);
        showToast('Failed to load reports', 'error');
    }
}

function populateReportsTable(reports) {
    const tbody = document.querySelector('#reports-page tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    reports.forEach(report => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="checkbox"></td>
            <td>${report.id}</td>
            <td>${escapeHtml(report.type)}</td>
            <td>${escapeHtml(report.reporter)}</td>
            <td>${escapeHtml(report.reason)}</td>
            <td><span class="status-badge ${report.status.toLowerCase()}">${report.status}</span></td>
            <td>${report.created}</td>
            <td class="action-cell">
                <button class="btn-icon" title="Review"><i class="fas fa-eye"></i></button>
                <button class="btn-icon" title="Resolve"><i class="fas fa-check"></i></button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ============== HELPER FUNCTIONS ==============
function updatePagination(pageId, totalPages, currentPage) {
    const pagination = document.querySelector(`#${pageId} .pagination`);
    if (!pagination) return;
    
    // Határozd meg az oldal típusát
    let loadFunction;
    if (pageId === 'users-page') {
        loadFunction = loadUsersData;
    } else if (pageId === 'posts-page') {
        loadFunction = loadPostsData;
    } else if (pageId === 'reports-page') {
        loadFunction = loadReportsData;
    }
    
    // Töröld az összes oldal gombot és a page-info-t (de tartsd meg a Previous és Next gombokat)
    const allButtons = pagination.querySelectorAll('.page-btn');
    const pageInfo = pagination.querySelector('.page-info');
    
    // Tárolj Previous és Next gombokat
    const prevBtn = allButtons[0];
    const nextBtn = allButtons[allButtons.length - 1];
    
    // Távolítsd el az összes köztes gombot (1, 2, 3...)
    for (let i = 1; i < allButtons.length - 1; i++) {
        allButtons[i].remove();
    }
    
    // Távolítsd el a page-info-t
    if (pageInfo) pageInfo.remove();
    
    // Módosítsd a Previous gombot
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = (e) => {
        e.preventDefault();
        if (currentPage > 1 && loadFunction) loadFunction(currentPage - 1);
    };
    
    // Módosítsd a Next gombot
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = (e) => {
        e.preventDefault();
        if (currentPage < totalPages && loadFunction) loadFunction(currentPage + 1);
    };
    
    // Generálj oldal gombokat 1-től totalPages-ig
    for (let i = 1; i <= totalPages; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = 'page-btn';
        if (i === currentPage) pageBtn.classList.add('active');
        pageBtn.textContent = i;
        pageBtn.onclick = (e) => {
            e.preventDefault();
            if (loadFunction) loadFunction(i);
        };
        
        // Szúrd be az új gombot a Next gomb előtt
        pagination.insertBefore(pageBtn, nextBtn);
    }
    
    // Generálj és szúrd be az oldal info szöveget a Next gomb előtt
    const newPageInfo = document.createElement('span');
    newPageInfo.className = 'page-info';
    newPageInfo.textContent = `... Page ${currentPage} of ${totalPages}`;
    pagination.insertBefore(newPageInfo, nextBtn);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}