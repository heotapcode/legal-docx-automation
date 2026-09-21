window.wizardState = {
    step: 1,
    template: null,
    vneIdData: null,
    formData: {},
    maNganh: []
};



function renderWizard() {
    return `
        <!-- Navbar minimal -->
        <nav class="navbar scrolled">
            <div class="container navbar-container">
                <a href="#/" class="navbar-brand">
                    <i class="fa-solid fa-building text-gradient"></i> NAC
                </a>
                <a href="#/" class="btn btn-ghost btn-sm"><i class="fa-solid fa-xmark"></i> Thoát</a>
            </div>
        </nav>

        <section class="section" style="padding-top: var(--space-24); min-height: 100vh;">
            <div class="container" style="max-width: 900px;">
                <!-- Progress Bar -->
                <div class="wizard-progress mb-8">
                    <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-2);" class="text-sm text-secondary font-bold" id="wizard-step-text">
                        <span>Bước 1/5: Chọn thủ tục</span>
                    </div>
                    <div style="width: 100%; height: 8px; background: var(--bg-glass); border-radius: var(--radius-full); overflow: hidden;">
                        <div id="wizard-progress-bar" style="width: 20%; height: 100%; background: var(--accent-gradient); transition: width 0.3s ease;"></div>
                    </div>
                </div>

                <!-- Wizard Content Area -->
                <div id="wizard-content" class="card card-glass" style="min-height: 500px; position: relative;">
                    <!-- Content injected here by JS -->
                </div>
                
                <!-- Wizard Footer Controls -->
                <div id="wizard-controls" style="display: flex; justify-content: space-between; margin-top: var(--space-6);">
                    <!-- Buttons injected here by JS -->
                </div>
            </div>
        </section>
    `;
}

window.initWizard = async function() {
    // Reset state on init
    window.wizardState = {
        step: 1,
        template: null,
        vneIdData: null,
        formData: {},
        maNganh: [],
        templatesList: []
    };
    
    // Initial loading state
    renderCurrentStep();
    
    // Fetch real templates from backend
    try {
        const res = await fetch('/api/templates');
        if (res.ok) {
            const data = await res.json();
            window.wizardState.templatesList = data.templates.map(t => ({
                id: t.name,
                name: t.display_name,
                price: t.category === 'Thành lập mới' ? '199K' : 'FREE',
                priceNum: t.category === 'Thành lập mới' ? 199000 : 0,
                category: t.category,
                files: t.file_count
            }));
            // Re-render to show templates
            renderCurrentStep();
        }
    } catch(err) {
        console.error('Failed to load templates:', err);
    }
};

function renderCurrentStep() {
    const content = document.getElementById('wizard-content');
    const controls = document.getElementById('wizard-controls');
    const progressBar = document.getElementById('wizard-progress-bar');
    const stepText = document.getElementById('wizard-step-text');
    
    if(!content) return;
    
    content.style.opacity = '0';
    
    setTimeout(() => {
        progressBar.style.width = `${(window.wizardState.step / 4) * 100}%`;
        
        switch(window.wizardState.step) {
            case 1:
                stepText.innerHTML = '<span>Bước 1/4: Chọn thủ tục</span>';
                content.innerHTML = renderStep1();
                controls.innerHTML = `<button class="btn btn-ghost" disabled>Quay lại</button>`;
                break;
            case 2:
                stepText.innerHTML = '<span>Bước 2/4: Điền thông tin</span>';
                content.innerHTML = renderStep3(); // Keeping function name for simplicity
                controls.innerHTML = `
                    <button class="btn btn-ghost" onclick="prevStep()">Quay lại</button>
                    <button class="btn btn-primary" onclick="nextStep()">Tiếp theo &rarr;</button>
                `;
                // Load form fields after render
                loadFormFields();
                break;
            case 3:
                stepText.innerHTML = '<span>Bước 3/4: Chọn mã ngành</span>';
                content.innerHTML = renderStep4();
                controls.innerHTML = `
                    <button class="btn btn-ghost" onclick="prevStep()">Quay lại</button>
                    <button class="btn btn-primary" onclick="nextStep()">Tiếp theo &rarr;</button>
                `;
                break;
            case 4:
                stepText.innerHTML = '<span>Bước 4/4: Xác nhận & Tải hồ sơ</span>';
                content.innerHTML = renderStep5();
                controls.innerHTML = `
                    <button class="btn btn-ghost" onclick="prevStep()" id="btn-back-final">Quay lại</button>
                    <button class="btn btn-primary" onclick="generateDocuments()" id="btn-download">
                        <i class="fa-solid fa-download"></i> Tải hồ sơ (${window.wizardState.template.price})
                    </button>
                `;
                break;
        }
        
        content.style.opacity = '1';
        content.style.transition = 'opacity 0.3s ease';
    }, 150);
}

window.nextStep = function() {
    // Collect data before leaving step 2 (form filling)
    if (window.wizardState.step === 2) {
        if (window.wizardState.template && window.wizardState.template.name === 'Chuyển nhượng Công ty TNHH 2 TV') {
            if (window.collectCN2TVData) {
                const success = window.collectCN2TVData();
                if (!success) return; // validation failed
            }
        } else if (window.wizardState.template && window.wizardState.template.name === 'Chuyển đổi loại hình 1TV sang 2 TV') {
            if (window.collectCD1TV2TVData) {
                const success = window.collectCD1TV2TVData();
                if (!success) return; // validation failed
            }
        } else {
            const inputs = document.querySelectorAll('#dynamic-form-container input');
            inputs.forEach(input => {
                if (input.name && input.type !== 'radio' && input.type !== 'checkbox') {
                    window.wizardState.formData[input.name] = input.value;
                }
            });
        }
        
        // Collect DKKD selected checkboxes
        const dkkdCbs = document.querySelectorAll('.dkkd-cb:checked');
        if (dkkdCbs.length > 0) {
            window.wizardState.dkkdSelected = Array.from(dkkdCbs).map(cb => cb.value);
        } else {
            window.wizardState.dkkdSelected = null;
        }

        // Auto-fill CHUC_DANH_KY / CHUC_VU_KY based on company type
        let cType = window.wizardState.companyType;
        if (!cType && window.wizardState.template) {
            // Fallback for Thành lập mới
            const tId = window.wizardState.template.id;
            if (tId.includes('1tv')) cType = '1tv';
            else if (tId.includes('2tv')) cType = '2tv';
            else if (tId.includes('cp')) cType = 'cp';
        }
        if (cType === '1tv') {
            window.wizardState.formData['CHUC_DANH_KY'] = 'CHỦ SỞ HỮU';
            window.wizardState.formData['CHUC_VU_KY'] = 'GIÁM ĐỐC';
        } else if (cType === '2tv') {
            window.wizardState.formData['CHUC_DANH_KY'] = 'HỘI ĐỒNG THÀNH VIÊN';
            window.wizardState.formData['CHUC_VU_KY'] = 'GIÁM ĐỐC';
        } else if (cType === 'cp') {
            window.wizardState.formData['CHUC_DANH_KY'] = 'ĐẠI HỘI ĐỒNG CỔ ĐÔNG';
            window.wizardState.formData['CHUC_VU_KY'] = 'GIÁM ĐỐC';
        }
    }

    if (window.wizardState.step < 4) {
        window.wizardState.step++;
        renderCurrentStep();
    }
};

window.prevStep = function() {
    if (window.wizardState.step > 1) {
        window.wizardState.step--;
        renderCurrentStep();
    }
};

window.selectTemplate = function(id) {
    window.wizardState.template = window.wizardState.templatesList.find(t => t.id === id);
    nextStep();
};

// STEP 1
function renderStep1() {
    if (!window.wizardState.templatesList || window.wizardState.templatesList.length === 0) {
        return `<div class="text-center py-12"><i class="fa-solid fa-spinner fa-spin fa-2x text-accent"></i><p class="mt-4 text-secondary">Đang tải danh sách thủ tục...</p></div>`;
    }
    
    // Group templates by category
    const categories = [...new Set(window.wizardState.templatesList.map(t => t.category))];
    let html = `<h2 class="text-2xl font-bold mb-6">Chọn loại thủ tục bạn muốn thực hiện</h2>`;
    
    categories.forEach(cat => {
        html += `
            <h3 class="text-lg font-bold mt-6 mb-4 text-gradient">${cat}</h3>
            <div class="grid-2" style="gap: var(--space-4);">
        `;
        window.wizardState.templatesList.filter(t => t.category === cat).forEach(t => {
            const isFree = t.priceNum === 0;
            html += `
                <div class="card card-glass" style="cursor: pointer; padding: var(--space-4);" onclick="selectTemplate('${t.id}')" onmouseover="this.style.borderColor='var(--accent-primary)'" onmouseout="this.style.borderColor='var(--border-glass)'">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div class="font-bold mb-1">${t.name}</div>
                            <div class="text-xs text-muted"><i class="fa-solid fa-file-lines"></i> ${t.files} biểu mẫu</div>
                        </div>
                        <div class="badge" style="background: ${isFree ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.2)'}; color: ${isFree ? 'var(--success)' : 'var(--accent-primary)'}">
                            ${t.price}
                        </div>
                    </div>
                </div>
            `;
        });
        html += `</div>`;
    });
    
    return html;
}



// STEP 3
function renderStep3() {
    return `
        <h2 class="text-2xl font-bold mb-2">Điền thông tin hồ sơ</h2>
        <p class="text-secondary mb-6">Mẫu: <span class="text-gradient font-bold">${window.wizardState.template ? window.wizardState.template.name : ''}</span></p>
        
        <div id="dynamic-form-container">
            <div class="text-center py-8"><i class="fa-solid fa-spinner fa-spin"></i> Đang tải biểu mẫu...</div>
        </div>
    `;
}

window.loadFormFields = async function() {
    const container = document.getElementById('dynamic-form-container');
    if(!container) return;
    
    // Get actual backend template name
    const templateName = window.wizardState.template.name;

    if (templateName === 'Chuyển nhượng Công ty TNHH 2 TV') {
        if (window.renderCN2TVWizard) {
            window.renderCN2TVWizard(container);
            return;
        }
    }

    if (templateName === 'Chuyển đổi loại hình 1TV sang 2 TV') {
        if (window.renderCD1TV2TVWizard) {
            window.renderCD1TV2TVWizard(container);
            return;
        }
    }

    container.innerHTML = '<div class="text-center py-8"><i class="fa-solid fa-spinner fa-spin"></i> Đang phân tích biểu mẫu...</div>';
    
    try {
        const response = await fetch(`/api/templates/${encodeURIComponent(templateName)}/fields`);
        if(!response.ok) throw new Error('API Error');
        const data = await response.json();
        const fields = data.fields || [];
        
        if(fields.length === 0) {
            container.innerHTML = '<div class="text-center py-8 text-warning"><i class="fa-solid fa-triangle-exclamation"></i> Không tìm thấy trường dữ liệu nào cho biểu mẫu này.</div>';
            return;
        }

        // Group fields by their group attribute
        const groupedFields = fields.reduce((acc, field) => {
            if(!acc[field.group]) acc[field.group] = [];
            acc[field.group].push(field);
            return acc;
        }, {});

        const hasVNeID = window.wizardState.vneIdData != null;
        const autoBadge = `<span class="badge" style="background: rgba(16,185,129,0.1); color: var(--success); font-size: 10px; margin-left: 8px;">Từ VNeID</span>`;

        let html = '<div style="display: flex; flex-direction: column; gap: var(--space-4);">';
        
        const groupIcons = {
            'Thông tin Công ty': '<i class="fa-solid fa-building"></i>',
            'Đại diện pháp luật CŨ': '<i class="fa-solid fa-user-clock"></i>',
            'Đại diện pháp luật MỚI': '<i class="fa-solid fa-user-tie"></i>',
            'Người đại diện pháp luật': '<i class="fa-solid fa-user-tie"></i>',
            'Thành viên 1': '<i class="fa-solid fa-user"></i>',
            'Thành viên 2': '<i class="fa-solid fa-users"></i>',
            'Người ký (Tự động điền)': '<i class="fa-solid fa-pen-nib"></i>'
        };
        const groupColors = {
            'Thông tin Công ty': 'var(--info)',
            'Đại diện pháp luật CŨ': 'var(--warning)',
            'Đại diện pháp luật MỚI': 'var(--accent-secondary)',
            'Người đại diện pháp luật': 'var(--accent-secondary)',
            'Thành viên 1': 'var(--success)',
            'Thành viên 2': 'var(--success)',
            'Người ký (Tự động điền)': 'var(--text-muted)'
        };

        const groupOrder = [
            'Thông tin Công ty',
            'Đại diện pháp luật CŨ',
            'Thành viên 1',
            'Thành viên 2',
            'Đại diện pháp luật MỚI',
            'Người đại diện pháp luật',
            'Người ký (Tự động điền)'
        ];

        const sortedGroups = Object.keys(groupedFields).sort((a, b) => {
            let idxA = groupOrder.indexOf(a);
            let idxB = groupOrder.indexOf(b);
            if(idxA === -1) idxA = 999;
            if(idxB === -1) idxB = 999;
            return idxA - idxB;
        });

        for(const group of sortedGroups) {
            const groupFields = groupedFields[group];
            
            // Hide 'Người ký' if we want it to be fully auto
            const displayStyle = group === 'Người ký (Tự động điền)' ? 'display: none;' : '';

            html += `
                <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); ${displayStyle}">
                    <h3 class="font-bold mb-4" style="color: ${groupColors[group] || 'var(--text-primary)'};">${groupIcons[group] || ''} ${group}</h3>
                    <div class="grid-2" style="gap: var(--space-4);">
            `;

            groupFields.forEach(field => {
                let value = '';

                // Make full width for long fields like addresses
                const isFullWidth = field.key.includes('DIA_CHI') || field.key.includes('TEN_CONG_TY');
                const colSpan = isFullWidth ? 'grid-column: span 2;' : '';

                let extraAction = '';
                if(field.key === 'MA_SO_THUE') {
                    extraAction += `<div class="mt-2"><button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0;" onclick="lookupMST(event)"><i class="fa-solid fa-magnifying-glass"></i> Tra cứu tự động</button></div>`;
                } else if(field.key.endsWith('_HO_TEN')) {
                    const prefix = field.key.replace('_HO_TEN', '');
                    extraAction += `<div class="mt-2"><button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0; color: var(--success); border-color: var(--success);" onclick="triggerInlineOCR_Standard('${prefix}', event)"><i class="fa-solid fa-id-card"></i> Quét VNeID/CCCD</button></div>`;
                }

                html += `
                    <div style="${colSpan}">
                        <label class="text-sm text-muted mb-1 block">${field.label}</label>
                        <input type="text" name="${field.key}" id="input-${field.key}" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${value}">
                        ${extraAction}
                    </div>
                `;
            });
            
            if (group === 'Công ty') {
                html += `
                    <div id="dkkd-company-type-container" style="display: none; grid-column: span 2; margin-top: var(--space-2); padding: var(--space-3); background: rgba(0,0,0,0.2); border-radius: var(--radius-md);">
                        <p class="text-sm font-bold text-warning mb-2"><i class="fa-solid fa-triangle-exclamation"></i> Công ty này là TNHH 1 Thành viên hay 2 Thành viên trở lên?</p>
                        <div style="display: flex; gap: var(--space-4);">
                            <label style="cursor: pointer;"><input type="radio" name="tnhh_type" value="1tv" onchange="toggleA3(false)"> TNHH 1 Thành viên</label>
                            <label style="cursor: pointer;"><input type="radio" name="tnhh_type" value="2tv" onchange="toggleA3(true)"> TNHH 2 Thành viên trở lên</label>
                        </div>
                    </div>
                `;
            }

            html += `
                    </div>
                </div>
            `;
        }
        
        // Inject DKKD specific block if template is Thay doi DKKD
        if (templateName === 'Thay đổi nội dung ĐKKD') {
            html += `
                <div class="card card-glass mt-6" style="border-color: var(--accent-primary);">
                    <h3 class="text-lg font-bold mb-4 text-gradient"><i class="fa-solid fa-list-check"></i> Chọn Nội Dung Thay Đổi</h3>
                    <div class="grid-2" style="gap: var(--space-3);" id="dkkd-checkboxes">
                        <label style="display: flex; gap: 8px; cursor: pointer; align-items: start;">
                            <input type="checkbox" class="dkkd-cb" value="A1" style="margin-top: 4px;"> <span><b>A1:</b> Thay đổi tên doanh nghiệp</span>
                        </label>
                        <label style="display: flex; gap: 8px; cursor: pointer; align-items: start;">
                            <input type="checkbox" class="dkkd-cb" value="A2" style="margin-top: 4px;"> <span><b>A2:</b> Thay đổi địa chỉ trụ sở chính</span>
                        </label>
                        <label id="lbl-A3" style="display: flex; gap: 8px; cursor: pointer; align-items: start;">
                            <input type="checkbox" class="dkkd-cb" value="A3" style="margin-top: 4px;"> <span><b>A3:</b> Thay đổi thành viên CT TNHH</span>
                        </label>
                        <label style="display: flex; gap: 8px; cursor: pointer; align-items: start;">
                            <input type="checkbox" class="dkkd-cb" value="A4" style="margin-top: 4px;"> <span><b>A4:</b> Thay đổi vốn điều lệ</span>
                        </label>
                        <label style="display: flex; gap: 8px; cursor: pointer; align-items: start;">
                            <input type="checkbox" class="dkkd-cb" value="A5" style="margin-top: 4px;"> <span><b>A5:</b> Thay đổi ngành, nghề KD</span>
                        </label>
                        <label style="display: flex; gap: 8px; cursor: pointer; align-items: start;">
                            <input type="checkbox" class="dkkd-cb" value="A6" style="margin-top: 4px;"> <span><b>A6:</b> Thay đổi thông tin đăng ký thuế</span>
                        </label>
                        <label style="display: flex; gap: 8px; cursor: pointer; align-items: start; grid-column: span 2;">
                            <input type="checkbox" class="dkkd-cb" value="A7" style="margin-top: 4px;"> <span><b>A7:</b> Chủ sở hữu hưởng lợi</span>
                        </label>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        container.innerHTML = html;

    } catch(err) {
        console.error(err);
        container.innerHTML = '<div class="text-center py-8 text-error"><i class="fa-solid fa-circle-xmark"></i> Có lỗi khi tải form biểu mẫu.</div>';
    }
}

window.lookupMST = async function(event) {
    const mstInput = document.getElementById('input-MA_SO_THUE');
    if(!mstInput || !mstInput.value) {
        alert("Vui lòng nhập Mã số thuế vào ô trên trước khi tra cứu.");
        return;
    }
    
    const btn = event.currentTarget;
    const oldHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang tra cứu...';
    btn.disabled = true;

    try {
        const response = await fetch(`/api/mst/${encodeURIComponent(mstInput.value)}`);
        const result = await response.json();
        
        if(result.success && result.data && result.data.name) {
            const nameInput = document.getElementById('input-TEN_CONG_TY_VN');
            const addressInput = document.getElementById('input-DIA_CHI_DAY_DU');
            const nameEnInput = document.getElementById('input-TEN_CONG_TY_EN');
            const nameShortInput = document.getElementById('input-TEN_CONG_TY_VIET_TAT');
            
            if(nameInput) {
                nameInput.value = result.data.name;
                nameInput.style.color = 'var(--success)';
            }
            if(addressInput) {
                addressInput.value = result.data.address;
                addressInput.style.color = 'var(--success)';
            }
            if(nameEnInput && result.data.internationalName) {
                nameEnInput.value = result.data.internationalName;
                nameEnInput.style.color = 'var(--success)';
            }
            if(nameShortInput && result.data.shortName) {
                nameShortInput.value = result.data.shortName;
                nameShortInput.style.color = 'var(--success)';
            }
            
            // Auto-split address for company intelligently (District removed)
            const parts = result.data.address.split(',').map(p => p.trim()).filter(p => p);
            let pTinhThanh = '', pXaPhuong = '', pSoNha = '';
            
            if (parts.length > 0) pTinhThanh = parts.pop();
            if (parts.length > 0) pXaPhuong = parts.pop();
            if (parts.length > 0) pSoNha = parts.join(', ');
            
            const pTinhThanhInput = document.getElementById('input-DIA_CHI_TINH_THANH');
            const pQuanHuyenInput = document.getElementById('input-DIA_CHI_QUAN_HUYEN');
            const pXaPhuongInput = document.getElementById('input-DIA_CHI_XA_PHUONG');
            const pSoNhaInput = document.getElementById('input-DIA_CHI_SO_NHA');
            
            if(pTinhThanhInput && pTinhThanh) { pTinhThanhInput.value = pTinhThanh; pTinhThanhInput.style.color = 'var(--success)'; }
            if(pQuanHuyenInput) { pQuanHuyenInput.value = ''; }
            if(pXaPhuongInput && pXaPhuong) { pXaPhuongInput.value = pXaPhuong; pXaPhuongInput.style.color = 'var(--success)'; }
            if(pSoNhaInput && pSoNha) { pSoNhaInput.value = pSoNha; pSoNhaInput.style.color = 'var(--success)'; }
            
            // Detect company type logic
            const upperName = result.data.name.toUpperCase();
            const a3Label = document.getElementById('lbl-A3');
            const typeContainer = document.getElementById('dkkd-company-type-container');
            
            if (upperName.includes("CỔ PHẦN") || upperName.includes(" CP ")) {
                window.wizardState.companyType = 'cp';
                if (a3Label) a3Label.style.display = 'none';
                if(typeContainer) typeContainer.style.display = 'none';
            } else if (upperName.includes("MỘT THÀNH VIÊN") || upperName.includes("MTV") || upperName.includes("1 THÀNH VIÊN")) {
                window.wizardState.companyType = '1tv';
                if (a3Label) a3Label.style.display = 'none';
                if(typeContainer) typeContainer.style.display = 'none';
            } else if (upperName.includes("TNHH") || upperName.includes("TRÁCH NHIỆM HỮU HẠN")) {
                window.wizardState.companyType = null;
                // It's a TNHH but we don't know if 1 or >=2. Ask user.
                if(typeContainer) {
                    typeContainer.style.display = 'block';
                    // Default hide A3 until they select 2TV
                    if (a3Label) a3Label.style.display = 'none';
                }
            } else {
                window.wizardState.companyType = null;
            }
            
        } else {
            alert('Không tìm thấy thông tin công ty. Bạn vui lòng kiểm tra lại Mã số thuế.');
        }
    } catch(err) {
        console.error(err);
        alert('Lỗi tra cứu MST: ' + err.message);
    }
    
    btn.innerHTML = oldHTML;
    btn.disabled = false;
}

window.toggleA3 = function(is2TV) {
            window.wizardState.companyType = is2TV ? '2tv' : '1tv';
            const a3Label = document.getElementById('lbl-A3');
            if (a3Label) {
                a3Label.style.display = is2TV ? 'flex' : 'none';
                if (!is2TV) {
                    const cb = a3Label.querySelector('input[type="checkbox"]');
                    if (cb) cb.checked = false;
                }
            }
        }

// STEP 4
function renderStep4() {
    const isTLM = window.wizardState.template && window.wizardState.template.category === 'Thành lập mới';
    
    if (!isTLM) {
        return `
            <div class="text-center py-12">
                <div style="font-size: 3rem; color: var(--success); margin-bottom: var(--space-4);"><i class="fa-solid fa-forward-step"></i></div>
                <h2 class="text-2xl font-bold mb-2">Không cần chọn mã ngành</h2>
                <p class="text-secondary mb-6">Thủ tục này không yêu cầu cập nhật mã ngành kinh doanh.</p>
                <button class="btn btn-primary" onclick="nextStep()">Tiếp tục &rarr;</button>
            </div>
        `;
    }

    return `
        <h2 class="text-2xl font-bold mb-2">Chọn mã ngành kinh doanh</h2>
        <p class="text-secondary mb-6">Nhập từ khóa để tìm kiếm và chọn các ngành nghề (mã ngành đầu tiên sẽ là ngành chính).</p>
        
        <div style="position: relative; margin-bottom: var(--space-6);">
            <i class="fa-solid fa-search" style="position: absolute; left: 12px; top: 12px; color: var(--text-muted);"></i>
            <input type="text" placeholder="Tìm kiếm (VD: phần mềm, thương mại...)" style="width: 100%; background: rgba(0,0,0,0.2); border: 1px solid var(--border-glass); color: white; padding: 10px 10px 10px 36px; border-radius: var(--radius-md);" onkeyup="window.searchNganh(this.value)">
        </div>
        
        <div id="nganh-results" style="max-height: 200px; overflow-y: auto; background: rgba(255,255,255,0.02); border-radius: var(--radius-md); padding: var(--space-2); margin-bottom: var(--space-6);">
            <div class="text-muted text-sm text-center py-4">Nhập từ khóa để tìm kiếm...</div>
        </div>
        
        <h3 class="font-bold text-sm text-secondary mb-2">Ngành đã chọn:</h3>
        <div id="nganh-selected" style="border: 1px solid var(--border-glass); border-radius: var(--radius-md); min-height: 100px; padding: var(--space-2);">
            <div class="text-muted text-sm text-center py-4">Chưa chọn ngành nào</div>
        </div>
    `;
}

window.searchNganh = function(val) {
    const results = document.getElementById('nganh-results');
    if(val.length < 2) {
        results.innerHTML = '<div class="text-muted text-sm text-center py-4">Nhập từ khóa để tìm kiếm...</div>';
        return;
    }
    
    // Mock results
    results.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 8px; padding: 8px; hover:background: rgba(255,255,255,0.1); border-bottom: 1px solid var(--border-glass);">
            <input type="checkbox" id="n6201" onclick="window.toggleNganh('6201', 'Lập trình máy vi tính')" style="margin-top: 4px;">
            <label for="n6201" style="cursor: pointer;"><span class="font-bold text-gradient">6201</span> - Lập trình máy vi tính</label>
        </div>
        <div style="display: flex; align-items: flex-start; gap: 8px; padding: 8px; hover:background: rgba(255,255,255,0.1);">
            <input type="checkbox" id="n6202" onclick="window.toggleNganh('6202', 'Tư vấn máy vi tính và quản trị hệ thống máy vi tính')" style="margin-top: 4px;">
            <label for="n6202" style="cursor: pointer;"><span class="font-bold text-gradient">6202</span> - Tư vấn máy vi tính và quản trị hệ thống máy vi tính</label>
        </div>
    `;
}

window.toggleNganh = function(code, name) {
    const exists = window.wizardState.maNganh.findIndex(n => n.code === code);
    if(exists > -1) {
        window.wizardState.maNganh.splice(exists, 1);
    } else {
        window.wizardState.maNganh.push({code, name});
    }
    
    const sel = document.getElementById('nganh-selected');
    if(window.wizardState.maNganh.length === 0) {
        sel.innerHTML = '<div class="text-muted text-sm text-center py-4">Chưa chọn ngành nào</div>';
        return;
    }
    
    let h = '';
    window.wizardState.maNganh.forEach((n, idx) => {
        h += `
            <div style="background: rgba(255,255,255,0.05); padding: 6px 12px; border-radius: 4px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    ${idx === 0 ? '<span class="badge" style="background: var(--warning); color: #000; padding: 2px 6px; font-size: 9px; margin-right: 8px;">CHÍNH</span>' : ''}
                    <span class="font-bold">${n.code}</span> - ${n.name}
                </div>
            </div>
        `;
    });
    sel.innerHTML = h;
}

// STEP 5
function renderStep5() {
    const t = window.wizardState.template;
    return `
        <div id="step5-content">
            <h2 class="text-2xl font-bold mb-2">Xác nhận thông tin</h2>
            <p class="text-secondary mb-6">Vui lòng kiểm tra lại trước khi tải hồ sơ.</p>
            
            <div style="background: rgba(0,0,0,0.3); border-radius: var(--radius-lg); padding: var(--space-6); margin-bottom: var(--space-6);">
                <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed var(--border-glass); padding-bottom: var(--space-4); margin-bottom: var(--space-4);">
                    <span class="text-muted">Loại thủ tục</span>
                    <span class="font-bold">${t ? t.name : ''}</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed var(--border-glass); padding-bottom: var(--space-4); margin-bottom: var(--space-4);">
                    <span class="text-muted">Số lượng file</span>
                    <span class="font-bold">${t ? t.files : 0} biểu mẫu Word/Excel</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="text-muted">Tổng thanh toán</span>
                    <span class="text-2xl font-bold text-gradient">${t ? t.price : '0'}</span>
                </div>
            </div>
        </div>
        
        <div id="step5-loading" style="display: none; text-align: center; padding: var(--space-12) 0;">
            <div style="font-size: 3rem; color: var(--accent-primary); margin-bottom: var(--space-4);"><i class="fa-solid fa-cog fa-spin"></i></div>
            <h3 class="font-bold text-xl mb-2">Đang tạo hồ sơ...</h3>
            <p class="text-secondary">AI đang điền thông tin vào các biểu mẫu pháp lý.</p>
        </div>
        
        <div id="step5-success" style="display: none;">
            <div class="text-center mb-8">
                <div style="font-size: 4rem; color: var(--success); margin-bottom: var(--space-4);"><i class="fa-solid fa-check-circle"></i></div>
                <h2 class="text-3xl font-bold mb-2 text-success">Tải thành công!</h2>
                <p class="text-secondary">Bộ hồ sơ hoàn chỉnh đã được lưu vào máy của bạn.</p>
            </div>
            
            <div style="background: var(--accent-gradient); border-radius: var(--radius-lg); padding: var(--space-6);">
                <div class="badge mb-4" style="background: rgba(255,255,255,0.2); color: white; border: none;">BƯỚC TIẾP THEO</div>
                <h3 class="text-xl font-bold text-white mb-4">Các dịch vụ hỗ trợ của NAC</h3>
                
                <div style="display: flex; flex-direction: column; gap: var(--space-3); margin-bottom: var(--space-6);">
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; color: white;">
                        <input type="checkbox" checked disabled> Nộp hồ sơ & Nhận kết quả (500K)
                    </label>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; color: white;">
                        <input type="checkbox" checked disabled> Kế toán thuế trọn gói (3tr/tháng)
                    </label>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; color: white;">
                        <input type="checkbox" checked disabled> Chữ ký số (1.5tr) & HĐĐT (1tr)
                    </label>
                </div>
                
                <div style="background: rgba(0,0,0,0.2); padding: var(--space-4); border-radius: var(--radius-md); text-align: center; margin-bottom: var(--space-4);">
                    <div class="font-bold text-white mb-1">🎁 MUA GÓI KHỞI NGHIỆP TRỌN GÓI</div>
                    <div class="text-2xl font-bold text-white">Chỉ 4.5 Triệu Đồng</div>
                </div>
                
                <button class="btn" style="background: white; color: var(--accent-primary); width: 100%;">
                    <i class="fa-solid fa-comment-dots"></i> Nhắn tin Zalo ngay
                </button>
            </div>
        </div>
    `;
}

window.generateDocuments = async function() {
    document.getElementById('step5-content').style.display = 'none';
    document.getElementById('btn-back-final').style.display = 'none';
    document.getElementById('btn-download').style.display = 'none';
    document.getElementById('step5-loading').style.display = 'block';
    
    const payload = {
        template_name: window.wizardState.template.name,
        data: window.wizardState.formData,
        dkkd_selected: window.wizardState.dkkdSelected,
        cn2tv_data: window.wizardState.cn2tvData,
        cd1tv2tv_data: window.wizardState.cd1tv2tvData,
        ma_nganh: window.wizardState.maNganh.map((n, idx) => ({
            ma: n.code,
            ten: n.name,
            is_main: idx === 0
        }))
    };

    try {
        const response = await fetch('/api/documents/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            const errData = await response.json();
            throw new Error(errData.message || 'API Error');
        }

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        // Download ZIP blob
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `Ho_So_${window.wizardState.template.id}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        document.getElementById('step5-loading').style.display = 'none';
        document.getElementById('step5-success').style.display = 'block';
    } catch (error) {
        console.error('Download error:', error);
        alert('Có lỗi xảy ra khi tạo hồ sơ. Vui lòng kiểm tra lại kết nối hoặc log server.');
        document.getElementById('step5-content').style.display = 'block';
        document.getElementById('btn-back-final').style.display = 'inline-block';
        document.getElementById('btn-download').style.display = 'inline-block';
        document.getElementById('step5-loading').style.display = 'none';
    }
}

window.triggerInlineOCR_Standard = function(prefix, event) {
    const btn = event.currentTarget;
    
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/png, image/jpeg';
    
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if(!file) return;

        const oldHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang quét...';
        btn.disabled = true;

        const formData = new FormData();
        formData.append('image', file);
        formData.append('target', prefix);

        try {
            const response = await fetch('/api/ocr/vneid', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if(!result.success) throw new Error(result.message);

            let gt = result.data.gioi_tinh || '';
            if (gt.toLowerCase().includes('việt nam') || gt.toLowerCase().includes('viet nam')) {
                gt = '';
            }
            const map = {
                'HO_TEN': result.data.ho_ten,
                'SO_CCCD': result.data.so_cccd,
                'NGAY_SINH': result.data.ngay_sinh,
                'GIOI_TINH': gt,
                'DIA_CHI_DAY_DU': result.data.dia_chi,
                'DIA_CHI_SO_NHA': result.data.dia_chi_so_nha,
                'DIA_CHI_XA_PHUONG': result.data.dia_chi_xa_phuong,
                'DIA_CHI_QUAN_HUYEN': result.data.dia_chi_quan_huyen,
                'DIA_CHI_TINH_THANH': result.data.dia_chi_tinh_thanh
            };

            for (const [suffix, val] of Object.entries(map)) {
                if (val) {
                    const el = document.getElementById(`input-${prefix}_${suffix}`);
                    if (el) {
                        el.value = val;
                        el.style.color = 'var(--success)';
                    }
                }
            }
        } catch(err) {
            console.error(err);
            alert('Lỗi trích xuất: ' + err.message);
        }
        
        btn.innerHTML = oldHTML;
        btn.disabled = false;
    };
    
    fileInput.click();
};
