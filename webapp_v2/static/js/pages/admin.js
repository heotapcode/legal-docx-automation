/**
 * Trang quản trị mẫu (Mục 10) — #/admin.
 * Bước 10.1: đăng nhập / đăng xuất. Các bước sau thêm quản lý bộ mẫu vào renderAdminHome().
 * Mọi yêu cầu thay đổi dữ liệu gửi kèm header X-Requested-With: nac-admin (chống CSRF, xem services/auth.py).
 */
(function () {
    'use strict';

    const CSRF = { 'X-Requested-With': 'nac-admin' };

    async function adminFetch(url, options) {
        const opts = Object.assign({ credentials: 'same-origin' }, options || {});
        opts.headers = Object.assign({}, CSRF, opts.headers || {});
        const res = await fetch(url, opts);
        let body = null;
        try { body = await res.json(); } catch (e) { body = null; }
        return { ok: res.ok, status: res.status, body };
    }

    function shell(inner) {
        return `
            <nav class="navbar scrolled">
                <div class="container navbar-container">
                    <a href="#/" class="navbar-brand"><i class="fa-solid fa-building text-gradient"></i> NAC</a>
                    <div class="navbar-menu"><a href="#/wizard">Tạo hồ sơ</a></div>
                    <span class="text-secondary text-sm">Quản trị mẫu</span>
                </div>
            </nav>
            <section class="section" style="padding-top: var(--space-24);">
                <div class="container" style="max-width: 720px;">
                    <div id="admin-root">${inner}</div>
                </div>
            </section>`;
    }

    function loginForm(message) {
        return `
            <div class="card">
                <h1 class="text-2xl font-bold mb-4">Đăng nhập quản trị</h1>
                <form id="admin-login-form" autocomplete="on">
                    <div class="form-group">
                        <label class="form-label" for="admin-username">Tên đăng nhập</label>
                        <input id="admin-username" name="username" class="form-control" autocomplete="username" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="admin-password">Mật khẩu</label>
                        <input id="admin-password" name="password" type="password" class="form-control"
                               autocomplete="current-password" required>
                    </div>
                    <div id="admin-login-error" class="text-error text-sm mb-2">${message ? escapeHtml(message) : ''}</div>
                    <button type="submit" class="btn btn-primary">Đăng nhập</button>
                </form>
                <p class="text-xs text-secondary mt-4">
                    Tài khoản được tạo trên máy chủ bằng lệnh <code>python -m tools.admin_user create &lt;tên&gt;</code>.
                </p>
            </div>`;
    }

    function renderAdminHome(user) {
        return `
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px;">
                    <h1 class="text-2xl font-bold">Quản trị mẫu</h1>
                    <div class="text-sm">
                        <span class="text-secondary">Đăng nhập:</span> <b id="admin-current-user">${escapeHtml(user.username)}</b>
                        <button type="button" id="admin-logout" class="btn btn-secondary btn-sm" style="margin-left: 8px;">Đăng xuất</button>
                    </div>
                </div>
                <p class="text-secondary mt-4">Chức năng tải mẫu mới, xem phiên bản và quay lại bản cũ sẽ có ở các bước tiếp theo.</p>
            </div>`;
    }

    function root() { return document.getElementById('admin-root'); }

    function showLogin(message) {
        root().innerHTML = loginForm(message);
        document.getElementById('admin-login-form').addEventListener('submit', async ev => {
            ev.preventDefault();
            const r = await adminFetch('/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: document.getElementById('admin-username').value,
                    password: document.getElementById('admin-password').value,
                }),
            });
            if (r.ok) showHome(r.body);
            else showLogin((r.body && r.body.detail) || 'Đăng nhập thất bại');
        });
    }

    function showHome(user) {
        root().innerHTML = renderAdminHome(user);
        document.getElementById('admin-logout').addEventListener('click', async () => {
            await adminFetch('/api/admin/logout', { method: 'POST' });
            showLogin();
        });
    }

    window.renderAdmin = function () { return shell('<div class="card text-secondary">Đang tải...</div>'); };

    window.initAdmin = async function () {
        const r = await adminFetch('/api/admin/me');
        if (r.ok) showHome(r.body);
        else showLogin();
    };

    window.adminFetch = adminFetch;
})();
