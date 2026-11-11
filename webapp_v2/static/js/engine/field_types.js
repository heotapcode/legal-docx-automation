/**
 * Các kiểu ô của form nhập liệu: text, money (kèm số tiền bằng chữ), mst_lookup, phone, email, select,
 * checkbox_group, person (thẻ một người), person_list (danh sách thành viên / cổ đông).
 *
 * FormRenderer (form_renderer.js) gọi renderField() cho các kiểu này; kiểu date, cccd, percent, number,
 * address, list do FormRenderer tự vẽ. Kiểu ô mới: thêm ở form_renderer.js.
 * Dữ liệu: ô thường ở wizardState.formData; danh sách thành viên ở wizardState.thanhVienList
 * (ô có class .m-field, data-idx, data-prop).
 * Phụ thuộc: utils.js, pages/wizard.js (wizardState, formatMoneyStr, renderStep2Form, collectFormData).
 */
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
