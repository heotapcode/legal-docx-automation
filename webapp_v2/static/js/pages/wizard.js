// Universal Schema-Driven Wizard for Webapp v2

window.wizardState = {
    step: 1,
    templatesList: [],
    template: null,
    schema: null,
    formData: {},
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
                    <a href="/" class="navbar-brand">
                        <i class="fa-solid fa-building text-gradient"></i> NAC <span class="badge badge-green" style="font-size:10px;">v2 Jinja2</span>
                    </a>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <button type="button" class="btn btn-secondary btn-sm" onclick="toggleGlobalUIMode()">
                            <i class="fa-solid fa-scale-balanced" style="color: #d4af37;"></i> Dùng giao diện Harvey
                        </button>
                        <a href="/" class="btn btn-ghost btn-sm"><i class="fa-solid fa-xmark"></i> Thoát</a>
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
                    <a href="/" style="text-decoration: none; display: flex; align-items: center; gap: 10px;">
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
                    <a href="/" class="btn harvey-btn-ghost btn-sm"><i class="fa-solid fa-house"></i> Trang chủ</a>
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

window.initWizard = async function() {
    window.wizardState = {
        step: 1,
        templatesList: [],
        template: null,
        schema: null,
        formData: {},
        maNganh: [],
        dkkdSelected: []
    };

    renderCurrentStep();

    try {
        const res = await fetch('/api/templates');
        if (res.ok) {
            const data = await res.json();
            window.wizardState.templatesList = data.templates;
            // Link từ trang giới thiệu: /app#/wizard?t=<id bộ mẫu> mở thẳng thủ tục đó
            const wanted = new URLSearchParams(window.location.hash.split('?')[1] || '').get('t');
            const found = wanted && data.templates.find(t => t.id === wanted);
            if (found) { window.selectTemplate(found.name); return; }
            renderCurrentStep();
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

/**
 * Dữ liệu wizard theo đúng key của schema. blankLists: form trống nhưng giữ số dòng của mỗi danh sách
 * (để tính số mục cần kiểm tra cho thanh "MỨC HOÀN THIỆN").
 */
function wizardDataForSchema(schema, blankLists) {
    const s = window.wizardState;
    const fd = s.formData || {};
    const data = blankLists ? {} : Object.assign({}, fd);
    ((schema && schema.steps) || []).forEach(st => (st.fields || []).forEach(f => {
        if (f.type === 'checkbox_group') { if (!blankLists) data[f.key] = s.dkkdSelected || []; }
        else if (f.type === 'list' && blankLists) data[f.key] = (Array.isArray(fd[f.key]) ? fd[f.key] : []).map(() => ({}));
    }));
    return data;
}

/**
 * Lỗi dữ liệu [{label, name | list+idx+key}] theo _schema.json, kèm errors.total
 * (số mục cần kiểm tra, dùng để tính % hoàn thiện).
 */
function validateRequiredFields(schema) {
    const out = [];
    out.total = 0;
    if (!schema || !schema.steps || !window.SchemaEngine) return out;
    SchemaEngine.validate(schema, wizardDataForSchema(schema, false)).forEach(e => {
        const item = { label: e.message };
        const list = window.FormRenderer ? FormRenderer.listOfError(e) : null;
        if (e.index === undefined || !list) item.name = e.key;
        else { item.list = list; item.idx = e.index; item.key = e.key; }
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
    if (window.nacTrack && window.wizardState.template) {
        window.nacTrack('begin_form', { template_id: window.wizardState.template.id });
    }
    window.wizardState.step = 2;
    renderCurrentStep();
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
                <p class="text-secondary text-sm">Hệ thống hỗ trợ ${list.length} bộ mẫu hồ sơ chuẩn hóa theo quy định mới nhất</p>
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
        // Kiểu cũ person_list (bộ mẫu cũ) -> danh sách chung `list`, cùng cách với máy chủ
        window.wizardState.schema = SchemaEngine.normalizeSchema(schema);

        renderStep2Form(window.wizardState.schema);
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

/** Danh sách có auto_ratio (vd thành viên: vốn góp / vốn điều lệ) trong schema đang mở, hoặc null. */
function ratioListField() {
    const steps = (window.wizardState.schema && window.wizardState.schema.steps) || [];
    for (const st of steps) for (const f of (st.fields || [])) if (f.type === 'list' && f.auto_ratio) return f;
    return null;
}

window.updateUniversalCapitalDistribution = function() {
    const container = document.getElementById('universal-capital-bar-container');
    if (!container) return;
    const field = ratioListField();
    const fd = window.wizardState.formData;
    const totalInput = field ? document.querySelector(`[name="${field.auto_ratio.total}"]`) : null;
    const totalVon = parseInt(String((totalInput ? totalInput.value : fd[field && field.auto_ratio.total]) || '').replace(/\D/g, '') || '0', 10);
    const memberList = field && Array.isArray(fd[field.key]) ? fd[field.key] : [];
    if (!memberList.length || totalVon <= 0) {
        container.innerHTML = '';
        return;
    }
    const part = field.auto_ratio.part;

    const colors = ['#f97316', '#3b82f6', '#10b981', '#a855f7', '#ec4899', '#eab308', '#06b6d4'];
    let distributed = 0;
    let segmentsHtml = '';
    let badgesHtml = '';

    memberList.forEach((m, idx) => {
        const valStr = (m && m[part]) || '0';
        const mVal = parseInt(String(valStr).replace(/\D/g, '') || '0', 10);
        distributed += mVal;

        const pct = ((mVal / totalVon) * 100).toFixed(1);
        const color = colors[idx % colors.length];
        const name = (m && m.ho_ten) || `Thành viên ${idx + 1}`;

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

/** Mục 8.3: dải gợi ý chuyển sang thủ tục gộp, khi schema có "shortcut" và bộ đích có trong danh sách. */
function shortcutBannerHtml(schema) {
    const sc = schema && schema.shortcut;
    if (!sc || !(window.wizardState.templatesList || []).some(t => t.name === sc.template)) return '';
    const label = sc.label || 'Thay đổi thêm nội dung khác cùng lúc';
    return `
        <div id="combined-shortcut" style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; padding: 12px 16px; margin-bottom: 16px; border: 1px dashed var(--gold-border-subtle, rgba(212,175,55,0.35)); border-radius: var(--radius-md, 8px); background: rgba(212, 175, 55, 0.06);">
            <div style="font-size: 13px;">
                <i class="fa-solid fa-layer-group" style="color: var(--gold-primary, #d4af37);"></i>
                Cần đổi thêm tên, địa chỉ, vốn, ngành nghề, người đại diện... trong cùng một bộ hồ sơ?
                Chuyển sang thủ tục <b>${escapeHtml(sc.template)}</b>, dữ liệu đã nhập được giữ lại.
            </div>
            <button type="button" class="btn btn-secondary btn-sm" id="btn-combined-shortcut" onclick="openCombinedProcedure()" style="white-space: nowrap;">
                <i class="fa-solid fa-arrow-right-arrow-left"></i> ${escapeHtml(label)}
            </button>
        </div>`;
}

/** Mở thủ tục gộp: giữ dữ liệu đã nhập (đổi tên key theo shortcut.map), đặt sẵn giá trị trong shortcut.preset. */
window.openCombinedProcedure = function() {
    const st = window.wizardState;
    const sc = st.schema && st.schema.shortcut;
    if (!sc) return;
    collectFormData();
    const fd = Object.assign({}, st.formData);
    Object.entries(sc.map || {}).forEach(([src, dst]) => {
        if (fd[src] !== undefined && fd[src] !== '') fd[dst] = fd[src];
    });
    const preset = sc.preset || {};
    Object.entries(preset).forEach(([k, v]) => { if (!Array.isArray(v)) fd[k] = v; });
    st.formData = fd;
    st.dkkdSelected = Array.isArray(preset.dkkd_selected) ? preset.dkkd_selected.slice() : [];
    st.schema = null;
    selectTemplate(sc.template);
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
            ${shortcutBannerHtml(schema)}
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
                        <div class="harvey-kpi-num" id="kpi-member-count">${(window.wizardState.formData.thanh_vien || []).length} Người</div>
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

            ${shortcutBannerHtml(schema)}

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

// Các kiểu ô (renderField, thẻ người, danh sách thành viên): static/js/engine/field_types.js

// --- DATA COLLECTION ---
function collectFormData() {
    // Collect standard inputs
    const inputs = document.querySelectorAll('#dynamic-form-container input, #dynamic-form-container select');
    inputs.forEach(inp => {
        if (inp.name && inp.type !== 'file') {
            if (inp.type === 'checkbox') {
                // handled separately
            } else {
                window.wizardState.formData[inp.name] = inp.value;
            }
        }
    });

    // Collect DKKD checkboxes
    const cbs = document.querySelectorAll('.dkkd-cb:checked');
    window.wizardState.dkkdSelected = Array.from(cbs).map(c => c.value);

    // Danh sách lặp kiểu mới (type "list") của bộ vẽ form chung
    if (window.FormRenderer) FormRenderer.collectLists(document.getElementById('dynamic-form-container'));
}

// Quét CCCD/VNeID: static/js/engine/ocr_scan.js

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

// Bước 3 (chọn mã ngành): static/js/pages/wizard_nganh.js

// --- STEP 4: REVIEW & DOWNLOAD ---
function renderStep4Download() {
    const tpl = window.wizardState.template;
    const fd = window.wizardState.formData;
    const tv = Array.isArray(window.wizardState.formData.thanh_vien) ? window.wizardState.formData.thanh_vien : [];
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

    // Bước để lại số Zalo trước khi tải (static/js/engine/lead_gate.js)
    const lead = window.LeadGate
        ? await window.LeadGate.ask(window.wizardState.template.display_name || window.wizardState.template.name,
                                    '', window.wizardState.template.id)
        : null;
    if (window.LeadGate && !lead) return;

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
            dkkd_selected: window.wizardState.dkkdSelected,
            // Dữ liệu theo đúng key của schema (vd checkbox_group/list có key riêng), cùng cách backend kiểm tra
            ...wizardDataForSchema(window.wizardState.schema, false)
        },
        ma_nganh: window.wizardState.maNganh.map(n => ({
            ma: n.ma,
            ten: n.ten,
            is_main: !!n.is_main
        })),
        lead: lead || undefined
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
        trackDownload(lead);
        if (window.LeadGate) window.LeadGate.thankYou(lead, response.headers.get('X-Lead-Package'), response.headers.get('X-Lead-Code'));
    } catch (err) {
        console.error('Lỗi tải hồ sơ:', err);
        alert('Có lỗi xảy ra khi tạo hồ sơ: ' + err.message);
        if (loadingEl) loadingEl.style.display = 'none';
        if (btnDl) btnDl.disabled = false;
        if (btnBack) btnBack.disabled = false;
    }
};

// Đo phễu (Google Analytics): tải hồ sơ, để lại thông tin. Không gửi họ tên, số điện thoại hay dữ liệu hồ sơ.
function trackDownload(lead) {
    if (!window.nacTrack) return;
    const t = window.wizardState.template || {};
    window.nacTrack('tai_ho_so', { template_id: t.id || '' });
    if (lead) {
        window.nacTrack('generate_lead', {
            template_id: t.id || '', hinh_thuc: lead.delegated ? 'nho_nop' : 'tu_nop',
            goi: lead.package || '', cach_gui: lead.delivery || '',
        });
    }
}
