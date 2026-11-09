// Universal Schema-Driven Wizard for Webapp v2

window.wizardState = {
    step: 1,
    templatesList: [],
    template: null,
    schema: null,
    formData: {},
    thanhVienList: [],
    transferList: [],
    maNganh: [],
    dkkdSelected: []
};

// Client-side money & number to words helpers
function formatMoneyStr(val) {
    if (!val) return '';
    const digits = String(val).replace(/\D/g, '');
    if (!digits) return '';
    return Number(digits).toLocaleString('vi-VN');
}
window.formatMoneyStr = formatMoneyStr;
window.formatMoneyInput = function(input) {
    if (!input) return;
    const raw = String(input.value || '').replace(/\D/g, '');
    input.value = raw ? Number(raw).toLocaleString('vi-VN') : '';
};
window.formatCurrencyInput = window.formatMoneyInput;

function numToVietnameseWords(s) {
    if (!s) return '';
    const digits = String(s).replace(/\D/g, '');
    if (!digits) return '';
    if (/^0+$/.test(digits)) return 'Không đồng';

    const donVi = ['', 'nghìn', 'triệu', 'tỷ', 'nghìn tỷ', 'triệu tỷ'];
    const chuSo = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín'];

    function docBaChuSo(val, coNhomCao) {
        const tram = Math.floor(val / 100);
        const chuc = Math.floor((val % 100) / 10);
        const dv = val % 10;
        let res = '';

        if (tram > 0) {
            res += chuSo[tram] + ' trăm ';
            if (chuc === 0 && dv > 0) res += 'linh ';
        } else if (coNhomCao) {
            res += 'không trăm ';
            if (chuc === 0 && dv > 0) res += 'linh ';
        }

        if (chuc > 1) {
            res += chuSo[chuc] + ' mươi ';
            if (dv === 1) res += 'mốt ';
            else if (dv === 5) res += 'lăm ';
            else if (dv > 0) res += chuSo[dv] + ' ';
        } else if (chuc === 1) {
            res += 'mười ';
            if (dv === 1) res += 'một ';
            else if (dv === 5) res += 'lăm ';
            else if (dv > 0) res += chuSo[dv] + ' ';
        } else {
            if (dv > 0) res += chuSo[dv] + ' ';
        }
        return res.trim();
    }

    let chuoiKq = '';
    let tempN = BigInt(digits);
    let i = 0;
    while (tempN > 0n) {
        const phanBa = Number(tempN % 1000n);
        const coNhomCao = (tempN / 1000n) > 0n;
        if (phanBa > 0) {
            const docPhanBa = docBaChuSo(phanBa, coNhomCao);
            if (docPhanBa) {
                const prefix = donVi[i] ? donVi[i] + ' ' : '';
                chuoiKq = docPhanBa + ' ' + prefix + chuoiKq;
            }
        }
        tempN = tempN / 1000n;
        i++;
    }

    chuoiKq = chuoiKq.trim();
    if (!chuoiKq) return '';
    return chuoiKq.charAt(0).toUpperCase() + chuoiKq.slice(1) + ' đồng';
}
window.docSoThanhChu = numToVietnameseWords;

function renderWizard() {
    const isHarvey = window.isGlobalModernUI(); // true by default

    if (!isHarvey) {
        return `
            <!-- Navbar minimal -->
            <nav class="navbar">
                <div class="container navbar-container">
                    <a href="#/" class="navbar-brand">
                        <i class="fa-solid fa-building text-gradient"></i> NAC <span class="badge badge-green" style="font-size:10px;">v2 Jinja2</span>
                    </a>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <button type="button" class="btn btn-secondary btn-sm" onclick="toggleGlobalUIMode()">
                            <i class="fa-solid fa-scale-balanced" style="color: #d4af37;"></i> Dùng giao diện Harvey
                        </button>
                        <a href="#/" class="btn btn-ghost btn-sm"><i class="fa-solid fa-xmark"></i> Thoát</a>
                    </div>
                </div>
            </nav>

            <section class="section" style="padding-top: var(--space-24); min-height: 100vh; padding-bottom: var(--space-12);">
                <div class="container" style="max-width: 950px;">
                    <!-- Progress Bar -->
                    <div class="wizard-progress mb-6">
                        <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-2);" class="text-sm text-secondary font-bold" id="wizard-step-text">
                            <span>Bước 1/4: Chọn thủ tục</span>
                        </div>
                        <div style="width: 100%; height: 8px; background: var(--bg-glass); border-radius: var(--radius-full); overflow: hidden;">
                            <div id="wizard-progress-bar" style="width: 25%; height: 100%; background: var(--accent-gradient); transition: width 0.3s ease;"></div>
                        </div>
                    </div>

                    <!-- Wizard Content Area -->
                    <div id="wizard-content" class="card card-glass" style="min-height: 520px; position: relative;">
                        <!-- Injected here -->
                    </div>

                    <!-- Wizard Footer Controls -->
                    <div id="wizard-controls" style="display: flex; justify-content: space-between; margin-top: var(--space-6);">
                        <!-- Buttons -->
                    </div>
                </div>
            </section>
        `;
    }

    // HARVEY LEGAL TECH EXECUTIVE (FULL-WIDTH SPLIT-SCREEN NO SIDEBAR)
    return `
        <div class="harvey-app-shell">
            <!-- Top Command Bar -->
            <header class="harvey-topbar" style="position: sticky; top: 0; z-index: 100; height: 60px; padding: 0 32px; background: rgba(9, 14, 29, 0.94); backdrop-filter: blur(14px); border-bottom: 1px solid var(--gold-border-subtle); display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <a href="#/" style="text-decoration: none; display: flex; align-items: center; gap: 10px;">
                        <div class="harvey-seal-logo" style="width: 32px; height: 32px; font-size: 14px;"><i class="fa-solid fa-scale-balanced"></i></div>
                        <span class="harvey-brand-title" style="font-size: 14.5px;">HARVEY LEGAL OS</span>
                    </a>
                    <span style="color: var(--gold-border-subtle);">|</span>
                    <div class="harvey-breadcrumbs" id="harvey-breadcrumb">
                        <span style="color: var(--harvey-text-muted);">Pháp nhân</span>
                        <span style="color: var(--gold-primary);">/</span>
                        <span style="color: var(--harvey-text-muted);">Hồ sơ ĐKKD</span>
                        <span style="color: var(--gold-primary);">/</span>
                        <span style="color: var(--harvey-text-heading); font-weight: 600;" id="harvey-topbar-title">Chọn thủ tục doanh nghiệp</span>
                    </div>
                </div>

                <div class="harvey-search-bar" onclick="const inp = document.getElementById('search-tpl-input') || document.getElementById('harvey-quick-search'); if(inp) inp.focus();">
                    <i class="fa-solid fa-magnifying-glass" style="color: var(--gold-primary);"></i>
                    <input type="text" id="harvey-quick-search" placeholder="Tra cứu thủ tục, MST, mã ngành..." style="background: transparent; border: none; outline: none; color: #fff; width: 100%; font-size: 12.5px;" onkeyup="window.filterTemplates ? window.filterTemplates(this.value) : null">
                    <span style="font-family: var(--font-mono); font-size: 10.5px; background: rgba(212, 175, 55, 0.1); color: var(--gold-primary); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(212, 175, 55, 0.25);">⌘K</span>
                </div>

                <div style="display: flex; align-items: center; gap: 12px;">
                    <button type="button" class="btn harvey-btn-ghost btn-sm" onclick="toggleGlobalUIMode()" title="Chuyển về giao diện form truyền thống">
                        <i class="fa-solid fa-rotate-left"></i> Giao diện cũ
                    </button>
                    <a href="#/" class="btn harvey-btn-ghost btn-sm"><i class="fa-solid fa-house"></i> Trang chủ</a>
                </div>
            </header>

            <!-- Main Executive App Area -->
            <main class="harvey-main-area" style="width: 100%;">
                <div class="harvey-workspace" style="max-width: 1540px; width: 96%; margin: 26px auto 80px auto; padding: 0 16px;">
                    <!-- Progress Line -->
                    <div style="margin-bottom: 22px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div style="font-size: 13px; font-weight: 600; color: var(--gold-light);" id="wizard-step-text">
                                <span>Bước 1/4: Chọn thủ tục</span>
                            </div>
                        </div>
                        <div style="width: 100%; height: 5px; background: rgba(255,255,255,0.06); border-radius: 9999px; overflow: hidden;">
                            <div id="wizard-progress-bar" style="width: 25%; height: 100%; background: linear-gradient(90deg, #d4af37 0%, #3b82f6 100%); transition: width 0.3s ease;"></div>
                        </div>
                    </div>

                    <!-- Wizard Content Area -->
                    <div id="wizard-content" style="min-height: 520px; position: relative;">
                        <!-- Injected here -->
                    </div>

                    <!-- Wizard Footer Controls -->
                    <div id="wizard-controls" style="display: flex; justify-content: space-between; margin-top: 24px;">
                        <!-- Buttons -->
                    </div>
                </div>
            </main>
        </div>
    `;
}

window.updateSidebarNav = function() {
    const nav = document.getElementById('sidebar-procedures-nav');
    if (!nav) return;
    const list = window.wizardState.templatesList || [];
    if (!list.length) return;

    const currentTplName = window.wizardState.template ? window.wizardState.template.name : '';
    const categories = [...new Set(list.map(t => t.category || 'Khác'))];

    let html = '';
    categories.forEach(cat => {
        const items = list.filter(t => (t.category || 'Khác') === cat);
        html += `<div class="harvey-nav-group-title">${cat}</div>`;
        items.forEach(item => {
            const isActive = item.name === currentTplName ? 'active' : '';
            html += `
                <a class="harvey-nav-item ${isActive}" onclick="selectTemplate('${escapeHtml(item.name)}')">
                    <i class="fa-solid fa-file-contract"></i>
                    <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(item.display_name)}</span>
                    <span class="harvey-nav-badge">${item.file_count || 5}</span>
                </a>
            `;
        });
    });

    html += `
        <div class="harvey-nav-group-title" style="margin-top: 14px;">Quản trị Pháp lý</div>
        <a class="harvey-nav-item" onclick="if (window.showToast) window.showToast('Kho dữ liệu Pháp nhân & CCCD'); else alert('Kho dữ liệu Pháp nhân & CCCD');">
            <i class="fa-solid fa-building-user"></i>
            <span>Kho Pháp nhân & CCCD</span>
        </a>
        <a class="harvey-nav-item" onclick="if (window.showToast) window.showToast('Bộ biểu mẫu chuẩn hóa theo Nghị định 01/2021'); else alert('Bộ biểu mẫu chuẩn hóa (19 bộ)');">
            <i class="fa-solid fa-file-word"></i>
            <span>Mẫu biểu chuẩn (19 bộ)</span>
        </a>
    `;

    nav.innerHTML = html;
};

window.initWizard = async function() {
    window.wizardState = {
        step: 1,
        templatesList: [],
        template: null,
        schema: null,
        formData: {},
        thanhVienList: [],
        transferList: [],
        maNganh: [],
        dkkdSelected: []
    };

    renderCurrentStep();

    try {
        const res = await fetch('/api/templates');
        if (res.ok) {
            const data = await res.json();
            window.wizardState.templatesList = data.templates;
            renderCurrentStep();
            window.updateSidebarNav();
        }
    } catch (err) {
        console.error('Lỗi khi tải danh sách mẫu:', err);
    }
};

function renderCurrentStep() {
    const content = document.getElementById('wizard-content');
    const controls = document.getElementById('wizard-controls');
    const progressBar = document.getElementById('wizard-progress-bar');
    const stepText = document.getElementById('wizard-step-text');

    if (!content) return;

    content.style.opacity = '0';

    setTimeout(() => {
        const currentStep = window.wizardState.step;
        progressBar.style.width = `${(currentStep / 4) * 100}%`;

        const pCont = content.closest('.container');
        if (pCont) {
            if (currentStep === 1 || currentStep === 3) {
                pCont.style.maxWidth = '1300px';
                pCont.style.width = '96%';
                pCont.style.padding = '0 16px';
            } else if (currentStep === 4) {
                pCont.style.maxWidth = '1200px';
                pCont.style.width = '96%';
                pCont.style.padding = '0 16px';
            }
        }

        switch (currentStep) {
            case 1:
                stepText.innerHTML = '<span>Bước 1/4: Chọn thủ tục</span>';
                content.innerHTML = renderStep1();
                controls.innerHTML = `<button class="btn btn-ghost" disabled>Quay lại</button>`;
                break;
            case 2:
                stepText.innerHTML = `<span>Bước 2/4: Điền thông tin — <b>${window.wizardState.template.display_name}</b></span>`;
                content.innerHTML = renderStep2Loading();
                controls.innerHTML = `
                    <button class="btn btn-ghost" onclick="prevStep()">Quay lại</button>
                    <button class="btn btn-primary" onclick="nextStep()">Tiếp theo &rarr;</button>
                `;
                loadStep2Schema();
                break;
            case 3:
                stepText.innerHTML = '<span>Bước 3/4: Chọn mã ngành kinh doanh</span>';
                content.innerHTML = renderStep3Nganh();
                controls.innerHTML = `
                    <button class="btn btn-ghost" onclick="prevStep()">Quay lại</button>
                    <button class="btn btn-primary" onclick="nextStep()">Tiếp theo &rarr;</button>
                `;
                if (window.loadCombos) window.loadCombos();
                break;
            case 4:
                stepText.innerHTML = '<span>Bước 4/4: Xác nhận & Tải trọn bộ hồ sơ</span>';
                content.innerHTML = renderStep4Download();
                controls.innerHTML = `
                    <button class="btn btn-ghost" onclick="prevStep()" id="btn-back-final">Quay lại</button>
                    <button class="btn btn-primary" onclick="generateDocuments()" id="btn-download">
                        <i class="fa-solid fa-download"></i> Tải trọn bộ hồ sơ (.ZIP)
                    </button>
                `;
                break;
        }

        content.style.opacity = '1';
    }, 120);
}

// --- VALIDATION: dùng lõi chung static/js/engine/schema_engine.js (cùng hành vi với backend) ---
const TRANSFER_KEYS = new Set(['ben_a.ho_ten', 'ben_b.ho_ten', 'gia_tri_so']);

/** Dữ liệu wizard theo đúng key của schema (danh sách lưu riêng trong wizardState). */
function wizardDataForSchema(schema, blankLists) {
    const s = window.wizardState;
    const data = blankLists ? {} : Object.assign({}, s.formData || {});
    ((schema && schema.steps) || []).forEach(st => (st.fields || []).forEach(f => {
        let list = null;
        if (f.type === 'person_list') list = s.thanhVienList || [];
        else if (f.type === 'transfer_list') list = s.transferList || [];
        else if (f.type === 'checkbox_group') { if (!blankLists) data[f.key] = s.dkkdSelected || []; return; }
        if (list) data[f.key] = blankLists ? list.map(() => ({})) : list;
    }));
    return data;
}

/**
 * Lỗi dữ liệu [{label, name | member+prop | tr+path}] theo _schema.json, kèm errors.total
 * (số mục cần kiểm tra, dùng để tính % hoàn thiện).
 */
function validateRequiredFields(schema) {
    const out = [];
    out.total = 0;
    if (!schema || !schema.steps || !window.SchemaEngine) return out;
    SchemaEngine.validate(schema, wizardDataForSchema(schema, false)).forEach(e => {
        const item = { label: e.message };
        const list = window.FormRenderer ? FormRenderer.listOfError(e) : null;
        if (e.index === undefined) item.name = e.key;
        else if (list) { item.list = list; item.idx = e.index; item.key = e.key; }
        else if (TRANSFER_KEYS.has(e.key)) { item.tr = e.index; item.path = e.key; }
        else { item.member = e.index; item.prop = e.key; }
        out.push(item);
    });
    // Số mục cần kiểm tra = số lỗi khi form còn trống (giữ nguyên số dòng danh sách hiện có)
    out.total = Math.max(SchemaEngine.validate(schema, wizardDataForSchema(schema, true)).length, out.length);
    return out;
}
window.validateRequiredFields = validateRequiredFields;

/** Đánh dấu ô lỗi, focus ô đầu tiên và báo cho người dùng. Trả về true nếu hợp lệ. */
function ensureRequiredFields() {
    document.querySelectorAll('.input-invalid').forEach(el => el.classList.remove('input-invalid'));
    const errors = validateRequiredFields(window.wizardState.schema);
    if (window.FormRenderer) FormRenderer.showInlineErrors(document.getElementById('dynamic-form-container'), true);
    if (errors.length === 0) return true;

    let firstEl = null;
    errors.forEach(e => {
        let el = null;
        if (e.name) el = document.querySelector(`[name="${e.name}"]`);
        else if (e.list) {
            el = document.querySelector(`.lf-field[data-list="${CSS.escape(e.list)}"][data-idx="${e.idx}"][data-key="${CSS.escape(e.key)}"]`);
        }
        else if (e.member !== undefined) {
            el = document.querySelector(`.m-field[data-idx="${e.member}"][data-prop="${e.prop}"]`);
        }
        else if (e.tr !== undefined) el = document.querySelector(`.tr-field[data-idx="${e.tr}"][data-path="${e.path}"]`);
        if (el) {
            el.classList.add('input-invalid');
            if (!firstEl) firstEl = el;
        }
    });
    if (firstEl) {
        firstEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstEl.focus({ preventScroll: true });
    }
    const shown = errors.slice(0, 8).map(e => '• ' + e.label).join('\n');
    const more = errors.length > 8 ? `\n... và ${errors.length - 8} trường khác` : '';
    alert(`Vui lòng kiểm tra lại các thông tin sau:\n${shown}${more}`);
    return false;
}
window.ensureRequiredFields = ensureRequiredFields;

window.nextStep = function() {
    if (window.wizardState.step === 2) {
        collectFormData();
        if (!ensureRequiredFields()) return;
        // Check if template has nganh
        const hasNganh = window.wizardState.schema && window.wizardState.schema.has_nganh;
        if (!hasNganh) {
            // Skip step 3 directly to 4
            window.wizardState.step = 4;
            renderCurrentStep();
            return;
        }
    }

    if (window.wizardState.step < 4) {
        window.wizardState.step++;
        renderCurrentStep();
    }
};

window.prevStep = function() {
    if (window.wizardState.step === 4) {
        const hasNganh = window.wizardState.schema && window.wizardState.schema.has_nganh;
        if (!hasNganh) {
            window.wizardState.step = 2;
            renderCurrentStep();
            return;
        }
    }

    if (window.wizardState.step > 1) {
        window.wizardState.step--;
        renderCurrentStep();
    }
};

window.selectTemplate = function(name) {
    window.wizardState.template = window.wizardState.templatesList.find(t => t.name === name);
    window.wizardState.step = 2;
    renderCurrentStep();
    if (window.updateSidebarNav) window.updateSidebarNav();
};

// --- STEP 1: PROCEDURE SELECTION ---
function renderStep1() {
    const list = window.wizardState.templatesList;
    if (!list || list.length === 0) {
        return `
            <div class="text-center py-12">
                <i class="fa-solid fa-spinner fa-spin fa-2x text-cyan"></i>
                <p class="mt-4 text-secondary">Đang tải danh sách biểu mẫu...</p>
            </div>
        `;
    }

    const categories = [...new Set(list.map(t => t.category || 'Khác'))];

    let html = `
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: var(--space-4);">
            <div>
                <h2 class="text-2xl font-bold">Chọn thủ tục doanh nghiệp</h2>
                <p class="text-secondary text-sm">Hệ thống hỗ trợ 19 bộ mẫu hồ sơ chuẩn hóa theo quy định mới nhất</p>
            </div>
            <div style="width: 260px;">
                <input type="text" id="search-tpl-input" class="form-control" placeholder="Tìm thủ tục..." onkeyup="filterTemplates(this.value)">
            </div>
        </div>
        <div id="templates-container" style="display: flex; flex-direction: column; gap: var(--space-6);">
    `;

    categories.forEach(cat => {
        const items = list.filter(t => (t.category || 'Khác') === cat);
        html += `
            <div class="cat-group">
                <h3 class="text-md font-bold mb-3 text-gradient">${cat} (${items.length})</h3>
                <div class="grid-2">
        `;
        items.forEach(item => {
            html += `
                <div class="card card-sub card-clickable tpl-item" onclick="selectTemplate('${item.name}')">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-2);">
                        <h4 class="font-bold text-md" style="color: #fff;">${item.display_name}</h4>
                        <span class="badge">${item.file_count} biểu mẫu</span>
                    </div>
                    <p class="text-secondary text-xs mb-3">${item.description || 'Bộ hồ sơ đầy đủ các văn bản pháp lý theo quy định.'}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="badge badge-green" style="font-size: 11px;">Jinja2 Template</span>
                        <span class="text-cyan text-xs font-bold">Bắt đầu <i class="fa-solid fa-arrow-right"></i></span>
                    </div>
                </div>
            `;
        });
        html += `</div></div>`;
    });

    html += `</div>`;
    return html;
}

window.filterTemplates = function(query) {
    const q = query.toLowerCase().trim();
    const items = document.querySelectorAll('.tpl-item');
    items.forEach(el => {
        const txt = el.innerText.toLowerCase();
        el.style.display = txt.includes(q) ? 'block' : 'none';
    });
};

// --- STEP 2: SCHEMA-DRIVEN FORM ---
function renderStep2Loading() {
    return `
        <div class="text-center py-12">
            <i class="fa-solid fa-circle-notch fa-spin fa-2x text-cyan"></i>
            <p class="mt-4 text-secondary">Đang tải cấu trúc biểu mẫu...</p>
        </div>
    `;
}

async function loadStep2Schema() {
    const tplName = window.wizardState.template.name;
    const content = document.getElementById('wizard-content');

    try {
        const res = await fetch(`/api/templates/${encodeURIComponent(tplName)}/schema`);
        if (!res.ok) throw new Error('Schema not found');
        const schema = await res.json();
        await loadCatalogsForSchema(schema);
        window.wizardState.schema = schema;

        // Initialize person list if schema has person_list
        const steps = schema.steps || [];
        steps.forEach(st => {
            (st.fields || []).forEach(f => {
                if (f.type === 'person_list' && (!window.wizardState.thanhVienList || window.wizardState.thanhVienList.length === 0)) {
                    const min = f.min || 1;
                    window.wizardState.thanhVienList = [];
                    for (let i = 0; i < min; i++) {
                        window.wizardState.thanhVienList.push({
                            stt: i + 1,
                            ho_ten: '',
                            gioi_tinh: 'Nam',
                            ngay_sinh: '',
                            so_cccd: '',
                            dia_chi_so_nha: '',
                            dia_chi_xa_phuong: '',
                            dia_chi_tinh_thanh: '',
                            von_gop: '',
                            ty_le: ''
                        });
                    }
                }
                if (f.type === 'transfer_list' && (!window.wizardState.transferList || window.wizardState.transferList.length === 0)) {
                    window.wizardState.transferList = [{
                        ben_a: { ho_ten: '', so_cccd: '', dia_chi_day_du: '' },
                        ben_b: { ho_ten: '', so_cccd: '', dia_chi_so_nha: '', dia_chi_xa_phuong: '', dia_chi_tinh_thanh: '' },
                        gia_tri_so: '',
                        ty_le: ''
                    }];
                }
            });
        });

        renderStep2Form(schema);
    } catch (err) {
        console.error('Lỗi tải schema:', err);
        const content = document.getElementById('wizard-content');
        if (content) {
            content.innerHTML = `
                <div class="text-center py-12 text-error">
                    <i class="fa-solid fa-triangle-exclamation fa-2x"></i>
                    <p class="mt-4">Không tìm thấy cấu trúc biểu mẫu cho "${tplName}".</p>
                </div>
            `;
        }
    }
}

// escapeHtml() được định nghĩa dùng chung trong /static/js/utils.js

window.isGlobalModernUI = function() {
    return localStorage.getItem('global_ui_mode') !== 'legacy';
};

window.toggleGlobalUIMode = function() {
    const current = window.isGlobalModernUI();
    localStorage.setItem('global_ui_mode', current ? 'legacy' : 'modern');
    if (window.wizardState && window.wizardState.step === 2 && window.wizardState.schema) {
        renderStep2Form(window.wizardState.schema);
    }
};

window.previewDocInfo = function(docName) {
    if (window.showToast) {
        window.showToast(`Biểu mẫu "${docName}" đã sẵn sàng và sẽ được tạo tự động với đầy đủ dữ liệu.`);
    } else {
        alert(`Biểu mẫu "${docName}" sẽ được tạo tự động khi bạn xuất hồ sơ.`);
    }
};

/** % hoàn thiện thật: số mục hợp lệ / số mục cần kiểm tra theo _schema.json (cùng lõi kiểm tra với backend). */
window.updateUniversalCompleteness = function() {
    if (!window.wizardState || !window.wizardState.schema) return;
    const errors = validateRequiredFields(window.wizardState.schema);
    const total = errors.total || 0;
    const pct = total ? Math.round(((total - errors.length) / total) * 100) : 100;
    const scoreEl = document.getElementById('universal-completeness-score');
    const fillEl = document.getElementById('universal-progress-fill');
    if (scoreEl) scoreEl.innerText = `${pct}%`;
    if (fillEl) fillEl.style.width = `${pct}%`;
};

window.updateUniversalCapitalDistribution = function() {
    const vonInput = document.getElementById('input-von_dieu_le_so');
    const container = document.getElementById('universal-capital-bar-container');
    if (!container) return;

    if (!vonInput) {
        container.innerHTML = '';
        return;
    }

    const totalVon = parseInt(vonInput.value.replace(/\D/g, '') || '0', 10);
    const memberList = window.wizardState.thanhVienList || [];
    if (!memberList.length || totalVon <= 0) {
        container.innerHTML = '';
        return;
    }

    const colors = ['#f97316', '#3b82f6', '#10b981', '#a855f7', '#ec4899', '#eab308', '#06b6d4'];
    let distributed = 0;
    let segmentsHtml = '';
    let badgesHtml = '';

    memberList.forEach((m, idx) => {
        const mInput = document.querySelector(`.m-field[data-idx="${idx}"][data-prop="von_gop"]`);
        const valStr = mInput ? mInput.value : (m.von_gop || '0');
        const mVal = parseInt(String(valStr).replace(/\D/g, '') || '0', 10);
        distributed += mVal;

        const pct = ((mVal / totalVon) * 100).toFixed(1);
        const color = colors[idx % colors.length];
        const nameInput = document.querySelector(`.m-field[data-idx="${idx}"][data-prop="ho_ten"]`);
        const name = (nameInput && nameInput.value) ? nameInput.value : (m.ho_ten || `Thành viên ${idx + 1}`);

        if (mVal > 0) {
            segmentsHtml += `<div style="width: ${pct}%; background: ${color}; height: 100%; transition: width 0.3s;" title="${escapeHtml(name)}: ${pct}% (${formatMoneyStr(String(mVal))} đ)"></div>`;
        }
        badgesHtml += `
            <div style="display: flex; align-items: center; gap: 6px; font-size: 12px; background: rgba(0,0,0,0.2); padding: 4px 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.06);">
                <span style="display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: ${color};"></span>
                <span style="color: var(--text-secondary); max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(name)}:</span>
                <b style="color: ${color}; font-family: var(--font-mono);">${pct}%</b>
            </div>
        `;
    });

    const remain = totalVon - distributed;
    const remainPct = ((remain / totalVon) * 100).toFixed(1);

    let statusBadge = '';
    if (remain === 0) {
        statusBadge = '<span class="badge badge-green"><i class="fa-solid fa-check"></i> Khớp 100% vốn</span>';
    } else if (remain > 0) {
        statusBadge = `<span class="badge" style="background: rgba(234, 179, 8, 0.2); color: #facc15;"><i class="fa-solid fa-triangle-exclamation"></i> Còn thiếu: ${formatMoneyStr(String(remain))} đ (${remainPct}%)</span>`;
    } else {
        statusBadge = `<span class="badge badge-red"><i class="fa-solid fa-triangle-exclamation"></i> Vượt mức: +${formatMoneyStr(String(Math.abs(remain)))} đ</span>`;
    }

    container.innerHTML = `
        <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-glass); border-radius: var(--radius-md); padding: 14px 16px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 13px; font-weight: 700; color: #fff;">
                    <i class="fa-solid fa-chart-pie text-cyan"></i> Phân bổ vốn điều lệ (${formatMoneyStr(String(totalVon))} đ)
                </span>
                <div>${statusBadge}</div>
            </div>
            <div style="height: 10px; background: rgba(255,255,255,0.07); border-radius: 5px; overflow: hidden; display: flex; margin-bottom: 10px;">
                ${segmentsHtml || '<div style="width: 100%; background: rgba(255,255,255,0.08);"></div>'}
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px 12px;">
                ${badgesHtml}
            </div>
        </div>
    `;
};

function renderStep2Form(schema) {
    const content = document.getElementById('wizard-content');
    if (!content) return;

    const isModern = window.isGlobalModernUI();
    const parentContainer = content.closest('.container');
    if (parentContainer) {
        parentContainer.style.maxWidth = isModern ? '1540px' : '950px';
        parentContainer.style.width = isModern ? '96%' : '100%';
        parentContainer.style.padding = '0 16px';
    }

    if (!isModern) {
        let html = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-4); gap: 16px;">
                <div>
                    <h2 class="text-2xl font-bold">${schema.display_name}</h2>
                    <p class="text-secondary text-sm">${schema.description || ''}</p>
                </div>
                <button type="button" class="btn btn-secondary btn-sm" onclick="toggleGlobalUIMode()" style="white-space: nowrap;">
                    <i class="fa-solid fa-scale-balanced" style="color: #d4af37;"></i> Dùng giao diện Harvey
                </button>
            </div>
            <div id="dynamic-form-container" style="display: flex; flex-direction: column; gap: var(--space-6);">
        `;

        html += FormRenderer.renderSteps(schema, (step, sIdx, total, inner) => `
                <div class="card-sub" style="border-left: 4px solid var(--accent-primary);">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: var(--space-4);">
                        <i class="fa-solid fa-clipboard-list text-cyan"></i>
                        <h3 class="font-bold text-lg">${escapeHtml(step.title)}</h3>
                    </div>
                    <div>${inner}</div>
                </div>`);

        html += `</div>`;
        content.innerHTML = html;
        FormRenderer.attach(document.getElementById('dynamic-form-container'));
        return;
    }

    // HARVEY LEGAL TECH EXECUTIVE STUDIO (SPLIT-SCREEN + SIDEBAR READY)
    const docFiles = schema.doc_files || [];
    const docCount = docFiles.length || (schema.file_count || 0);

    let docListHtml = '';
    if (docFiles.length > 0) {
        docListHtml = docFiles.map((doc, idx) => {
            const cleanName = doc.replace(/\.docx$/i, '');
            return `
                <div class="brief-item" title="${escapeHtml(doc)}" onclick="previewDocInfo('${escapeHtml(doc)}')">
                    <span class="brief-item-left">
                        <i class="fa-solid fa-file-contract"></i>
                        <span>${escapeHtml(cleanName)}</span>
                    </span>
                    <span class="seal-check"><i class="fa-solid fa-circle-check"></i></span>
                </div>
            `;
        }).join('');
    } else {
        docListHtml = `
            <div class="text-center py-6 text-sm" style="border: 1px dashed var(--gold-border-subtle); border-radius: var(--radius-sm); color: var(--harvey-text-muted);">
                <i class="fa-solid fa-file-contract fa-2x mb-2" style="opacity: 0.5; color: var(--gold-primary);"></i>
                <div>Bộ hồ sơ gồm các biểu mẫu chuẩn hóa theo Nghị định 01/2021/NĐ-CP</div>
            </div>
        `;
    }

    const formStepsHtml = FormRenderer.renderSteps(schema, (step, sIdx, total, inner) => `
            <div class="harvey-card">
                <div class="card-header-bar">
                    <div class="card-title">
                        <i class="fa-solid fa-landmark"></i>
                        <span>${escapeHtml(step.title)}</span>
                    </div>
                    <span class="legal-seal-badge">MỤC ${sIdx + 1}/${total}</span>
                </div>
                <div>${inner}</div>
            </div>`);

    const ctaBtnHtml = schema.has_nganh ? `
        <button type="button" class="btn harvey-btn-gold" style="width: 100%; padding: 13px;" onclick="nextStep()">
            <i class="fa-solid fa-arrow-right"></i> Tiếp tục: Chọn ngành nghề &rarr;
        </button>
    ` : `
        <button type="button" class="btn harvey-btn-gold" style="width: 100%; padding: 13px;" onclick="generateDocuments()">
            <i class="fa-solid fa-stamp"></i> Xuất Trọn Bộ Hồ Sơ (.ZIP)
        </button>
    `;

    const html = `
        <div>
            <!-- Executive KPI Strip -->
            <div class="harvey-kpi-grid">
                <div class="harvey-kpi-card">
                    <div>
                        <div class="kpi-label">VĂN BẢN CHUẨN HÓA</div>
                        <div class="harvey-kpi-num" id="kpi-doc-count">${docCount} Files Word</div>
                        <div style="font-size: 11px; color: var(--status-green); margin-top: 3px;"><i class="fa-solid fa-check"></i> Đủ bộ theo NĐ 01/2021</div>
                    </div>
                    <div class="kpi-icon-box" style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: rgba(212, 175, 55, 0.08); border: 1px solid var(--gold-border-subtle); display: flex; align-items: center; justify-content: center; color: var(--gold-primary); font-size: 15px;"><i class="fa-solid fa-file-contract"></i></div>
                </div>

                <div class="harvey-kpi-card">
                    <div>
                        <div class="kpi-label">TỔNG VỐN ĐIỀU LỆ</div>
                        <div class="harvey-kpi-num" id="kpi-capital-val">${formatMoneyStr(String(window.wizardState.formData['von_dieu_le_so'] || '0')) || '0'} đ</div>
                        <div style="font-size: 11px; color: var(--gold-primary); margin-top: 3px;" id="kpi-capital-status"><i class="fa-solid fa-coins"></i> Cân đối phần vốn</div>
                    </div>
                    <div class="kpi-icon-box" style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: rgba(212, 175, 55, 0.08); border: 1px solid var(--gold-border-subtle); display: flex; align-items: center; justify-content: center; color: var(--gold-primary); font-size: 15px;"><i class="fa-solid fa-vault"></i></div>
                </div>

                <div class="harvey-kpi-card">
                    <div>
                        <div class="kpi-label">THÀNH VIÊN SÁNG LẬP</div>
                        <div class="harvey-kpi-num" id="kpi-member-count">${(window.wizardState.thanhVienList || []).length} Người</div>
                        <div style="font-size: 11px; color: var(--status-green); margin-top: 3px;"><i class="fa-solid fa-id-card"></i> VNeID Verified</div>
                    </div>
                    <div class="kpi-icon-box" style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: rgba(212, 175, 55, 0.08); border: 1px solid var(--gold-border-subtle); display: flex; align-items: center; justify-content: center; color: var(--gold-primary); font-size: 15px;"><i class="fa-solid fa-users"></i></div>
                </div>

                <div class="harvey-kpi-card">
                    <div style="flex: 1;">
                        <div class="kpi-label">MỨC HOÀN THIỆN</div>
                        <div class="harvey-kpi-num" id="universal-completeness-score">0%</div>
                        <div style="height: 4px; margin-top: 6px; border-radius: 2px; background: rgba(255,255,255,0.08); overflow: hidden;">
                            <div id="universal-progress-fill" style="height: 100%; width: 0%; background: var(--gold-primary); transition: width 0.3s;"></div>
                        </div>
                    </div>
                    <div class="kpi-icon-box" style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: rgba(212, 175, 55, 0.08); border: 1px solid var(--gold-border-subtle); display: flex; align-items: center; justify-content: center; color: var(--gold-primary); font-size: 15px;"><i class="fa-solid fa-list-check"></i></div>
                </div>
            </div>

            <!-- Citation Banner Line -->
            <div class="hero-banner-line">
                <div>
                    <div class="hero-citation">
                        <i class="fa-solid fa-certificate"></i> NGHỊ ĐỊNH 01/2021/NĐ-CP &bull; LUẬT DOANH NGHIỆP 2020
                    </div>
                    <h2 class="hero-heading">${escapeHtml(schema.display_name)}</h2>
                    <p class="hero-subtext">${escapeHtml(schema.description || 'Quy trình thẩm định và tự động lập trọn bộ hồ sơ pháp lý doanh nghiệp chuẩn hóa với Sở Kế hoạch & Đầu tư')}</p>
                </div>
                <div>
                    <span class="legal-seal-badge" style="padding: 6px 12px; font-size: 11px;">
                        <i class="fa-solid fa-award"></i> HARVEY VERIFIED LEGAL DOSSIER
                    </span>
                </div>
            </div>

            <!-- Studio 2-Column Split Grid -->
            <div class="studio-grid">
                <!-- Left Form Column -->
                <div class="form-col">
                    <div id="dynamic-form-container" style="display: flex; flex-direction: column; gap: 20px;">
                        ${formStepsHtml}
                    </div>
                </div>

                <!-- Right Column: Executive Legal Brief -->
                <div class="brief-col">
                    <div class="brief-card">
                        <div class="brief-header">
                            <div class="brief-title">
                                <i class="fa-solid fa-scroll"></i>
                                <span>Bảng Thẩm Định Hồ Sơ</span>
                            </div>
                            <span class="brief-status-tag"><i class="fa-solid fa-shield-check"></i> HỢP LỆ</span>
                        </div>

                        <div style="font-size: 12px; color: var(--harvey-text-muted); margin-bottom: 12px;">
                            Hồ sơ pháp lý tạo bởi Jinja2 docxtpl engine:
                        </div>

                        <div class="brief-list" id="brief-items-list">
                            ${docListHtml}
                        </div>

                        ${ctaBtnHtml}

                        <div style="margin-top: 14px; font-size: 11.5px; color: var(--gold-light); text-align: center; opacity: 0.85;">
                            <i class="fa-solid fa-award"></i> Tiêu chuẩn chứng thực văn bản pháp lý quốc gia
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    content.innerHTML = html;

    // Attach listener & initial calculations
    const formContainer = document.getElementById('dynamic-form-container');
    FormRenderer.attach(formContainer);
    if (formContainer) {
        // Sau listener của FormRenderer.attach (đã thu dữ liệu vào wizardState)
        ['input', 'change'].forEach(ev => {
            formContainer.removeEventListener(ev, updateUniversalCompleteness);
            formContainer.addEventListener(ev, updateUniversalCompleteness);
        });
        updateUniversalCompleteness();
    }
    setTimeout(() => {
        if (window.updateUniversalCapitalDistribution) {
            window.updateUniversalCapitalDistribution();
        }
    }, 50);
}

function renderField(field) {
    const fKey = field.key;
    const fLabel = field.label;
    const reqBadge = field.required ? '<span class="text-error">*</span>' : '';
    const curVal = window.wizardState.formData[fKey] || '';

    // MST Lookup
    if (field.type === 'mst_lookup') {
        return `
            <div class="form-group">
                <label class="form-label">${fLabel} ${reqBadge}</label>
                <div class="input-with-btn">
                    <input type="text" id="input-${fKey}" name="${fKey}" value="${escapeHtml(curVal)}" class="form-control font-mono font-bold" placeholder="Nhập mã số thuế (10 hoặc 13 số)" onkeydown="if(event.key==='Enter'){event.preventDefault();lookupMST('${fKey}');}">
                    <button type="button" class="btn btn-secondary btn-sm" onclick="lookupMST('${fKey}')">
                        <i class="fa-solid fa-search"></i> Tra cứu
                    </button>
                </div>
                <div id="mst-status" class="text-xs text-secondary mt-1"></div>
            </div>
        `;
    }

    // Money field
    if (field.type === 'money') {
        const spellout = curVal ? numToVietnameseWords(curVal) : '';
        return `
            <div class="form-group">
                <label class="form-label">${fLabel} ${reqBadge}</label>
                <input type="text" id="input-${fKey}" name="${fKey}" value="${escapeHtml(curVal ? formatMoneyStr(curVal) : '')}" class="form-control" placeholder="Ví dụ: 1,000,000,000" onkeyup="handleMoneyChange(this, 'spellout-${fKey}')">
                <div id="spellout-${fKey}" class="money-spellout">${spellout ? 'Bằng chữ: ' + spellout : ''}</div>
            </div>
        `;
    }

    // Person field (single person with OCR)
    if (field.type === 'person') {
        return renderPersonCard(fKey, fLabel, field.ocr);
    }

    // Person List field (dynamic multiple persons)
    if (field.type === 'person_list') {
        return renderPersonList(field);
    }

    // Transfer List field
    if (field.type === 'transfer_list') {
        return renderTransferList(field);
    }

    // Checkbox Group
    if (field.type === 'checkbox_group') {
        let opts = '';
        (field.options || []).forEach(opt => {
            const checked = window.wizardState.dkkdSelected.includes(opt.value) ? 'checked' : '';
            opts += `
                <label style="display: flex; align-items: center; gap: 8px; font-size: var(--font-size-sm); margin-bottom: 6px; cursor: pointer;">
                    <input type="checkbox" class="dkkd-cb" value="${escapeHtml(opt.value)}" ${checked}>
                    <span>${opt.label}</span>
                </label>
            `;
        });
        return `
            <div class="form-group">
                <label class="form-label">${fLabel}</label>
                <div style="background: rgba(0,0,0,0.2); padding: var(--space-3); border-radius: var(--radius-sm); border: 1px solid var(--border-glass);">
                    ${opts}
                </div>
            </div>
        `;
    }

    // Ô chọn (danh sách sổ xuống): lựa chọn từ field.options hoặc danh mục dùng chung (options_source)
    if (field.type === 'select') {
        const cat = field.options_source ? window.__catalogs[field.options_source] : null;
        let val = curVal || field.default || (cat && cat.defaultValue) || '';
        if (val && !window.wizardState.formData[fKey]) window.wizardState.formData[fKey] = val;
        return `
            <div class="form-group">
                <label class="form-label">${fLabel} ${reqBadge}</label>
                <select id="input-${fKey}" name="${fKey}" class="form-control">
                    ${val ? '' : '<option value="">-- Chọn --</option>'}
                    ${renderSelectOptions(getCatalogOptions(field), val)}
                </select>
            </div>
        `;
    }

    // Standard text / phone / email
    const inputType = field.type === 'phone' ? 'tel' : field.type === 'email' ? 'email' : 'text';
    return `
        <div class="form-group">
            <label class="form-label">${fLabel} ${reqBadge}</label>
            <input type="${inputType}" id="input-${fKey}" name="${fKey}" value="${escapeHtml(curVal)}" class="form-control" placeholder="${escapeHtml(field.placeholder)}">
        </div>
    `;
}

function handleMoneyChange(input, spelloutId) {
    const raw = input.value.replace(/\D/g, '');
    input.value = raw ? Number(raw).toLocaleString('vi-VN') : '';
    const words = raw ? (window.docSoThanhChu ? window.docSoThanhChu(raw) : numToVietnameseWords(raw)) : '';
    const sp = document.getElementById(spelloutId);
    if (sp) {
        sp.innerText = words ? 'Bằng chữ: ' + words : '';
    }

    // Tự động tìm ô số vốn bằng chữ tương ứng trên form để điền (nếu có)
    const fKey = input.name || input.id.replace('input-', '');
    let chuKey = '';
    if (fKey.endsWith('_so')) {
        chuKey = fKey.replace(/_so$/, '_chu');
    } else {
        chuKey = fKey + '_chu';
    }

    const chuInput = document.getElementById(`input-${chuKey}`) || document.querySelector(`[name="${chuKey}"]`);
    if (chuInput && words) {
        chuInput.value = words;
        if (window.wizardState && window.wizardState.formData) {
            window.wizardState.formData[chuKey] = words;
        }
    }

    // Nếu sửa vốn điều lệ, tự tính lại tỷ lệ của tất cả các thành viên
    if (fKey === 'von_dieu_le_so' || input.id === 'input-von_dieu_le_so') {
        const totalVon = parseInt(raw || '0', 10);
        if (totalVon > 0) {
            (window.wizardState.thanhVienList || []).forEach((m, idx) => {
                const mInput = document.querySelector(`.m-field[data-idx="${idx}"][data-prop="von_gop"]`);
                const valStr = mInput ? mInput.value : (m.von_gop || '0');
                const mVal = parseInt(String(valStr).replace(/\D/g, '') || '0', 10);
                if (mVal > 0) {
                    const pct = ((mVal / totalVon) * 100).toFixed(1);
                    const tyLeInput = document.querySelector(`.m-field[data-idx="${idx}"][data-prop="ty_le"]`);
                    if (tyLeInput) {
                        tyLeInput.value = pct;
                        m.ty_le = pct;
                    }
                }
            });
        }
    }

    if (window.updateUniversalCapitalDistribution) {
        window.updateUniversalCapitalDistribution();
    }
}

// Single Person Card
function renderPersonCard(key, label, hasOcr) {
    const pfx = key + '_';
    const fd = window.wizardState.formData;
    return `
        <div class="person-card" id="card-${key}">
            <div class="person-card-header">
                <span class="font-bold text-sm text-cyan"><i class="fa-solid fa-user-tie"></i> ${label}</span>
                ${hasOcr ? `
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <input type="file" id="ocr-file-${key}" accept="image/*" style="display: none;" onchange="handleOcrUpload(this, '${key}')">
                        <button type="button" class="btn btn-ocr" onclick="document.getElementById('ocr-file-${key}').click()">
                            <i class="fa-solid fa-id-card"></i> Quét ảnh VNeID
                        </button>
                    </div>
                ` : ''}
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Họ và tên <span class="text-error">*</span></label>
                    <input type="text" name="${pfx}ho_ten" id="input-${pfx}ho_ten" value="${escapeHtml(fd[pfx + 'ho_ten'] || '')}" class="form-control" placeholder="NGUYỄN VĂN A">
                </div>
                <div class="grid-form-2">
                    <div class="form-group">
                        <label class="form-label">Giới tính</label>
                        <select name="${pfx}gioi_tinh" id="input-${pfx}gioi_tinh" class="form-control">
                            <option value="Nam" ${(fd[pfx + 'gioi_tinh'] || '') === 'Nam' ? 'selected' : ''}>Nam</option>
                            <option value="Nữ" ${(fd[pfx + 'gioi_tinh'] || '') === 'Nữ' ? 'selected' : ''}>Nữ</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Ngày sinh</label>
                        <input type="text" name="${pfx}ngay_sinh" id="input-${pfx}ngay_sinh" value="${escapeHtml(fd[pfx + 'ngay_sinh'] || '')}" class="form-control" placeholder="DD/MM/YYYY">
                    </div>
                </div>
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Số CCCD / Căn cước (12 số) <span class="text-error">*</span></label>
                    <input type="text" name="${pfx}so_cccd" id="input-${pfx}so_cccd" value="${escapeHtml(fd[pfx + 'so_cccd'] || '')}" class="form-control" placeholder="001090001234">
                </div>
                <div class="form-group">
                    <label class="form-label">Số nhà, đường</label>
                    <input type="text" name="${pfx}dia_chi_so_nha" id="input-${pfx}dia_chi_so_nha" value="${escapeHtml(fd[pfx + 'dia_chi_so_nha'] || '')}" class="form-control" placeholder="Số 12, đường...">
                </div>
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Xã/Phường</label>
                    <input type="text" name="${pfx}dia_chi_xa_phuong" id="input-${pfx}dia_chi_xa_phuong" value="${escapeHtml(fd[pfx + 'dia_chi_xa_phuong'] || '')}" class="form-control" placeholder="Xã/Phường">
                </div>
                <div class="form-group">
                    <label class="form-label">Tỉnh/Thành phố</label>
                    <input type="text" name="${pfx}dia_chi_tinh_thanh" id="input-${pfx}dia_chi_tinh_thanh" value="${escapeHtml(fd[pfx + 'dia_chi_tinh_thanh'] || '')}" class="form-control" placeholder="Tỉnh/Thành phố">
                </div>
            </div>
        </div>
    `;
}

// Person List UI
function renderPersonList(field) {
    const list = window.wizardState.thanhVienList || [];
    let html = `
        <div id="person-list-wrapper">
            <div id="universal-capital-bar-container"></div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-3);">
                <span class="font-bold text-sm text-secondary">${field.label} (${list.length})</span>
                <button type="button" class="btn btn-secondary btn-sm" onclick="addMember()">
                    <i class="fa-solid fa-plus"></i> Thêm thành viên
                </button>
            </div>
            <div id="person-list-items" style="display: flex; flex-direction: column; gap: var(--space-4);">
    `;

    list.forEach((m, idx) => {
        html += renderMemberItem(m, idx, field.extra_fields || []);
    });

    html += `</div></div>`;
    return html;
}

function renderMemberItem(m, idx, extraFields) {
    return `
        <div class="person-card" id="member-card-${idx}">
            <div class="person-card-header">
                <span class="font-bold text-sm text-green"><i class="fa-solid fa-user"></i> Thành viên #${idx + 1}</span>
                <div style="display: flex; gap: 8px;">
                    <input type="file" id="ocr-member-${idx}" accept="image/*" style="display: none;" onchange="handleMemberOcrUpload(this, ${idx})">
                    <button type="button" class="btn btn-ocr" onclick="document.getElementById('ocr-member-${idx}').click()">
                        <i class="fa-solid fa-id-card"></i> VNeID
                    </button>
                    ${idx >= 1 ? `
                        <button type="button" class="btn btn-ghost btn-sm text-error" onclick="removeMember(${idx})">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    ` : ''}
                </div>
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Họ và tên <span class="text-error">*</span></label>
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="ho_ten" value="${escapeHtml(m.ho_ten || '')}" placeholder="Họ và tên">
                </div>
                <div class="grid-form-2">
                    <div class="form-group">
                        <label class="form-label">Giới tính</label>
                        <select class="form-control m-field" data-idx="${idx}" data-prop="gioi_tinh">
                            <option value="Nam" ${m.gioi_tinh === 'Nam' ? 'selected' : ''}>Nam</option>
                            <option value="Nữ" ${m.gioi_tinh === 'Nữ' ? 'selected' : ''}>Nữ</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Ngày sinh</label>
                        <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="ngay_sinh" value="${escapeHtml(m.ngay_sinh || '')}" placeholder="DD/MM/YYYY">
                    </div>
                </div>
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Số CCCD (12 số) <span class="text-error">*</span></label>
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="so_cccd" value="${escapeHtml(m.so_cccd || '')}" placeholder="Số CCCD">
                </div>
                <div class="form-group">
                    <label class="form-label">Số nhà, đường</label>
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="dia_chi_so_nha" value="${escapeHtml(m.dia_chi_so_nha || '')}" placeholder="Số nhà">
                </div>
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Xã/Phường</label>
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="dia_chi_xa_phuong" value="${escapeHtml(m.dia_chi_xa_phuong || '')}" placeholder="Xã/Phường">
                </div>
                <div class="form-group">
                    <label class="form-label">Tỉnh/Thành phố</label>
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="dia_chi_tinh_thanh" value="${escapeHtml(m.dia_chi_tinh_thanh || '')}" placeholder="Tỉnh/Thành">
                </div>
            </div>

            ${extraFields.length > 0 ? `
                <div class="grid-form-2 mt-2 pt-2" style="border-top: 1px dashed rgba(255,255,255,0.05);">
                    ${extraFields.map(ef => `
                        <div class="form-group">
                            <label class="form-label">${ef.label}</label>
                            <input type="${ef.type === 'money' ? 'text' : ef.type}" class="form-control m-field" data-idx="${idx}" data-prop="${ef.key}" value="${escapeHtml(m[ef.key] || '')}" placeholder="${ef.label}" onkeyup="${ef.type === 'money' ? 'handleMemberMoneyChange(this)' : ''}">
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

function handleMemberMoneyChange(input) {
    const raw = input.value.replace(/\D/g, '');
    input.value = raw ? Number(raw).toLocaleString('vi-VN') : '';

    // Auto calculate and update ty_le if von_dieu_le_so exists
    const vonInput = document.getElementById('input-von_dieu_le_so');
    if (vonInput) {
        const totalVon = parseInt(vonInput.value.replace(/\D/g, '') || '0', 10);
        const idx = input.getAttribute('data-idx');
        if (totalVon > 0 && idx !== null) {
            const mVal = parseInt(raw || '0', 10);
            const pct = ((mVal / totalVon) * 100).toFixed(1);
            const tyLeInput = document.querySelector(`.m-field[data-idx="${idx}"][data-prop="ty_le"]`);
            if (tyLeInput) {
                tyLeInput.value = pct;
                if (window.wizardState.thanhVienList[idx]) {
                    window.wizardState.thanhVienList[idx]['ty_le'] = pct;
                }
            }
        }
    }

    if (window.updateUniversalCapitalDistribution) {
        window.updateUniversalCapitalDistribution();
    }
}

window.addMember = function() {
    collectFormData();
    window.wizardState.thanhVienList.push({
        stt: window.wizardState.thanhVienList.length + 1,
        ho_ten: '',
        gioi_tinh: 'Nam',
        ngay_sinh: '',
        so_cccd: '',
        dia_chi_so_nha: '',
        dia_chi_xa_phuong: '',
        dia_chi_tinh_thanh: '',
        von_gop: '',
        ty_le: ''
    });
    renderStep2Form(window.wizardState.schema);
};

window.removeMember = function(idx) {
    collectFormData();
    window.wizardState.thanhVienList.splice(idx, 1);
    renderStep2Form(window.wizardState.schema);
};

// Transfer list UI for Chuyển nhượng
function renderTransferList(field) {
    const list = window.wizardState.transferList || [];
    return `
        <div id="transfer-list-wrapper">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-3);">
                <span class="font-bold text-sm text-secondary">${field.label} (${list.length})</span>
                <button type="button" class="btn btn-secondary btn-sm" onclick="addTransfer()">
                    <i class="fa-solid fa-plus"></i> Thêm giao dịch
                </button>
            </div>
            <div id="transfer-list-items">
                ${list.map((tr, idx) => `
                    <div class="person-card mb-3" id="transfer-card-${idx}">
                        <div class="person-card-header">
                            <span class="font-bold text-sm text-cyan">Hợp đồng chuyển nhượng #${idx + 1}</span>
                            ${idx >= 1 ? `
                                <button type="button" class="btn btn-ghost btn-sm text-error" onclick="removeTransfer(${idx})">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            ` : ''}
                        </div>
                        <div class="grid-form-2">
                            <div class="form-group">
                                <label class="form-label">Bên chuyển nhượng (Bên A)</label>
                                <input type="text" class="form-control tr-field" data-idx="${idx}" data-path="ben_a.ho_ten" value="${escapeHtml(tr.ben_a ? tr.ben_a.ho_ten : '')}" placeholder="Họ tên Bên A">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Bên nhận chuyển nhượng (Bên B)</label>
                                <input type="text" class="form-control tr-field" data-idx="${idx}" data-path="ben_b.ho_ten" value="${escapeHtml(tr.ben_b ? tr.ben_b.ho_ten : '')}" placeholder="Họ tên Bên B">
                            </div>
                        </div>
                        <div class="grid-form-2">
                            <div class="form-group">
                                <label class="form-label">Giá trị chuyển nhượng (VNĐ)</label>
                                <input type="text" class="form-control tr-field" data-idx="${idx}" data-path="gia_tri_so" value="${escapeHtml(tr.gia_tri_so || '')}" placeholder="Ví dụ: 500,000,000" onkeyup="handleMemberMoneyChange(this)">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Tỷ lệ chuyển nhượng (%)</label>
                                <input type="number" class="form-control tr-field" data-idx="${idx}" data-path="ty_le" value="${escapeHtml(tr.ty_le || '')}" placeholder="Ví dụ: 50">
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

window.addTransfer = function() {
    collectFormData();
    window.wizardState.transferList.push({
        ben_a: { ho_ten: '', so_cccd: '', dia_chi_day_du: '' },
        ben_b: { ho_ten: '', so_cccd: '', dia_chi_so_nha: '', dia_chi_xa_phuong: '', dia_chi_tinh_thanh: '' },
        gia_tri_so: '',
        ty_le: ''
    });
    renderStep2Form(window.wizardState.schema);
};

window.removeTransfer = function(idx) {
    collectFormData();
    window.wizardState.transferList.splice(idx, 1);
    renderStep2Form(window.wizardState.schema);
};

// --- DATA COLLECTION ---
function collectFormData() {
    // Collect standard inputs
    const inputs = document.querySelectorAll('#dynamic-form-container input, #dynamic-form-container select');
    inputs.forEach(inp => {
        if (inp.name && !inp.classList.contains('m-field') && !inp.classList.contains('tr-field') && inp.type !== 'file') {
            if (inp.type === 'checkbox') {
                // handled separately
            } else {
                window.wizardState.formData[inp.name] = inp.value;
            }
        }
    });

    // Collect member fields
    const mInputs = document.querySelectorAll('.m-field');
    mInputs.forEach(inp => {
        const idx = parseInt(inp.getAttribute('data-idx'), 10);
        const prop = inp.getAttribute('data-prop');
        if (window.wizardState.thanhVienList[idx]) {
            window.wizardState.thanhVienList[idx][prop] = inp.value;
        }
    });

    // Collect transfer fields
    const trInputs = document.querySelectorAll('.tr-field');
    trInputs.forEach(inp => {
        const idx = parseInt(inp.getAttribute('data-idx'), 10);
        const path = inp.getAttribute('data-path');
        if (window.wizardState.transferList[idx]) {
            const parts = path.split('.');
            if (parts.length === 1) {
                window.wizardState.transferList[idx][parts[0]] = inp.value;
            } else if (parts.length === 2) {
                if (!window.wizardState.transferList[idx][parts[0]]) {
                    window.wizardState.transferList[idx][parts[0]] = {};
                }
                window.wizardState.transferList[idx][parts[0]][parts[1]] = inp.value;
            }
        }
    });

    // Collect DKKD checkboxes
    const cbs = document.querySelectorAll('.dkkd-cb:checked');
    window.wizardState.dkkdSelected = Array.from(cbs).map(c => c.value);

    // Danh sách lặp kiểu mới (type "list") của bộ vẽ form chung
    if (window.FormRenderer) FormRenderer.collectLists(document.getElementById('dynamic-form-container'));
}

// --- OCR HANDLERS ---
window.handleOcrUpload = async function(fileInput, targetKey) {
    const file = fileInput.files[0];
    if (!file) return;

    // Lưu dữ liệu form hiện thời trước khi xử lý
    collectFormData();

    const btn = fileInput.nextElementSibling;
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang đọc VNeID...';
        btn.disabled = true;
    }

    try {
        const fd = new FormData();
        fd.append('image', file);
        fd.append('target', targetKey);

        const res = await fetch('/api/ocr/vneid', { method: 'POST', body: fd });
        const resData = await res.json();

        if (resData.success && resData.data) {
            const data = resData.data;
            const pfx = targetKey + '_';

            // Chuẩn hóa giới tính
            let gt = (data.gioi_tinh || '').trim();
            if (gt.toLowerCase() === 'nữ' || gt.toLowerCase() === 'nu' || gt.toLowerCase().includes('nữ')) {
                gt = 'Nữ';
            } else {
                gt = 'Nam';
            }

            // Populate inputs
            const mapProps = {
                ho_ten: data.ho_ten || '',
                gioi_tinh: gt,
                ngay_sinh: data.ngay_sinh || '',
                so_cccd: data.so_cccd || '',
                dia_chi_so_nha: data.dia_chi_so_nha || '',
                dia_chi_xa_phuong: data.dia_chi_xa_phuong || '',
                dia_chi_tinh_thanh: data.dia_chi_tinh_thanh || '',
                dia_chi_day_du: data.dia_chi || ''
            };

            for (const [k, v] of Object.entries(mapProps)) {
                const el = document.getElementById(`input-${pfx}${k}`);
                if (el) {
                    el.value = v || '';
                    el.style.borderColor = 'var(--accent-green)';
                }
                window.wizardState.formData[pfx + k] = v || '';
            }

            markOcrReview(data, k => document.getElementById(`input-${pfx}${k}`));

            if (data.dia_chi) {
                window.wizardState.formData[pfx + 'dia_chi_day_du'] = data.dia_chi;
            }

            if (btn) {
                btn.innerHTML = ocrDoneLabel(data);
                btn.disabled = false;
            }
        } else {
            alert(resData.message || 'Không nhận diện được thông tin từ ảnh VNeID. Vui lòng kiểm tra lại ảnh.');
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    } catch (err) {
        console.error('Lỗi OCR:', err);
        alert('Có lỗi xảy ra khi xử lý ảnh VNeID.');
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    } finally {
        fileInput.value = '';
        if (btn) btn.disabled = false;
    }
};

// Ô cần người dùng rà lại sau khi đọc CCCD (đọc OCR có thể sai dấu, hoặc dữ liệu không khớp)
function markOcrReview(data, getEl) {
    const keys = data.can_kiem_tra || [];
    // Biểu mẫu chỉ có một ô địa chỉ đầy đủ thì cờ của các phần địa chỉ dồn về ô đó
    keys.concat(keys.some(k => k.startsWith('dia_chi')) ? ['dia_chi_day_du'] : []).forEach(k => {
        const el = getEl(k);
        if (el) el.style.borderColor = 'var(--accent-orange)';
    });
}

function ocrDoneLabel(data) {
    const source = data.nguon === 'qr' ? 'QR' : 'OCR';
    return (data.can_kiem_tra || []).length
        ? `<i class="fa-solid fa-triangle-exclamation"></i> Đã đọc ${source}, hãy rà ô viền cam`
        : `<i class="fa-solid fa-check text-success"></i> Đã nhận diện (${source})`;
}

window.handleMemberOcrUpload = async function(fileInput, memberIdx) {
    const file = fileInput.files[0];
    if (!file) return;

    // Lưu ngay toàn bộ dữ liệu form hiện thời (thông tin công ty, ĐDPL, các thành viên khác)
    collectFormData();

    const btn = fileInput.nextElementSibling;
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang đọc VNeID...';
        btn.disabled = true;
    }

    try {
        const fd = new FormData();
        fd.append('image', file);
        fd.append('target', `member_${memberIdx}`);

        const res = await fetch('/api/ocr/vneid', { method: 'POST', body: fd });
        const resData = await res.json();

        if (resData.success && resData.data) {
            const data = resData.data;
            const targetMember = window.wizardState.thanhVienList[memberIdx];
            if (targetMember) {
                targetMember.ho_ten = data.ho_ten || '';
                targetMember.gioi_tinh = data.gioi_tinh || 'Nam';
                targetMember.ngay_sinh = data.ngay_sinh || '';
                targetMember.so_cccd = data.so_cccd || '';
                targetMember.dia_chi_so_nha = data.dia_chi_so_nha || '';
                targetMember.dia_chi_xa_phuong = data.dia_chi_xa_phuong || '';
                targetMember.dia_chi_tinh_thanh = data.dia_chi_tinh_thanh || '';
            }

            // Điền trực tiếp vào DOM của thẻ thành viên tương ứng, tránh re-render làm mất thông tin công ty
            const card = document.getElementById(`member-card-${memberIdx}`);
            if (card) {
                const mapProps = {
                    ho_ten: data.ho_ten || '',
                    gioi_tinh: data.gioi_tinh || 'Nam',
                    ngay_sinh: data.ngay_sinh || '',
                    so_cccd: data.so_cccd || '',
                    dia_chi_so_nha: data.dia_chi_so_nha || '',
                    dia_chi_xa_phuong: data.dia_chi_xa_phuong || '',
                    dia_chi_tinh_thanh: data.dia_chi_tinh_thanh || ''
                };
                for (const [prop, val] of Object.entries(mapProps)) {
                    const el = card.querySelector(`[data-prop="${prop}"]`);
                    if (el) {
                        el.value = val;
                        el.style.borderColor = 'var(--accent-green)';
                    }
                }
                markOcrReview(data, k => card.querySelector(`[data-prop="${k}"]`));
            }

            if (btn) {
                btn.innerHTML = ocrDoneLabel(data);
                btn.disabled = false;
            }
        } else {
            alert(resData.message || 'Không thể nhận diện ảnh VNeID. Vui lòng thử lại.');
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    } catch (err) {
        console.error('Lỗi OCR member:', err);
        alert('Có lỗi xảy ra khi xử lý ảnh VNeID.');
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    } finally {
        fileInput.value = '';
    }
};

// Quét CCCD cho một phần tử của danh sách kiểu `list` (vd Thành viên cũ)
window.handleListOcrUpload = async function(fileInput, listKey, idx) {
    const file = fileInput.files[0];
    if (!file) return;
    collectFormData();

    const btn = fileInput.nextElementSibling;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang đọc VNeID...';
    btn.disabled = true;

    try {
        const fd = new FormData();
        fd.append('image', file);
        fd.append('target', `${listKey}_${idx}`);
        const resData = await (await fetch('/api/ocr/vneid', { method: 'POST', body: fd })).json();
        if (!resData.success || !resData.data) {
            alert(resData.message || 'Không thể nhận diện ảnh VNeID. Vui lòng thử lại.');
            btn.innerHTML = originalText;
            return;
        }

        const data = resData.data;
        const getEl = k => document.querySelector(`.lf-field[data-list="${CSS.escape(listKey)}"][data-idx="${idx}"][data-key="${k}"]`);
        const values = {
            ho_ten: data.ho_ten, gioi_tinh: data.gioi_tinh, ngay_sinh: data.ngay_sinh,
            so_cccd: data.so_cccd, dia_chi_day_du: data.dia_chi
        };
        for (const [k, v] of Object.entries(values)) {
            const el = getEl(k);
            if (el && v) {
                el.value = v;
                el.style.borderColor = 'var(--accent-green)';
            }
        }
        markOcrReview(data, getEl);
        btn.innerHTML = ocrDoneLabel(data);
        // Để form thu dữ liệu, xóa báo lỗi và cập nhật danh sách chọn bên chuyển nhượng
        const nameEl = getEl('ho_ten');
        if (nameEl) nameEl.dispatchEvent(new Event('change', { bubbles: true }));
    } catch (err) {
        console.error('Lỗi OCR danh sách:', err);
        alert('Có lỗi xảy ra khi xử lý ảnh VNeID.');
        btn.innerHTML = originalText;
    } finally {
        fileInput.value = '';
        btn.disabled = false;
    }
};

// --- MST LOOKUP ---
window.lookupMST = async function(fieldKey) {
    const el = document.getElementById(`input-${fieldKey}`);
    const statusEl = document.getElementById('mst-status');
    if (!el || !el.value) {
        alert('Vui lòng nhập Mã số thuế trước khi tra cứu.');
        return;
    }

    if (statusEl) statusEl.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-cyan"></i> Đang tra cứu thông tin thuế...';

    try {
        const res = await fetch(`/api/mst/${encodeURIComponent(el.value.trim())}`);
        const result = await res.json();

        if (result.success && result.data && result.data.name) {
            const data = result.data;
            if (statusEl) statusEl.innerHTML = `<span class="text-success"><i class="fa-solid fa-check"></i> Tìm thấy: <b>${escapeHtml(data.name)}</b></span>`;

            // Auto-fill company fields
            window.wizardState.formData['ma_so_thue'] = el.value.trim();

            const nameEl = document.getElementById('input-ten_cong_ty_vn');
            if (nameEl) {
                nameEl.value = data.name;
                nameEl.style.borderColor = 'var(--accent-green)';
                window.wizardState.formData['ten_cong_ty_vn'] = data.name;
            }

            const nnEl = document.getElementById('input-ten_cong_ty_nn');
            if (nnEl && (data.internationalName || data.ten_quoc_te)) {
                const val = data.internationalName || data.ten_quoc_te;
                nnEl.value = val;
                nnEl.style.borderColor = 'var(--accent-green)';
                window.wizardState.formData['ten_cong_ty_nn'] = val;
            }

            const vtEl = document.getElementById('input-ten_cong_ty_viet_tat');
            if (vtEl && (data.shortName || data.ten_viet_tat)) {
                const val = data.shortName || data.ten_viet_tat;
                vtEl.value = val;
                vtEl.style.borderColor = 'var(--accent-green)';
                window.wizardState.formData['ten_cong_ty_viet_tat'] = val;
            }

            // Parse address if available
            if (data.address) {
                const parts = data.address.split(',').map(p => p.trim());
                const tinh = parts.length > 0 ? parts.pop() : '';
                const xa = parts.length > 0 ? parts.pop() : '';
                const sonha = parts.join(', ');

                const snEl = document.getElementById('input-dia_chi_so_nha');
                const xpEl = document.getElementById('input-dia_chi_xa_phuong');
                const ttEl = document.getElementById('input-dia_chi_tinh_thanh');
                const fullEl = document.getElementById('input-dia_chi_day_du');

                if (snEl) { 
                    snEl.value = sonha; 
                    snEl.style.borderColor = 'var(--accent-green)';
                    window.wizardState.formData['dia_chi_so_nha'] = sonha; 
                }
                if (xpEl) { 
                    xpEl.value = xa; 
                    xpEl.style.borderColor = 'var(--accent-green)';
                    window.wizardState.formData['dia_chi_xa_phuong'] = xa; 
                }
                if (ttEl) { 
                    ttEl.value = tinh; 
                    ttEl.style.borderColor = 'var(--accent-green)';
                    window.wizardState.formData['dia_chi_tinh_thanh'] = tinh; 
                }
                if (fullEl) {
                    fullEl.value = data.address;
                    fullEl.style.borderColor = 'var(--accent-green)';
                    window.wizardState.formData['dia_chi_day_du'] = data.address;
                }
            }
        } else {
            if (statusEl) statusEl.innerHTML = '<span class="text-warning"><i class="fa-solid fa-circle-exclamation"></i> Không tìm thấy dữ liệu từ Tổng cục Thuế. Vui lòng nhập tay.</span>';
        }
    } catch (err) {
        console.error('Lỗi tra cứu MST:', err);
        if (statusEl) statusEl.innerHTML = '<span class="text-error">Lỗi kết nối tra cứu MST.</span>';
    }
};

// --- STEP 3: INDUSTRY CODES & COMBOS ---
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

// --- STEP 4: REVIEW & DOWNLOAD ---
function renderStep4Download() {
    const tpl = window.wizardState.template;
    const fd = window.wizardState.formData;
    const tv = window.wizardState.thanhVienList;
    const nganh = window.wizardState.maNganh;

    const companyName = fd['ten_cong_ty_vn'] || 'Chưa cập nhật';
    const ddplName = fd['ddpl_ho_ten'] || 'Chưa cập nhật';

    return `
        <div class="text-center mb-6">
            <h2 class="text-3xl font-bold mb-2 text-gradient">Hồ sơ đã sẵn sàng!</h2>
            <p class="text-secondary text-sm">Kiểm tra thông tin tóm tắt và tải trọn bộ hồ sơ dạng file nén (.ZIP) gồm các file Word (.docx) chuẩn hóa.</p>
        </div>

        <div class="card-sub mb-6" style="background: rgba(255,255,255,0.02);">
            <h3 class="font-bold text-md text-cyan mb-4"><i class="fa-solid fa-circle-info"></i> Tóm tắt hồ sơ</h3>
            <div class="grid-form-2 text-sm" style="row-gap: 12px;">
                <div><span class="text-muted">Loại thủ tục:</span> <b class="text-white">${tpl.display_name}</b></div>
                <div><span class="text-muted">Số lượng biểu mẫu:</span> <span class="badge badge-green">${tpl.file_count} files Word (.docx)</span></div>
                <div><span class="text-muted">Tên doanh nghiệp:</span> <b class="text-white">${companyName}</b></div>
                <div><span class="text-muted">Đại diện pháp luật:</span> <b class="text-white">${ddplName}</b></div>
                ${tv.length > 0 ? `<div><span class="text-muted">Thành viên / Cổ đông:</span> <b class="text-white">${tv.length} người</b></div>` : ''}
                ${nganh.length > 0 ? `<div><span class="text-muted">Mã ngành nghề:</span> <b class="text-white">${nganh.length} ngành</b></div>` : ''}
            </div>
        </div>

        <div id="gen-loading" style="display: none; text-align: center; padding: var(--space-8);">
            <div style="font-size: 3rem; color: var(--accent-primary); margin-bottom: var(--space-4);"><i class="fa-solid fa-cog fa-spin"></i></div>
            <h3 class="font-bold text-xl mb-2">Đang khởi tạo các biểu mẫu Word...</h3>
            <p class="text-secondary text-sm">Jinja2 docxtpl engine đang điền tự động các điều khoản pháp lý.</p>
        </div>

        <div id="gen-success" style="display: none; text-align: center; padding: var(--space-6); background: rgba(80, 250, 123, 0.05); border-radius: var(--radius-lg); border: 1px solid rgba(80, 250, 123, 0.2);">
            <div style="font-size: 3.5rem; color: var(--accent-green); margin-bottom: var(--space-3);"><i class="fa-solid fa-circle-check"></i></div>
            <h3 class="text-2xl font-bold text-success mb-2">Tải thành công!</h3>
            <p class="text-secondary text-sm mb-4">Bộ hồ sơ hoàn chỉnh đã được tải xuống máy tính của bạn.</p>
            <a href="#/wizard" class="btn btn-secondary btn-sm" onclick="initWizard()"><i class="fa-solid fa-rotate-left"></i> Tạo bộ hồ sơ khác</a>
        </div>
    `;
}

window.generateDocuments = async function() {
    if (window.wizardState.step === 2) {
        collectFormData();
    }
    if (!ensureRequiredFields()) return;

    const loadingEl = document.getElementById('gen-loading');
    const successEl = document.getElementById('gen-success');
    const btnDl = document.getElementById('btn-download');
    const btnBack = document.getElementById('btn-back-final');

    if (loadingEl) loadingEl.style.display = 'block';
    if (btnDl) btnDl.disabled = true;
    if (btnBack) btnBack.disabled = true;

    const payload = {
        template_name: window.wizardState.template.name,
        data: {
            ...window.wizardState.formData,
            thanh_vien: window.wizardState.thanhVienList,
            chuyen_nhuong: window.wizardState.transferList,
            dkkd_selected: window.wizardState.dkkdSelected,
            // Dữ liệu theo đúng key của schema (vd checkbox_group/list có key riêng), cùng cách backend kiểm tra
            ...wizardDataForSchema(window.wizardState.schema, false)
        },
        ma_nganh: window.wizardState.maNganh.map(n => ({
            ma: n.ma,
            ten: n.ten,
            is_main: !!n.is_main
        })),
        special_payload: {
            chuyen_nhuong: window.wizardState.transferList,
            thanh_vien: window.wizardState.thanhVienList
        }
    };

    try {
        const response = await fetch('/api/documents/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errJson = await response.json().catch(() => ({}));
            throw new Error(errJson.detail || errJson.message || 'Lỗi server');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const safeName = window.wizardState.template.name.replace(/\s+/g, '_');
        a.download = `Ho_So_${safeName}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        if (loadingEl) loadingEl.style.display = 'none';
        if (successEl) successEl.style.display = 'block';
    } catch (err) {
        console.error('Lỗi tải hồ sơ:', err);
        alert('Có lỗi xảy ra khi tạo hồ sơ: ' + err.message);
        if (loadingEl) loadingEl.style.display = 'none';
        if (btnDl) btnDl.disabled = false;
        if (btnBack) btnBack.disabled = false;
    }
};
