/**
 * utils.js - Tiện ích & Enum cho NAC CRM
 */
window.CRM = window.CRM || {};

CRM.Utils = (() => {
  // ── Enum: Loại hồ sơ ──────────────────────────────────────
  const RECORD_TYPES = {
    thanh_lap_tnhh_1tv: "Thành lập TNHH 1TV",
    thanh_lap_tnhh_2tv: "Thành lập TNHH 2TV",
    thanh_lap_co_phan: "Thành lập Cổ phần",
    thanh_lap_ddkd: "Thành lập ĐĐKD",
    thay_doi_dia_chi: "Thay đổi địa chỉ",
    thay_doi_nganh_nghe: "Thay đổi ngành nghề",
    thay_doi_nguoi_dai_dien: "Thay đổi người đại diện",
    tang_von_tnhh_2tv: "Tăng vốn TNHH 2TV",
    tang_von_co_phan: "Tăng vốn Cổ phần",
    thay_doi_thanh_vien: "Thay đổi TV/CĐ",
    chuyen_nhuong: "Chuyển nhượng",
    chuyen_doi_loai_hinh: "Chuyển đổi loại hình",
    tam_dung_tnhh_1tv: "Tạm dừng TNHH 1TV",
    tam_dung_tnhh_2tv: "Tạm dừng TNHH 2TV",
    tam_dung_co_phan: "Tạm dừng Cổ phần",
    giai_the_tnhh_1tv: "Giải thể TNHH 1TV",
    giai_the_tnhh_2tv: "Giải thể TNHH 2TV",
    giai_the_co_phan: "Giải thể Cổ phần",
    hoat_dong_lai: "Hoạt động lại",
    cap_lai_dkkd: "Cấp lại ĐKKD",
    cham_dut_ddkd: "Chấm dứt ĐĐKD",
    khac: "Loại khác"
  };

  const RECORD_TYPE_GROUPS = {
    "Thành lập mới": ["thanh_lap_tnhh_1tv","thanh_lap_tnhh_2tv","thanh_lap_co_phan","thanh_lap_ddkd"],
    "Thay đổi nội dung": ["thay_doi_dia_chi","thay_doi_nganh_nghe","thay_doi_nguoi_dai_dien","tang_von_tnhh_2tv","tang_von_co_phan","thay_doi_thanh_vien"],
    "Chuyển đổi": ["chuyen_nhuong","chuyen_doi_loai_hinh"],
    "Tạm ngưng/Giải thể": ["tam_dung_tnhh_1tv","tam_dung_tnhh_2tv","tam_dung_co_phan","giai_the_tnhh_1tv","giai_the_tnhh_2tv","giai_the_co_phan","hoat_dong_lai"],
    "Khác": ["cap_lai_dkkd","cham_dut_ddkd","khac"]
  };

  // ── Enum: Trạng thái hồ sơ ────────────────────────────────
  const RECORD_STATUSES = {
    tiep_nhan: { label: "Tiếp nhận", color: "#64748b", bg: "rgba(100,116,139,0.15)" },
    dang_xu_ly: { label: "Đang xử lý", color: "#f59e0b", bg: "rgba(245,158,11,0.15)" },
    cho_nop: { label: "Chờ nộp", color: "#8b5cf6", bg: "rgba(139,92,246,0.15)" },
    da_nop: { label: "Đã nộp", color: "#3b82f6", bg: "rgba(59,130,246,0.15)" },
    hoan_thanh: { label: "Hoàn thành", color: "#10b981", bg: "rgba(16,185,129,0.15)" },
    tra_lai: { label: "Trả lại", color: "#ef4444", bg: "rgba(239,68,68,0.15)" }
  };

  // ── Enum: Danh mục chi phí ────────────────────────────────
  const TRANSACTION_CATEGORIES = {
    phi_dich_vu: "Phí dịch vụ",
    le_phi_nha_nuoc: "Lệ phí nhà nước",
    phi_cong_chung: "Phí công chứng",
    chi_phi_in_an: "Chi phí in ấn",
    nhan_cong: "Nhân công",
    van_chuyen: "Vận chuyển",
    khac: "Khác"
  };

  // ── Enum: Trạng thái thanh toán ───────────────────────────
  const PAYMENT_STATUSES = {
    chua_thanh_toan: { label: "Chưa thanh toán", color: "#ef4444", bg: "rgba(239,68,68,0.15)" },
    thanh_toan_mot_phan: { label: "TT một phần", color: "#f59e0b", bg: "rgba(245,158,11,0.15)" },
    da_thanh_toan: { label: "Đã thanh toán", color: "#10b981", bg: "rgba(16,185,129,0.15)" }
  };

  // ── Enum: Loại hình doanh nghiệp ─────────────────────────
  const BUSINESS_TYPES = {
    tnhh_1tv: "TNHH 1 Thành viên",
    tnhh_2tv: "TNHH 2+ Thành viên",
    co_phan: "Cổ phần",
    ho_kinh_doanh: "Hộ kinh doanh",
    ca_nhan: "Cá nhân"
  };

  // ── Format helpers ────────────────────────────────────────
  function formatCurrency(amount) {
    if (amount == null || isNaN(amount)) return '0 ₫';
    return new Intl.NumberFormat('vi-VN').format(Math.round(amount)) + ' ₫';
  }

  function formatNumber(n) {
    if (n == null || isNaN(n)) return '0';
    return new Intl.NumberFormat('vi-VN').format(n);
  }

  function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })
      + ' ' + d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  }

  function timeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const seconds = Math.floor((now - date) / 1000);
    if (seconds < 60) return 'Vừa xong';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} phút trước`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} giờ trước`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days} ngày trước`;
    const months = Math.floor(days / 30);
    if (months < 12) return `${months} tháng trước`;
    return `${Math.floor(months / 12)} năm trước`;
  }

  function daysUntil(dateStr) {
    if (!dateStr) return null;
    const now = new Date();
    now.setHours(0,0,0,0);
    const target = new Date(dateStr);
    target.setHours(0,0,0,0);
    return Math.ceil((target - now) / (1000 * 60 * 60 * 24));
  }

  // ── Label helpers ─────────────────────────────────────────
  function getRecordTypeLabel(type) { return RECORD_TYPES[type] || type || '—'; }
  function getStatusLabel(status) { return (RECORD_STATUSES[status] || {}).label || status || '—'; }
  function getCategoryLabel(cat) { return TRANSACTION_CATEGORIES[cat] || cat || '—'; }
  function getPaymentStatusLabel(status) { return (PAYMENT_STATUSES[status] || {}).label || status || '—'; }
  function getBusinessTypeLabel(type) { return BUSINESS_TYPES[type] || type || '—'; }

  // ── Badge HTML helpers ────────────────────────────────────
  function getStatusBadge(status) {
    const s = RECORD_STATUSES[status];
    if (!s) return `<span class="badge badge-secondary">${status || '—'}</span>`;
    return `<span class="badge" style="background:${s.bg};color:${s.color}">${s.label}</span>`;
  }

  function getPaymentBadge(status) {
    const s = PAYMENT_STATUSES[status];
    if (!s) return `<span class="badge badge-secondary">${status || '—'}</span>`;
    return `<span class="badge" style="background:${s.bg};color:${s.color}">${s.label}</span>`;
  }

  function getTypeBadge(type) {
    return `<span class="badge badge-primary">${getRecordTypeLabel(type)}</span>`;
  }

  function getBusinessTypeBadge(type) {
    return `<span class="badge badge-info">${getBusinessTypeLabel(type)}</span>`;
  }

  // ── Debounce ──────────────────────────────────────────────
  function debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  // ── Escape HTML ───────────────────────────────────────────
  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ── Build select options ──────────────────────────────────
  function buildOptions(map, selected = '', placeholder = '-- Tất cả --') {
    let html = placeholder ? `<option value="">${placeholder}</option>` : '';
    for (const [key, label] of Object.entries(map)) {
      html += `<option value="${key}" ${key === selected ? 'selected' : ''}>${label}</option>`;
    }
    return html;
  }

  function buildGroupedOptions(groups, types, selected = '', placeholder = '-- Tất cả --') {
    let html = placeholder ? `<option value="">${placeholder}</option>` : '';
    for (const [group, keys] of Object.entries(groups)) {
      html += `<optgroup label="${group}">`;
      for (const key of keys) {
        html += `<option value="${key}" ${key === selected ? 'selected' : ''}>${types[key]}</option>`;
      }
      html += '</optgroup>';
    }
    return html;
  }

  // ── Deadline display helper ───────────────────────────────
  function getDeadlineDisplay(deadline, status) {
    if (!deadline || status === 'hoan_thanh') return formatDate(deadline);
    const days = daysUntil(deadline);
    if (days === null) return '—';
    if (days < 0) return `<span class="overdue-text">${formatDate(deadline)} (Quá ${Math.abs(days)} ngày)</span>`;
    if (days <= 3) return `<span class="deadline-warning">${formatDate(deadline)} (Còn ${days} ngày)</span>`;
    return formatDate(deadline);
  }

  return {
    RECORD_TYPES, RECORD_TYPE_GROUPS, RECORD_STATUSES,
    TRANSACTION_CATEGORIES, PAYMENT_STATUSES, BUSINESS_TYPES,
    formatCurrency, formatNumber, formatDate, formatDateTime, timeAgo, daysUntil,
    getRecordTypeLabel, getStatusLabel, getCategoryLabel, getPaymentStatusLabel, getBusinessTypeLabel,
    getStatusBadge, getPaymentBadge, getTypeBadge, getBusinessTypeBadge,
    debounce, escapeHtml, buildOptions, buildGroupedOptions, getDeadlineDisplay
  };
})();
