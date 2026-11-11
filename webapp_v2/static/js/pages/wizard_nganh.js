/**
 * Bước 3 của wizard: chọn mã ngành nghề kinh doanh (tìm kiếm, bộ ngành gợi ý, ngành chính).
 * Dữ liệu: wizardState.maNganh = [{ma, ten, is_main}]. Phụ thuộc: pages/wizard.js.
 */
let _cachedCombos = null;
let _loadingCombos = false;

// Fallback combos if API is offline or returns error
const FALLBACK_COMBOS = [
    {
        id: "cntt",
        name: "Công nghệ thông tin & Phần mềm",
        icon: "fa-solid fa-laptop-code",
        badge_color: "#38bdf8",
        description: "Lập trình máy tính, tư vấn HTTT, xử lý dữ liệu, xuất bản phần mềm",
        danh_sach_nganh: [
            { ma: "6219", ten: "Lập trình máy tính khác", is_main: true },
            { ma: "6220", ten: "Tư vấn máy tính và quản lý cơ sở hạ tầng máy tính", is_main: false },
            { ma: "6290", ten: "Hoạt động dịch vụ máy tính và công nghệ thông tin khác", is_main: false },
            { ma: "6310", ten: "Cơ sở hạ tầng công nghệ thông tin, xử lý dữ liệu, lưu trữ và các hoạt động liên quan", is_main: false },
            { ma: "5829", ten: "Xuất bản phần mềm khác", is_main: false },
            { ma: "4651", ten: "Bán buôn máy tính, thiết bị ngoại vi và phần mềm", is_main: false }
        ]
    },
    {
        id: "tmdt",
        name: "Thương mại & Bán lẻ",
        icon: "fa-solid fa-cart-shopping",
        badge_color: "#fb923c",
        description: "Dịch vụ trung gian bán lẻ, bán lẻ tổng hợp, bán buôn tổng hợp & xúc tiến thương mại",
        danh_sach_nganh: [
            { ma: "4790", ten: "Hoạt động dịch vụ trung gian bán lẻ", is_main: true },
            { ma: "4719", ten: "Bán lẻ tổng hợp khác", is_main: false },
            { ma: "4690", ten: "Bán buôn tổng hợp", is_main: false },
            { ma: "8230", ten: "Tổ chức giới thiệu và xúc tiến thương mại", is_main: false },
            { ma: "8299", ten: "Hoạt động dịch vụ hỗ trợ kinh doanh khác còn lại chưa được phân vào đâu", is_main: false }
        ]
    },
    {
        id: "tuvan",
        name: "Tư vấn quản lý & Kế toán",
        icon: "fa-solid fa-briefcase",
        badge_color: "#c084fc",
        description: "Tư vấn quản lý doanh nghiệp, kế toán kiểm toán thuế, quảng cáo và nghiên cứu thị trường",
        danh_sach_nganh: [
            { ma: "7020", ten: "Hoạt động tư vấn quản lý kinh doanh và hoạt động tư vấn quản lý khác", is_main: true },
            { ma: "6920", ten: "Hoạt động liên quan đến kế toán, kiểm toán và tư vấn về thuế", is_main: false },
            { ma: "7310", ten: "Quảng cáo", is_main: false },
            { ma: "7320", ten: "Nghiên cứu thị trường và thăm dò dư luận", is_main: false },
            { ma: "8299", ten: "Hoạt động dịch vụ hỗ trợ kinh doanh khác còn lại chưa được phân vào đâu", is_main: false }
        ]
    },
    {
        id: "xaydung",
        name: "Xây dựng & Kiến trúc",
        icon: "fa-solid fa-helmet-safety",
        badge_color: "#facc15",
        description: "Xây dựng nhà ở, hoàn thiện công trình, điện nước, kiến trúc và tư vấn kỹ thuật",
        danh_sach_nganh: [
            { ma: "4101", ten: "Xây dựng nhà để ở", is_main: true },
            { ma: "4102", ten: "Xây dựng nhà không để ở", is_main: false },
            { ma: "4321", ten: "Lắp đặt hệ thống điện", is_main: false },
            { ma: "4322", ten: "Lắp đặt hệ thống cấp, thoát nước, hệ thống sưởi và điều hoà không khí", is_main: false },
            { ma: "4330", ten: "Hoàn thiện công trình xây dựng", is_main: false },
            { ma: "7110", ten: "Hoạt động kiến trúc và tư vấn kỹ thuật có liên quan", is_main: false }
        ]
    },
    {
        id: "bds",
        name: "Kinh doanh Bất động sản",
        icon: "fa-solid fa-building",
        badge_color: "#22c55e",
        description: "Kinh doanh BĐS, dịch vụ môi giới, tư vấn và trung gian bất động sản",
        danh_sach_nganh: [
            { ma: "6810", ten: "Kinh doanh bất động sản, quyền sử dụng đất thuộc chủ sở hữu, chủ sử dụng hoặc đi thuê", is_main: true },
            { ma: "6821", "ten": "Dịch vụ trung gian cho hoạt động bất động sản", is_main: false },
            { ma: "6829", "ten": "Hoạt động bất động sản khác trên cơ sở phí hoặc hợp đồng", is_main: false },
            { ma: "7020", "ten": "Hoạt động tư vấn quản lý kinh doanh và hoạt động tư vấn quản lý khác", is_main: false }
        ]
    },
    {
        id: "fb",
        name: "Nhà hàng & F&B",
        icon: "fa-solid fa-utensils",
        badge_color: "#f43f5e",
        description: "Nhà hàng, quán ăn, dịch vụ tiệc và dịch vụ phục vụ đồ uống",
        danh_sach_nganh: [
            { ma: "5610", ten: "Nhà hàng và các dịch vụ ăn uống phục vụ lưu động", is_main: true },
            { ma: "5621", ten: "Cung cấp dịch vụ ăn uống theo hợp đồng không thường xuyên với khách hàng", is_main: false },
            { ma: "5629", ten: "Dịch vụ ăn uống khác", is_main: false },
            { ma: "5630", ten: "Dịch vụ phục vụ đồ uống", is_main: false }
        ]
    },
    {
        id: "logistics",
        name: "Vận tải & Logistics",
        icon: "fa-solid fa-truck-fast",
        badge_color: "#06b6d4",
        description: "Vận tải hàng hóa bằng đường bộ, kho bãi và dịch vụ hỗ trợ vận tải",
        danh_sach_nganh: [
            { ma: "4933", ten: "Vận tải hàng hóa bằng đường bộ", is_main: true },
            { ma: "5210", ten: "Kho bãi và lưu giữ hàng hóa", is_main: false },
            { ma: "5229", ten: "Hoạt động dịch vụ hỗ trợ khác liên quan đến vận tải", is_main: false }
        ]
    },
    {
        id: "dulich",
        name: "Du lịch & Lưu trú",
        icon: "fa-solid fa-plane-departure",
        badge_color: "#10b981",
        description: "Điều hành tour du lịch, đại lý lữ hành, dịch vụ lưu trú khách sạn",
        danh_sach_nganh: [
            { ma: "7912", ten: "Điều hành tua du lịch", is_main: true },
            { ma: "7911", ten: "Đại lý lữ hành", is_main: false },
            { ma: "7990", ten: "Hoạt động liên quan đến du lịch khác", is_main: false },
            { ma: "5510", ten: "Khách sạn và dịch vụ lưu trú tương tự", is_main: false }
        ]
    }
];

// Small toast notification helper
let _nganhToastTimer = null;
function showNganhToast(message, type) {
    type = type || 'success';
    let toast = document.getElementById('wizard-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'wizard-toast';
        toast.className = 'wizard-toast toast-out';
        document.body.appendChild(toast);
    }
    const icon = type === 'success' 
        ? '<i class="fa-solid fa-circle-check" style="color: var(--accent-green, #22c55e);"></i>' 
        : '<i class="fa-solid fa-circle-info" style="color: var(--accent-cyan, #38bdf8);"></i>';
    toast.innerHTML = `${icon} <span>${escapeHtml(message)}</span>`;
    toast.className = 'wizard-toast toast-in';
    clearTimeout(_nganhToastTimer);
    _nganhToastTimer = setTimeout(() => {
        toast.className = 'wizard-toast toast-out';
    }, 2500);
}
if (!window.showToast) {
    window.showToast = function(msg) {
        showNganhToast(msg, 'info');
    };
}

window.loadCombos = async function() {
    const container = document.getElementById('combo-nganh-list');
    if (!container) return;

    if (_cachedCombos) {
        renderComboPills(_cachedCombos);
        return;
    }

    if (_loadingCombos) return;
    _loadingCombos = true;

    try {
        const res = await fetch('/api/nganh/combos');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        _cachedCombos = (data && data.combos && data.combos.length > 0) ? data.combos : FALLBACK_COMBOS;
    } catch (err) {
        console.warn('Không tải được combos từ API, sử dụng danh sách fallback:', err);
        _cachedCombos = FALLBACK_COMBOS;
    } finally {
        _loadingCombos = false;
        renderComboPills(_cachedCombos);
    }
};

function renderComboPills(combos) {
    const container = document.getElementById('combo-nganh-list');
    if (!container) return;

    if (!combos || combos.length === 0) {
        container.innerHTML = '<span class="text-xs text-muted">Không có gói ngành có sẵn</span>';
        return;
    }

    const selectedCodes = new Set((window.wizardState.maNganh || []).map(n => n.ma));

    container.innerHTML = combos.map(c => {
        const count = c.danh_sach_nganh ? c.danh_sach_nganh.length : 0;
        const isAllSelected = count > 0 && c.danh_sach_nganh.every(n => selectedCodes.has(n.ma));
        const colorStyle = c.badge_color ? `style="--combo-color: ${c.badge_color};"` : '';
        const tooltip = escapeHtml(`${c.description || c.name} (${count} mã ngành)`);

        return `
            <button type="button" 
                    class="combo-pill ${isAllSelected ? 'active' : ''}" 
                    id="combo-pill-${c.id}" 
                    onclick="applyCombo('${c.id}')"
                    data-tooltip="${tooltip}"
                    title="${tooltip}"
                    ${colorStyle}>
                <i class="${c.icon || 'fa-solid fa-briefcase'} combo-icon"></i>
                <span class="combo-name">${escapeHtml(c.name)}</span>
                <span class="combo-badge-count">${count} ngành</span>
                <i class="fa-solid fa-check combo-check"></i>
            </button>
        `;
    }).join('');

    updateClearButtonVisibility();
}

window.applyCombo = function(comboId) {
    if (!_cachedCombos) return;
    const combo = _cachedCombos.find(c => c.id === comboId);
    if (!combo || !combo.danh_sach_nganh || combo.danh_sach_nganh.length === 0) return;

    if (!Array.isArray(window.wizardState.maNganh)) {
        window.wizardState.maNganh = [];
    }

    const currentList = window.wizardState.maNganh;
    const comboCodes = new Set(combo.danh_sach_nganh.map(n => n.ma));
    const allSelected = combo.danh_sach_nganh.every(n => currentList.some(item => item.ma === n.ma));

    if (allSelected) {
        // Toggle OFF: remove this combo's industries
        window.wizardState.maNganh = currentList.filter(item => !comboCodes.has(item.ma));
        
        // If main was removed, set the first remaining industry as main
        if (window.wizardState.maNganh.length > 0 && !window.wizardState.maNganh.some(item => item.is_main)) {
            window.wizardState.maNganh[0].is_main = true;
        }

        updateSelectedNganhUI();
        searchNganhNow();
        showNganhToast(`Đã bỏ chọn gói "${combo.name}"`, 'info');
        return;
    }

    // Toggle ON / Add combo industries
    let addedCount = 0;
    const hasAnyMain = currentList.some(item => item.is_main);

    combo.danh_sach_nganh.forEach(ci => {
        if (!currentList.some(existing => existing.ma === ci.ma)) {
            // If no industry in wizardState.maNganh is set as main, preserve the combo's main industry
            const isMain = (!hasAnyMain && (ci.is_main || (addedCount === 0 && currentList.length === 0)));
            currentList.push({
                ma: ci.ma,
                ten: ci.ten,
                is_main: !!isMain
            });
            addedCount++;
        }
    });

    // Ensure at least one industry has is_main = true
    if (currentList.length > 0 && !currentList.some(item => item.is_main)) {
        currentList[0].is_main = true;
    }

    updateSelectedNganhUI();
    searchNganhNow();

    if (addedCount > 0) {
        showNganhToast(`Đã thêm +${addedCount} mã ngành từ gói "${combo.name}"`, 'success');
    } else {
        showNganhToast(`Tất cả ngành trong gói "${combo.name}" đã có trong danh sách`, 'info');
    }
};

window.clearAllNganh = function() {
    if (!window.wizardState.maNganh || window.wizardState.maNganh.length === 0) return;
    const count = window.wizardState.maNganh.length;
    window.wizardState.maNganh = [];
    updateSelectedNganhUI();
    searchNganhNow();
    showNganhToast(`Đã xóa toàn bộ ${count} ngành nghề đã chọn`, 'info');
};

function updateComboPillsState() {
    if (!_cachedCombos) return;
    const selectedCodes = new Set((window.wizardState.maNganh || []).map(n => n.ma));

    _cachedCombos.forEach(c => {
        const el = document.getElementById(`combo-pill-${c.id}`);
        if (el) {
            const count = c.danh_sach_nganh ? c.danh_sach_nganh.length : 0;
            const isAllSelected = count > 0 && c.danh_sach_nganh.every(n => selectedCodes.has(n.ma));
            if (isAllSelected) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        }
    });

    updateClearButtonVisibility();
}

function updateClearButtonVisibility() {
    const clearBtn = document.getElementById('combo-clear-btn');
    if (clearBtn) {
        const hasItems = window.wizardState.maNganh && window.wizardState.maNganh.length > 0;
        clearBtn.style.display = hasItems ? 'inline-flex' : 'none';
    }
}

function renderStep3Nganh() {
    setTimeout(() => {
        if (window.loadCombos) window.loadCombos();
    }, 10);

    const hasSelected = window.wizardState.maNganh && window.wizardState.maNganh.length > 0;

    return `
        <div style="margin-bottom: var(--space-4);">
            <h2 class="text-2xl font-bold">Chọn ngành nghề kinh doanh</h2>
            <p class="text-secondary text-sm">Tìm kiếm và chọn các ngành nghề theo Hệ thống ngành kinh tế Việt Nam (VSIC). Ngành đầu tiên được chọn làm ngành chính.</p>
        </div>

        <!-- Combo Ngành Nhanh -->
        <div class="combo-nganh-wrapper">
            <div class="combo-header">
                <span class="combo-header-title">
                    <i class="fa-solid fa-wand-magic-sparkles text-orange"></i> Gợi ý theo gói ngành nghề phổ biến (Combo nhanh)
                </span>
                <button type="button" 
                        id="combo-clear-btn" 
                        class="combo-btn-clear" 
                        onclick="clearAllNganh()" 
                        style="display: ${hasSelected ? 'inline-flex' : 'none'};" 
                        title="Xóa tất cả ngành nghề đã chọn">
                    <i class="fa-solid fa-rotate-left"></i> Xóa tất cả đã chọn
                </button>
            </div>
            <div id="combo-nganh-list" class="combo-nganh-container">
                <div class="text-secondary text-xs" style="opacity: 0.7; padding: 4px 0;">
                    <i class="fa-solid fa-spinner fa-spin"></i> Đang tải gói ngành phổ biến...
                </div>
            </div>
        </div>

        <div class="form-group" style="margin-bottom: var(--space-4);">
            <div class="input-with-btn">
                <input type="text" id="nganh-search-input" class="form-control" placeholder="Nhập từ khóa (Ví dụ: phần mềm, bất động sản, thương mại, tư vấn...)" onkeyup="searchNganhDebounced(this.value)">
                <button type="button" class="btn btn-secondary" onclick="searchNganhNow()">
                    <i class="fa-solid fa-search"></i> Tìm
                </button>
            </div>
        </div>

        <div id="nganh-results" style="max-height: 220px; overflow-y: auto; background: rgba(0,0,0,0.25); border: 1px solid var(--border-glass); border-radius: var(--radius-md); padding: var(--space-2); margin-bottom: var(--space-6);">
            <div class="text-center py-6 text-muted text-sm">Nhập từ khóa phía trên để tra cứu mã ngành...</div>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-3);">
            <span class="font-bold text-sm text-secondary">Ngành nghề đã chọn (<span id="nganh-count">${window.wizardState.maNganh.length}</span>):</span>
            <span class="text-xs text-muted">Bấm vào biểu tượng ngôi sao để đổi ngành chính</span>
        </div>
        <div id="nganh-selected-container" style="min-height: 120px; background: rgba(0,0,0,0.15); border: 1px solid var(--border-glass); border-radius: var(--radius-md); padding: var(--space-3);">
            ${renderSelectedNganhList()}
        </div>
    `;
}

let _searchNganhTimeout = null;
function searchNganhDebounced(val) {
    clearTimeout(_searchNganhTimeout);
    _searchNganhTimeout = setTimeout(() => {
        searchNganh(val);
    }, 300);
}

function searchNganhNow() {
    const el = document.getElementById('nganh-search-input');
    if (el) searchNganh(el.value);
}

async function searchNganh(query) {
    const resBox = document.getElementById('nganh-results');
    if (!resBox) return;
    const q = (query || '').trim();
    if (!q) {
        resBox.innerHTML = '<div class="text-center py-6 text-muted text-sm">Nhập từ khóa phía trên để tra cứu mã ngành...</div>';
        return;
    }

    resBox.innerHTML = '<div class="text-center py-4 text-secondary text-sm"><i class="fa-solid fa-spinner fa-spin"></i> Đang tìm kiếm...</div>';

    try {
        const res = await fetch(`/api/nganh/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        const results = data.results || [];

        if (results.length === 0) {
            resBox.innerHTML = '<div class="text-center py-6 text-muted text-sm">Không tìm thấy mã ngành phù hợp.</div>';
            return;
        }

        let html = '';
        results.forEach(r => {
            const isAdded = window.wizardState.maNganh.some(n => n.ma === r.ma);
            html += `
                <div class="nganh-item">
                    <div style="flex: 1; padding-right: 12px;">
                        <div>
                            <span class="badge" style="margin-right: 8px; font-weight: bold;">${r.ma}</span>
                            <span class="text-sm font-bold text-white">${escapeHtml(r.ten)}</span>
                        </div>
                        ${r.match_note ? `
                            <div style="font-size: 11px; color: var(--accent-yellow, #f59e0b); margin-top: 3px; display: flex; align-items: center; gap: 4px;">
                                <i class="fa-solid fa-circle-info"></i> <span>${escapeHtml(r.match_note)}</span>
                            </div>
                        ` : ''}
                    </div>
                    <div>
                        ${isAdded ? `
                            <span class="badge badge-green"><i class="fa-solid fa-check"></i> Đã thêm</span>
                        ` : `
                            <button type="button" class="btn btn-secondary btn-sm" onclick="addNganh('${r.ma}', '${encodeURIComponent(r.ten)}')">
                                + Thêm
                            </button>
                        `}
                    </div>
                </div>
            `;
        });
        resBox.innerHTML = html;
    } catch (err) {
        console.error('Lỗi tìm ngành:', err);
        resBox.innerHTML = '<div class="text-center py-4 text-error text-sm">Lỗi kết nối tra cứu ngành nghề.</div>';
    }
}

window.addNganh = function(ma, encTen) {
    const ten = decodeURIComponent(encTen);
    if (!window.wizardState.maNganh.some(n => n.ma === ma)) {
        window.wizardState.maNganh.push({
            ma,
            ten,
            is_main: window.wizardState.maNganh.length === 0
        });
        updateSelectedNganhUI();
        searchNganhNow();
    }
};

window.removeNganh = function(ma) {
    window.wizardState.maNganh = window.wizardState.maNganh.filter(n => n.ma !== ma);
    if (window.wizardState.maNganh.length > 0 && !window.wizardState.maNganh.some(n => n.is_main)) {
        window.wizardState.maNganh[0].is_main = true;
    }
    updateSelectedNganhUI();
    searchNganhNow();
};

window.setMainNganh = function(ma) {
    window.wizardState.maNganh.forEach(n => {
        n.is_main = (n.ma === ma);
    });
    updateSelectedNganhUI();
};

function updateSelectedNganhUI() {
    const container = document.getElementById('nganh-selected-container');
    const countEl = document.getElementById('nganh-count');
    if (container) container.innerHTML = renderSelectedNganhList();
    if (countEl) countEl.innerText = window.wizardState.maNganh.length;
    updateComboPillsState();
}

function renderSelectedNganhList() {
    const list = window.wizardState.maNganh;
    if (list.length === 0) {
        return '<div class="text-center py-8 text-muted text-sm">Chưa có ngành nghề nào được chọn.</div>';
    }

    return list.map((n, idx) => `
        <div class="nganh-selected-item">
            <div style="display: flex; align-items: center; gap: 8px;">
                <button type="button" class="btn btn-ghost btn-sm" title="${n.is_main ? 'Ngành chính' : 'Đặt làm ngành chính'}" onclick="setMainNganh('${n.ma}')" style="color: ${n.is_main ? 'var(--accent-yellow)' : 'var(--text-muted)'}; padding: 2px 6px;">
                    <i class="fa-solid fa-star"></i>
                </button>
                <span class="badge font-bold">${n.ma}</span>
                <span class="text-sm ${n.is_main ? 'font-bold text-yellow' : 'text-white'}">${escapeHtml(n.ten)}</span>
                ${n.is_main ? '<span class="badge badge-orange" style="font-size: 10px;">Ngành chính</span>' : ''}
            </div>
            <button type="button" class="btn btn-ghost btn-sm text-error" onclick="removeNganh('${n.ma}')">
                <i class="fa-solid fa-trash"></i>
            </button>
        </div>
    `).join('');
}
