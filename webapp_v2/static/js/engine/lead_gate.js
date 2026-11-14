/**
 * Bước để lại thông tin trước khi tải hồ sơ (phễu khách) và màn hình sau khi tải.
 *
 * - LeadGate.ask(tenThuTuc): mở cửa sổ hỏi họ tên, số Zalo, vai trò, ô đồng ý; trả Promise<lead | null>.
 *   Hai nút: "Nhờ nộp trọn gói" (delegated = true) và "Tự nộp: tải hồ sơ miễn phí".
 * - LeadGate.thankYou(lead): sau khi tải, hiện các gói dịch vụ, cam kết, nút nhắn Zalo.
 * - Nguồn khách (utm_*, ref, trang vào đầu tiên, trang giới thiệu) lấy từ địa chỉ trang ở lần vào đầu, gửi kèm lead.
 * Cấu hình (Zalo, bảng giá, câu đồng ý): GET /api/public/kinh-doanh (routes/leads.py).
 */
(function () {
    'use strict';

    const KEY_SOURCE = 'nac_source';
    const KEY_CONTACT = 'nac_contact';
    const e = s => escapeHtml(s === undefined || s === null ? '' : String(s));

    function store(kind) {
        try { return kind === 'session' ? window.sessionStorage : window.localStorage; } catch (err) { return null; }
    }

    // Ghi nguồn khách một lần mỗi phiên (lần chạm đầu)
    (function captureSource() {
        const s = store('session');
        if (!s || s.getItem(KEY_SOURCE)) return;
        const out = {};
        const params = new URLSearchParams(window.location.search);
        const hashQuery = (window.location.hash.split('?')[1] || '');
        new URLSearchParams(hashQuery).forEach((v, k) => params.set(k, v));
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'ref'].forEach(k => {
            if (params.get(k)) out[k] = params.get(k).slice(0, 200);
        });
        out.landing = (window.location.pathname + window.location.hash.split('?')[0]).slice(0, 200);
        if (document.referrer && !document.referrer.startsWith(window.location.origin)) {
            out.referrer = document.referrer.slice(0, 200);
        }
        try { s.setItem(KEY_SOURCE, JSON.stringify(out)); } catch (err) { /* bỏ qua */ }
    })();

    let cfgPromise = null;
    function loadConfig() {
        if (!cfgPromise) {
            cfgPromise = fetch('/api/public/kinh-doanh').then(r => r.json()).catch(() => null);
        }
        return cfgPromise;
    }

    function source() {
        const s = store('session');
        try { return JSON.parse((s && s.getItem(KEY_SOURCE)) || '{}'); } catch (err) { return {}; }
    }

    function savedContact() {
        const s = store('local');
        try { return JSON.parse((s && s.getItem(KEY_CONTACT)) || '{}'); } catch (err) { return {}; }
    }

    function overlay(inner) {
        const old = document.getElementById('lead-gate');
        if (old) old.remove();
        const el = document.createElement('div');
        el.id = 'lead-gate';
        el.className = 'lead-gate-overlay';
        el.setAttribute('role', 'dialog');
        el.setAttribute('aria-modal', 'true');
        el.innerHTML = `<div class="lead-gate-card card">${inner}</div>`;
        document.body.appendChild(el);
        return el;
    }

    function packagesHtml(cfg, limit, first) {
        const all = cfg && cfg.goi ? cfg.goi.slice() : [];
        // Gói nên chào cho thủ tục này (máy chủ gửi qua header X-Lead-Package) đứng đầu
        all.sort((a, b) => (b.ma === first) - (a.ma === first));
        const list = all.slice(0, limit || 99);
        return list.map(g => `
            <div class="lead-gate-pkg">
                <div><b>${e(g.ten)}</b> <span class="lead-gate-price">${e(g.gia)}</span></div>
                <div class="text-xs text-secondary">${e(g.mo_ta)}</div>
            </div>`).join('');
    }

    function zaloLink(cfg) {
        return cfg && cfg.zalo ? `https://zalo.me/${encodeURIComponent(cfg.zalo)}` : '#';
    }

    window.LeadGate = {
        ask: async function (tenThuTuc, errorText) {
            const cfg = await loadConfig();
            const c = savedContact();
            const el = overlay(`
                <button type="button" class="lead-gate-close" data-lg="close" aria-label="Đóng">&times;</button>
                <h3 class="text-xl font-bold mb-2">Nhận bộ hồ sơ ${e(tenThuTuc)}</h3>
                <p class="text-sm text-secondary mb-4">Để lại số Zalo để nhận hồ sơ. Trong file có tờ hướng dẫn các bước
                    nộp và bảng giá nếu anh/chị muốn nhờ nộp hộ.</p>
                <div class="form-group">
                    <label class="form-label" for="lg-name">Họ tên *</label>
                    <input id="lg-name" class="form-control" autocomplete="name" value="${e(c.name)}">
                </div>
                <div class="form-group">
                    <label class="form-label" for="lg-phone">Số điện thoại Zalo *</label>
                    <input id="lg-phone" class="form-control" type="tel" inputmode="tel" autocomplete="tel"
                           placeholder="09xx xxx xxx" value="${e(c.phone)}">
                </div>
                <div class="form-group">
                    <label class="form-label" for="lg-role">Anh/chị là</label>
                    <select id="lg-role" class="form-control">
                        <option value="chu_dn">Chủ doanh nghiệp / người sáng lập</option>
                        <option value="ke_toan" ${c.role === 'ke_toan' ? 'selected' : ''}>Kế toán / đơn vị dịch vụ</option>
                    </select>
                </div>
                <label class="lead-gate-consent text-sm">
                    <input type="checkbox" id="lg-consent">
                    <span>${e(cfg ? cfg.loi_dong_y : 'Tôi đồng ý lưu thông tin liên hệ để được tư vấn về hồ sơ này.')}</span>
                </label>
                <div id="lg-error" class="text-error text-sm mb-2">${e(errorText || '')}</div>
                <div class="lead-gate-actions">
                    <button type="button" class="btn btn-primary" data-lg="delegated" id="lg-delegated">
                        Nhờ nộp trọn gói (tư vấn viên gọi lại)</button>
                    <button type="button" class="btn btn-secondary" data-lg="free" id="lg-free">
                        Tự nộp: tải hồ sơ miễn phí</button>
                </div>
                ${cfg && cfg.cam_ket ? `<p class="text-xs text-secondary mt-2">${e(cfg.cam_ket)}</p>` : ''}`);
            return new Promise(resolve => {
                el.addEventListener('click', ev => {
                    const btn = ev.target.closest('[data-lg]');
                    if (!btn && ev.target !== el) return;
                    const action = btn ? btn.dataset.lg : 'close';
                    if (action === 'close') { el.remove(); resolve(null); return; }
                    const lead = {
                        name: document.getElementById('lg-name').value.trim(),
                        phone: document.getElementById('lg-phone').value.trim(),
                        role: document.getElementById('lg-role').value,
                        consent: document.getElementById('lg-consent').checked,
                        delegated: action === 'delegated',
                        source: source(),
                    };
                    const err = document.getElementById('lg-error');
                    const digits = lead.phone.replace(/[\s.\-()]/g, '').replace(/^\+84/, '0');
                    if (!lead.name) { err.textContent = 'Vui lòng nhập họ tên'; return; }
                    if (!/^0\d{9}$/.test(digits)) { err.textContent = 'Số điện thoại Zalo gồm 10 chữ số, bắt đầu bằng 0'; return; }
                    if (!lead.consent) { err.textContent = 'Vui lòng đánh dấu ô đồng ý để tải hồ sơ'; return; }
                    const s = store('local');
                    try { if (s) s.setItem(KEY_CONTACT, JSON.stringify({ name: lead.name, phone: lead.phone, role: lead.role })); }
                    catch (er) { /* bỏ qua */ }
                    el.remove();
                    resolve(lead);
                });
                const first = document.getElementById(c.name ? 'lg-consent' : 'lg-name');
                if (first) first.focus();
            });
        },

        thankYou: async function (lead, recommended) {
            const cfg = await loadConfig();
            const el = overlay(`
                <button type="button" class="lead-gate-close" data-lg="close" aria-label="Đóng">&times;</button>
                <h3 class="text-xl font-bold mb-2">Đã tải bộ hồ sơ</h3>
                <p class="text-sm mb-4">${lead && lead.delegated
                    ? 'Tư vấn viên sẽ nhắn Zalo cho anh/chị trong ít phút để nhận hồ sơ và báo giá cụ thể.'
                    : 'Mở file <b>00. Hướng dẫn nộp hồ sơ</b> trong file .zip để xem các bước anh/chị còn phải làm.'}</p>
                <p class="text-sm text-secondary mb-2">Nếu muốn nhờ nộp hộ, giá tham khảo:</p>
                <div class="lead-gate-pkgs">${packagesHtml(cfg, 3, recommended)}</div>
                ${cfg && cfg.cam_ket ? `<p class="text-sm mt-2">${e(cfg.cam_ket)}</p>` : ''}
                <div class="lead-gate-actions mt-4">
                    <a class="btn btn-primary" href="${zaloLink(cfg)}" target="_blank" rel="noopener" id="lg-zalo">
                        Nhắn Zalo ${e(cfg ? cfg.zalo : '')}</a>
                    <button type="button" class="btn btn-secondary" data-lg="close">Đóng</button>
                </div>`);
            el.addEventListener('click', ev => {
                const btn = ev.target.closest('[data-lg]');
                if ((btn && btn.dataset.lg === 'close') || ev.target === el) el.remove();
            });
        },
    };
})();
