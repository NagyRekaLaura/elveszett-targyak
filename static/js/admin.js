
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
            console.log('Filter changed:', this.value);
        });
    });

    resetButtons.forEach(btn => {
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
            console.log('Searching for:', this.value);
        });
    });

    const searchButtons = document.querySelectorAll('.search-bar button');
    searchButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const input = this.previousElementSibling;
            if (input && input.value) {
                console.log('Search submitted:', input.value);
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
