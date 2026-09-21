/**
 * notification.js - Component chuông thông báo
 */
window.CRM = window.CRM || {};

CRM.Notification = (() => {
  let refreshInterval = null;
  let isOpen = false;

  function init() {
    refresh();
    refreshInterval = setInterval(refresh, 60000);
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.notification-bell') && !e.target.closest('.notification-dropdown')) {
        const dd = document.querySelector('.notification-dropdown');
        if (dd) { dd.classList.remove('show'); isOpen = false; }
      }
    });
  }

  async function refresh() {
    try {
      const res = await CRM.API.get('/api/notifications');
      updateBadge(res.unread_count || 0);
      if (isOpen) renderDropdown(res.data || []);
    } catch (e) { /* silent */ }
  }

  function updateBadge(count) {
    const badge = document.getElementById('notif-badge');
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
  }

  function toggle() {
    const dd = document.querySelector('.notification-dropdown');
    if (!dd) return;
    isOpen = !isOpen;
    if (isOpen) {
      dd.classList.add('show');
      loadNotifications();
    } else {
      dd.classList.remove('show');
    }
  }

  async function loadNotifications() {
    try {
      const res = await CRM.API.get('/api/notifications');
      renderDropdown(res.data || []);
    } catch (e) {
      console.error('Load notifications error:', e);
    }
  }

  function renderDropdown(notifications) {
    const dd = document.querySelector('.notification-dropdown');
    if (!dd) return;

    let html = `
      <div class="notification-dropdown-header">
        <h3>Thông báo</h3>
        <button class="btn btn-sm btn-secondary" id="mark-all-read">Đọc tất cả</button>
      </div>
    `;

    if (notifications.length === 0) {
      html += '<div class="notification-empty"><i class="fa-solid fa-bell-slash" style="font-size:24px;margin-bottom:8px;opacity:0.3"></i><br>Không có thông báo</div>';
    } else {
      notifications.forEach(n => {
        const iconClass = n.type === 'overdue' ? 'overdue' : n.type === 'deadline' ? 'deadline' : 'info';
        const iconName = n.type === 'overdue' ? 'fa-exclamation' : n.type === 'deadline' ? 'fa-clock' : 'fa-info';
        html += `
          <div class="notification-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
            <div class="notification-item-icon ${iconClass}"><i class="fa-solid ${iconName}"></i></div>
            <div class="notification-item-content">
              <div class="notification-item-title">${CRM.Utils.escapeHtml(n.title)}</div>
              <div class="notification-item-message">${CRM.Utils.escapeHtml(n.message)}</div>
              <div class="notification-item-time">${CRM.Utils.timeAgo(n.created_at)}</div>
            </div>
          </div>
        `;
      });
    }

    dd.innerHTML = html;

    // Mark all read
    const markAllBtn = document.getElementById('mark-all-read');
    if (markAllBtn) {
      markAllBtn.addEventListener('click', async () => {
        try {
          await CRM.API.put('/api/notifications/read-all');
          refresh();
        } catch (e) { CRM.Toast.error(e.message); }
      });
    }

    // Mark single read on click
    dd.querySelectorAll('.notification-item.unread').forEach(item => {
      item.addEventListener('click', async () => {
        try {
          await CRM.API.put(`/api/notifications/${item.dataset.id}/read`);
          item.classList.remove('unread');
          refresh();
        } catch (e) { /* silent */ }
      });
    });
  }

  function destroy() {
    if (refreshInterval) { clearInterval(refreshInterval); refreshInterval = null; }
  }

  return { init, refresh, toggle, destroy };
})();
