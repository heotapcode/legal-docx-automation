/**
 * CRM.Pages.Finance - Quản lý Thu chi & Công nợ
 * Renders financial management page with transactions CRUD and debt tracking
 */
(function () {
  'use strict';
  window.CRM = window.CRM || {};
  CRM.Pages = CRM.Pages || {};

  // ── State ──────────────────────────────────────────────────────────
  let currentTab = 'transactions'; // 'transactions' | 'debt'
  let currentPage = 1;
  const perPage = 20;
  let filters = { search: '', type: '', category: '', payment_status: '', customer_id: '', date_from: '', date_to: '' };
  let customersList = [];
  let delegatedHandler = null;
  let delegatedChangeHandler = null;
  let searchDebounce = null;

  // ── Helpers ────────────────────────────────────────────────────────
  function getPageContent() {
    return document.getElementById('page-content');
  }

  function buildQueryString() {
    const params = new URLSearchParams();
    if (filters.search) params.set('search', filters.search);
    if (filters.type) params.set('type', filters.type);
    if (filters.category) params.set('category', filters.category);
    if (filters.payment_status) params.set('payment_status', filters.payment_status);
    if (filters.customer_id) params.set('customer_id', filters.customer_id);
    if (filters.date_from) params.set('date_from', filters.date_from);
    if (filters.date_to) params.set('date_to', filters.date_to);
    params.set('page', currentPage);
    params.set('per_page', perPage);
    return params.toString();
  }

  function getTypeBadge(type) {
    if (type === 'thu') {
      return '<span class="badge" style="background:rgba(16,185,129,0.15);color:#10b981;">Thu</span>';
    }
    return '<span class="badge" style="background:rgba(239,68,68,0.15);color:#ef4444;">Chi</span>';
  }

  // ── Render Main Layout ─────────────────────────────────────────────
  function renderLayout() {
    return `
      <div class="stats-grid" id="finance-stats"></div>

      <div style="display:flex;gap:8px;margin-bottom:20px;">
        <button class="btn ${currentTab === 'transactions' ? 'btn-primary' : 'btn-secondary'}" data-tab="transactions">
          <i class="fa-solid fa-exchange-alt"></i> Giao dịch
        </button>
        <button class="btn ${currentTab === 'debt' ? 'btn-primary' : 'btn-secondary'}" data-tab="debt">
          <i class="fa-solid fa-file-invoice-dollar"></i> Công nợ
        </button>
      </div>

      <div id="tab-content"></div>
    `;
  }

  // ── Stats Cards ────────────────────────────────────────────────────
  async function loadStats() {
    const container = document.getElementById('finance-stats');
    if (!container) return;

    try {
      // Fetch all transactions (no pagination, large per_page to get all)
      const res = await CRM.API.get('/api/transactions?per_page=9999');
      const transactions = res.data || res || [];

      let totalThu = 0, totalChi = 0, totalDebt = 0;
      transactions.forEach(t => {
        const amt = parseFloat(t.amount) || 0;
        if (t.type === 'thu') {
          totalThu += amt;
          if (t.payment_status !== 'da_thanh_toan') {
            totalDebt += amt - (parseFloat(t.paid_amount) || 0);
          }
        } else {
          totalChi += amt;
        }
      });

      const profit = totalThu - totalChi;

      container.innerHTML = `
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(16,185,129,0.15);">
            <i class="fa-solid fa-arrow-down" style="color:#10b981;font-size:22px;"></i>
          </div>
          <div>
            <div class="stat-value" style="color:#10b981;">${CRM.Utils.formatCurrency(totalThu)}</div>
            <div class="stat-label">Tổng thu</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(239,68,68,0.15);">
            <i class="fa-solid fa-arrow-up" style="color:#ef4444;font-size:22px;"></i>
          </div>
          <div>
            <div class="stat-value" style="color:#ef4444;">${CRM.Utils.formatCurrency(totalChi)}</div>
            <div class="stat-label">Tổng chi</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(59,130,246,0.15);">
            <i class="fa-solid fa-chart-line" style="color:#3b82f6;font-size:22px;"></i>
          </div>
          <div>
            <div class="stat-value" style="color:${profit >= 0 ? '#10b981' : '#ef4444'};">${CRM.Utils.formatCurrency(profit)}</div>
            <div class="stat-label">Lợi nhuận</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(245,158,11,0.15);">
            <i class="fa-solid fa-file-invoice-dollar" style="color:#f59e0b;font-size:22px;"></i>
          </div>
          <div>
            <div class="stat-value" style="color:#f59e0b;">${CRM.Utils.formatCurrency(totalDebt)}</div>
            <div class="stat-label">Công nợ</div>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = '';
      console.error('Error loading finance stats:', err);
    }
  }

  // ── Fetch Customers List (for dropdowns) ───────────────────────────
  async function fetchCustomersList() {
    try {
      const res = await CRM.API.get('/api/customers/all/list');
      customersList = res.data || res || [];
    } catch (err) {
      customersList = [];
      console.error('Error fetching customers list:', err);
    }
  }

  // ── Transactions Tab ───────────────────────────────────────────────
  function renderTransactionsTab() {
    const container = document.getElementById('tab-content');
    if (!container) return;

    const categories = CRM.Utils.TRANSACTION_CATEGORIES || {};
    const paymentStatuses = CRM.Utils.PAYMENT_STATUSES || {};

    const customerOptions = customersList.map(c =>
      `<option value="${c.id}" ${filters.customer_id == c.id ? 'selected' : ''}>${c.code} - ${c.company_name}</option>`
    ).join('');

    const categoryOptions = Object.entries(categories).map(([k, v]) =>
      `<option value="${k}" ${filters.category === k ? 'selected' : ''}>${v}</option>`
    ).join('');

    const paymentOptions = Object.entries(paymentStatuses).map(([k, v]) =>
      `<option value="${k}" ${filters.payment_status === k ? 'selected' : ''}>${v.label}</option>`
    ).join('');

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h3 class="card-title"><i class="fa-solid fa-exchange-alt"></i> Danh sách giao dịch</h3>
          <button class="btn btn-primary btn-sm" id="btn-add-transaction">
            <i class="fa-solid fa-plus"></i> Thêm giao dịch
          </button>
        </div>
        <div class="card-body">
          <div class="toolbar">
            <div class="filter-bar" style="flex:1;">
              <div class="filter-group">
                <div class="search-bar">
                  <i class="fa-solid fa-magnifying-glass search-icon"></i>
                  <input type="text" class="form-control" id="filter-search" placeholder="Tìm kiếm mã GD, ghi chú..." value="${filters.search}">
                </div>
              </div>
              <div class="filter-group">
                <select class="form-control" id="filter-type" style="min-width:120px;">
                  <option value="">-- Loại --</option>
                  <option value="thu" ${filters.type === 'thu' ? 'selected' : ''}>Thu</option>
                  <option value="chi" ${filters.type === 'chi' ? 'selected' : ''}>Chi</option>
                </select>
              </div>
              <div class="filter-group">
                <select class="form-control" id="filter-category" style="min-width:140px;">
                  <option value="">-- Danh mục --</option>
                  ${categoryOptions}
                </select>
              </div>
              <div class="filter-group">
                <select class="form-control" id="filter-payment" style="min-width:150px;">
                  <option value="">-- TT Thanh toán --</option>
                  ${paymentOptions}
                </select>
              </div>
              <div class="filter-group">
                <select class="form-control" id="filter-customer" style="min-width:180px;">
                  <option value="">-- Khách hàng --</option>
                  ${customerOptions}
                </select>
              </div>
              <div class="filter-group">
                <input type="date" class="form-control" id="filter-date-from" value="${filters.date_from}" title="Từ ngày" style="min-width:140px;">
              </div>
              <div class="filter-group">
                <input type="date" class="form-control" id="filter-date-to" value="${filters.date_to}" title="Đến ngày" style="min-width:140px;">
              </div>
            </div>
          </div>
          <div id="transactions-table">
            <div class="loading-spinner" style="text-align:center;padding:40px;">
              <i class="fa-solid fa-spinner fa-spin" style="font-size:24px;color:var(--text-muted);"></i>
              <p style="color:var(--text-muted);margin-top:8px;">Đang tải dữ liệu...</p>
            </div>
          </div>
        </div>
      </div>
    `;

    loadTransactions();
  }

  async function loadTransactions() {
    const tableContainer = document.getElementById('transactions-table');
    if (!tableContainer) return;

    try {
      const qs = buildQueryString();
      const res = await CRM.API.get(`/api/transactions?${qs}`);
      const data = res.data || res || [];
      const pagination = res.pagination || null;

      CRM.Table.render('transactions-table', {
        columns: [
          { key: 'code', label: 'Mã GD', width: '100px' },
          {
            key: 'type', label: 'Loại', width: '80px',
            render: (val) => getTypeBadge(val)
          },
          {
            key: 'category', label: 'Danh mục', width: '130px',
            render: (val) => CRM.Utils.getCategoryLabel(val) || val || '-'
          },
          {
            key: 'amount', label: 'Số tiền', width: '130px',
            render: (val, row) => `<span style="font-weight:600;color:${row.type === 'thu' ? '#10b981' : '#ef4444'};">${CRM.Utils.formatCurrency(val)}</span>`
          },
          {
            key: 'transaction_date', label: 'Ngày GD', width: '110px',
            render: (val) => val ? CRM.Utils.formatDate(val) : '-'
          },
          {
            key: 'customer_name', label: 'Khách hàng', width: '160px',
            render: (val) => val || '<span style="color:var(--text-muted);">-</span>'
          },
          {
            key: 'record_code', label: 'Hồ sơ', width: '120px',
            render: (val) => val || '<span style="color:var(--text-muted);">-</span>'
          },
          {
            key: 'payment_status', label: 'TT Thanh toán', width: '130px',
            render: (val) => CRM.Utils.getPaymentBadge(val)
          }
        ],
        data: data,
        actions: [
          {
            icon: 'fa-solid fa-pen-to-square',
            className: 'btn btn-secondary btn-icon btn-sm',
            label: 'Sửa',
            onClick: (row) => openTransactionModal(row)
          },
          {
            icon: 'fa-solid fa-trash-can',
            className: 'btn btn-danger btn-icon btn-sm',
            label: 'Xóa',
            onClick: (row) => deleteTransaction(row)
          }
        ],
        pagination: pagination,
        onPageChange: (page) => {
          currentPage = page;
          loadTransactions();
        },
        emptyMessage: 'Chưa có giao dịch nào',
        emptyIcon: 'fa-solid fa-receipt'
      });
    } catch (err) {
      tableContainer.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-circle-exclamation" style="font-size:40px;margin-bottom:12px;color:var(--color-danger);"></i>
          <p>Lỗi tải dữ liệu giao dịch</p>
        </div>
      `;
      console.error('Error loading transactions:', err);
    }
  }

  // ── Transaction Modal (Add/Edit) ──────────────────────────────────
  async function openTransactionModal(existingData) {
    const isEdit = !!existingData;
    const title = isEdit ? 'Chỉnh sửa giao dịch' : 'Thêm giao dịch mới';

    // Ensure customers list is loaded
    if (customersList.length === 0) {
      await fetchCustomersList();
    }

    const categories = CRM.Utils.TRANSACTION_CATEGORIES || {};
    const paymentStatuses = CRM.Utils.PAYMENT_STATUSES || {};

    const d = existingData || {};

    const customerOptions = customersList.map(c =>
      `<option value="${c.id}" ${d.customer_id == c.id ? 'selected' : ''}>${c.code} - ${c.company_name}</option>`
    ).join('');

    const categoryOptions = Object.entries(categories).map(([k, v]) =>
      `<option value="${k}" ${d.category === k ? 'selected' : ''}>${v}</option>`
    ).join('');

    const paymentOptions = Object.entries(paymentStatuses).map(([k, v]) =>
      `<option value="${k}" ${d.payment_status === k ? 'selected' : ''}>${v.label}</option>`
    ).join('');

    const body = `
      <form id="transaction-form">
        <div class="form-group">
          <label class="form-label">Loại giao dịch <span style="color:var(--color-danger);">*</span></label>
          <div style="display:flex;gap:16px;">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:10px 20px;border-radius:var(--border-radius-sm);border:1px solid var(--border-color);background:${(!d.type || d.type === 'thu') ? 'rgba(16,185,129,0.15)' : 'transparent'};transition:all 0.2s;" class="type-radio-label" data-type="thu">
              <input type="radio" name="txn_type" value="thu" ${!d.type || d.type === 'thu' ? 'checked' : ''} style="accent-color:#10b981;">
              <i class="fa-solid fa-arrow-down" style="color:#10b981;"></i>
              <span style="font-weight:500;">Thu</span>
            </label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:10px 20px;border-radius:var(--border-radius-sm);border:1px solid var(--border-color);background:${d.type === 'chi' ? 'rgba(239,68,68,0.15)' : 'transparent'};transition:all 0.2s;" class="type-radio-label" data-type="chi">
              <input type="radio" name="txn_type" value="chi" ${d.type === 'chi' ? 'checked' : ''} style="accent-color:#ef4444;">
              <i class="fa-solid fa-arrow-up" style="color:#ef4444;"></i>
              <span style="font-weight:500;">Chi</span>
            </label>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Danh mục <span style="color:var(--color-danger);">*</span></label>
            <select class="form-control" id="txn-category" required>
              <option value="">-- Chọn danh mục --</option>
              ${categoryOptions}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Số tiền <span style="color:var(--color-danger);">*</span></label>
            <input type="number" class="form-control" id="txn-amount" min="0" step="1000" value="${d.amount || ''}" placeholder="0" required>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Ngày giao dịch</label>
            <input type="date" class="form-control" id="txn-date" value="${d.transaction_date || new Date().toISOString().split('T')[0]}">
          </div>
          <div class="form-group">
            <label class="form-label">Khách hàng</label>
            <select class="form-control" id="txn-customer">
              <option value="">-- Chọn khách hàng --</option>
              ${customerOptions}
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Hồ sơ</label>
            <select class="form-control" id="txn-record" ${!d.customer_id ? 'disabled' : ''}>
              <option value="">-- Chọn hồ sơ --</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Trạng thái thanh toán</label>
            <select class="form-control" id="txn-payment-status">
              ${paymentOptions}
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Hạn thanh toán</label>
            <input type="date" class="form-control" id="txn-due-date" value="${d.payment_due_date || ''}">
          </div>
          <div class="form-group">
            <label class="form-label">Đã thanh toán</label>
            <input type="number" class="form-control" id="txn-paid-amount" min="0" step="1000" value="${d.paid_amount || 0}" placeholder="0">
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Ghi chú</label>
          <textarea class="form-control" id="txn-notes" rows="3" placeholder="Nhập ghi chú...">${d.notes || ''}</textarea>
        </div>
      </form>
    `;

    const footer = `
      <button class="btn btn-secondary" id="btn-cancel-txn">Hủy</button>
      <button class="btn btn-primary" id="btn-save-txn">
        <i class="fa-solid fa-check"></i> ${isEdit ? 'Cập nhật' : 'Lưu'}
      </button>
    `;

    CRM.Modal.show({
      title: title,
      body: body,
      footer: footer,
      size: 'lg'
    });

    // Load records if customer pre-selected
    if (d.customer_id) {
      await loadRecordsForCustomer(d.customer_id, d.record_id);
    }

    // ── Modal event listeners ──
    const modalOverlay = document.getElementById('modal-overlay');
    if (!modalOverlay) return;

    modalOverlay.addEventListener('click', function modalClickHandler(e) {
      // Radio type toggle visual
      if (e.target.closest('.type-radio-label') || e.target.matches('input[name="txn_type"]')) {
        const labels = modalOverlay.querySelectorAll('.type-radio-label');
        labels.forEach(lbl => {
          const radio = lbl.querySelector('input[type="radio"]');
          if (radio && radio.checked) {
            lbl.style.background = radio.value === 'thu' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)';
          } else {
            lbl.style.background = 'transparent';
          }
        });
      }

      // Cancel
      if (e.target.closest('#btn-cancel-txn')) {
        CRM.Modal.close();
      }

      // Save
      if (e.target.closest('#btn-save-txn')) {
        saveTransaction(isEdit, d.id);
      }
    });

    // Customer change → load records
    modalOverlay.addEventListener('change', function modalChangeHandler(e) {
      if (e.target.id === 'txn-customer') {
        const custId = e.target.value;
        const recordSelect = document.getElementById('txn-record');
        if (custId) {
          recordSelect.disabled = false;
          loadRecordsForCustomer(custId);
        } else {
          recordSelect.disabled = true;
          recordSelect.innerHTML = '<option value="">-- Chọn hồ sơ --</option>';
        }
      }

      // Radio type styling on change
      if (e.target.name === 'txn_type') {
        const labels = modalOverlay.querySelectorAll('.type-radio-label');
        labels.forEach(lbl => {
          const radio = lbl.querySelector('input[type="radio"]');
          if (radio && radio.checked) {
            lbl.style.background = radio.value === 'thu' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)';
          } else {
            lbl.style.background = 'transparent';
          }
        });
      }
    });
  }

  async function loadRecordsForCustomer(customerId, selectedRecordId) {
    const recordSelect = document.getElementById('txn-record');
    if (!recordSelect) return;

    try {
      const res = await CRM.API.get(`/api/records?customer_id=${customerId}&per_page=999`);
      const records = res.data || res || [];
      let options = '<option value="">-- Chọn hồ sơ --</option>';
      records.forEach(r => {
        const sel = (selectedRecordId && r.id == selectedRecordId) ? 'selected' : '';
        const typeLabel = CRM.Utils.getRecordTypeLabel ? CRM.Utils.getRecordTypeLabel(r.type) : r.type;
        options += `<option value="${r.id}" ${sel}>${r.code} - ${typeLabel}</option>`;
      });
      recordSelect.innerHTML = options;
      recordSelect.disabled = false;
    } catch (err) {
      console.error('Error loading records for customer:', err);
      recordSelect.innerHTML = '<option value="">-- Lỗi tải hồ sơ --</option>';
    }
  }

  async function saveTransaction(isEdit, id) {
    const typeRadio = document.querySelector('input[name="txn_type"]:checked');
    const category = document.getElementById('txn-category')?.value;
    const amount = document.getElementById('txn-amount')?.value;
    const transactionDate = document.getElementById('txn-date')?.value;
    const customerId = document.getElementById('txn-customer')?.value;
    const recordId = document.getElementById('txn-record')?.value;
    const paymentStatus = document.getElementById('txn-payment-status')?.value;
    const dueDate = document.getElementById('txn-due-date')?.value;
    const paidAmount = document.getElementById('txn-paid-amount')?.value;
    const notes = document.getElementById('txn-notes')?.value;

    if (!typeRadio || !category || !amount) {
      CRM.Toast.warning('Vui lòng điền đầy đủ thông tin bắt buộc');
      return;
    }

    const payload = {
      type: typeRadio.value,
      category,
      amount: parseFloat(amount),
      transaction_date: transactionDate || null,
      customer_id: customerId ? parseInt(customerId) : null,
      record_id: recordId ? parseInt(recordId) : null,
      payment_status: paymentStatus || 'chua_thanh_toan',
      payment_due_date: dueDate || null,
      paid_amount: parseFloat(paidAmount) || 0,
      notes: notes || null
    };

    try {
      const saveBtn = document.getElementById('btn-save-txn');
      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang lưu...';
      }

      if (isEdit) {
        await CRM.API.put(`/api/transactions/${id}`, payload);
        CRM.Toast.success('Cập nhật giao dịch thành công');
      } else {
        await CRM.API.post('/api/transactions', payload);
        CRM.Toast.success('Thêm giao dịch thành công');
      }

      CRM.Modal.close();
      loadTransactions();
      loadStats();
    } catch (err) {
      CRM.Toast.error('Lỗi: ' + (err.message || 'Không thể lưu giao dịch'));
      const saveBtn = document.getElementById('btn-save-txn');
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<i class="fa-solid fa-check"></i> ${isEdit ? 'Cập nhật' : 'Lưu'}`;
      }
    }
  }

  function deleteTransaction(row) {
    CRM.Modal.confirm({
      title: 'Xóa giao dịch',
      message: `Bạn có chắc chắn muốn xóa giao dịch <strong>${row.code}</strong>?<br>Hành động này không thể hoàn tác.`,
      confirmText: 'Xóa',
      confirmClass: 'btn btn-danger',
      onConfirm: async () => {
        try {
          await CRM.API.delete(`/api/transactions/${row.id}`);
          CRM.Toast.success('Đã xóa giao dịch');
          loadTransactions();
          loadStats();
        } catch (err) {
          CRM.Toast.error('Lỗi: Không thể xóa giao dịch');
        }
      }
    });
  }

  // ── Công nợ Tab ────────────────────────────────────────────────────
  async function renderDebtTab() {
    const container = document.getElementById('tab-content');
    if (!container) return;

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h3 class="card-title"><i class="fa-solid fa-file-invoice-dollar"></i> Danh sách công nợ khách hàng</h3>
        </div>
        <div class="card-body">
          <div id="debt-table">
            <div class="loading-spinner" style="text-align:center;padding:40px;">
              <i class="fa-solid fa-spinner fa-spin" style="font-size:24px;color:var(--text-muted);"></i>
              <p style="color:var(--text-muted);margin-top:8px;">Đang tải dữ liệu công nợ...</p>
            </div>
          </div>
        </div>
      </div>
    `;

    try {
      // Fetch unpaid thu transactions
      const res = await CRM.API.get('/api/transactions?type=thu&per_page=9999');
      const allTransactions = (res.data || res || []).filter(t => t.payment_status !== 'da_thanh_toan');

      if (allTransactions.length === 0) {
        document.getElementById('debt-table').innerHTML = `
          <div class="empty-state">
            <i class="fa-solid fa-check-circle" style="font-size:48px;margin-bottom:12px;color:var(--color-success);"></i>
            <p style="font-size:16px;font-weight:500;">Không có công nợ</p>
            <p style="color:var(--text-muted);">Tất cả giao dịch đã được thanh toán</p>
          </div>
        `;
        return;
      }

      // Group by customer
      const debtMap = {};
      const today = new Date().toISOString().split('T')[0];

      allTransactions.forEach(t => {
        const custId = t.customer_id || 0;
        const custName = t.customer_name || 'Không xác định';
        if (!debtMap[custId]) {
          debtMap[custId] = {
            customer_id: custId,
            customer_name: custName,
            total_amount: 0,
            total_paid: 0,
            total_debt: 0,
            overdue_count: 0,
            transactions: []
          };
        }
        const amt = parseFloat(t.amount) || 0;
        const paid = parseFloat(t.paid_amount) || 0;
        debtMap[custId].total_amount += amt;
        debtMap[custId].total_paid += paid;
        debtMap[custId].total_debt += (amt - paid);
        if (t.payment_due_date && t.payment_due_date < today) {
          debtMap[custId].overdue_count++;
        }
        debtMap[custId].transactions.push(t);
      });

      const debtData = Object.values(debtMap).sort((a, b) => b.total_debt - a.total_debt);

      CRM.Table.render('debt-table', {
        columns: [
          { key: 'customer_name', label: 'Khách hàng', width: '200px' },
          {
            key: 'total_amount', label: 'Tổng phải thu', width: '140px',
            render: (val) => `<span style="font-weight:600;">${CRM.Utils.formatCurrency(val)}</span>`
          },
          {
            key: 'total_paid', label: 'Đã thu', width: '140px',
            render: (val) => `<span style="color:#10b981;font-weight:500;">${CRM.Utils.formatCurrency(val)}</span>`
          },
          {
            key: 'total_debt', label: 'Còn nợ', width: '140px',
            render: (val) => `<span style="color:#ef4444;font-weight:600;">${CRM.Utils.formatCurrency(val)}</span>`
          },
          {
            key: 'overdue_count', label: 'GD quá hạn', width: '110px',
            render: (val) => {
              if (val > 0) {
                return `<span class="badge" style="background:rgba(239,68,68,0.15);color:#ef4444;">${val}</span>`;
              }
              return '<span style="color:var(--text-muted);">0</span>';
            }
          }
        ],
        data: debtData,
        actions: [
          {
            icon: 'fa-solid fa-eye',
            className: 'btn btn-secondary btn-icon btn-sm',
            label: 'Xem chi tiết',
            onClick: (row) => showDebtDetail(row)
          }
        ],
        emptyMessage: 'Không có công nợ',
        emptyIcon: 'fa-solid fa-check-circle'
      });
    } catch (err) {
      document.getElementById('debt-table').innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-circle-exclamation" style="font-size:40px;margin-bottom:12px;color:var(--color-danger);"></i>
          <p>Lỗi tải dữ liệu công nợ</p>
        </div>
      `;
      console.error('Error loading debt data:', err);
    }
  }

  function showDebtDetail(debtRow) {
    const transactions = debtRow.transactions || [];
    const today = new Date().toISOString().split('T')[0];

    let rows = '';
    transactions.forEach(t => {
      const amt = parseFloat(t.amount) || 0;
      const paid = parseFloat(t.paid_amount) || 0;
      const remaining = amt - paid;
      const isOverdue = t.payment_due_date && t.payment_due_date < today;

      rows += `
        <tr${isOverdue ? ' style="background:rgba(239,68,68,0.05);"' : ''}>
          <td>${t.code || '-'}</td>
          <td>${CRM.Utils.getCategoryLabel(t.category) || t.category || '-'}</td>
          <td style="font-weight:500;">${CRM.Utils.formatCurrency(amt)}</td>
          <td style="color:#10b981;">${CRM.Utils.formatCurrency(paid)}</td>
          <td style="color:#ef4444;font-weight:600;">${CRM.Utils.formatCurrency(remaining)}</td>
          <td>${t.payment_due_date ? CRM.Utils.formatDate(t.payment_due_date) : '-'}${isOverdue ? ' <span class="badge" style="background:rgba(239,68,68,0.15);color:#ef4444;font-size:10px;">Quá hạn</span>' : ''}</td>
          <td>${CRM.Utils.getPaymentBadge(t.payment_status)}</td>
        </tr>
      `;
    });

    const body = `
      <div style="margin-bottom:16px;">
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
          <div>
            <span style="color:var(--text-muted);font-size:13px;">Tổng phải thu</span>
            <div style="font-size:18px;font-weight:700;">${CRM.Utils.formatCurrency(debtRow.total_amount)}</div>
          </div>
          <div>
            <span style="color:var(--text-muted);font-size:13px;">Đã thu</span>
            <div style="font-size:18px;font-weight:700;color:#10b981;">${CRM.Utils.formatCurrency(debtRow.total_paid)}</div>
          </div>
          <div>
            <span style="color:var(--text-muted);font-size:13px;">Còn nợ</span>
            <div style="font-size:18px;font-weight:700;color:#ef4444;">${CRM.Utils.formatCurrency(debtRow.total_debt)}</div>
          </div>
        </div>
      </div>
      <div class="divider"></div>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Mã GD</th>
              <th>Danh mục</th>
              <th>Số tiền</th>
              <th>Đã TT</th>
              <th>Còn lại</th>
              <th>Hạn TT</th>
              <th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;

    CRM.Modal.show({
      title: `Công nợ - ${debtRow.customer_name}`,
      body: body,
      size: 'lg'
    });
  }

  // ── Event Delegation ───────────────────────────────────────────────
  function handleClick(e) {
    // Tab switching
    const tabBtn = e.target.closest('[data-tab]');
    if (tabBtn) {
      const tab = tabBtn.getAttribute('data-tab');
      if (tab !== currentTab) {
        currentTab = tab;
        renderTabButtons();
        if (tab === 'transactions') {
          renderTransactionsTab();
        } else {
          renderDebtTab();
        }
      }
      return;
    }

    // Add transaction button
    if (e.target.closest('#btn-add-transaction')) {
      openTransactionModal(null);
      return;
    }
  }

  function handleChange(e) {
    const id = e.target.id;

    if (id === 'filter-search') {
      filters.search = e.target.value;
      currentPage = 1;
      if (searchDebounce) clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => loadTransactions(), 300);
      return;
    }
    if (id === 'filter-type') {
      filters.type = e.target.value;
      currentPage = 1;
      loadTransactions();
      return;
    }
    if (id === 'filter-category') {
      filters.category = e.target.value;
      currentPage = 1;
      loadTransactions();
      return;
    }
    if (id === 'filter-payment') {
      filters.payment_status = e.target.value;
      currentPage = 1;
      loadTransactions();
      return;
    }
    if (id === 'filter-customer') {
      filters.customer_id = e.target.value;
      currentPage = 1;
      loadTransactions();
      return;
    }
    if (id === 'filter-date-from') {
      filters.date_from = e.target.value;
      currentPage = 1;
      loadTransactions();
      return;
    }
    if (id === 'filter-date-to') {
      filters.date_to = e.target.value;
      currentPage = 1;
      loadTransactions();
      return;
    }
  }

  function renderTabButtons() {
    const pageContent = getPageContent();
    if (!pageContent) return;
    const buttons = pageContent.querySelectorAll('[data-tab]');
    buttons.forEach(btn => {
      const tab = btn.getAttribute('data-tab');
      btn.className = `btn ${tab === currentTab ? 'btn-primary' : 'btn-secondary'}`;
    });
  }

  // ── Page Module ────────────────────────────────────────────────────
  CRM.Pages.Finance = {
    async render() {
      CRM.App.setPageTitle('Thu/Chi', 'Quản lý Thu chi & Công nợ');

      const pageContent = getPageContent();
      if (!pageContent) return;

      // Reset state
      currentTab = 'transactions';
      currentPage = 1;
      filters = { search: '', type: '', category: '', payment_status: '', customer_id: '', date_from: '', date_to: '' };

      // Show loading
      pageContent.innerHTML = `
        <div class="loading-spinner" style="text-align:center;padding:80px;">
          <i class="fa-solid fa-spinner fa-spin" style="font-size:32px;color:var(--text-muted);"></i>
          <p style="color:var(--text-muted);margin-top:12px;">Đang tải trang Thu/Chi...</p>
        </div>
      `;

      // Fetch customers for dropdown
      await fetchCustomersList();

      // Render layout
      pageContent.innerHTML = renderLayout();

      // Setup event delegation
      delegatedHandler = handleClick;
      delegatedChangeHandler = handleChange;
      pageContent.addEventListener('click', delegatedHandler);
      pageContent.addEventListener('change', delegatedChangeHandler);
      pageContent.addEventListener('input', delegatedChangeHandler);

      // Load stats and default tab
      loadStats();
      renderTransactionsTab();
    },

    destroy() {
      const pageContent = getPageContent();
      if (pageContent) {
        if (delegatedHandler) pageContent.removeEventListener('click', delegatedHandler);
        if (delegatedChangeHandler) {
          pageContent.removeEventListener('change', delegatedChangeHandler);
          pageContent.removeEventListener('input', delegatedChangeHandler);
        }
      }
      delegatedHandler = null;
      delegatedChangeHandler = null;
      if (searchDebounce) {
        clearTimeout(searchDebounce);
        searchDebounce = null;
      }
      customersList = [];
    }
  };
})();
