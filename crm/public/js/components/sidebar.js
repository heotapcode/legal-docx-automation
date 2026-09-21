/**
 * sidebar.js - Component sidebar điều hướng
 */
window.CRM = window.CRM || {};

CRM.Sidebar = (() => {
  const menuItems = [
    { id: 'dashboard', icon: 'fa-chart-pie', label: 'Dashboard' },
    { id: 'records', icon: 'fa-folder-open', label: 'Hồ sơ' },
    { id: 'customers', icon: 'fa-users', label: 'Khách hàng' },
    { id: 'finance', icon: 'fa-money-bill-wave', label: 'Thu/Chi' },
    { id: 'reports', icon: 'fa-chart-bar', label: 'Báo cáo' },
    { id: 'settings', icon: 'fa-gear', label: 'Cài đặt' }
  ];

  function init() {
    render();
    // Mobile toggle
    const toggle = document.querySelector('.sidebar-toggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('mobile-open');
        document.querySelector('.sidebar-overlay').classList.toggle('show');
      });
    }
  }

  function render() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    const user = CRM.Store.getUser() || {};
    const initial = (user.full_name || 'U').charAt(0).toUpperCase();

    let navHtml = '';
    menuItems.forEach(item => {
      navHtml += `
        <div class="sidebar-nav-item" data-page="${item.id}">
          <i class="fa-solid ${item.icon}"></i>
          <span>${item.label}</span>
        </div>
      `;
    });

    sidebar.innerHTML = `
      <div class="sidebar-logo">
        <div class="sidebar-logo-icon">NAC</div>
        <h1>NAC CRM</h1>
        <div class="company-sub">Quản lý Hồ sơ ĐKKD</div>
      </div>
      <nav class="sidebar-nav">${navHtml}</nav>
      <div class="sidebar-user">
        <div class="avatar" style="background:${user.avatar_color || '#667eea'}">${initial}</div>
        <div class="sidebar-user-info">
          <div class="sidebar-user-name">${CRM.Utils.escapeHtml(user.full_name || 'User')}</div>
          <div class="sidebar-user-role">${user.role === 'admin' ? 'Quản trị viên' : 'Nhân viên'}</div>
        </div>
        <button class="sidebar-logout" title="Đăng xuất" id="sidebar-logout">
          <i class="fa-solid fa-right-from-bracket"></i>
        </button>
      </div>
    `;

    // Nav click handlers
    sidebar.querySelectorAll('.sidebar-nav-item').forEach(item => {
      item.addEventListener('click', () => {
        const page = item.dataset.page;
        CRM.Router.navigate(page);
        // Close mobile menu
        sidebar.classList.remove('mobile-open');
        const overlay = document.querySelector('.sidebar-overlay');
        if (overlay) overlay.classList.remove('show');
      });
    });

    // Logout
    const logoutBtn = document.getElementById('sidebar-logout');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => CRM.Auth.logout());
    }
  }

  function setActive(pageId) {
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.page === pageId);
    });
  }

  return { init, render, setActive };
})();
