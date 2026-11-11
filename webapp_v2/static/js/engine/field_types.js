/**
 * Các kiểu ô của form nhập liệu: text, money (kèm số tiền bằng chữ), mst_lookup, phone, email, select,
 * checkbox_group, person (thẻ một người).
 *
 * FormRenderer (form_renderer.js) gọi renderField() cho các kiểu này; kiểu date, cccd, percent, number,
 * address, list do FormRenderer tự vẽ. Kiểu ô mới: thêm ở form_renderer.js.
 * Dữ liệu: wizardState.formData. Danh sách thành viên / cổ đông là kiểu list (FormRenderer), key thanh_vien.
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
