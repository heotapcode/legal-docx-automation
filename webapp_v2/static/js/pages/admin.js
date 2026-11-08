/**
 * Trang quản trị mẫu (Mục 10) — #/admin.
 *
 * Màn hình: đăng nhập -> danh sách bộ mẫu -> một bộ mẫu (phiên bản, bản nháp) -> một bản nháp
 * (file Word, _schema.json, quét mẫu, sinh thử, xuất bản). API: routes/admin_templates.py.
 *
 * Mọi yêu cầu thay đổi dữ liệu gửi kèm header X-Requested-With: nac-admin (chống CSRF, xem services/auth.py).
 * Nút bấm dùng data-action (không nhúng dữ liệu vào onclick), mọi chữ hiển thị đều qua escapeHtml.
 */
(function () {
    'use strict';

    const CSRF = { 'X-Requested-With': 'nac-admin' };
    const LEVEL_LABEL = { error: 'Lỗi', warning: 'Cảnh báo', info: 'Thông tin' };
    const SOURCE_LABEL = { initial: 'Bản ban đầu', publish: 'Xuất bản', rollback: 'Quay lại' };
    const st = { user: null, templateId: null, draftId: null };

    async function adminFetch(url, options) {
        const opts = Object.assign({ credentials: 'same-origin' }, options || {});
        opts.headers = Object.assign({}, CSRF, opts.headers || {});
        const res = await fetch(url, opts);
        let body = null;
        try { body = await res.json(); } catch (e) { body = null; }
        return { ok: res.ok, status: res.status, body };
    }

    function jsonBody(method, data) {
        return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) };
    }

    const e = s => escapeHtml(s === undefined || s === null ? '' : String(s));

    function root() { return document.getElementById('admin-root'); }

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
                <div class="container" style="max-width: 1000px;">
                    <div id="admin-root">${inner}</div>
                </div>
            </section>`;
    }

    function header(title, back) {
        return `
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;" class="mb-4">
                <div>
                    ${back ? `<button type="button" class="btn btn-secondary btn-sm" data-action="${back}">← Quay lại</button>` : ''}
                    <h1 class="text-2xl font-bold" style="display: inline-block; margin-left: 8px;">${e(title)}</h1>
                </div>
                <div class="text-sm">
                    <span class="text-secondary">Đăng nhập:</span> <b id="admin-current-user">${e(st.user.username)}</b>
                    <button type="button" class="btn btn-secondary btn-sm" data-action="logout" id="admin-logout" style="margin-left: 8px;">Đăng xuất</button>
                </div>
            </div>
            <div id="admin-message" class="text-sm mb-2"></div>`;
    }

    function message(text, isError) {
        const box = document.getElementById('admin-message');
        if (box) {
            box.className = 'text-sm mb-2 ' + (isError ? 'text-error' : 'text-success');
            box.textContent = text || '';
        }
    }

    function failed(r, fallback) {
        message((r.body && r.body.detail) || fallback || `Lỗi ${r.status}`, true);
        if (r.status === 401) showLogin('Phiên đăng nhập đã hết, vui lòng đăng nhập lại');
    }

    // ---------- Đăng nhập ----------

    function showLogin(msg) {
        st.user = null;
        root().innerHTML = `
            <div class="card" style="max-width: 520px; margin: 0 auto;">
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
                    <div id="admin-login-error" class="text-error text-sm mb-2">${msg ? e(msg) : ''}</div>
                    <button type="submit" class="btn btn-primary">Đăng nhập</button>
                </form>
                <p class="text-xs text-secondary mt-4">
                    Tài khoản được tạo trên máy chủ bằng lệnh <code>python -m tools.admin_user create &lt;tên&gt;</code>.
                </p>
            </div>`;
        document.getElementById('admin-login-form').addEventListener('submit', async ev => {
            ev.preventDefault();
            const r = await adminFetch('/api/admin/login', jsonBody('POST', {
                username: document.getElementById('admin-username').value,
                password: document.getElementById('admin-password').value,
            }));
            if (r.ok) { st.user = r.body; showTemplates(); }
            else showLogin((r.body && r.body.detail) || 'Đăng nhập thất bại');
        });
    }

    // ---------- Danh sách bộ mẫu ----------

    async function showTemplates() {
        st.templateId = st.draftId = null;
        const r = await adminFetch('/api/admin/templates');
        if (!r.ok) return failed(r);
        const rows = r.body.templates.map(t => `
            <tr>
                <td>${e(t.display_name)}<div class="text-xs text-secondary">${e(t.category)}</div></td>
                <td>v${e(t.version)}</td>
                <td>${e(t.files.length)} file</td>
                <td><button type="button" class="btn btn-secondary btn-sm" data-action="open-template" data-id="${e(t.id)}">Quản lý</button></td>
            </tr>`).join('');
        root().innerHTML = `
            <div class="card">
                ${header('Quản trị mẫu')}
                <table class="admin-table" id="admin-templates" style="width: 100%;">
                    <thead><tr><th>Bộ mẫu</th><th>Phiên bản</th><th>File</th><th></th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>`;
    }

    // ---------- Một bộ mẫu: phiên bản và bản nháp ----------

    async function showTemplate(templateId) {
        st.templateId = templateId;
        st.draftId = null;
        const [list, versions, drafts] = await Promise.all([
            adminFetch('/api/admin/templates'),
            adminFetch(`/api/admin/templates/${encodeURIComponent(templateId)}/versions`),
            adminFetch(`/api/admin/templates/${encodeURIComponent(templateId)}/drafts`),
        ]);
        if (!list.ok) return failed(list);
        const t = list.body.templates.find(x => x.id === templateId);
        if (!t) return showTemplates();
        const vRows = (versions.body.versions || []).map(v => `
            <tr data-version="${e(v.version)}">
                <td>v${e(v.version)}${v.current ? ' <span class="badge badge-green">đang dùng</span>' : ''}</td>
                <td>${e(SOURCE_LABEL[v.source] || v.source)}</td>
                <td>${e(v.note)}${v.legal_basis ? `<div class="text-xs text-secondary">Căn cứ: ${e(v.legal_basis)}</div>` : ''}
                    ${v.effective_from ? `<div class="text-xs text-secondary">Hiệu lực: ${e(v.effective_from)}</div>` : ''}</td>
                <td class="text-xs">${e(v.username || '')}<br>${e(v.created_at)}</td>
                <td>${v.current ? '' : `<button type="button" class="btn btn-secondary btn-sm" data-action="rollback" data-version="${e(v.version)}">Dùng lại bản này</button>`}</td>
            </tr>`).join('');
        const dRows = (drafts.body.drafts || []).map(d => `
            <li class="mb-2">Bản nháp từ v${e(d.base_version)} — ${e(d.username || '')}, ${e(d.created_at)}
                <button type="button" class="btn btn-secondary btn-sm" data-action="open-draft" data-id="${e(d.id)}">Mở</button>
            </li>`).join('');
        root().innerHTML = `
            <div class="card">
                ${header(t.display_name, 'back-templates')}
                <p class="text-secondary text-sm">Đang dùng phiên bản <b>v${e(t.version)}</b>, ${e(t.files.length)} file Word.</p>
                <h2 class="text-lg font-bold mt-4 mb-2">Bản nháp</h2>
                <ul id="admin-drafts">${dRows || '<li class="text-secondary text-sm">Chưa có bản nháp.</li>'}</ul>
                <button type="button" class="btn btn-primary btn-sm" data-action="new-draft">+ Tạo bản nháp từ bản đang dùng</button>
                <h2 class="text-lg font-bold mt-6 mb-2">Lịch sử phiên bản</h2>
                ${vRows ? `<table class="admin-table" id="admin-versions" style="width: 100%;">
                    <thead><tr><th>Phiên bản</th><th>Loại</th><th>Ghi chú</th><th>Người, thời gian</th><th></th></tr></thead>
                    <tbody>${vRows}</tbody></table>`
                    : '<p class="text-secondary text-sm" id="admin-versions">Chưa xuất bản lần nào từ trang quản trị (đang dùng bản trong mã nguồn, tính là v1).</p>'}
            </div>`;
    }

    // ---------- Một bản nháp ----------

    async function showDraft(draftId, note) {
        st.draftId = draftId;
        const r = await adminFetch(`/api/admin/drafts/${encodeURIComponent(draftId)}`);
        if (!r.ok) { failed(r); return showTemplate(st.templateId); }
        const d = r.body;
        st.templateId = d.template_id;
        const files = d.files.map(f => `
            <li class="mb-1">${e(f)}
                <button type="button" class="btn btn-secondary btn-sm" data-action="delete-file" data-name="${e(f)}">Xóa</button>
            </li>`).join('');
        root().innerHTML = `
            <div class="card">
                ${header(`Bản nháp: ${d.schema.display_name || d.template_id}`, 'back-template')}
                <p class="text-secondary text-sm">Tạo từ phiên bản v${e(d.base_version)}. Sửa bản nháp không ảnh hưởng bộ mẫu đang dùng cho tới khi xuất bản.</p>

                <h2 class="text-lg font-bold mt-4 mb-2">1. File Word</h2>
                <ul id="admin-draft-files">${files}</ul>
                <div class="form-group mt-2">
                    <label class="form-label" for="admin-upload">Tải lên file .docx (trùng tên thì thay file cũ)</label>
                    <input type="file" id="admin-upload" accept=".docx" multiple class="form-control">
                </div>

                <h2 class="text-lg font-bold mt-4 mb-2">2. Cấu hình form (_schema.json)</h2>
                <textarea id="admin-schema" class="form-control" rows="14" spellcheck="false"
                          style="font-family: monospace; font-size: 12px;">${e(JSON.stringify(d.schema, null, 2))}</textarea>
                <button type="button" class="btn btn-secondary btn-sm mt-2" data-action="save-schema">Lưu cấu hình</button>

                <h2 class="text-lg font-bold mt-4 mb-2">3. Kiểm tra</h2>
                <button type="button" class="btn btn-secondary btn-sm" data-action="lint">Quét mẫu</button>
                <button type="button" class="btn btn-secondary btn-sm" data-action="preview">Sinh thử (tải ZIP)</button>
                <div id="admin-lint" class="mt-2"></div>

                <h2 class="text-lg font-bold mt-4 mb-2">4. Xuất bản</h2>
                <form id="admin-publish-form">
                    <div class="form-group">
                        <label class="form-label" for="admin-note">Ghi chú nội dung thay đổi <span class="text-error">*</span></label>
                        <input id="admin-note" class="form-control" required placeholder="VD: Cập nhật mẫu Thông báo theo thông tư mới">
                    </div>
                    <div class="grid-form-2">
                        <div class="form-group">
                            <label class="form-label" for="admin-legal-basis">Căn cứ pháp lý</label>
                            <input id="admin-legal-basis" class="form-control" value="${e(d.schema.legal_basis || '')}">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="admin-effective-from">Ngày hiệu lực</label>
                            <input id="admin-effective-from" type="date" class="form-control" value="${e(d.schema.effective_from || '')}">
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary">Xuất bản</button>
                    <button type="button" class="btn btn-secondary" data-action="discard-draft">Bỏ bản nháp</button>
                </form>
            </div>`;
        if (note) message(note, false);
        document.getElementById('admin-upload').addEventListener('change', uploadFiles);
        document.getElementById('admin-publish-form').addEventListener('submit', publish);
    }

    async function uploadFiles(ev) {
        const files = Array.from(ev.target.files || []);
        for (const f of files) {
            const fd = new FormData();
            fd.append('file', f, f.name);
            const r = await adminFetch(`/api/admin/drafts/${encodeURIComponent(st.draftId)}/files`, { method: 'POST', body: fd });
            if (!r.ok) return failed(r, `Không tải được ${f.name}`);
        }
        showDraft(st.draftId, `Đã tải lên ${files.length} file`);
    }

    function renderFindings(report, title) {
        const box = document.getElementById('admin-lint');
        const s = report.summary || {};
        const rows = (report.findings || report.errors || []).map(f => `
            <tr class="lint-${e(f.level)}"><td>${e(LEVEL_LABEL[f.level] || f.level)}</td><td>${e(f.code)}</td>
                <td>${e(f.file)}</td><td>${e(f.message)}</td></tr>`).join('');
        box.innerHTML = `
            <p class="text-sm">${e(title || '')}${report.summary ? ` ${e(s.error || 0)} lỗi, ${e(s.warning || 0)} cảnh báo, ${e(s.info || 0)} thông tin.` : ''}</p>
            ${rows ? `<table class="admin-table" id="admin-lint-table" style="width: 100%;"><thead><tr><th>Mức</th><th>Mã</th><th>File</th><th>Nội dung</th></tr></thead>
                <tbody>${rows}</tbody></table>` : ''}`;
    }

    async function publish(ev) {
        ev.preventDefault();
        const r = await adminFetch(`/api/admin/drafts/${encodeURIComponent(st.draftId)}/publish`, jsonBody('POST', {
            note: document.getElementById('admin-note').value,
            legal_basis: document.getElementById('admin-legal-basis').value,
            effective_from: document.getElementById('admin-effective-from').value,
        }));
        if (r.ok) {
            await showTemplate(st.templateId);
            message(`Đã xuất bản phiên bản v${r.body.version}`, false);
        } else {
            failed(r);
            if (r.status === 422 && r.body.errors) renderFindings({ findings: r.body.errors }, 'Chưa xuất bản được, cần sửa các lỗi sau:');
        }
    }

    async function preview() {
        message('Đang sinh thử...', false);
        const res = await fetch(`/api/admin/drafts/${encodeURIComponent(st.draftId)}/preview`,
            { method: 'POST', headers: CSRF, credentials: 'same-origin' });
        if (!res.ok) {
            let body = null;
            try { body = await res.json(); } catch (err) { body = null; }
            return failed({ status: res.status, body }, 'Sinh thử thất bại');
        }
        const url = URL.createObjectURL(await res.blob());
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ban_nhap_sinh_thu.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        message('Đã tải bộ hồ sơ sinh thử', false);
    }

    // ---------- Xử lý nút bấm ----------

    const ACTIONS = {
        'logout': async () => { await adminFetch('/api/admin/logout', { method: 'POST' }); showLogin(); },
        'back-templates': () => showTemplates(),
        'back-template': () => showTemplate(st.templateId),
        'open-template': el => showTemplate(el.dataset.id),
        'open-draft': el => showDraft(el.dataset.id),
        'new-draft': async () => {
            const r = await adminFetch(`/api/admin/templates/${encodeURIComponent(st.templateId)}/drafts`, { method: 'POST' });
            if (r.ok) showDraft(r.body.id, 'Đã tạo bản nháp'); else failed(r);
        },
        'rollback': async el => {
            const v = parseInt(el.dataset.version, 10);
            if (!window.confirm(`Dùng lại nội dung phiên bản v${v}? Thao tác này tạo một phiên bản mới, lịch sử được giữ nguyên.`)) return;
            const r = await adminFetch(`/api/admin/templates/${encodeURIComponent(st.templateId)}/rollback`, jsonBody('POST', { version: v }));
            if (r.ok) { await showTemplate(st.templateId); message(`Đã dùng lại v${v}, thành phiên bản v${r.body.version}`, false); }
            else failed(r);
        },
        'delete-file': async el => {
            if (!window.confirm(`Xóa file "${el.dataset.name}" khỏi bản nháp?`)) return;
            const r = await adminFetch(`/api/admin/drafts/${encodeURIComponent(st.draftId)}/files/${encodeURIComponent(el.dataset.name)}`, { method: 'DELETE' });
            if (r.ok) showDraft(st.draftId, 'Đã xóa file'); else failed(r);
        },
        'save-schema': async () => {
            let schema;
            try { schema = JSON.parse(document.getElementById('admin-schema').value); }
            catch (err) { return message(`Cấu hình không phải JSON hợp lệ: ${err.message}`, true); }
            const r = await adminFetch(`/api/admin/drafts/${encodeURIComponent(st.draftId)}/schema`, jsonBody('PUT', schema));
            if (r.ok) message('Đã lưu cấu hình', false); else failed(r);
        },
        'lint': async () => {
            const r = await adminFetch(`/api/admin/drafts/${encodeURIComponent(st.draftId)}/lint`);
            if (r.ok) renderFindings(r.body, 'Kết quả quét:'); else failed(r);
        },
        'preview': () => preview(),
        'discard-draft': async () => {
            if (!window.confirm('Bỏ bản nháp này? Mọi thay đổi trong bản nháp sẽ mất.')) return;
            const r = await adminFetch(`/api/admin/drafts/${encodeURIComponent(st.draftId)}`, { method: 'DELETE' });
            if (r.ok) { await showTemplate(st.templateId); message('Đã bỏ bản nháp', false); } else failed(r);
        },
    };

    function onClick(ev) {
        const el = ev.target.closest('[data-action]');
        if (!el || !root() || !root().contains(el)) return;
        const fn = ACTIONS[el.dataset.action];
        if (fn) { ev.preventDefault(); fn(el); }
    }

    window.renderAdmin = function () { return shell('<div class="card text-secondary">Đang tải...</div>'); };

    window.initAdmin = async function () {
        root().addEventListener('click', onClick);
        const r = await adminFetch('/api/admin/me');
        if (r.ok) { st.user = r.body; showTemplates(); }
        else showLogin();
    };

    window.adminFetch = adminFetch;
})();
