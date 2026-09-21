/**
 * app.js - Entry point & Layout cho NAC CRM
 */
window.CRM = window.CRM || {};

CRM.App = (() => {
  function init() {
    CRM.Auth.init();
  }

  function renderLayout() {
    CRM.Sidebar.init();
    renderHeader();
    CRM.Notification.init();
    CRM.Router.init();
  }

  function renderHeader() {
    const header = document.getElementById('top-header');
    if (!header) return;

    const user = CRM.Store.getUser() || {};
    const initial = (user.full_name || 'U').charAt(0).toUpperCase();

    header.innerHTML = `
      <div class="header-left">
        <button class="sidebar-toggle"><i class="fa-solid fa-bars"></i></button>
        <div>
          <div class="header-title" id="header-title">Dashboard</div>
          <div class="header-subtitle" id="header-subtitle">Tổng quan hệ thống</div>
        </div>
      </div>
      <div class="header-right">
        <div class="notification-bell" onclick="CRM.Notification.toggle()">
          <i class="fa-solid fa-bell"></i>
          <span class="notification-badge" id="notif-badge" style="display:none">0</span>
          <div class="notification-dropdown"></div>
        </div>
        <div class="flex align-center gap-2">
          <div class="avatar" style="background:${user.avatar_color || '#667eea'}">${initial}</div>
          <span style="font-size:13px;font-weight:500;color:var(--text-secondary)">${CRM.Utils.escapeHtml(user.full_name || '')}</span>
        </div>
      </div>
    `;

    // Mobile sidebar toggle
    const toggle = header.querySelector('.sidebar-toggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('mobile-open');
        // Create or toggle overlay
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
          overlay = document.createElement('div');
          overlay.className = 'sidebar-overlay';
          document.body.appendChild(overlay);
          overlay.addEventListener('click', () => {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('show');
          });
        }
        overlay.classList.toggle('show');
      });
    }
  }

  function setPageTitle(title, subtitle = '') {
    const titleEl = document.getElementById('header-title');
    const subEl = document.getElementById('header-subtitle');
    if (titleEl) titleEl.textContent = title;
    if (subEl) subEl.textContent = subtitle;
  }

  function refreshNotifications() {
    CRM.Notification.refresh();
  }

  return { init, renderLayout, setPageTitle, refreshNotifications };
})();

// ── Bootstrap ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => CRM.App.init());
