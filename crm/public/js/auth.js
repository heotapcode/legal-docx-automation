/**
 * auth.js - Xử lý đăng nhập / đăng xuất
 */
window.CRM = window.CRM || {};

CRM.Auth = (() => {
  function init() {
    if (CRM.Store.isLoggedIn()) {
      showApp();
    } else {
      renderLogin();
    }
  }

  function renderLogin() {
    document.getElementById('main-app').style.display = 'none';
    const loginScreen = document.getElementById('login-screen');
    loginScreen.style.display = 'flex';

    loginScreen.innerHTML = `
      <div class="login-card">
        <div class="login-logo">
          <div class="login-logo-icon">NAC</div>
          <div class="login-title">NAC CRM</div>
          <div class="login-subtitle">Công ty TNHH Dịch vụ Tư Vấn NAC</div>
        </div>
        <div class="login-error" id="login-error"></div>
        <form class="login-form" id="login-form">
          <div class="form-group">
            <label class="form-label">Tên đăng nhập</label>
            <input type="text" class="form-control" id="login-username" placeholder="Nhập tên đăng nhập" autocomplete="username" required>
          </div>
          <div class="form-group">
            <label class="form-label">Mật khẩu</label>
            <input type="password" class="form-control" id="login-password" placeholder="Nhập mật khẩu" autocomplete="current-password" required>
          </div>
          <button type="submit" class="btn btn-primary login-btn" id="login-btn">
            <span class="spinner"></span>
            <span class="btn-text">Đăng nhập</span>
          </button>
        </form>
        <div style="margin-top:20px;text-align:center;font-size:12px;color:var(--text-muted)">
          Demo: <strong>admin</strong> / <strong>admin123</strong>
        </div>
      </div>
    `;

    document.getElementById('login-form').addEventListener('submit', handleLoginSubmit);
  }

  async function handleLoginSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    const btn = document.getElementById('login-btn');

    if (!username || !password) {
      errorEl.textContent = 'Vui lòng nhập đầy đủ thông tin';
      errorEl.classList.add('show');
      return;
    }

    btn.classList.add('loading');
    btn.disabled = true;
    errorEl.classList.remove('show');

    try {
      const res = await CRM.API.post('/api/auth/login', { username, password });
      CRM.Store.setToken(res.data.token);
      CRM.Store.setUser(res.data.user);
      showApp();
    } catch (err) {
      errorEl.textContent = err.message || 'Đăng nhập thất bại';
      errorEl.classList.add('show');
    } finally {
      btn.classList.remove('loading');
      btn.disabled = false;
    }
  }

  function showApp() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('main-app').style.display = 'flex';
    CRM.App.renderLayout();
  }

  function logout() {
    CRM.Modal.confirm({
      title: 'Đăng xuất',
      message: 'Bạn có chắc muốn đăng xuất khỏi hệ thống?',
      confirmText: 'Đăng xuất',
      onConfirm: () => {
        CRM.Store.removeToken();
        CRM.Store.removeUser();
        CRM.Notification.destroy();
        renderLogin();
      }
    });
  }

  return { init, renderLogin, logout };
})();
