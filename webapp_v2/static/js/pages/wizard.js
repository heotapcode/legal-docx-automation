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

function numToVietnameseWords(s) {
    if (!s) return '';
    const digits = String(s).replace(/\D/g, '');
    if (!digits) return '';
    const n = parseInt(digits, 10);
    if (n === 0) return 'Không đồng';

    const donVi = ['', 'nghìn', 'triệu', 'tỷ', 'nghìn tỷ', 'triệu tỷ'];
    const chuSo = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín'];

    function docBaChuSo(val) {
        const tram = Math.floor(val / 100);
        const chuc = Math.floor((val % 100) / 10);
        const dv = val % 10;
        let res = '';
        if (tram > 0) {
            res += chuSo[tram] + ' trăm ';
            if (chuc === 0 && dv > 0) res += 'lẻ ';
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
    let tempN = n;
    let i = 0;
    while (tempN > 0) {
        const phanBa = tempN % 1000;
        if (phanBa > 0) {
            const docPhanBa = docBaChuSo(phanBa);
            if (docPhanBa) {
                chuoiKq = docPhanBa + ' ' + donVi[i] + ' ' + chuoiKq;
            }
        }
        tempN = Math.floor(tempN / 1000);
        i++;
    }
    chuoiKq = chuoiKq.trim();
    return chuoiKq.charAt(0).toUpperCase() + chuoiKq.slice(1) + ' đồng';
}

function renderWizard() {
    return `
        <!-- Navbar minimal -->
        <nav class="navbar">
            <div class="container navbar-container">
                <a href="#/" class="navbar-brand">
                    <i class="fa-solid fa-building text-gradient"></i> NAC <span class="badge badge-green" style="font-size:10px;">v2 Jinja2</span>
                </a>
                <a href="#/" class="btn btn-ghost btn-sm"><i class="fa-solid fa-xmark"></i> Thoát</a>
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
                    <!-- Buttons injected here -->
                </div>
            </div>
        </section>
    `;
}

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

window.nextStep = function() {
    if (window.wizardState.step === 2) {
        const tplName = window.wizardState.template ? window.wizardState.template.name : '';
        if (tplName === 'Chuyển nhượng Công ty TNHH 2 TV' && window.collectCN2TVData) {
            const ok = window.collectCN2TVData();
            if (!ok) return;
            window.wizardState.step = 4;
            renderCurrentStep();
            return;
        }
        if (tplName === 'Chuyển đổi loại hình 1TV sang 2 TV' && window.collectCD1TV2TVData) {
            const cdStep = window.cd1tv2tvState ? window.cd1tv2tvState.step : 1;
            if (cdStep === 1) {
                window.cd1tv2tvGotoStep(2);
                return;
            } else if (cdStep === 2) {
                window.cd1tv2tvGotoStep(3);
                return;
            } else {
                const ok = window.collectCD1TV2TVData();
                if (!ok) return;
                window.wizardState.step = 3;
                renderCurrentStep();
                return;
            }
        }

        collectFormData();
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
    const tplName = window.wizardState.template ? window.wizardState.template.name : '';
    if (window.wizardState.step === 2 && tplName === 'Chuyển đổi loại hình 1TV sang 2 TV' && window.cd1tv2tvState) {
        if (window.cd1tv2tvState.step > 1) {
            window.cd1tv2tvGotoStep(window.cd1tv2tvState.step - 1);
            return;
        }
    }

    if (window.wizardState.step === 4) {
        if (tplName === 'Chuyển nhượng Công ty TNHH 2 TV') {
            window.wizardState.step = 2;
            renderCurrentStep();
            return;
        }
        const hasNganh = window.wizardState.schema && window.wizardState.schema.has_nganh;
        if (!hasNganh) {
            window.wizardState.step = 2;
            renderCurrentStep();
            return;
        }
    }

    if (window.wizardState.step === 3 && tplName === 'Chuyển nhượng Công ty TNHH 2 TV') {
        window.wizardState.step = 2;
        renderCurrentStep();
        return;
    }

    if (window.wizardState.step > 1) {
        window.wizardState.step--;
        renderCurrentStep();
    }
};

window.selectTemplate = function(name) {
    if (window.wizardState.template && window.wizardState.template.name !== name) {
        window.cn2tvState = null;
        window.cd1tv2tvState = null;
    }
    window.wizardState.template = window.wizardState.templatesList.find(t => t.name === name);
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

    // Check for custom specialized wizards
    if (tplName === 'Chuyển nhượng Công ty TNHH 2 TV' && window.renderCN2TVWizard) {
        window.wizardState.schema = { has_nganh: false, display_name: tplName };
        content.innerHTML = '<div id="cn2tv-custom-wrapper" style="padding: 10px;"></div>';
        window.renderCN2TVWizard(document.getElementById('cn2tv-custom-wrapper'));
        return;
    }

    if (tplName === 'Chuyển đổi loại hình 1TV sang 2 TV' && window.renderCD1TV2TVWizard) {
        window.wizardState.schema = { has_nganh: true, display_name: tplName };
        content.innerHTML = '<div id="cd1tv-custom-wrapper" style="padding: 10px;"></div>';
        window.renderCD1TV2TVWizard(document.getElementById('cd1tv-custom-wrapper'));
        return;
    }

    try {
        const res = await fetch(`/api/templates/${encodeURIComponent(tplName)}/schema`);
        if (!res.ok) throw new Error('Schema not found');
        const schema = await res.json();
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

function renderStep2Form(schema) {
    const content = document.getElementById('wizard-content');
    if (!content) return;

    let html = `
        <div style="margin-bottom: var(--space-4);">
            <h2 class="text-2xl font-bold">${schema.display_name}</h2>
            <p class="text-secondary text-sm">${schema.description || ''}</p>
        </div>
        <div id="dynamic-form-container" style="display: flex; flex-direction: column; gap: var(--space-6);">
    `;

    (schema.steps || []).forEach((step, sIdx) => {
        html += `
            <div class="card-sub" style="border-left: 4px solid var(--accent-primary);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: var(--space-4);">
                    <i class="fa-solid fa-clipboard-list text-cyan"></i>
                    <h3 class="font-bold text-lg">${step.title}</h3>
                </div>
                <div>
        `;

        (step.fields || []).forEach(f => {
            html += renderField(f);
        });

        html += `</div></div>`;
    });

    html += `</div>`;
    content.innerHTML = html;
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
                    <input type="text" id="input-${fKey}" name="${fKey}" value="${curVal}" class="form-control" placeholder="Nhập mã số thuế (10 hoặc 13 số)">
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
                <input type="text" id="input-${fKey}" name="${fKey}" value="${curVal ? formatMoneyStr(curVal) : ''}" class="form-control" placeholder="Ví dụ: 1,000,000,000" onkeyup="handleMoneyChange(this, 'spellout-${fKey}')">
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
                    <input type="checkbox" class="dkkd-cb" value="${opt.value}" ${checked}>
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

    // Standard text / phone / email
    const inputType = field.type === 'phone' ? 'tel' : field.type === 'email' ? 'email' : 'text';
    return `
        <div class="form-group">
            <label class="form-label">${fLabel} ${reqBadge}</label>
            <input type="${inputType}" id="input-${fKey}" name="${fKey}" value="${curVal}" class="form-control" placeholder="${field.placeholder || ''}">
        </div>
    `;
}

function handleMoneyChange(input, spelloutId) {
    const raw = input.value.replace(/\D/g, '');
    input.value = raw ? Number(raw).toLocaleString('vi-VN') : '';
    const sp = document.getElementById(spelloutId);
    if (sp) {
        sp.innerText = raw ? 'Bằng chữ: ' + numToVietnameseWords(raw) : '';
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
                    <input type="text" name="${pfx}ho_ten" id="input-${pfx}ho_ten" value="${fd[pfx + 'ho_ten'] || ''}" class="form-control" placeholder="NGUYỄN VĂN A">
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
                        <input type="text" name="${pfx}ngay_sinh" id="input-${pfx}ngay_sinh" value="${fd[pfx + 'ngay_sinh'] || ''}" class="form-control" placeholder="DD/MM/YYYY">
                    </div>
                </div>
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Số CCCD / Căn cước (12 số) <span class="text-error">*</span></label>
                    <input type="text" name="${pfx}so_cccd" id="input-${pfx}so_cccd" value="${fd[pfx + 'so_cccd'] || ''}" class="form-control" placeholder="001090001234">
                </div>
                <div class="form-group">
                    <label class="form-label">Số nhà, đường</label>
                    <input type="text" name="${pfx}dia_chi_so_nha" id="input-${pfx}dia_chi_so_nha" value="${fd[pfx + 'dia_chi_so_nha'] || ''}" class="form-control" placeholder="Số 12, đường...">
                </div>
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Xã/Phường</label>
                    <input type="text" name="${pfx}dia_chi_xa_phuong" id="input-${pfx}dia_chi_xa_phuong" value="${fd[pfx + 'dia_chi_xa_phuong'] || ''}" class="form-control" placeholder="Xã/Phường">
                </div>
                <div class="form-group">
                    <label class="form-label">Tỉnh/Thành phố</label>
                    <input type="text" name="${pfx}dia_chi_tinh_thanh" id="input-${pfx}dia_chi_tinh_thanh" value="${fd[pfx + 'dia_chi_tinh_thanh'] || ''}" class="form-control" placeholder="Tỉnh/Thành phố">
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
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="ho_ten" value="${m.ho_ten || ''}" placeholder="Họ và tên">
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
                        <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="ngay_sinh" value="${m.ngay_sinh || ''}" placeholder="DD/MM/YYYY">
                    </div>
                </div>
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Số CCCD (12 số) <span class="text-error">*</span></label>
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="so_cccd" value="${m.so_cccd || ''}" placeholder="Số CCCD">
                </div>
                <div class="form-group">
                    <label class="form-label">Số nhà, đường</label>
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="dia_chi_so_nha" value="${m.dia_chi_so_nha || ''}" placeholder="Số nhà">
                </div>
            </div>

            <div class="grid-form-2">
                <div class="form-group">
                    <label class="form-label">Xã/Phường</label>
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="dia_chi_xa_phuong" value="${m.dia_chi_xa_phuong || ''}" placeholder="Xã/Phường">
                </div>
                <div class="form-group">
                    <label class="form-label">Tỉnh/Thành phố</label>
                    <input type="text" class="form-control m-field" data-idx="${idx}" data-prop="dia_chi_tinh_thanh" value="${m.dia_chi_tinh_thanh || ''}" placeholder="Tỉnh/Thành">
                </div>
            </div>

            ${extraFields.length > 0 ? `
                <div class="grid-form-2 mt-2 pt-2" style="border-top: 1px dashed rgba(255,255,255,0.05);">
                    ${extraFields.map(ef => `
                        <div class="form-group">
                            <label class="form-label">${ef.label}</label>
                            <input type="${ef.type === 'money' ? 'text' : ef.type}" class="form-control m-field" data-idx="${idx}" data-prop="${ef.key}" value="${m[ef.key] || ''}" placeholder="${ef.label}" onkeyup="${ef.type === 'money' ? 'handleMemberMoneyChange(this)' : ''}">
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
                                <input type="text" class="form-control tr-field" data-idx="${idx}" data-path="ben_a.ho_ten" value="${tr.ben_a ? tr.ben_a.ho_ten : ''}" placeholder="Họ tên Bên A">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Bên nhận chuyển nhượng (Bên B)</label>
                                <input type="text" class="form-control tr-field" data-idx="${idx}" data-path="ben_b.ho_ten" value="${tr.ben_b ? tr.ben_b.ho_ten : ''}" placeholder="Họ tên Bên B">
                            </div>
                        </div>
                        <div class="grid-form-2">
                            <div class="form-group">
                                <label class="form-label">Giá trị chuyển nhượng (VNĐ)</label>
                                <input type="text" class="form-control tr-field" data-idx="${idx}" data-path="gia_tri_so" value="${tr.gia_tri_so || ''}" placeholder="Ví dụ: 500,000,000" onkeyup="handleMemberMoneyChange(this)">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Tỷ lệ chuyển nhượng (%)</label>
                                <input type="number" class="form-control tr-field" data-idx="${idx}" data-path="ty_le" value="${tr.ty_le || ''}" placeholder="Ví dụ: 50">
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
}

// --- OCR HANDLERS ---
window.handleOcrUpload = async function(fileInput, targetKey) {
    const file = fileInput.files[0];
    if (!file) return;

    const card = document.getElementById(`card-${targetKey}`);
    const originalText = fileInput.nextElementSibling ? fileInput.nextElementSibling.innerHTML : '';
    if (fileInput.nextElementSibling) {
        fileInput.nextElementSibling.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang đọc VNeID...';
        fileInput.nextElementSibling.disabled = true;
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

            // Populate inputs
            const mapProps = {
                ho_ten: data.ho_ten,
                gioi_tinh: data.gioi_tinh,
                ngay_sinh: data.ngay_sinh,
                so_cccd: data.so_cccd,
                dia_chi_so_nha: data.dia_chi_so_nha,
                dia_chi_xa_phuong: data.dia_chi_xa_phuong,
                dia_chi_tinh_thanh: data.dia_chi_tinh_thanh
            };

            for (const [k, v] of Object.entries(mapProps)) {
                const el = document.getElementById(`input-${pfx}${k}`);
                if (el) {
                    el.value = v || '';
                    el.style.borderColor = 'var(--accent-green)';
                }
                window.wizardState.formData[pfx + k] = v || '';
            }

            if (fileInput.nextElementSibling) {
                fileInput.nextElementSibling.innerHTML = '<i class="fa-solid fa-check text-success"></i> Đã nhận diện';
            }
        } else {
            alert('Không nhận diện được thông tin từ ảnh VNeID. Vui lòng kiểm tra lại ảnh.');
            if (fileInput.nextElementSibling) fileInput.nextElementSibling.innerHTML = originalText;
        }
    } catch (err) {
        console.error('Lỗi OCR:', err);
        alert('Có lỗi xảy ra khi xử lý ảnh VNeID.');
        if (fileInput.nextElementSibling) fileInput.nextElementSibling.innerHTML = originalText;
    }
};

window.handleMemberOcrUpload = async function(fileInput, memberIdx) {
    const file = fileInput.files[0];
    if (!file) return;

    const originalText = fileInput.nextElementSibling.innerHTML;
    fileInput.nextElementSibling.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>...';

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
            renderStep2Form(window.wizardState.schema);
        } else {
            alert('Không thể nhận diện ảnh VNeID.');
            fileInput.nextElementSibling.innerHTML = originalText;
        }
    } catch (err) {
        console.error('Lỗi OCR member:', err);
        fileInput.nextElementSibling.innerHTML = originalText;
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
            if (statusEl) statusEl.innerHTML = `<span class="text-success"><i class="fa-solid fa-check"></i> Tìm thấy: <b>${data.name}</b></span>`;

            // Auto-fill company fields
            const nameEl = document.getElementById('input-ten_cong_ty_vn');
            if (nameEl) {
                nameEl.value = data.name;
                nameEl.style.borderColor = 'var(--accent-green)';
                window.wizardState.formData['ten_cong_ty_vn'] = data.name;
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

                if (snEl) { snEl.value = sonha; window.wizardState.formData['dia_chi_so_nha'] = sonha; }
                if (xpEl) { xpEl.value = xa; window.wizardState.formData['dia_chi_xa_phuong'] = xa; }
                if (ttEl) { ttEl.value = tinh; window.wizardState.formData['dia_chi_tinh_thanh'] = tinh; }
            }
        } else {
            if (statusEl) statusEl.innerHTML = '<span class="text-warning"><i class="fa-solid fa-circle-exclamation"></i> Không tìm thấy dữ liệu từ Tổng cục Thuế. Vui lòng nhập tay.</span>';
        }
    } catch (err) {
        console.error('Lỗi tra cứu MST:', err);
        if (statusEl) statusEl.innerHTML = '<span class="text-error">Lỗi kết nối tra cứu MST.</span>';
    }
};

// --- STEP 3: INDUSTRY CODES ---
function renderStep3Nganh() {
    return `
        <div style="margin-bottom: var(--space-4);">
            <h2 class="text-2xl font-bold">Chọn ngành nghề kinh doanh</h2>
            <p class="text-secondary text-sm">Tìm kiếm và chọn các ngành nghề theo Hệ thống ngành kinh tế Việt Nam (VSIC). Ngành đầu tiên được chọn làm ngành chính.</p>
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
    const q = query.trim();
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
                    <div>
                        <span class="badge" style="margin-right: 8px;">${r.ma}</span>
                        <span class="text-sm font-bold text-white">${r.ten}</span>
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
                <span class="text-sm ${n.is_main ? 'font-bold text-yellow' : 'text-white'}">${n.ten}</span>
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
    const tplName = window.wizardState.template ? window.wizardState.template.name : '';
    if (tplName === 'Chuyển nhượng Công ty TNHH 2 TV' && window.collectCN2TVData) {
        if (document.getElementById('COMP_TEN_CONG_TY_VN')) {
            window.collectCN2TVData();
        }
    } else if (tplName === 'Chuyển đổi loại hình 1TV sang 2 TV' && window.collectCD1TV2TVData) {
        if (document.getElementById('cd_ten_cty')) {
            window.collectCD1TV2TVData();
        }
    } else {
        if (window.wizardState.step === 2) {
            collectFormData();
        }
    }

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
            dkkd_selected: window.wizardState.dkkdSelected
        },
        ma_nganh: window.wizardState.maNganh.map(n => ({
            ma: n.ma,
            ten: n.ten,
            is_main: !!n.is_main
        })),
        special_payload: {
            cn2tv_data: window.wizardState.cn2tvData,
            cd1tv2tv_data: window.wizardState.cd1tv2tvData,
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
