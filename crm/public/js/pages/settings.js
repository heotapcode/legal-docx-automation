/**
 * settings.js - Trang cài đặt hệ thống
 */
window.CRM = window.CRM || {};
CRM.Pages = CRM.Pages || {};

CRM.Pages.Settings = (() => {
  function render() {
    CRM.App.setPageTitle('Cài đặt', 'Cài đặt hệ thống');
    const isAdmin = CRM.Store.isAdmin();
    const content = document.getElementById('page-content');

    content.innerHTML = `
      <!-- Thông tin công ty -->
      <div class="card mb-4">
        <div class="card-header"><div class="card-title"><i class="fa-solid fa-building"></i> Thông tin công ty</div></div>
        <div class="card-body">
          <div class="detail-grid">
            <div class="detail-item"><div class="detail-label">Tên công ty</div><div class="detail-value">Công ty TNHH Dịch vụ Tư Vấn NAC</div></div>
            <div class="detail-item"><div class="detail-label">Hệ thống</div><div class="detail-value">NAC CRM v1.0</div></div>
          </div>
        </div>
      </div>

      ${isAdmin ? `
      <!-- Quản lý người dùng -->
      <div class="card mb-4">
        <div class="card-header">
          <div class="card-title"><i class="fa-solid fa-users-gear"></i> Quản lý người dùng</div>
          <button class="btn btn-primary btn-sm" id="add-user-btn"><i class="fa-solid fa-plus"></i> Thêm user</button>
        </div>
        <div class="card-body no-padding" id="users-table">
          <div class="loading-container"><div class="spinner spinner-lg"></div></div>
        </div>
      </div>
      ` : ''}

      <!-- Sao lưu & Khôi phục -->
      <div class="card mb-4">
        <div class="card-header"><div class="card-title"><i class="fa-solid fa-database"></i> Sao lưu & Khôi phục</div></div>
        <div class="card-body">
          <p class="text-secondary mb-3" style="font-size:13px">Xuất toàn bộ dữ liệu ra file JSON để backup, hoặc nhập lại dữ liệu từ file backup.</p>
          <div class="flex gap-2 flex-wrap">
            <button class="btn btn-success" id="export-data-btn"><i class="fa-solid fa-download"></i> Xuất dữ liệu (JSON)</button>
            <button class="btn btn-warning" id="import-data-btn"><i class="fa-solid fa-upload"></i> Nhập dữ liệu (JSON)</button>
            <input type="file" id="import-file-input" accept=".json" style="display:none">
          </div>
          <div id="import-result" class="mt-2"></div>
        </div>
      </div>

      <!-- Danh mục chi phí -->
      <div class="card mb-4">
        <div class="card-header"><div class="card-title"><i class="fa-solid fa-tags"></i> Danh mục chi phí</div></div>
        <div class="card-body">
          <div class="detail-grid">
            ${Object.entries(CRM.Utils.TRANSACTION_CATEGORIES).map(([key, label]) => `
              <div class="detail-item"><div class="detail-label">${key}</div><div class="detail-value">${label}</div></div>
            `).join('')}
          </div>
          <p class="text-muted mt-2 text-sm">Các danh mục này được cấu hình sẵn trong hệ thống.</p>
        </div>
      </div>

      <!-- Loại hồ sơ -->
      <div class="card mb-4">
        <div class="card-header"><div class="card-title"><i class="fa-solid fa-list-check"></i> Loại hồ sơ ĐKKD</div></div>
        <div class="card-body">
          ${Object.entries(CRM.Utils.RECORD_TYPE_GROUPS).map(([group, types]) => `
            <div class="mb-3">
              <div class="text-bold mb-1" style="font-size:13px;color:var(--accent-primary)">${group}</div>
              <div class="flex gap-1 flex-wrap">
                ${types.map(t => `<span class="badge badge-primary" style="margin-bottom:4px">${CRM.Utils.getRecordTypeLabel(t)}</span>`).join('')}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Event listeners
    if (isAdmin) {
      document.getElementById('add-user-btn').addEventListener('click', () => showUserForm());
      loadUsers();
    }

    document.getElementById('export-data-btn').addEventListener('click', exportData);
    document.getElementById('import-data-btn').addEventListener('click', () => document.getElementById('import-file-input').click());
    document.getElementById('import-file-input').addEventListener('change', importData);
  }

  async function loadUsers() {
    try {
      const res = await CRM.API.get('/api/users');
      const currentUser = CRM.Store.getUser();

      CRM.Table.render('users-table', {
        columns: [
          { key: 'username', label: 'Username' },
          { key: 'full_name', label: 'Họ tên', render: v => CRM.Utils.escapeHtml(v) },
          { key: 'role', label: 'Vai trò', render: v => v === 'admin' ? '<span class="badge badge-purple">Admin</span>' : '<span class="badge badge-info">Nhân viên</span>' },
          { key: 'avatar_color', label: 'Màu', render: v => `<div style="width:24px;height:24px;border-radius:50%;background:${v}"></div>` },
          { key: 'created_at', label: 'Ngày tạo', render: v => CRM.Utils.formatDate(v) }
        ],
        data: res.data,
        actions: [
          { icon: 'fa-pen', label: 'Sửa', className: 'btn-secondary', onClick: (row) => showUserForm(row) },
          { icon: 'fa-trash', label: 'Xóa', className: 'btn-danger', onClick: (row) => {
            if (row.id === currentUser.id) { CRM.Toast.warning('Không thể xóa chính mình'); return; }
            CRM.Modal.confirm({
              title: 'Xóa người dùng',
              message: `Xóa user <strong>${CRM.Utils.escapeHtml(row.full_name)}</strong>?`,
              onConfirm: async () => {
                try {
                  await CRM.API.delete(`/api/users/${row.id}`);
                  CRM.Toast.success('Đã xóa người dùng');
                  loadUsers();
                } catch (e) { CRM.Toast.error(e.message); }
              }
            });
          }}
        ],
        emptyMessage: 'Chưa có người dùng'
      });
    } catch (err) { CRM.Toast.error(err.message); }
  }

  function showUserForm(user = null) {
    const isEdit = !!user;
    const u = user || {};
    const colors = ['#667eea','#764ba2','#f59e0b','#10b981','#ef4444','#3b82f6','#8b5cf6','#ec4899','#06b6d4','#84cc16'];
    const selectedColor = u.avatar_color || colors[0];

    CRM.Modal.show({
      title: isEdit ? 'Sửa người dùng' : 'Thêm người dùng',
      body: `
        <form id="user-form">
          <div class="form-group">
            <label class="form-label">Username <span class="required">*</span></label>
            <input type="text" class="form-control" id="uf-username" value="${u.username || ''}" ${isEdit ? 'disabled' : ''} required>
          </div>
          <div class="form-group">
            <label class="form-label">${isEdit ? 'Mật khẩu mới (bỏ trống nếu không đổi)' : 'Mật khẩu *'}</label>
            <input type="password" class="form-control" id="uf-password" ${isEdit ? '' : 'required'}>
          </div>
          <div class="form-group">
            <label class="form-label">Họ tên <span class="required">*</span></label>
            <input type="text" class="form-control" id="uf-name" value="${CRM.Utils.escapeHtml(u.full_name || '')}" required>
          </div>
          <div class="form-group">
            <label class="form-label">Vai trò</label>
            <select class="form-control" id="uf-role">
              <option value="employee" ${u.role === 'employee' ? 'selected' : ''}>Nhân viên</option>
              <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Màu avatar</label>
            <div class="color-picker-group" id="color-picker">
              ${colors.map(c => `
                <div class="color-picker-item ${c === selectedColor ? 'selected' : ''}" style="background:${c}" data-color="${c}">
                  <i class="fa-solid fa-check"></i>
                </div>
              `).join('')}
            </div>
            <input type="hidden" id="uf-color" value="${selectedColor}">
          </div>
        </form>
      `,
      footer: `
        <button class="btn btn-secondary" onclick="CRM.Modal.close()">Hủy</button>
        <button class="btn btn-primary" id="user-save-btn">${isEdit ? 'Cập nhật' : 'Tạo mới'}</button>
      `
    });

    setTimeout(() => {
      // Color picker
      document.querySelectorAll('#color-picker .color-picker-item').forEach(item => {
        item.addEventListener('click', () => {
          document.querySelectorAll('#color-picker .color-picker-item').forEach(i => i.classList.remove('selected'));
          item.classList.add('selected');
          document.getElementById('uf-color').value = item.dataset.color;
        });
      });

      // Save
      document.getElementById('user-save-btn').addEventListener('click', async () => {
        const data = {
          full_name: document.getElementById('uf-name').value.trim(),
          role: document.getElementById('uf-role').value,
          avatar_color: document.getElementById('uf-color').value
        };
        const password = document.getElementById('uf-password').value;

        if (!data.full_name) { CRM.Toast.warning('Vui lòng nhập họ tên'); return; }

        if (!isEdit) {
          data.username = document.getElementById('uf-username').value.trim();
          if (!data.username) { CRM.Toast.warning('Vui lòng nhập username'); return; }
          if (!password) { CRM.Toast.warning('Vui lòng nhập mật khẩu'); return; }
          data.password = password;
        } else if (password) {
          data.password = password;
        }

        try {
          if (isEdit) {
            await CRM.API.put(`/api/users/${user.id}`, data);
            CRM.Toast.success('Cập nhật thành công');
          } else {
            await CRM.API.post('/api/users', data);
            CRM.Toast.success('Tạo user thành công');
          }
          CRM.Modal.close();
          loadUsers();
        } catch (e) { CRM.Toast.error(e.message); }
      });
    }, 50);
  }

  async function exportData() {
    try {
      const res = await CRM.API.get('/api/data/export');
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nac_crm_backup_${new Date().toISOString().slice(0,10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      CRM.Toast.success('Đã xuất dữ liệu thành công');
    } catch (e) { CRM.Toast.error(e.message); }
  }

  async function importData(e) {
    const file = e.target.files[0];
    if (!file) return;

    CRM.Modal.confirm({
      title: 'Nhập dữ liệu',
      message: '⚠️ <strong>Cảnh báo:</strong> Dữ liệu hiện tại sẽ bị thay thế bằng dữ liệu từ file backup. Bạn có chắc chắn muốn tiếp tục?',
      confirmText: 'Nhập dữ liệu',
      confirmClass: 'btn-warning',
      onConfirm: async () => {
        try {
          const text = await file.text();
          const data = JSON.parse(text);
          const res = await CRM.API.post('/api/data/import', data);
          const stats = res.stats || {};
          document.getElementById('import-result').innerHTML = `
            <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);border-radius:8px;padding:12px;margin-top:12px">
              <div class="text-success text-bold mb-1">✅ Nhập dữ liệu thành công!</div>
              <div class="text-sm text-secondary">
                KH: ${stats.customers || 0} | HS: ${stats.records || 0} | GD: ${stats.transactions || 0}
              </div>
            </div>
          `;
          CRM.Toast.success('Nhập dữ liệu thành công');
        } catch (err) {
          CRM.Toast.error('Lỗi nhập dữ liệu: ' + err.message);
        }
      }
    });

    e.target.value = '';
  }

  function destroy() {}

  return { render, destroy };
})();
