/**
 * Tiện ích dùng chung cho mọi trang.
 * Nạp TRƯỚC các file trong /static/js/pages/ (xem index.html).
 */

/**
 * Escape chuỗi trước khi chèn vào HTML (nội dung thẻ hoặc giá trị thuộc tính).
 * Bắt buộc dùng cho MỌI dữ liệu do người dùng nhập hoặc lấy từ API ngoài
 * (OCR, tra cứu MST...) khi dựng HTML bằng template literal / innerHTML.
 * null/undefined -> '' ; số 0 vẫn giữ nguyên là "0".
 */
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
window.escapeHtml = escapeHtml;

/**
 * Danh mục dùng chung cho ô chọn (field.options_source trong _schema.json).
 * Tải một lần rồi lưu lại; renderField() đọc đồng bộ qua getCatalogOptions().
 */
const CATALOG_URLS = {
    tinh_thanh: '/api/dia-ban/tinh-thanh',
};
window.__catalogs = window.__catalogs || {};

async function loadCatalog(name) {
    if (window.__catalogs[name]) return window.__catalogs[name];
    const url = CATALOG_URLS[name];
    if (!url) return null;
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        window.__catalogs[name] = {
            defaultValue: data.mac_dinh || '',
            options: (data.tinh_thanh || data.options || []).map(o => ({ value: o.value, label: o.label })),
        };
    } catch (e) {
        console.warn(`Không tải được danh mục ${name}:`, e);
        return null;
    }
    return window.__catalogs[name];
}
window.loadCatalog = loadCatalog;

/** Tải mọi danh mục mà schema cần (gọi trước khi vẽ form). */
async function loadCatalogsForSchema(schema) {
    const names = new Set();
    (schema && schema.steps || []).forEach(st => (st.fields || []).forEach(f => {
        if (f.options_source) names.add(f.options_source);
    }));
    await Promise.all([...names].map(loadCatalog));
}
window.loadCatalogsForSchema = loadCatalogsForSchema;

function getCatalogOptions(field) {
    if (field.options && field.options.length) return field.options;
    const cat = field.options_source && window.__catalogs[field.options_source];
    return cat ? cat.options : [];
}
window.getCatalogOptions = getCatalogOptions;

/**
 * HTML các <option> cho ô chọn. Giá trị hiện tại không có trong danh sách vẫn được giữ lại
 * (đánh dấu "không có trong danh mục") để người dùng thấy và chọn lại, không bị mất âm thầm.
 */
function renderSelectOptions(options, current) {
    let html = '';
    const found = options.some(o => String(o.value) === String(current));
    if (current && !found) {
        html += `<option value="${escapeHtml(current)}" selected>${escapeHtml(current)} (không có trong danh mục)</option>`;
    }
    options.forEach(o => {
        const sel = String(o.value) === String(current) ? 'selected' : '';
        html += `<option value="${escapeHtml(o.value)}" ${sel}>${escapeHtml(o.label)}</option>`;
    });
    return html;
}
window.renderSelectOptions = renderSelectOptions;

/**
 * Ô chọn tỉnh/thành phố nơi đăng ký cho các wizard riêng (không vẽ form từ schema).
 * Ghi giá trị vào window.wizardState.formData.tinh_dang_ky.
 */
function renderTinhDangKySelect(extraClass) {
    const fd = (window.wizardState && window.wizardState.formData) || {};
    const cat = window.__catalogs.tinh_thanh;
    const options = cat ? cat.options : [{ value: 'Hà Nội', label: 'Thành phố Hà Nội' }];
    if (!fd.tinh_dang_ky) fd.tinh_dang_ky = (cat && cat.defaultValue) || 'Hà Nội';
    return `
        <div class="form-group">
            <label class="form-label">Tỉnh/Thành phố nơi đăng ký <span class="text-error">*</span></label>
            <select name="tinh_dang_ky" id="input-tinh_dang_ky" class="form-control ${extraClass || ''}"
                    onchange="window.wizardState.formData.tinh_dang_ky = this.value">
                ${renderSelectOptions(options, fd.tinh_dang_ky)}
            </select>
        </div>
    `;
}
window.renderTinhDangKySelect = renderTinhDangKySelect;
