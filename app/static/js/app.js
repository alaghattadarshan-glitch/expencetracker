/**
 * Personal Expense Tracker - Frontend Controller
 * Pure Vanilla JavaScript (ES6+) interacting with Flask REST Endpoints
 */

// Category Constants
const EXPENSE_CATEGORIES = [
    'Food', 'Transport', 'Shopping', 'Bills', 'Education',
    'Health', 'Entertainment', 'Rent', 'Travel', 'Other'
];

const INCOME_CATEGORIES = [
    'Salary', 'Freelance', 'Business', 'Allowance', 'Initial Balance', 'Other'
];

// Application State
const state = {
    currentPage: 'dashboard',
    currency: '₹',
    userDisplayName: 'User',
    transactions: [],
    pagination: {
        page: 1,
        limit: 10,
        total: 0,
        totalPages: 1
    },
    filters: {
        search: '',
        type: '',
        category: '',
        startDate: '',
        endDate: '',
        sort: 'date_desc'
    },
    budgets: [],
    analytics: null,
    charts: {} // Stores Chart.js instances to destroy/recreate cleanly
};

// ==========================================================================
// Initialization
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initSettings();
    initTransactionForm();
    initBudgetForm();
    initFilters();
    initModals();
    setCurrentDate();

    // Initial Data Fetch
    loadSettings();
    loadDashboard();
});

function setCurrentDate() {
    const dateDisplay = document.getElementById('currentDateDisplay');
    if (dateDisplay) {
        const now = new Date();
        const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
        dateDisplay.textContent = now.toLocaleDateString('en-IN', options);
    }
    
    // Set default transaction date to today
    const dateInput = document.getElementById('transactionDate');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }
    
    // Set default month/year for budget
    const budgetMonth = document.getElementById('budgetMonth');
    const budgetYear = document.getElementById('budgetYear');
    if (budgetMonth && budgetYear) {
        const now = new Date();
        budgetMonth.value = now.getMonth() + 1;
        budgetYear.value = now.getFullYear();
    }
}

// ==========================================================================
// Navigation & Routing
// ==========================================================================

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.page-section');
    const pageTitle = document.getElementById('pageTitle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOpenBtn = document.getElementById('sidebarOpenBtn');
    const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
    const quickAddBtn = document.getElementById('quickAddBtn');

    function switchPage(targetPage) {
        state.currentPage = targetPage;
        
        navItems.forEach(item => {
            if (item.dataset.page === targetPage) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        sections.forEach(sec => {
            if (sec.id === `section-${targetPage}`) {
                sec.classList.add('active');
            } else {
                sec.classList.remove('active');
            }
        });

        // Set topbar title
        const titles = {
            dashboard: 'Dashboard',
            transactions: 'Transactions',
            'add-transaction': 'Add Transaction',
            budget: 'Monthly Budget',
            analytics: 'Financial Analytics',
            settings: 'Settings'
        };
        if (pageTitle) pageTitle.textContent = titles[targetPage] || 'Dashboard';

        // Close sidebar on mobile after clicking
        if (sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }

        // Trigger page-specific data loads
        if (targetPage === 'dashboard') loadDashboard();
        if (targetPage === 'transactions') loadTransactions();
        if (targetPage === 'budget') loadBudgets();
        if (targetPage === 'analytics') loadAnalytics();
        if (targetPage === 'settings') loadSettings();
        if (targetPage === 'add-transaction') resetTransactionForm();
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            window.location.hash = page;
            switchPage(page);
        });
    });

    if (quickAddBtn) {
        quickAddBtn.addEventListener('click', () => {
            window.location.hash = 'add-transaction';
            switchPage('add-transaction');
        });
    }

    // Hash change handler for direct links and browser back/forward
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.replace('#', '') || 'dashboard';
        switchPage(hash);
    });

    if (sidebarOpenBtn && sidebar) {
        sidebarOpenBtn.addEventListener('click', () => sidebar.classList.add('open'));
    }
    if (sidebarCloseBtn && sidebar) {
        sidebarCloseBtn.addEventListener('click', () => sidebar.classList.remove('open'));
    }

    // Default to hash or dashboard
    const initialHash = window.location.hash.replace('#', '') || 'dashboard';
    switchPage(initialHash);
}

// ==========================================================================
// Formatting Helpers (Realistic Indian & Currency formatting)
// ==========================================================================

function formatCurrency(amount) {
    const num = Number(amount) || 0;
    const isNegative = num < 0;
    const absNum = Math.abs(num);
    const formatted = absNum.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    return isNegative ? `-${state.currency}${formatted}` : `${state.currency}${formatted}`;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ==========================================================================
// Notification Toast System
// ==========================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ==========================================================================
// Confirmation Modal System
// ==========================================================================

let confirmCallback = null;

function showConfirmModal(title, message, onConfirm) {
    const modal = document.getElementById('confirmModal');
    const modalTitle = document.getElementById('confirmModalTitle');
    const modalMessage = document.getElementById('confirmModalMessage');
    
    if (modalTitle) modalTitle.textContent = title;
    if (modalMessage) modalMessage.textContent = message;
    confirmCallback = onConfirm;
    
    if (modal) modal.classList.add('active');
}

function initModals() {
    const modal = document.getElementById('confirmModal');
    const cancelBtn = document.getElementById('confirmModalCancel');
    const closeBtn = document.getElementById('confirmModalClose');
    const confirmBtn = document.getElementById('confirmModalConfirm');

    function closeModal() {
        if (modal) modal.classList.remove('active');
        confirmCallback = null;
    }

    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
            if (typeof confirmCallback === 'function') {
                confirmCallback();
            }
            closeModal();
        });
    }
}

// ==========================================================================
// API Interaction: Dashboard
// ==========================================================================

async function loadDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        if (!response.ok) throw new Error('Failed to load dashboard data');
        const data = await response.json();

        // 1. Update Summary Cards
        const balanceEl = document.getElementById('cardTotalBalance');
        if (balanceEl) {
            balanceEl.textContent = formatCurrency(data.summary.total_balance);
            if (data.summary.total_balance < 0) {
                balanceEl.classList.add('text-expense');
                balanceEl.classList.remove('text-income');
            } else if (data.summary.total_balance > 0) {
                balanceEl.classList.add('text-income');
                balanceEl.classList.remove('text-expense');
            } else {
                balanceEl.classList.remove('text-expense', 'text-income');
            }
        }
        document.getElementById('cardTotalIncome').textContent = formatCurrency(data.summary.monthly_income);
        document.getElementById('cardTotalExpense').textContent = formatCurrency(data.summary.monthly_expense);
        document.getElementById('cardRemainingBudget').textContent = formatCurrency(data.summary.remaining_budget);

        // Savings Rate Badge
        const savingsBadge = document.getElementById('savingsRateBadge');
        if (savingsBadge) {
            savingsBadge.textContent = `${data.summary.savings_rate}% savings rate`;
        }

        // Budget Bar
        const budgetBar = document.getElementById('cardBudgetBar');
        const budgetPercent = document.getElementById('cardBudgetPercentage');
        if (budgetBar && budgetPercent) {
            const pct = Math.min(Math.max(data.summary.budget_used_percentage, 0), 100);
            budgetBar.style.width = `${pct}%`;
            budgetPercent.textContent = `${data.summary.budget_used_percentage}% used`;
            
            budgetBar.className = 'progress-bar-fill';
            if (data.summary.budget_used_percentage >= 100) {
                budgetBar.classList.add('danger');
            } else if (data.summary.budget_used_percentage >= 80) {
                budgetBar.classList.add('warning');
            }
        }

        // 2. Render Recent Transactions Table
        renderRecentTransactions(data.recent_transactions);

        // 3. Render Dashboard Charts
        renderIncomeExpenseChart(data.monthly_trends);
        renderCategoryDoughnut(data.category_spending);

        // 4. Render Budget Health Widget
        renderDashboardBudgetHealth(data.budget_health);

    } catch (err) {
        console.error('Error fetching dashboard:', err);
        showToast('Error loading dashboard data. Check backend/database connection.', 'error');
    }
}

function renderRecentTransactions(transactions) {
    const tbody = document.getElementById('recentTransactionsBody');
    if (!tbody) return;

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">No recent transactions recorded.</td></tr>`;
        return;
    }

    tbody.innerHTML = transactions.map(tx => {
        const isIncome = tx.type === 'Income';
        const amountClass = isIncome ? 'text-income' : 'text-expense';
        const prefix = isIncome ? '+' : '-';
        return `
            <tr>
                <td><strong>${escapeHtml(tx.title)}</strong></td>
                <td><span class="type-pill ${isIncome ? 'income' : 'expense'}">${escapeHtml(tx.category)}</span></td>
                <td class="text-muted">${formatDate(tx.transaction_date)}</td>
                <td class="text-right ${amountClass}"><strong>${prefix}${formatCurrency(tx.amount)}</strong></td>
            </tr>
        `;
    }).join('');
}

function renderDashboardBudgetHealth(budgets) {
    const container = document.getElementById('dashboardBudgetList');
    if (!container) return;

    if (!budgets || budgets.length === 0) {
        container.innerHTML = `<div class="text-center text-muted py-4">No monthly budgets configured. <a href="#budget">Set a budget</a></div>`;
        return;
    }

    container.innerHTML = budgets.map(b => {
        const pct = Math.min(Math.max(b.used_percentage, 0), 100);
        let colorClass = 'normal';
        let barClass = '';
        if (b.used_percentage >= 100) {
            colorClass = 'danger';
            barClass = 'danger';
        } else if (b.used_percentage >= 80) {
            colorClass = 'warning';
            barClass = 'warning';
        }

        return `
            <div class="mb-3">
                <div class="flex-between text-sm mb-1">
                    <span class="font-semibold">${escapeHtml(b.category)}</span>
                    <span class="text-muted">${formatCurrency(b.spent)} / ${formatCurrency(b.monthly_limit)} (${b.used_percentage}%)</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill ${barClass}" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

// Charts Management
function renderIncomeExpenseChart(trends) {
    const canvas = document.getElementById('chartIncomeVsExpense');
    if (!canvas) return;

    if (state.charts.incomeExpense) {
        state.charts.incomeExpense.destroy();
    }

    const labels = trends.map(t => t.month_label);
    const incomeData = trends.map(t => t.income);
    const expenseData = trends.map(t => t.expense);

    state.charts.incomeExpense = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    backgroundColor: '#1b7a4d',
                    borderRadius: 2
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    backgroundColor: '#c0362c',
                    borderRadius: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { family: 'Inter', size: 12 } } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f0f2f4' },
                    ticks: {
                        callback: (val) => state.currency + Number(val).toLocaleString('en-IN')
                    }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderCategoryDoughnut(categories) {
    const canvas = document.getElementById('chartCategoryDoughnut');
    if (!canvas) return;

    if (state.charts.categoryDoughnut) {
        state.charts.categoryDoughnut.destroy();
    }

    if (!categories || categories.length === 0) {
        // Fallback display if no expense yet
        categories = [{ category: 'No Expenses', total: 1 }];
    }

    const labels = categories.map(c => c.category);
    const data = categories.map(c => c.total);

    const colors = [
        '#22262c', '#636d77', '#1b7a4d', '#c0362c', '#b45309',
        '#475569', '#334155', '#64748b', '#94a3b8', '#0f172a'
    ];

    state.charts.categoryDoughnut = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.label}: ${formatCurrency(ctx.raw)}`
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// ==========================================================================
// API Interaction: Transactions CRUD & Filtering
// ==========================================================================

function initFilters() {
    const filterSearch = document.getElementById('filterSearch');
    const filterType = document.getElementById('filterType');
    const filterCategory = document.getElementById('filterCategory');
    const filterStartDate = document.getElementById('filterStartDate');
    const filterEndDate = document.getElementById('filterEndDate');
    const filterSort = document.getElementById('filterSort');
    const resetBtn = document.getElementById('resetFiltersBtn');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    // Populate category dropdown
    populateCategoryDropdown(filterCategory, [...EXPENSE_CATEGORIES, ...INCOME_CATEGORIES]);

    const debounce = (fn, delay = 300) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => fn(...args), delay);
        };
    };

    filterSearch.addEventListener('input', debounce(() => {
        state.filters.search = filterSearch.value.trim();
        state.pagination.page = 1;
        loadTransactions();
    }));

    filterType.addEventListener('change', () => {
        state.filters.type = filterType.value;
        state.pagination.page = 1;
        loadTransactions();
    });

    filterCategory.addEventListener('change', () => {
        state.filters.category = filterCategory.value;
        state.pagination.page = 1;
        loadTransactions();
    });

    filterStartDate.addEventListener('change', () => {
        state.filters.startDate = filterStartDate.value;
        state.pagination.page = 1;
        loadTransactions();
    });

    filterEndDate.addEventListener('change', () => {
        state.filters.endDate = filterEndDate.value;
        state.pagination.page = 1;
        loadTransactions();
    });

    filterSort.addEventListener('change', () => {
        state.filters.sort = filterSort.value;
        state.pagination.page = 1;
        loadTransactions();
    });

    resetBtn.addEventListener('click', () => {
        filterSearch.value = '';
        filterType.value = '';
        filterCategory.value = '';
        filterStartDate.value = '';
        filterEndDate.value = '';
        filterSort.value = 'date_desc';

        state.filters = {
            search: '',
            type: '',
            category: '',
            startDate: '',
            endDate: '',
            sort: 'date_desc'
        };
        state.pagination.page = 1;
        loadTransactions();
    });

    prevBtn.addEventListener('click', () => {
        if (state.pagination.page > 1) {
            state.pagination.page--;
            loadTransactions();
        }
    });

    nextBtn.addEventListener('click', () => {
        if (state.pagination.page < state.pagination.totalPages) {
            state.pagination.page++;
            loadTransactions();
        }
    });
}

async function loadTransactions() {
    try {
        const params = new URLSearchParams({
            page: state.pagination.page,
            limit: state.pagination.limit,
            search: state.filters.search,
            type: state.filters.type,
            category: state.filters.category,
            start_date: state.filters.startDate,
            end_date: state.filters.endDate,
            sort: state.filters.sort
        });

        const res = await fetch(`/api/transactions?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to load transactions');
        const data = await res.json();

        state.transactions = data.transactions;
        state.pagination = data.pagination;

        renderTransactionsTable();
        updatePaginationControls();
    } catch (err) {
        console.error('Error fetching transactions:', err);
        showToast('Error loading transactions', 'error');
    }
}

function renderTransactionsTable() {
    const tbody = document.getElementById('transactionsTableBody');
    if (!tbody) return;

    if (!state.transactions || state.transactions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No matching transactions found.</td></tr>`;
        return;
    }

    tbody.innerHTML = state.transactions.map(tx => {
        const isIncome = tx.type === 'Income';
        const amountClass = isIncome ? 'text-income' : 'text-expense';
        const prefix = isIncome ? '+' : '-';
        return `
            <tr>
                <td class="text-muted">${formatDate(tx.transaction_date)}</td>
                <td><strong>${escapeHtml(tx.title)}</strong></td>
                <td><span class="type-pill ${isIncome ? 'income' : 'expense'}">${tx.type}</span></td>
                <td>${escapeHtml(tx.category)}</td>
                <td class="text-muted text-sm">${escapeHtml(tx.description || '-')}</td>
                <td class="text-right ${amountClass}"><strong>${prefix}${formatCurrency(tx.amount)}</strong></td>
                <td class="text-center">
                    <button class="btn-icon edit-tx-btn" onclick="editTransaction(${tx.id})" title="Edit">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="btn-icon text-danger delete-tx-btn" onclick="promptDeleteTransaction(${tx.id}, '${escapeHtml(tx.title)}')" title="Delete">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function updatePaginationControls() {
    const info = document.getElementById('paginationInfo');
    const pageNum = document.getElementById('pageNumber');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (info) {
        const start = state.pagination.total === 0 ? 0 : (state.pagination.page - 1) * state.pagination.limit + 1;
        const end = Math.min(state.pagination.page * state.pagination.limit, state.pagination.total);
        info.textContent = `Showing ${start}-${end} of ${state.pagination.total} transactions`;
    }

    if (pageNum) pageNum.textContent = state.pagination.page;
    if (prevBtn) prevBtn.disabled = state.pagination.page <= 1;
    if (nextBtn) nextBtn.disabled = state.pagination.page >= state.pagination.totalPages;
}

// ==========================================================================
// Add / Edit Transaction Form Handling
// ==========================================================================

function initTransactionForm() {
    const form = document.getElementById('transactionForm');
    const toggleExpense = document.getElementById('toggleExpenseLabel');
    const toggleIncome = document.getElementById('toggleIncomeLabel');
    const categorySelect = document.getElementById('transactionCategory');
    const cancelBtn = document.getElementById('cancelTransactionBtn');

    // Default to Expense categories
    populateCategoryDropdown(categorySelect, EXPENSE_CATEGORIES);

    // Toggle Type
    if (toggleExpense && toggleIncome) {
        toggleExpense.addEventListener('click', () => {
            toggleExpense.classList.add('active');
            toggleIncome.classList.remove('active');
            toggleExpense.querySelector('input').checked = true;
            populateCategoryDropdown(categorySelect, EXPENSE_CATEGORIES);
        });

        toggleIncome.addEventListener('click', () => {
            toggleIncome.classList.add('active');
            toggleExpense.classList.remove('active');
            toggleIncome.querySelector('input').checked = true;
            populateCategoryDropdown(categorySelect, INCOME_CATEGORIES);
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            resetTransactionForm();
            window.location.hash = 'transactions';
        });
    }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!validateTransactionForm()) return;

            const editId = document.getElementById('editTransactionId').value;
            const payload = {
                title: document.getElementById('transactionTitle').value.trim(),
                type: form.querySelector('input[name="transactionType"]:checked').value,
                amount: parseFloat(document.getElementById('transactionAmount').value),
                category: categorySelect.value,
                transaction_date: document.getElementById('transactionDate').value,
                description: document.getElementById('transactionDescription').value.trim()
            };

            try {
                const url = editId ? `/api/transactions/${editId}` : '/api/transactions';
                const method = editId ? 'PUT' : 'POST';

                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to save transaction');

                showToast(editId ? 'Transaction updated successfully!' : 'Transaction created successfully!', 'success');
                resetTransactionForm();
                window.location.hash = 'transactions';
            } catch (err) {
                console.error('Error saving transaction:', err);
                showToast(err.message, 'error');
            }
        });
    }
}

function validateTransactionForm() {
    let isValid = true;
    const title = document.getElementById('transactionTitle');
    const amount = document.getElementById('transactionAmount');
    const category = document.getElementById('transactionCategory');
    const date = document.getElementById('transactionDate');

    const titleError = document.getElementById('titleError');
    const amountError = document.getElementById('amountError');
    const categoryError = document.getElementById('categoryError');
    const dateError = document.getElementById('dateError');

    // Reset errors
    titleError.textContent = '';
    amountError.textContent = '';
    categoryError.textContent = '';
    dateError.textContent = '';

    if (!title.value.trim()) {
        titleError.textContent = 'Transaction title is required.';
        isValid = false;
    }

    const amtVal = parseFloat(amount.value);
    if (isNaN(amtVal) || amtVal <= 0) {
        amountError.textContent = 'Please enter a valid amount greater than 0.';
        isValid = false;
    }

    if (!category.value) {
        categoryError.textContent = 'Category selection is required.';
        isValid = false;
    }

    if (!date.value) {
        dateError.textContent = 'Date is required.';
        isValid = false;
    }

    return isValid;
}

function resetTransactionForm() {
    const form = document.getElementById('transactionForm');
    if (!form) return;
    form.reset();
    document.getElementById('editTransactionId').value = '';
    document.getElementById('transactionFormTitle').textContent = 'Add New Transaction';
    document.getElementById('saveTransactionBtn').textContent = 'Save Transaction';
    
    // Reset toggle to Expense
    const toggleExpense = document.getElementById('toggleExpenseLabel');
    const toggleIncome = document.getElementById('toggleIncomeLabel');
    if (toggleExpense && toggleIncome) {
        toggleExpense.classList.add('active');
        toggleIncome.classList.remove('active');
        toggleExpense.querySelector('input').checked = true;
    }
    
    populateCategoryDropdown(document.getElementById('transactionCategory'), EXPENSE_CATEGORIES);
    document.getElementById('transactionDate').value = new Date().toISOString().split('T')[0];
}

async function editTransaction(id) {
    try {
        const res = await fetch(`/api/transactions/${id}`);
        if (!res.ok) throw new Error('Failed to fetch transaction details');
        const tx = await res.json();

        // Switch page
        window.location.hash = 'add-transaction';
        
        document.getElementById('editTransactionId').value = tx.id;
        document.getElementById('transactionFormTitle').textContent = 'Edit Transaction';
        document.getElementById('saveTransactionBtn').textContent = 'Update Transaction';
        
        document.getElementById('transactionTitle').value = tx.title;
        document.getElementById('transactionAmount').value = tx.amount;
        document.getElementById('transactionDate').value = tx.transaction_date;
        document.getElementById('transactionDescription').value = tx.description || '';

        const toggleExpense = document.getElementById('toggleExpenseLabel');
        const toggleIncome = document.getElementById('toggleIncomeLabel');
        const categorySelect = document.getElementById('transactionCategory');

        if (tx.type === 'Income') {
            toggleIncome.classList.add('active');
            toggleExpense.classList.remove('active');
            toggleIncome.querySelector('input').checked = true;
            populateCategoryDropdown(categorySelect, INCOME_CATEGORIES);
        } else {
            toggleExpense.classList.add('active');
            toggleIncome.classList.remove('active');
            toggleExpense.querySelector('input').checked = true;
            populateCategoryDropdown(categorySelect, EXPENSE_CATEGORIES);
        }
        categorySelect.value = tx.category;

    } catch (err) {
        showToast('Error opening transaction for edit', 'error');
    }
}

function promptDeleteTransaction(id, title) {
    showConfirmModal(
        'Delete Transaction',
        `Are you sure you want to permanently delete "${title}"? This cannot be undone.`,
        async () => {
            try {
                const res = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
                if (!res.ok) throw new Error('Failed to delete transaction');
                showToast('Transaction deleted successfully', 'success');
                loadTransactions();
                loadDashboard();
            } catch (err) {
                showToast('Error deleting transaction', 'error');
            }
        }
    );
}

// ==========================================================================
// API Interaction: Budgets
// ==========================================================================

function initBudgetForm() {
    const form = document.getElementById('budgetForm');
    const categorySelect = document.getElementById('budgetCategory');
    const monthSelect = document.getElementById('budgetMonth');
    const yearInput = document.getElementById('budgetYear');

    // Populate categories: Overall + Expense categories
    populateCategoryDropdown(categorySelect, ['Overall', ...EXPENSE_CATEGORIES]);

    monthSelect.addEventListener('change', loadBudgets);
    yearInput.addEventListener('change', loadBudgets);

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                category: categorySelect.value,
                monthly_limit: parseFloat(document.getElementById('budgetLimit').value),
                month: parseInt(monthSelect.value),
                year: parseInt(yearInput.value)
            };

            if (isNaN(payload.monthly_limit) || payload.monthly_limit <= 0) {
                showToast('Enter a valid monthly budget limit', 'warning');
                return;
            }

            try {
                const res = await fetch('/api/budgets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to save budget');

                showToast('Budget saved successfully!', 'success');
                document.getElementById('budgetLimit').value = '';
                loadBudgets();
                loadDashboard();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }
}

async function loadBudgets() {
    try {
        const month = document.getElementById('budgetMonth').value;
        const year = document.getElementById('budgetYear').value;

        const res = await fetch(`/api/budgets?month=${month}&year=${year}`);
        if (!res.ok) throw new Error('Failed to load budgets');
        const budgets = await res.json();

        state.budgets = budgets;
        renderBudgetCards(budgets);
    } catch (err) {
        console.error('Error fetching budgets:', err);
        showToast('Error loading budgets', 'error');
    }
}

function renderBudgetCards(budgets) {
    const container = document.getElementById('budgetCardsList');
    if (!container) return;

    if (!budgets || budgets.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                No budget limits set for this month yet. Use the form on the left to set overall and category limits.
            </div>
        `;
        return;
    }

    container.innerHTML = budgets.map(b => {
        const pct = Math.min(Math.max(b.used_percentage, 0), 100);
        let borderClass = 'normal-border';
        let barClass = '';
        let alertBadge = '';

        if (b.used_percentage >= 100) {
            borderClass = 'danger-border';
            barClass = 'danger';
            alertBadge = `<span class="badge" style="background:#fef2f2; color:#ef4444;">Budget Exceeded!</span>`;
        } else if (b.used_percentage >= 80) {
            borderClass = 'warning-border';
            barClass = 'warning';
            alertBadge = `<span class="badge" style="background:#fffbeb; color:#d97706;">Approaching Limit (&gt;80%)</span>`;
        } else {
            alertBadge = `<span class="badge" style="background:#ecfdf5; color:#10b981;">On Track</span>`;
        }

        return `
            <div class="budget-card-item ${borderClass}">
                <div class="flex-between mb-2">
                    <div>
                        <strong style="font-size: 1.05rem;">${escapeHtml(b.category)}</strong>
                        <div class="text-muted text-sm">Remaining: ${formatCurrency(b.remaining)}</div>
                    </div>
                    <div class="text-right">
                        ${alertBadge}
                        <div class="mt-1">
                            <button class="btn-icon text-danger" onclick="deleteBudget(${b.id})" title="Delete budget">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"></polyline>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <div class="progress-bar-bg">
                    <div class="progress-bar-fill ${barClass}" style="width: ${pct}%"></div>
                </div>

                <div class="flex-between text-sm text-secondary mt-1">
                    <span>Spent: <strong>${formatCurrency(b.spent)}</strong></span>
                    <span>Limit: <strong>${formatCurrency(b.monthly_limit)}</strong> (${b.used_percentage}%)</span>
                </div>
            </div>
        `;
    }).join('');
}

async function deleteBudget(id) {
    showConfirmModal(
        'Delete Budget',
        'Are you sure you want to delete this budget limit?',
        async () => {
            try {
                const res = await fetch(`/api/budgets/${id}`, { method: 'DELETE' });
                if (!res.ok) throw new Error('Failed to delete budget');
                showToast('Budget deleted', 'success');
                loadBudgets();
                loadDashboard();
            } catch (err) {
                showToast('Error deleting budget', 'error');
            }
        }
    );
}

// ==========================================================================
// API Interaction: Analytics
// ==========================================================================

async function loadAnalytics() {
    try {
        const res = await fetch('/api/analytics');
        if (!res.ok) throw new Error('Failed to load analytics');
        const data = await res.json();
        state.analytics = data;

        // Metric cards
        document.getElementById('analyticsTotalSavings').textContent = formatCurrency(data.metrics.total_savings);
        document.getElementById('analyticsSavingsRate').textContent = `Savings Rate: ${data.metrics.savings_rate}%`;
        document.getElementById('analyticsTopCategory').textContent = data.metrics.highest_spending_category || 'None';
        document.getElementById('analyticsTopCategoryAmount').textContent = formatCurrency(data.metrics.highest_spending_amount);
        document.getElementById('analyticsDailyAvg').textContent = formatCurrency(data.metrics.average_daily_expense);
        document.getElementById('analyticsTxCount').textContent = data.metrics.total_transaction_count;

        // Render trend chart
        renderAnalyticsTrendChart(data.trends);
        renderAnalyticsCategoryBar(data.category_spending);
    } catch (err) {
        console.error('Error fetching analytics:', err);
        showToast('Error loading analytics', 'error');
    }
}

function renderAnalyticsTrendChart(trends) {
    const canvas = document.getElementById('chartAnalyticsTrend');
    if (!canvas) return;

    if (state.charts.analyticsTrend) {
        state.charts.analyticsTrend.destroy();
    }

    const labels = trends.map(t => t.month_label);
    const income = trends.map(t => t.income);
    const expense = trends.map(t => t.expense);
    const savings = trends.map(t => t.savings);

    state.charts.analyticsTrend = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: income,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Expense',
                    data: expense,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Net Savings',
                    data: savings,
                    borderColor: '#2563eb',
                    borderDash: [5, 5],
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    ticks: {
                        callback: (val) => state.currency + Number(val).toLocaleString('en-IN')
                    }
                }
            }
        }
    });
}

function renderAnalyticsCategoryBar(categories) {
    const canvas = document.getElementById('chartAnalyticsCategoryBar');
    if (!canvas) return;

    if (state.charts.analyticsCategory) {
        state.charts.analyticsCategory.destroy();
    }

    const labels = categories.map(c => c.category);
    const amounts = categories.map(c => c.total);

    state.charts.analyticsCategory = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total Spent',
                data: amounts,
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    ticks: {
                        callback: (val) => state.currency + Number(val).toLocaleString('en-IN')
                    }
                }
            }
        }
    });
}

// ==========================================================================
// API Interaction: Settings & Demo Seeding
// ==========================================================================

function initSettings() {
    const form = document.getElementById('settingsForm');
    const clearBtn = document.getElementById('clearAllDataBtn');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                display_name: document.getElementById('settingsDisplayName').value.trim(),
                currency: document.getElementById('settingsCurrency').value
            };

            try {
                const res = await fetch('/api/settings', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to update settings');

                showToast('Settings saved successfully!', 'success');
                loadSettings();
                loadDashboard();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', async () => {
            showConfirmModal(
                'Clear All Data',
                'This will erase all recorded transactions and custom budgets, leaving your expense tracker in a clean zero-balance state. Are you sure?',
                async () => {
                    try {
                        const res = await fetch('/api/settings/clear-data', { method: 'POST' });
                        const data = await res.json();
                        if (!res.ok) throw new Error(data.error || 'Failed to clear data');

                        showToast('All data cleared successfully (Clean State).', 'success');
                        loadDashboard();
                        loadTransactions();
                        loadBudgets();
                    } catch (err) {
                        showToast(err.message, 'error');
                    }
                }
            );
        });
    }
}

async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        if (!res.ok) throw new Error('Failed to load settings');
        const settings = await res.json();

        state.currency = settings.currency || '₹';
        state.userDisplayName = settings.display_name || 'User';

        // Update UI
        const displayNameEl = document.getElementById('userDisplayName');
        const avatarInitial = document.getElementById('avatarInitial');
        const settingsDisplayName = document.getElementById('settingsDisplayName');
        const settingsCurrency = document.getElementById('settingsCurrency');

        if (displayNameEl) displayNameEl.textContent = state.userDisplayName;
        if (avatarInitial) avatarInitial.textContent = state.userDisplayName.charAt(0).toUpperCase();
        if (settingsDisplayName) settingsDisplayName.value = state.userDisplayName;
        if (settingsCurrency) settingsCurrency.value = state.currency;
    } catch (err) {
        console.error('Error fetching settings:', err);
    }
}

// ==========================================================================
// Helper Utilities
// ==========================================================================

function populateCategoryDropdown(selectElement, categories) {
    if (!selectElement) return;
    const currentVal = selectElement.value;
    const isFilter = selectElement.id === 'filterCategory';

    let html = isFilter ? '<option value="">All Categories</option>' : '';
    html += categories.map(cat => `<option value="${cat}">${cat}</option>`).join('');
    selectElement.innerHTML = html;

    if (currentVal && categories.includes(currentVal)) {
        selectElement.value = currentVal;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
