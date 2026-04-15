
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
    if (!dashboardPage || typeof Chart === 'undefined') {
        return;
    }

    const ramCtx = document.getElementById('ramChart');
    if (ramCtx) {
        const totalRAM = 16;
        const ramUsagePercent = Math.floor(Math.random() * 100);
        const ramUsedGB = Math.round((ramUsagePercent / 100) * totalRAM * 10) / 10;
        const ramAvailable = 100 - ramUsagePercent;
        
        const ramDisplay = document.getElementById('ramUsageDisplay');
        if (ramDisplay) {
            ramDisplay.textContent = `${ramUsedGB} GB / ${totalRAM} GB`;
        }
        
        new Chart(ramCtx, {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Available'],
                datasets: [{
                    data: [ramUsagePercent, ramAvailable],
                    backgroundColor: ['#3498db', '#ecf0f1'],
                    borderColor: ['#2980b9', '#bdc3c7'],
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
        
        const chartBox = ramCtx.closest('.chart-box');
        if (chartBox) {
            let legendContainer = chartBox.querySelector('.custom-legend');
            if (!legendContainer) {
                legendContainer = document.createElement('div');
                legendContainer.className = 'custom-legend';
                chartBox.appendChild(legendContainer);
            }
            legendContainer.innerHTML = `
                <div class="legend-item"><span style="display:inline-block;width:12px;height:12px;background:#3498db;border-radius:2px;margin-right:6px;"></span>Used (${ramUsagePercent}%)</div>
                <div class="legend-item"><span style="display:inline-block;width:12px;height:12px;background:#ecf0f1;border-radius:2px;margin-right:6px;"></span>Available (${ramAvailable}%)</div>
            `;
        }
    }

    const cpuCtx = document.getElementById('cpuChart');
    if (cpuCtx) {
        const totalCPU = 4;
        const cpuUsagePercent = Math.floor(Math.random() * 100);
        const cpuUsedGHz = Math.round((cpuUsagePercent / 100) * totalCPU * 10) / 10;
        const cpuAvailable = 100 - cpuUsagePercent;
        
        const cpuDisplay = document.getElementById('cpuUsageDisplay');
        if (cpuDisplay) {
            cpuDisplay.textContent = `${cpuUsedGHz} GHz / ${totalCPU} GHz`;
        }
        
        new Chart(cpuCtx, {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Available'],
                datasets: [{
                    data: [cpuUsagePercent, cpuAvailable],
                    backgroundColor: ['#e74c3c', '#ecf0f1'],
                    borderColor: ['#c0392b', '#bdc3c7'],
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
        
        const chartBox = cpuCtx.closest('.chart-box');
        if (chartBox) {
            let legendContainer = chartBox.querySelector('.custom-legend');
            if (!legendContainer) {
                legendContainer = document.createElement('div');
                legendContainer.className = 'custom-legend';
                chartBox.appendChild(legendContainer);
            }
            legendContainer.innerHTML = `
                <div class="legend-item"><span style="display:inline-block;width:12px;height:12px;background:#e74c3c;border-radius:2px;margin-right:6px;"></span>Used (${cpuUsagePercent}%)</div>
                <div class="legend-item"><span style="display:inline-block;width:12px;height:12px;background:#ecf0f1;border-radius:2px;margin-right:6px;"></span>Available (${cpuAvailable}%)</div>
            `;
        }
    }
}
