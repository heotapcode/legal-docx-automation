/**
 * customers.js - Trang quản lý khách hàng
 */
window.CRM = window.CRM || {};
CRM.Pages = CRM.Pages || {};

CRM.Pages.Customers = (() => {
  let currentPage = 1;
  let currentFilters = { search: '', business_type: '' };

  function render() {
    CRM.App.setPageTitle('Khách hàng', 'Quản lý khách hàng');
    const content = document.getElementById('page-content');
    content.innerHTML = `
      <div class="toolbar">
        <div class="toolbar-left">
          <div class="search-bar">
            <i class="fa-solid fa-search search-icon"></i>
            <input type="text" class="form-control" id="cust-search" placeholder="Tìm theo tên, MST, SĐT...">
          </div>
          <select class="form-control" id="cust-filter-type" style="width:180px">
            ${CRM.Utils.buildOptions(CRM.Utils.BUSINESS_TYPES)}
          </select>
        </div>
        <div class="toolbar-right">
          <button class="btn btn-primary" id="cust-add-btn"><i class="fa-solid fa-plus"></i> Thêm KH</button>
        </div>
      </div>
      <div class="card">
        <div class="card-body no-padding" id="cust-table-container">
          <div class="loading-container"><div class="spinner spinner-lg"></div></div>
        </div>
      </div>
    `;

    // Event listeners
    document.getElementById('cust-search').addEventListener('input', CRM.Utils.debounce(e => {
      currentFilters.search = e.target.value;
      currentPage = 1;
      loadData();
    }));
    document.getElementById('cust-filter-type').addEventListener('change', e => {
      currentFilters.business_type = e.target.value;
      currentPage = 1;
      loadData();
    });
    document.getElementById('cust-add-btn').addEventListener('click', () => showForm());

    loadData();
  }

  async function loadData() {
    try {
      const params = new URLSearchParams({
        page: currentPage, per_page: 15,
        search: currentFilters.search,
        business_type: currentFilters.business_type
      });
      const res = await CRM.API.get(`/api/customers?${params}`);

      CRM.Table.render('cust-table-container', {
        columns: [
          { key: 'code', label: 'Mã KH', width: '100px' },
          { key: 'company_name', label: 'Tên công ty', render: (v, r) => CRM.Utils.escapeHtml(v || r.personal_name || '—') },
          { key: 'tax_code', label: 'MST', render: v => v || '—' },
          { key: 'business_type', label: 'Loại hình', render: v => CRM.Utils.getBusinessTypeBadge(v) },
          { key: 'representative', label: 'Người đại diện', render: v => CRM.Utils.escapeHtml(v || '—') },
          { key: 'phone', label: 'SĐT', render: v => v || '—' },
          { key: 'email', label: 'Email', render: v => v || '—' }
        ],
        data: res.data,
        actions: [
          { icon: 'fa-eye', label: 'Xem', className: 'btn-secondary', onClick: (row) => showDetail(row.id) },
          { icon: 'fa-pen', label: 'Sửa', className: 'btn-secondary', onClick: (row) => showForm(row) },
          { icon: 'fa-trash', label: 'Xóa', className: 'btn-danger', onClick: (row) => deleteCustomer(row) }
        ],
        pagination: res.pagination,
        onPageChange: (p) => { currentPage = p; loadData(); },
        emptyMessage: 'Chưa có khách hàng nào',
        emptyIcon: 'fa-users'
      });
    } catch (err) {
      CRM.Toast.error(err.message);
    }
  }

  function showForm(customer = null) {
    const isEdit = !!customer;
    const c = customer || {};

    CRM.Modal.show({
      title: isEdit ? 'Sửa khách hàng' : 'Thêm khách hàng mới',
      size: 'lg',
      body: `
        <form id="cust-form">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Tên công ty <span class="required">*</span></label>
              <input type="text" class="form-control" id="cf-company" value="${CRM.Utils.escapeHtml(c.company_name || '')}" required>
            </div>
            <div class="form-group">
              <label class="form-label">Tên cá nhân</label>
              <input type="text" class="form-control" id="cf-personal" value="${CRM.Utils.escapeHtml(c.personal_name || '')}">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Mã số thuế</label>
              <input type="text" class="form-control" id="cf-tax" value="${c.tax_code || ''}">
            </div>
            <div class="form-group">
              <label class="form-label">Loại hình DN <span class="required">*</span></label>
              <select class="form-control" id="cf-type" required>
                ${CRM.Utils.buildOptions(CRM.Utils.BUSINESS_TYPES, c.business_type || '', '-- Chọn --')}
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Địa chỉ</label>
            <input type="text" class="form-control" id="cf-address" value="${CRM.Utils.escapeHtml(c.address || '')}">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Người đại diện</label>
              <input type="text" class="form-control" id="cf-rep" value="${CRM.Utils.escapeHtml(c.representative || '')}">
            </div>
            <div class="form-group">
              <label class="form-label">Chức vụ</label>
              <input type="text" class="form-control" id="cf-pos" value="${CRM.Utils.escapeHtml(c.position || '')}">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Số điện thoại</label>
              <input type="text" class="form-control" id="cf-phone" value="${c.phone || ''}">
            </div>
            <div class="form-group">
              <label class="form-label">Email</label>
              <input type="email" class="form-control" id="cf-email" value="${c.email || ''}">
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Ghi chú</label>
            <textarea class="form-control" id="cf-notes" rows="3">${CRM.Utils.escapeHtml(c.notes || '')}</textarea>
          </div>
        </form>
      `,
      footer: `
        <button class="btn btn-secondary" onclick="CRM.Modal.close()">Hủy</button>
        <button class="btn btn-primary" id="cust-save-btn"><i class="fa-solid fa-check"></i> ${isEdit ? 'Cập nhật' : 'Tạo mới'}</button>
      `
    });

    setTimeout(() => {
      document.getElementById('cust-save-btn').addEventListener('click', async () => {
        const data = {
          company_name: document.getElementById('cf-company').value.trim(),
          personal_name: document.getElementById('cf-personal').value.trim(),
          tax_code: document.getElementById('cf-tax').value.trim(),
          business_type: document.getElementById('cf-type').value,
          address: document.getElementById('cf-address').value.trim(),
          representative: document.getElementById('cf-rep').value.trim(),
          position: document.getElementById('cf-pos').value.trim(),
          phone: document.getElementById('cf-phone').value.trim(),
          email: document.getElementById('cf-email').value.trim(),
          notes: document.getElementById('cf-notes').value.trim()
        };

        if (!data.company_name) { CRM.Toast.warning('Vui lòng nhập tên công ty'); return; }
        if (!data.business_type) { CRM.Toast.warning('Vui lòng chọn loại hình DN'); return; }

        try {
          if (isEdit) {
            await CRM.API.put(`/api/customers/${customer.id}`, data);
            CRM.Toast.success('Cập nhật khách hàng thành công');
          } else {
            await CRM.API.post('/api/customers', data);
            CRM.Toast.success('Thêm khách hàng thành công');
          }
          CRM.Modal.close();
          loadData();
        } catch (err) { CRM.Toast.error(err.message); }
      });
    }, 50);
  }

  async function showDetail(id) {
    try {
      const res = await CRM.API.get(`/api/customers/${id}`);
      const c = res.data;
      const records = res.records || [];
      const transactions = res.transactions || [];

      let recordsHtml = records.length > 0
        ? `<table class="data-table"><thead><tr><th>Mã HS</th><th>Loại</th><th>Trạng thái</th><th>Ngày nhận</th></tr></thead><tbody>
            ${records.map(r => `<tr><td>${r.code}</td><td>${CRM.Utils.getRecordTypeLabel(r.type)}</td><td>${CRM.Utils.getStatusBadge(r.status)}</td><td>${CRM.Utils.formatDate(r.received_date)}</td></tr>`).join('')}
           </tbody></table>`
        : '<div class="empty-state" style="padding:24px"><i class="fa-solid fa-folder-open empty-state-icon" style="font-size:28px"></i><div class="text-muted mt-1">Chưa có hồ sơ</div></div>';

      let txHtml = transactions.length > 0
        ? `<table class="data-table"><thead><tr><th>Mã GD</th><th>Loại</th><th>Danh mục</th><th>Số tiền</th><th>TT</th></tr></thead><tbody>
            ${transactions.map(t => `<tr><td>${t.code}</td><td>${t.type === 'thu' ? '<span class="badge badge-success">Thu</span>' : '<span class="badge badge-danger">Chi</span>'}</td><td>${CRM.Utils.getCategoryLabel(t.category)}</td><td>${CRM.Utils.formatCurrency(t.amount)}</td><td>${CRM.Utils.getPaymentBadge(t.payment_status)}</td></tr>`).join('')}
           </tbody></table>`
        : '<div class="empty-state" style="padding:24px"><i class="fa-solid fa-money-bill-wave empty-state-icon" style="font-size:28px"></i><div class="text-muted mt-1">Chưa có giao dịch</div></div>';

      CRM.Modal.show({
        title: `Khách hàng: ${c.code}`,
        size: 'lg',
        body: `
          <div class="detail-grid mb-4">
            <div class="detail-item"><div class="detail-label">Tên công ty</div><div class="detail-value">${CRM.Utils.escapeHtml(c.company_name || '—')}</div></div>
            <div class="detail-item"><div class="detail-label">MST</div><div class="detail-value">${c.tax_code || '—'}</div></div>
            <div class="detail-item"><div class="detail-label">Loại hình</div><div class="detail-value">${CRM.Utils.getBusinessTypeBadge(c.business_type)}</div></div>
            <div class="detail-item"><div class="detail-label">Người đại diện</div><div class="detail-value">${CRM.Utils.escapeHtml(c.representative || '—')}</div></div>
            <div class="detail-item"><div class="detail-label">SĐT</div><div class="detail-value">${c.phone || '—'}</div></div>
            <div class="detail-item"><div class="detail-label">Email</div><div class="detail-value">${c.email || '—'}</div></div>
            <div class="detail-item" style="grid-column:1/-1"><div class="detail-label">Địa chỉ</div><div class="detail-value">${CRM.Utils.escapeHtml(c.address || '—')}</div></div>
          </div>
          <div class="summary-row">
            <div class="summary-item"><div class="summary-item-value text-success">${CRM.Utils.formatCurrency(res.total_revenue || 0)}</div><div class="summary-item-label">Tổng thu</div></div>
            <div class="summary-item"><div class="summary-item-value text-danger">${CRM.Utils.formatCurrency(res.total_expense || 0)}</div><div class="summary-item-label">Tổng chi</div></div>
            <div class="summary-item"><div class="summary-item-value text-warning">${CRM.Utils.formatCurrency(res.debt || 0)}</div><div class="summary-item-label">Công nợ</div></div>
          </div>
          <div class="divider"></div>
          <div class="section-title"><i class="fa-solid fa-folder-open"></i> Hồ sơ liên quan (${records.length})</div>
          <div class="table-container mb-3">${recordsHtml}</div>
          <div class="section-title"><i class="fa-solid fa-money-bill-wave"></i> Giao dịch (${transactions.length})</div>
          <div class="table-container">${txHtml}</div>
        `
      });
    } catch (err) { CRM.Toast.error(err.message); }
  }

  function deleteCustomer(customer) {
    CRM.Modal.confirm({
      title: 'Xóa khách hàng',
      message: `Bạn có chắc muốn xóa khách hàng <strong>${CRM.Utils.escapeHtml(customer.company_name || customer.code)}</strong>? Thao tác này không thể hoàn tác.`,
      onConfirm: async () => {
        try {
          await CRM.API.delete(`/api/customers/${customer.id}`);
          CRM.Toast.success('Đã xóa khách hàng');
          loadData();
        } catch (err) { CRM.Toast.error(err.message); }
      }
    });
  }

  function destroy() {}

  return { render, destroy };
})();
