/**
 * CRM.Pages.Records
 * Trang quản lý hồ sơ ĐKKD
 * CRUD hồ sơ, lọc, tìm kiếm, xem chi tiết, đổi trạng thái
 */
;(function () {
  'use strict';

  // ── Biến module ──────────────────────────────────────────────
  let _filters = { search: '', type: '', status: '', assigned_to: '', date_from: '', date_to: '' };
  let _pagination = { page: 1, per_page: 20, total: 0, total_pages: 0 };
  let _users = [];       // Danh sách user cho dropdown
  let _customers = [];   // Danh sách khách hàng cho dropdown
  let _debounceSearch = null;

  // Workflow trạng thái: current → [next states]
  const STATUS_WORKFLOW = {
    tiep_nhan: ['dang_xu_ly'],
    dang_xu_ly: ['cho_nop', 'tra_lai'],
    cho_nop: ['da_nop', 'tra_lai'],
    da_nop: ['hoan_thanh', 'tra_lai'],
    tra_lai: ['dang_xu_ly'],
    hoan_thanh: []
  };

  // ── Helpers ──────────────────────────────────────────────────

  /**
   * Kiểm tra quá hạn
   */
  function isOverdue(deadline, status) {
    if (!deadline || status === 'hoan_thanh') return false;
    const now = new Date(); now.setHours(0, 0, 0, 0);
    const dl = new Date(deadline); dl.setHours(0, 0, 0, 0);
    return dl < now;
  }

  /**
   * Build grouped select options cho loại hồ sơ
   */
  function buildTypeOptions(selected) {
    const groups = CRM.Utils.RECORD_TYPE_GROUPS;
    let html = '<option value="">-- Tất cả loại --</option>';
    for (const [groupName, types] of Object.entries(groups)) {
      html += `<optgroup label="${groupName}">`;
      types.forEach(t => {
        const label = CRM.Utils.getRecordTypeLabel(t) || t;
        html += `<option value="${t}" ${selected === t ? 'selected' : ''}>${label}</option>`;
      });
      html += '</optgroup>';
    }
    return html;
  }

  /**
   * Build status select options
   */
  function buildStatusOptions(selected) {
    const statuses = CRM.Utils.RECORD_STATUSES;
    let html = '<option value="">-- Tất cả trạng thái --</option>';
    for (const [key, info] of Object.entries(statuses)) {
      html += `<option value="${key}" ${selected === key ? 'selected' : ''}>${info.label}</option>`;
    }
    return html;
  }

  /**
   * Build user select options
   */
  function buildUserOptions(selected, includeAll) {
    let html = includeAll ? '<option value="">-- Tất cả --</option>' : '<option value="">-- Chọn người phụ trách --</option>';
    _users.forEach(u => {
      html += `<option value="${u.id}" ${selected == u.id ? 'selected' : ''}>${CRM.Utils.escapeHtml(u.full_name || '')}</option>`;
    });
    return html;
  }

  /**
   * Build customer select options
   */
  function buildCustomerOptions(selected) {
    let html = '<option value="">-- Chọn khách hàng --</option>';
    _customers.forEach(c => {
      html += `<option value="${c.id}" ${selected == c.id ? 'selected' : ''}>${CRM.Utils.escapeHtml(c.code || '')} - ${CRM.Utils.escapeHtml(c.company_name || '')}</option>`;
    });
    return html;
  }

  // ── Render trang chính ───────────────────────────────────────

  function buildPageHTML() {
    return `
      <!-- Toolbar -->
      <div class="toolbar">
        <div style="display:flex; gap:12px; flex-wrap:wrap; flex:1; align-items:flex-end;">
          <div class="filter-group">
            <div class="search-bar" style="position:relative; min-width:260px;">
              <i class="fas fa-search search-icon" style="position:absolute; left:12px; top:50%; transform:translateY(-50%); color:var(--text-muted); font-size:14px;"></i>
              <input type="text" class="form-control" id="records-search" placeholder="Tìm kiếm mã HS, khách hàng..." style="padding-left:38px;" value="${_filters.search}">
            </div>
          </div>
          <div class="filter-group">
            <select class="form-control" id="records-filter-type" style="min-width:180px;">
              ${buildTypeOptions(_filters.type)}
            </select>
          </div>
          <div class="filter-group">
            <select class="form-control" id="records-filter-status" style="min-width:160px;">
              ${buildStatusOptions(_filters.status)}
            </select>
          </div>
          <div class="filter-group">
            <select class="form-control" id="records-filter-user" style="min-width:160px;">
              ${buildUserOptions(_filters.assigned_to, true)}
            </select>
          </div>
          <div class="filter-group">
            <input type="date" class="form-control" id="records-filter-from" value="${_filters.date_from}" title="Từ ngày" style="min-width:140px;">
          </div>
          <div class="filter-group">
            <input type="date" class="form-control" id="records-filter-to" value="${_filters.date_to}" title="Đến ngày" style="min-width:140px;">
          </div>
        </div>
        <div>
          <button class="btn btn-primary" id="btn-add-record" style="white-space:nowrap;">
            <i class="fas fa-plus" style="margin-right:6px;"></i>Thêm hồ sơ
          </button>
        </div>
      </div>

      <!-- Table container -->
      <div class="card">
        <div id="records-table-container"></div>
      </div>
    `;
  }

  // ── Fetch & Render bảng ──────────────────────────────────────

  async function fetchRecords() {
    try {
      const params = new URLSearchParams();
      if (_filters.search) params.set('search', _filters.search);
      if (_filters.type) params.set('type', _filters.type);
      if (_filters.status) params.set('status', _filters.status);
      if (_filters.assigned_to) params.set('assigned_to', _filters.assigned_to);
      if (_filters.date_from) params.set('date_from', _filters.date_from);
      if (_filters.date_to) params.set('date_to', _filters.date_to);
      params.set('page', _pagination.page);
      params.set('per_page', _pagination.per_page);

      const result = await CRM.API.get('/api/records?' + params.toString());
      const data = result.data || result;
      const records = Array.isArray(data) ? data : (data.data || data);
      const pagination = result.pagination || data.pagination || _pagination;

      _pagination = { ..._pagination, ...pagination };

      renderTable(Array.isArray(records) ? records : [], _pagination);
    } catch (err) {
      console.error('[Records] Lỗi tải hồ sơ:', err);
      CRM.Toast.error('Không thể tải danh sách hồ sơ');
    }
  }

  function renderTable(records, pagination) {
    CRM.Table.render('records-table-container', {
      columns: [
        { key: 'code', label: 'Mã HS', width: '110px', render: (v) => `<span style="font-weight:600; color:var(--accent-primary);">${v || ''}</span>` },
        { key: 'type', label: 'Loại', width: '180px', render: (v) => `<span style="font-size:13px;">${CRM.Utils.getRecordTypeLabel(v) || v || ''}</span>` },
        { key: 'customer_name', label: 'Khách hàng', width: '200px', render: (v) => `<span class="text-truncate" style="max-width:200px; display:inline-block;">${v || ''}</span>` },
        { key: 'received_date', label: 'Ngày nhận', width: '110px', render: (v) => v ? CRM.Utils.formatDate(v) : '—' },
        {
          key: 'deadline', label: 'Hạn nộp', width: '120px',
          render: (v, row) => {
            if (!v) return '—';
            const overdue = isOverdue(v, row.status);
            const style = overdue ? 'color:#ef4444; font-weight:600;' : '';
            const icon = overdue ? '<i class="fas fa-exclamation-circle" style="margin-right:4px; font-size:12px;"></i>' : '';
            return `<span style="${style}">${icon}${CRM.Utils.formatDate(v)}</span>`;
          }
        },
        { key: 'status', label: 'Trạng thái', width: '130px', render: (v) => CRM.Utils.getStatusBadge(v) },
        { key: 'assigned_name', label: 'Phụ trách', width: '130px', render: (v) => v || '<span style="color:var(--text-muted);">—</span>' },
        { key: 'fee_service', label: 'Phí DV', width: '120px', render: (v) => `<span style="font-weight:500;">${CRM.Utils.formatCurrency(v || 0)}</span>` }
      ],
      data: records,
      actions: [
        {
          icon: 'fa-eye',
          label: 'Xem',
          className: 'btn-icon btn-sm btn-secondary',
          onClick: (row) => showDetailModal(row.id)
        },
        {
          icon: 'fa-pen',
          label: 'Sửa',
          className: 'btn-icon btn-sm btn-secondary',
          onClick: (row) => showFormModal(row)
        },
        {
          icon: 'fa-trash',
          label: 'Xóa',
          className: 'btn-icon btn-sm btn-danger',
          onClick: (row) => confirmDelete(row)
        }
      ],
      pagination: pagination,
      onPageChange: (page) => {
        _pagination.page = page;
        fetchRecords();
      },
      emptyMessage: 'Không có hồ sơ nào',
      emptyIcon: 'fa-folder-open'
    });
  }

  // ── Xem chi tiết hồ sơ ──────────────────────────────────────

  async function showDetailModal(recordId) {
    CRM.Modal.show({
      title: 'Chi tiết hồ sơ',
      body: `<div style="display:flex; align-items:center; justify-content:center; padding:40px;"><div style="width:32px; height:32px; border:3px solid var(--border-color); border-top-color:var(--accent-primary); border-radius:50%; animation:spin 0.8s linear infinite;"></div></div>`,
      size: 'lg'
    });

    try {
      const result = await CRM.API.get('/api/records/' + recordId);
      const record = result.data || result;
      const history = result.history || [];
      const transactions = result.transactions || [];

      const statusInfo = CRM.Utils.RECORD_STATUSES[record.status] || {};
      const nextStatuses = STATUS_WORKFLOW[record.status] || [];

      // Build status buttons
      let statusButtons = '';
      if (nextStatuses.length > 0) {
        statusButtons = '<div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:16px;">';
        statusButtons += '<span style="color:var(--text-secondary); font-size:13px; align-self:center; margin-right:4px;">Chuyển trạng thái:</span>';
        nextStatuses.forEach(s => {
          const si = CRM.Utils.RECORD_STATUSES[s] || {};
          statusButtons += `<button class="btn btn-sm" data-change-status="${s}" data-record-id="${record.id}" style="background:${si.bg || 'rgba(255,255,255,0.08)'}; color:${si.color || '#e2e8f0'}; border:1px solid ${si.color || 'transparent'}30;">${si.label || s}</button>`;
        });
        statusButtons += '</div>';
      }

      // Build info section
      const infoHTML = `
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-bottom:20px;">
          <div>
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Mã hồ sơ</div>
            <div style="font-size:16px; font-weight:600; color:var(--accent-primary);">${CRM.Utils.escapeHtml(record.code || '')}</div>
          </div>
          <div>
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Trạng thái</div>
            <div>${CRM.Utils.getStatusBadge(record.status)}</div>
          </div>
          <div>
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Loại hồ sơ</div>
            <div style="color:var(--text-primary);">${CRM.Utils.getRecordTypeLabel(record.type) || ''}</div>
          </div>
          <div>
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Khách hàng</div>
            <div style="color:var(--text-primary);">${CRM.Utils.escapeHtml(record.customer_name || '')}</div>
          </div>
          <div>
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Ngày nhận</div>
            <div style="color:var(--text-primary);">${record.received_date ? CRM.Utils.formatDate(record.received_date) : '—'}</div>
          </div>
          <div>
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Hạn nộp</div>
            <div style="color:${isOverdue(record.deadline, record.status) ? '#ef4444' : 'var(--text-primary)'}; font-weight:${isOverdue(record.deadline, record.status) ? '600' : '400'};">${record.deadline ? CRM.Utils.formatDate(record.deadline) : '—'}</div>
          </div>
          <div>
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Người phụ trách</div>
            <div style="color:var(--text-primary);">${CRM.Utils.escapeHtml(record.assigned_name || '—')}</div>
          </div>
          <div>
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Phí dịch vụ / Phí nhà nước</div>
            <div style="color:var(--text-primary);">${CRM.Utils.formatCurrency(record.fee_service || 0)} / ${CRM.Utils.formatCurrency(record.fee_state || 0)}</div>
          </div>
        </div>
        ${record.notes ? `<div style="padding:12px 16px; background:var(--bg-input); border-radius:var(--border-radius-sm); margin-bottom:16px;"><div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;">Ghi chú</div><div style="font-size:13px; color:var(--text-secondary);">${CRM.Utils.escapeHtml(record.notes)}</div></div>` : ''}
        ${statusButtons}
      `;

      // Build transactions section
      let transHTML = '';
      if (transactions.length > 0) {
        let tRows = '';
        transactions.forEach(t => {
          const typeLabel = t.type === 'thu' ? '<span style="color:#10b981;">Thu</span>' : '<span style="color:#ef4444;">Chi</span>';
          tRows += `<tr>
            <td style="padding:8px 12px; font-size:13px; color:var(--accent-primary); font-weight:500;">${t.code || ''}</td>
            <td style="padding:8px 12px; font-size:13px;">${typeLabel}</td>
            <td style="padding:8px 12px; font-size:13px; color:var(--text-secondary);">${CRM.Utils.getCategoryLabel(t.category) || t.category || ''}</td>
            <td style="padding:8px 12px; font-size:13px; font-weight:500; color:var(--text-primary);">${CRM.Utils.formatCurrency(t.amount || 0)}</td>
            <td style="padding:8px 12px; font-size:13px;">${CRM.Utils.getPaymentBadge(t.payment_status)}</td>
          </tr>`;
        });
        transHTML = `
          <div class="divider"></div>
          <h4 style="font-size:14px; font-weight:600; color:var(--text-primary); margin-bottom:12px;"><i class="fas fa-money-bill-wave" style="color:#10b981; margin-right:8px;"></i>Giao dịch liên quan</h4>
          <div class="table-container">
            <table class="data-table" style="margin:0;">
              <thead><tr>
                <th style="padding:8px 12px;">Mã GD</th>
                <th style="padding:8px 12px;">Loại</th>
                <th style="padding:8px 12px;">Danh mục</th>
                <th style="padding:8px 12px;">Số tiền</th>
                <th style="padding:8px 12px;">Thanh toán</th>
              </tr></thead>
              <tbody>${tRows}</tbody>
            </table>
          </div>`;
      }

      // Build history section
      let histHTML = '';
      if (history.length > 0) {
        let hItems = '';
        history.forEach((h, idx) => {
          const colors = ['#667eea', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#3b82f6'];
          const avatarColor = colors[idx % colors.length];
          hItems += `
            <div style="display:flex; gap:12px; padding:10px 0; ${idx < history.length - 1 ? 'border-bottom:1px solid var(--border-color);' : ''}">
              <div style="width:8px; height:8px; border-radius:50%; background:${avatarColor}; margin-top:6px; flex-shrink:0;"></div>
              <div style="flex:1;">
                <div style="font-size:13px; color:var(--text-primary);"><strong>${h.user_name || ''}</strong> <span style="color:var(--text-secondary);">${h.action || ''}</span></div>
                ${h.details ? `<div style="font-size:12px; color:var(--text-muted); margin-top:2px;">${h.details}</div>` : ''}
                <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">${h.created_at ? CRM.Utils.timeAgo(h.created_at) : ''}</div>
              </div>
            </div>`;
        });
        histHTML = `
          <div class="divider"></div>
          <h4 style="font-size:14px; font-weight:600; color:var(--text-primary); margin-bottom:12px;"><i class="fas fa-history" style="color:#3b82f6; margin-right:8px;"></i>Lịch sử thay đổi</h4>
          <div style="max-height:300px; overflow-y:auto;">${hItems}</div>`;
      }

      // Update modal body
      CRM.Modal.show({
        title: `Chi tiết hồ sơ — ${record.code || ''}`,
        body: infoHTML + transHTML + histHTML,
        size: 'lg'
      });

      // Gắn event listener cho nút đổi trạng thái
      setTimeout(() => {
        document.querySelectorAll('[data-change-status]').forEach(btn => {
          btn.addEventListener('click', async function () {
            const newStatus = this.dataset.changeStatus;
            const rId = this.dataset.recordId;
            try {
              await CRM.API.put('/api/records/' + rId, { status: newStatus });
              CRM.Toast.success('Đã cập nhật trạng thái thành ' + CRM.Utils.getStatusLabel(newStatus));
              CRM.Modal.close();
              fetchRecords();
            } catch (e) {
              CRM.Toast.error('Lỗi cập nhật trạng thái');
            }
          });
        });
      }, 100);

    } catch (err) {
      console.error('[Records] Lỗi tải chi tiết:', err);
      CRM.Toast.error('Không thể tải chi tiết hồ sơ');
      CRM.Modal.close();
    }
  }

  // ── Form thêm/sửa hồ sơ ─────────────────────────────────────

  async function showFormModal(record) {
    const isEdit = !!record;
    const title = isEdit ? 'Sửa hồ sơ — ' + (record.code || '') : 'Thêm hồ sơ mới';

    // Đảm bảo đã load customers & users
    await loadDropdownData();

    const formHTML = `
      <form id="record-form">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Loại hồ sơ <span style="color:#ef4444;">*</span></label>
            <select class="form-control" name="type" required>
              ${buildTypeOptions(isEdit ? record.type : '')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Khách hàng <span style="color:#ef4444;">*</span></label>
            <select class="form-control" name="customer_id" required>
              ${buildCustomerOptions(isEdit ? record.customer_id : '')}
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Ngày nhận <span style="color:#ef4444;">*</span></label>
            <input type="date" class="form-control" name="received_date" value="${isEdit && record.received_date ? record.received_date.slice(0, 10) : ''}" required>
          </div>
          <div class="form-group">
            <label class="form-label">Hạn nộp</label>
            <input type="date" class="form-control" name="deadline" value="${isEdit && record.deadline ? record.deadline.slice(0, 10) : ''}">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Người phụ trách</label>
            <select class="form-control" name="assigned_to">
              ${buildUserOptions(isEdit ? record.assigned_to : '', false)}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Phí dịch vụ</label>
            <input type="number" class="form-control" name="fee_service" value="${isEdit ? (record.fee_service || 0) : ''}" min="0" placeholder="0">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Phí nhà nước</label>
            <input type="number" class="form-control" name="fee_state" value="${isEdit ? (record.fee_state || 0) : ''}" min="0" placeholder="0">
          </div>
          <div class="form-group"></div>
        </div>
        <div class="form-group">
          <label class="form-label">Ghi chú</label>
          <textarea class="form-control" name="notes" rows="3" placeholder="Nhập ghi chú...">${isEdit ? (record.notes || '') : ''}</textarea>
        </div>
      </form>
    `;

    CRM.Modal.show({
      title,
      body: formHTML,
      footer: `
        <button class="btn btn-secondary" id="btn-record-cancel">Hủy</button>
        <button class="btn btn-primary" id="btn-record-save"><i class="fas fa-save" style="margin-right:6px;"></i>${isEdit ? 'Cập nhật' : 'Tạo mới'}</button>
      `,
      size: 'lg'
    });

    // Event listeners cho form
    setTimeout(() => {
      const btnCancel = document.getElementById('btn-record-cancel');
      const btnSave = document.getElementById('btn-record-save');

      if (btnCancel) btnCancel.addEventListener('click', () => CRM.Modal.close());
      if (btnSave) btnSave.addEventListener('click', () => handleFormSubmit(isEdit ? record.id : null));
    }, 100);
  }

  async function handleFormSubmit(recordId) {
    const form = document.getElementById('record-form');
    if (!form) return;

    const formData = new FormData(form);
    const body = {};
    formData.forEach((val, key) => {
      if (key === 'fee_service' || key === 'fee_state') {
        body[key] = val ? parseFloat(val) : 0;
      } else if (key === 'assigned_to' || key === 'customer_id') {
        body[key] = val ? parseInt(val) : null;
      } else {
        body[key] = val || null;
      }
    });

    // Validate
    if (!body.type) { CRM.Toast.warning('Vui lòng chọn loại hồ sơ'); return; }
    if (!body.customer_id) { CRM.Toast.warning('Vui lòng chọn khách hàng'); return; }
    if (!body.received_date) { CRM.Toast.warning('Vui lòng nhập ngày nhận'); return; }

    try {
      if (recordId) {
        await CRM.API.put('/api/records/' + recordId, body);
        CRM.Toast.success('Đã cập nhật hồ sơ thành công');
      } else {
        await CRM.API.post('/api/records', body);
        CRM.Toast.success('Đã tạo hồ sơ mới thành công');
      }
      CRM.Modal.close();
      fetchRecords();
    } catch (err) {
      console.error('[Records] Lỗi lưu hồ sơ:', err);
      CRM.Toast.error(err.message || 'Lỗi lưu hồ sơ');
    }
  }

  // ── Xóa hồ sơ ───────────────────────────────────────────────

  function confirmDelete(record) {
    CRM.Modal.confirm({
      title: 'Xóa hồ sơ',
      message: `Bạn có chắc muốn xóa hồ sơ <strong>${record.code || ''}</strong>?<br><span style="color:var(--text-secondary); font-size:13px;">Hành động này không thể hoàn tác.</span>`,
      confirmText: 'Xóa',
      confirmClass: 'btn-danger',
      onConfirm: async () => {
        try {
          await CRM.API.delete('/api/records/' + record.id);
          CRM.Toast.success('Đã xóa hồ sơ ' + (record.code || ''));
          fetchRecords();
        } catch (err) {
          CRM.Toast.error('Lỗi xóa hồ sơ');
        }
      }
    });
  }

  // ── Load dữ liệu cho dropdown ───────────────────────────────

  async function loadDropdownData() {
    try {
      if (_users.length === 0) {
        const uResult = await CRM.API.get('/api/users');
        _users = uResult.data || uResult || [];
      }
    } catch (e) {
      console.warn('[Records] Không tải được danh sách users:', e);
    }

    try {
      if (_customers.length === 0) {
        const cResult = await CRM.API.get('/api/customers/all/list');
        _customers = cResult.data || cResult || [];
      }
    } catch (e) {
      console.warn('[Records] Không tải được danh sách khách hàng:', e);
    }
  }

  // ── Gắn event listeners ──────────────────────────────────────

  function bindEvents() {
    const container = document.getElementById('page-content');
    if (!container) return;

    // Search debounce
    const searchInput = document.getElementById('records-search');
    if (searchInput) {
      _debounceSearch = CRM.Utils.debounce(() => {
        _filters.search = searchInput.value.trim();
        _pagination.page = 1;
        fetchRecords();
      }, 300);
      searchInput.addEventListener('input', _debounceSearch);
    }

    // Filter: type
    const filterType = document.getElementById('records-filter-type');
    if (filterType) {
      filterType.addEventListener('change', () => {
        _filters.type = filterType.value;
        _pagination.page = 1;
        fetchRecords();
      });
    }

    // Filter: status
    const filterStatus = document.getElementById('records-filter-status');
    if (filterStatus) {
      filterStatus.addEventListener('change', () => {
        _filters.status = filterStatus.value;
        _pagination.page = 1;
        fetchRecords();
      });
    }

    // Filter: user
    const filterUser = document.getElementById('records-filter-user');
    if (filterUser) {
      filterUser.addEventListener('change', () => {
        _filters.assigned_to = filterUser.value;
        _pagination.page = 1;
        fetchRecords();
      });
    }

    // Filter: date from
    const filterFrom = document.getElementById('records-filter-from');
    if (filterFrom) {
      filterFrom.addEventListener('change', () => {
        _filters.date_from = filterFrom.value;
        _pagination.page = 1;
        fetchRecords();
      });
    }

    // Filter: date to
    const filterTo = document.getElementById('records-filter-to');
    if (filterTo) {
      filterTo.addEventListener('change', () => {
        _filters.date_to = filterTo.value;
        _pagination.page = 1;
        fetchRecords();
      });
    }

    // Nút thêm hồ sơ
    const btnAdd = document.getElementById('btn-add-record');
    if (btnAdd) {
      btnAdd.addEventListener('click', () => showFormModal(null));
    }
  }

  // ── Page Module ──────────────────────────────────────────────

  CRM.Pages = CRM.Pages || {};
  CRM.Pages.Records = {

    /**
     * Render trang quản lý hồ sơ
     */
    async render() {
      CRM.App.setPageTitle('Hồ sơ', 'Quản lý hồ sơ ĐKKD');

      const container = document.getElementById('page-content');
      if (!container) return;

      // Loading
      container.innerHTML = `
        <div class="loading-spinner" style="display:flex; align-items:center; justify-content:center; min-height:400px; flex-direction:column; gap:16px;">
          <div style="width:48px; height:48px; border: 3px solid var(--border-color); border-top-color: var(--accent-primary); border-radius:50%; animation: spin 0.8s linear infinite;"></div>
          <span style="color:var(--text-secondary); font-size:14px;">Đang tải dữ liệu...</span>
        </div>`;

      // Reset state
      _filters = { search: '', type: '', status: '', assigned_to: '', date_from: '', date_to: '' };
      _pagination = { page: 1, per_page: 20, total: 0, total_pages: 0 };

      // Load dropdown data
      await loadDropdownData();

      // Render page structure
      container.innerHTML = buildPageHTML();

      // Populate user filter dropdown (đã có data)
      const filterUser = document.getElementById('records-filter-user');
      if (filterUser) {
        filterUser.innerHTML = buildUserOptions('', true);
      }

      // Bind events
      bindEvents();

      // Fetch data lần đầu
      await fetchRecords();
    },

    /**
     * Dọn dẹp khi rời trang
     */
    destroy() {
      _debounceSearch = null;
      _users = [];
      _customers = [];
    }
  };

})();
