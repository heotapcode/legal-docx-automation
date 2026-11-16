/**
 * Đo lường dùng chung cho trang giới thiệu (/) và ứng dụng (/app):
 * - Ghi nguồn khách (utm_*, ref, trang vào đầu tiên, trang giới thiệu bên ngoài) một lần mỗi phiên vào sessionStorage
 *   khóa 'nac_source'; LeadGate gửi kèm khi khách để lại số Zalo. Mã đối tác ?ref= giữ thêm 30 ngày (localStorage).
 * - Google Analytics 4 / Google Ads: chỉ nạp khi máy chủ đặt window.NAC_GA4 (G-...) / NAC_ADS (AW-...), sửa ở trang
 *   quản trị > Kinh doanh. Có NAC_ADS_LEAD thì sự kiện generate_lead gửi thêm chuyển đổi Google Ads.
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
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'ref', 'gclid'].forEach(k => {
            if (params.get(k)) out[k] = params.get(k).slice(0, 200);
        });
        out.landing = (window.location.pathname + window.location.hash.split('?')[0]).slice(0, 200);
        if (document.referrer && !document.referrer.startsWith(window.location.origin)) {
            out.referrer = document.referrer.slice(0, 200);
        }
        try { s.setItem(KEY_SOURCE, JSON.stringify(out)); } catch (err) { /* bỏ qua */ }
    })();

    // Mã đối tác (?ref=): giữ 30 ngày trên máy khách để khách quay lại sau vẫn tính cho đối tác.
    // Link đối tác mới nhất thắng; mã gắn vào nguồn của phiên nếu phiên chưa có mã.
    (function keepPartnerRef() {
        const KEY_REF = 'nac_ref';
        const DAYS = 30;
        let ls = null, ss = null;
        try { ls = window.localStorage; ss = window.sessionStorage; } catch (err) { return; }
        if (!ls || !ss) return;
        const params = new URLSearchParams(window.location.search);
        new URLSearchParams(window.location.hash.split('?')[1] || '').forEach((v, k) => params.set(k, v));
        const fresh = (params.get('ref') || '').trim().toLowerCase().slice(0, 30);
        try {
            if (fresh) ls.setItem(KEY_REF, JSON.stringify({ ref: fresh, at: Date.now() }));
            const kept = JSON.parse(ls.getItem(KEY_REF) || 'null');
            if (!kept || Date.now() - kept.at > DAYS * 24 * 3600 * 1000) { ls.removeItem(KEY_REF); return; }
            const src = JSON.parse(ss.getItem(KEY_SOURCE) || '{}');
            if (!src.ref) { src.ref = kept.ref; ss.setItem(KEY_SOURCE, JSON.stringify(src)); }
        } catch (err) { /* bỏ qua */ }
    })();

    // Google Analytics 4 (NAC_GA4) và Google Ads (NAC_ADS): dùng chung thư viện gtag, chỉ nạp khi có mã
    const ga4 = window.NAC_GA4, ads = window.NAC_ADS;
    if (ga4 || ads) {
        window.dataLayer = window.dataLayer || [];
        window.gtag = function () { window.dataLayer.push(arguments); };
        window.gtag('js', new Date());
        // Ứng dụng /app đổi trang bằng dấu # nên tự gửi page_view theo từng trang (router.js)
        if (ga4) window.gtag('config', ga4, { send_page_view: !window.NAC_SPA });
        if (ads) window.gtag('config', ads);
        const sc = document.createElement('script');
        sc.async = true;
        sc.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ga4 || ads);
        document.head.appendChild(sc);
    }

    window.nacTrack = function (name, params) {
        try {
            if (!window.gtag) return;
            window.gtag('event', name, params || {});
            // Chuyển đổi Google Ads: khách để lại số Zalo và tải hồ sơ
            if (name === 'generate_lead' && ads && window.NAC_ADS_LEAD) {
                window.gtag('event', 'conversion', { send_to: ads + '/' + window.NAC_ADS_LEAD });
            }
        } catch (err) { /* đo lường không được làm hỏng trang */ }
    };

    // Mọi nút / link nhắn Zalo: đếm lượt bấm
    document.addEventListener('click', ev => {
        const a = ev.target.closest && ev.target.closest('a[href^="https://zalo.me/"]');
        if (a && !window.location.hash.startsWith('#/admin')) window.nacTrack('contact_zalo', { vi_tri: a.dataset.track || a.id || 'khac' });
    });
})();
