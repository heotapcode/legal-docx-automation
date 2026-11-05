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
