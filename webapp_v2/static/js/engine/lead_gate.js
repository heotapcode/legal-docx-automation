/**
 * Bước để lại thông tin trước khi tải hồ sơ (phễu khách) và màn hình sau khi tải.
 *
 * - LeadGate.ask(tenThuTuc): mở cửa sổ hỏi họ tên, số Zalo, vai trò, ô đồng ý; trả Promise<lead | null>.
 *   Hai nút: "Nhờ nộp trọn gói" (delegated = true) và "Tự nộp: tải hồ sơ miễn phí".
 *   Bấm "Nhờ nộp trọn gói" -> bước 2: chọn gói (bảng giá, gói hợp thủ tục đứng đầu) và cách gửi hồ sơ đã ký
 *   (scan qua Zalo / bản giấy qua bưu điện); lead có thêm package, delivery.
 * - LeadGate.thankYou(lead, goiGoiY, maHoSo): sau khi tải. Khách tự nộp: các gói, cam kết, nút nhắn Zalo.
 *   Khách nhờ nộp: mã QR đặt cọc (GET /api/public/thanh-toan/<mã hồ sơ>), cách ký và gửi hồ sơ.
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

    // Nguồn khách do static/js/track.js ghi vào sessionStorage (khóa KEY_SOURCE)

    const cfgCache = {};
    function loadConfig(templateId) {
        const k = templateId || '';
        if (!cfgCache[k]) {
            cfgCache[k] = fetch('/api/public/kinh-doanh?template_id=' + encodeURIComponent(k))
                .then(r => r.json()).catch(() => null);
        }
        return cfgCache[k];
    }

    const vnd = n => (Number(n) || 0).toLocaleString('vi-VN').replace(/,/g, '.') + 'đ';

    // Bước 2 khi khách bấm "Nhờ nộp trọn gói": chọn gói và cách gửi hồ sơ đã ký
    function choosePackage(cfg, tenThuTuc) {
        const suggested = (cfg && cfg.goi_goi_y) || [];
        const goi = (cfg && cfg.goi ? cfg.goi.slice() : [])
            .sort((a, b) => (suggested.indexOf(a.ma) + 1 || 99) - (suggested.indexOf(b.ma) + 1 || 99));
        const first = goi.length ? goi[0].ma : '';
        const pct = cfg ? cfg.ty_le_coc : 50;
        const el = overlay(`
            <button type="button" class="lead-gate-close" data-lg="close" aria-label="Đóng">&times;</button>
            <h3 class="text-xl font-bold mb-2">Chọn gói nộp hộ</h3>
            <p class="text-sm text-secondary mb-2">${e(tenThuTuc)}. Đặt cọc ${e(pct)}% sau khi chọn gói, phần còn lại
                thanh toán khi có kết quả.</p>
            <div class="lead-gate-pkgs" id="lg-packages">${goi.map(g => `
                <label class="lead-gate-pkg lead-gate-choice">
                    <input type="radio" name="lg-package" value="${e(g.ma)}" ${g.ma === first ? 'checked' : ''}>
                    <span><b>${e(g.ten)}</b> <span class="lead-gate-price">${e(g.gia)}</span>
                        ${suggested[0] === g.ma ? '<span class="lead-gate-tag">Phù hợp hồ sơ này</span>' : ''}
                        <span class="text-xs text-secondary" style="display:block">${e(g.mo_ta)}</span>
                        ${g.gia_so ? `<span class="text-xs" style="display:block">Đặt cọc: ${e(vnd(Math.round(g.gia_so * pct / 100 / 1000) * 1000))}</span>` : ''}
                    </span>
                </label>`).join('')}</div>
            <h4 class="font-bold mt-4 mb-2">Gửi hồ sơ đã ký cho chúng tôi</h4>
            <label class="lead-gate-choice text-sm">
                <input type="radio" name="lg-delivery" value="scan" checked>
                <span><b>Scan / chụp gửi qua Zalo</b> (nhanh nhất, nộp trong ngày)</span>
            </label>
            ${cfg && cfg.dia_chi_nhan_ho_so ? `
            <label class="lead-gate-choice text-sm">
                <input type="radio" name="lg-delivery" value="giay">
                <span><b>Gửi bản giấy qua bưu điện</b> tới ${e(cfg.dia_chi_nhan_ho_so)}</span>
            </label>` : ''}
            <p class="text-xs text-secondary mt-2">Ký bằng bút mực xanh, không cần đóng dấu.</p>
            <div class="lead-gate-actions mt-4">
                <button type="button" class="btn btn-primary" data-lg="confirm" id="lg-confirm">Xác nhận và tải hồ sơ</button>
                <button type="button" class="btn btn-secondary" data-lg="back">Quay lại</button>
            </div>`);
        return new Promise(resolve => {
            el.addEventListener('click', ev => {
                const btn = ev.target.closest('[data-lg]');
                if (!btn && ev.target !== el) return;
                const action = btn ? btn.dataset.lg : 'close';
                if (action === 'confirm') {
                    const pk = el.querySelector('input[name="lg-package"]:checked');
                    const dv = el.querySelector('input[name="lg-delivery"]:checked');
                    el.remove();
                    resolve({ package: pk ? pk.value : null, delivery: dv ? dv.value : 'scan' });
                } else if (action === 'back' || action === 'close') {
                    el.remove();
                    resolve(action === 'back' ? 'back' : null);
                }
            });
        });
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
        ask: async function (tenThuTuc, errorText, templateId) {
            const cfg = await loadConfig(templateId);
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
                    if (!lead.delegated) { resolve(lead); return; }
                    choosePackage(cfg, tenThuTuc).then(choice => {
                        if (choice === 'back') resolve(window.LeadGate.ask(tenThuTuc, '', templateId));
                        else if (!choice) resolve(null);
                        else resolve(Object.assign(lead, choice));
                    });
                });
                const first = document.getElementById(c.name ? 'lg-consent' : 'lg-name');
                if (first) first.focus();
            });
        },

        thankYou: async function (lead, recommended, code) {
            const cfg = await loadConfig();
            if (lead && lead.delegated && code) return this.payment(lead, code, cfg);
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
            closeable(el);
        },

        // Khách nhờ nộp: mã QR đặt cọc, nội dung chuyển khoản, cách gửi hồ sơ đã ký
        payment: async function (lead, code, cfg) {
            let info = null;
            try {
                const r = await fetch(`/api/public/thanh-toan/${encodeURIComponent(code)}?phone=${encodeURIComponent(lead.phone)}`);
                if (r.ok) info = await r.json();
            } catch (err) { info = null; }
            const bank = info ? info.bank : {};
            const pay = info && info.deposit ? `
                <div class="lead-gate-qr" id="lg-qr">${info.qr_svg || ''}</div>
                <table class="lead-gate-paytable text-sm">
                    <tr><td>Gói</td><td><b>${e(info.package)}</b> – ${e(info.gia)}</td></tr>
                    <tr><td>Đặt cọc ${e(info.ty_le_coc)}%</td><td><b class="lead-gate-price">${e(vnd(info.deposit))}</b></td></tr>
                    <tr><td>Ngân hàng</td><td>${e(bank.ten)}</td></tr>
                    <tr><td>Số tài khoản</td><td><b>${e(bank.so_tk)}</b></td></tr>
                    <tr><td>Chủ tài khoản</td><td>${e(bank.chu_tk)}</td></tr>
                    <tr><td>Nội dung</td><td><b id="lg-pay-content">${e(info.content)}</b></td></tr>
                </table>
                <p class="text-xs text-secondary">Quét mã bằng ứng dụng ngân hàng: số tiền và nội dung được điền sẵn.
                    Phần còn lại thanh toán khi có kết quả.</p>` : `
                <p class="text-sm">Gói này báo giá theo hồ sơ: tư vấn viên sẽ báo giá qua Zalo.</p>`;
            const giay = info && info.delivery === 'giay' && info.dia_chi_nhan_ho_so;
            const el = overlay(`
                <button type="button" class="lead-gate-close" data-lg="close" aria-label="Đóng">&times;</button>
                <h3 class="text-xl font-bold mb-2">Đã tải hồ sơ – mã ${e(code)}</h3>
                ${pay}
                <h4 class="font-bold mt-4 mb-2">Ký và gửi hồ sơ</h4>
                <ol class="text-sm lead-gate-steps">
                    <li>In hồ sơ, ký bằng <b>bút mực xanh</b> vào mọi chỗ ký, đúng người có tên dưới chỗ ký. Không cần đóng dấu.
                        Ai ký văn bản nào xem file <b>00. Hướng dẫn</b> trong file .zip.</li>
                    ${giay
                        ? `<li>Gửi bản giấy qua bưu điện tới <b>${e(info.dia_chi_nhan_ho_so)}</b>, ghi mã <b>${e(code)}</b> ngoài phong bì.</li>`
                        : '<li>Scan hoặc chụp đủ các trang, rõ chữ ký, gửi file PDF qua Zalo bên dưới.</li>'}
                    <li>Chúng tôi kiểm tra, nộp và báo kết quả qua Zalo.</li>
                </ol>
                <div class="lead-gate-actions mt-4">
                    <a class="btn btn-primary" href="${zaloLink(cfg)}" target="_blank" rel="noopener" id="lg-zalo">
                        ${giay ? 'Nhắn Zalo' : 'Gửi hồ sơ qua Zalo'} ${e(cfg ? cfg.zalo : '')}</a>
                    <button type="button" class="btn btn-secondary" data-lg="close">Đóng</button>
                </div>`);
            closeable(el);
        },
    };

    function closeable(el) {
        el.addEventListener('click', ev => {
            const btn = ev.target.closest('[data-lg]');
            if ((btn && btn.dataset.lg === 'close') || ev.target === el) el.remove();
        });
    }
})();
