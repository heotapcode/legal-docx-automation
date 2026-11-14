/**
 * Đo lường dùng chung cho trang giới thiệu (/) và ứng dụng (/app):
 * - Ghi nguồn khách (utm_*, ref, trang vào đầu tiên, trang giới thiệu bên ngoài) một lần mỗi phiên vào sessionStorage
 *   khóa 'nac_source'; LeadGate gửi kèm khi khách để lại số Zalo.
 * - Google Analytics 4: chỉ nạp khi máy chủ đặt window.NAC_GA4 (mã G-..., sửa ở trang quản trị > Kinh doanh).
 * - window.nacTrack(tên sự kiện, tham số): gửi sự kiện phễu. KHÔNG gửi họ tên, số điện thoại hay dữ liệu hồ sơ.
 */
(function () {
    'use strict';

    const KEY_SOURCE = 'nac_source';

    (function captureSource() {
        let s = null;
        try { s = window.sessionStorage; } catch (err) { return; }
        if (!s || s.getItem(KEY_SOURCE)) return;
        const out = {};
        const params = new URLSearchParams(window.location.search);
        new URLSearchParams(window.location.hash.split('?')[1] || '').forEach((v, k) => params.set(k, v));
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'ref'].forEach(k => {
            if (params.get(k)) out[k] = params.get(k).slice(0, 200);
        });
        out.landing = (window.location.pathname + window.location.hash.split('?')[0]).slice(0, 200);
        if (document.referrer && !document.referrer.startsWith(window.location.origin)) {
            out.referrer = document.referrer.slice(0, 200);
        }
        try { s.setItem(KEY_SOURCE, JSON.stringify(out)); } catch (err) { /* bỏ qua */ }
    })();

    const id = window.NAC_GA4;
    if (id) {
        window.dataLayer = window.dataLayer || [];
        window.gtag = function () { window.dataLayer.push(arguments); };
        window.gtag('js', new Date());
        // Ứng dụng /app đổi trang bằng dấu # nên tự gửi page_view theo từng trang (router.js)
        window.gtag('config', id, { send_page_view: !window.NAC_SPA });
        const sc = document.createElement('script');
        sc.async = true;
        sc.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id);
        document.head.appendChild(sc);
    }

    window.nacTrack = function (name, params) {
        try {
            if (window.gtag) window.gtag('event', name, params || {});
        } catch (err) { /* đo lường không được làm hỏng trang */ }
    };

    // Mọi nút / link nhắn Zalo: đếm lượt bấm
    document.addEventListener('click', ev => {
        const a = ev.target.closest && ev.target.closest('a[href^="https://zalo.me/"]');
        if (a && !window.location.hash.startsWith('#/admin')) window.nacTrack('contact_zalo', { vi_tri: a.dataset.track || a.id || 'khac' });
    });
})();
