window.cd1tv2tvState = {
    step: 1,
    oldCompany: {
        mst: '',
        name: '',
        address: '',
        von: ''
    },
    csh: {},
    ddplCu: {},
    newCompany: {
        nameVn: '',
        nameEn: '',
        nameShort: ''
    },
    ddplMoi: {},
    members: [
        { id: 1, ho_ten: '', cccd: '', ngay_sinh: '', dia_chi: '', gioi_tinh: '', von: '', ty_le: '', nhan_cn: '' },
        { id: 2, ho_ten: '', cccd: '', ngay_sinh: '', dia_chi: '', gioi_tinh: '', von: '', ty_le: '', nhan_cn: '' }
    ]
};

function cdRenderInput(label, id, val, placeholder = '', onChange = '') {
    return `
        <div>
            <label class="text-sm text-muted mb-1 block">${label}</label>
            <input type="text" id="${id}" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${val || ''}" placeholder="${placeholder}" onchange="${onChange}">
        </div>
    `;
}

window.renderCD1TV2TVWizard = function(container) {
    container.innerHTML = `
        <div class="flex justify-between mb-6 border-b border-gray-700 pb-4">
            <div class="text-center flex-1 cursor-pointer" onclick="window.cd1tv2tvGotoStep(1)">
                <div id="cd-step-1" class="font-bold text-accent">1. Công ty cũ & CSH</div>
            </div>
            <div class="text-center flex-1 cursor-pointer" onclick="window.cd1tv2tvGotoStep(2)">
                <div id="cd-step-2" class="text-muted">2. Công ty mới & Thành viên</div>
            </div>
            <div class="text-center flex-1 cursor-pointer" onclick="window.cd1tv2tvGotoStep(3)">
                <div id="cd-step-3" class="text-muted">3. Hợp đồng CN</div>
            </div>
        </div>

        <div id="cd-step1-container">
            ${renderCDStep1()}
        </div>
        <div id="cd-step2-container" style="display:none;">
            ${renderCDStep2()}
        </div>
        <div id="cd-step3-container" style="display:none;">
            ${renderCDStep3()}
        </div>
    `;
    
    document.getElementById('cd-csh-is-ddpl')?.addEventListener('change', function(e) {
        if (e.target.checked) {
            document.getElementById('ddpl_cu_ho_ten').value = document.getElementById('csh_ho_ten').value;
            document.getElementById('ddpl_cu_cccd').value = document.getElementById('csh_cccd').value;
            document.getElementById('ddpl_cu_ngay_sinh').value = document.getElementById('csh_ngay_sinh').value;
            document.getElementById('ddpl_cu_gioi_tinh').value = document.getElementById('csh_gioi_tinh').value;
            document.getElementById('ddpl_cu_dia_chi').value = document.getElementById('csh_dia_chi').value;
        }
    });
};

window.cd1tv2tvGotoStep = function(step) {
    window.cd1tv2tvState.step = step;
    document.getElementById('cd-step-1').className = step === 1 ? 'font-bold text-accent' : 'text-muted';
    document.getElementById('cd-step-2').className = step === 2 ? 'font-bold text-accent' : 'text-muted';
    document.getElementById('cd-step-3').className = step === 3 ? 'font-bold text-accent' : 'text-muted';
    
    document.getElementById('cd-step1-container').style.display = step === 1 ? 'block' : 'none';
    document.getElementById('cd-step2-container').style.display = step === 2 ? 'block' : 'none';
    
    if (step === 3) {
        document.getElementById('cd-step3-container').innerHTML = renderCDStep3();
        document.getElementById('cd-step3-container').style.display = 'block';
    } else {
        document.getElementById('cd-step3-container').style.display = 'none';
    }
};

function renderCDStep1() {
    return `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;">
            <h3 class="font-bold text-info mb-4"><i class="fa-solid fa-building"></i> Công ty 1TV cũ</h3>
            <div class="grid-2" style="gap: var(--space-4);">
                <div>
                    <label class="text-sm text-muted mb-1 block">Mã số thuế</label>
                    <input type="text" id="cd_mst" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" placeholder="Nhập MST">
                    <div class="mt-2"><button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0;" onclick="lookupCDMst()"><i class="fa-solid fa-magnifying-glass"></i> Tra cứu</button></div>
                </div>
                ${cdRenderInput('Tên công ty tiếng Việt', 'cd_ten_cty', '', 'Tự động điền')}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ trụ sở chính</label>
                    <input type="text" id="cd_dia_chi_cty" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" placeholder="Tự động điền">
                </div>
                ${cdRenderInput('Vốn điều lệ cũ (VNĐ)', 'cd_von_cu', '', 'VD: 1.000.000.000', 'formatCurrencyInput(this)')}
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem; border-color: var(--warning);">
            <h3 class="font-bold text-warning mb-4"><i class="fa-solid fa-user-tie"></i> Chủ sở hữu (Bên bán)</h3>
            <div class="grid-2" style="gap: var(--space-4);">
                <div class="col-span-2">
                    <button class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0; color: var(--success); border-color: var(--success);" onclick="triggerInlineOCR_CD1TV('csh', event)"><i class="fa-solid fa-id-card"></i> Quét VNeID/CCCD</button>
                </div>
                ${cdRenderInput('Họ và tên', 'csh_ho_ten', '')}
                ${cdRenderInput('Số CCCD', 'csh_cccd', '')}
                ${cdRenderInput('Ngày sinh', 'csh_ngay_sinh', '')}
                ${cdRenderInput('Giới tính', 'csh_gioi_tinh', '')}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ thường trú</label>
                    <input type="text" id="csh_dia_chi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;">
                </div>
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem; border-color: var(--accent);">
            <h3 class="font-bold text-accent mb-4"><i class="fa-solid fa-user-shield"></i> Đại diện pháp luật cũ</h3>
            <label class="flex items-center gap-2 mb-4 cursor-pointer text-sm font-bold text-success" style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;">
                <input type="checkbox" id="cd-csh-is-ddpl"> Chủ sở hữu đồng thời là Người đại diện pháp luật cũ
            </label>
            <div class="grid-2" style="gap: var(--space-4);">
                ${cdRenderInput('Họ và tên', 'ddpl_cu_ho_ten', '')}
                ${cdRenderInput('Số CCCD', 'ddpl_cu_cccd', '')}
                ${cdRenderInput('Ngày sinh', 'ddpl_cu_ngay_sinh', '')}
                ${cdRenderInput('Giới tính', 'ddpl_cu_gioi_tinh', '')}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ thường trú</label>
                    <input type="text" id="ddpl_cu_dia_chi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;">
                </div>
            </div>
        </div>
    `;
}

function renderCDStep2() {
    return `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;">
            <h3 class="font-bold text-info mb-4"><i class="fa-solid fa-building-circle-arrow-right"></i> Công ty 2TV mới</h3>
            <div class="grid-2" style="gap: var(--space-4);">
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Tên công ty tiếng Việt mới (nếu có đổi)</label>
                    <input type="text" id="cd_ten_cty_moi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" placeholder="VD: CÔNG TY TNHH HAI THÀNH VIÊN...">
                </div>
                ${cdRenderInput('Tên tiếng Anh', 'cd_ten_en', '')}
                ${cdRenderInput('Tên viết tắt', 'cd_ten_vt', '')}
                ${cdRenderInput('Số điện thoại', 'cd_sdt', '')}
                ${cdRenderInput('Email', 'cd_email', '')}
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem; border-color: var(--accent);">
            <h3 class="font-bold text-accent mb-4"><i class="fa-solid fa-user-shield"></i> Đại diện pháp luật mới</h3>
            <div class="grid-2" style="gap: var(--space-4);">
                <div class="col-span-2">
                    <button class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0; color: var(--success); border-color: var(--success);" onclick="triggerInlineOCR_CD1TV('ddpl_moi', event)"><i class="fa-solid fa-id-card"></i> Quét VNeID/CCCD</button>
                </div>
                ${cdRenderInput('Họ và tên', 'ddpl_moi_ho_ten', '')}
                ${cdRenderInput('Số CCCD', 'ddpl_moi_cccd', '')}
                ${cdRenderInput('Ngày sinh', 'ddpl_moi_ngay_sinh', '')}
                ${cdRenderInput('Giới tính', 'ddpl_moi_gioi_tinh', '')}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ thường trú</label>
                    <input type="text" id="ddpl_moi_dia_chi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;">
                </div>
            </div>
        </div>

        <div class="flex justify-between items-center mb-4">
            <h3 class="font-bold text-success text-xl"><i class="fa-solid fa-users"></i> Danh sách thành viên</h3>
            <button class="btn btn-primary btn-sm" onclick="cdAddMember()"><i class="fa-solid fa-plus"></i> Thêm thành viên</button>
        </div>
        <div id="cd-members-list">
            ${window.cd1tv2tvState.members.map((m, idx) => renderCDMemberCard(idx)).join('')}
        </div>
    `;
}

function renderCDMemberCard(idx) {
    const m = window.cd1tv2tvState.members[idx];
    return `
        <div class="relative cd-member-card" style="background: rgba(255,255,255,0.03); border: 1px solid var(--success); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;" data-idx="${idx}">
            ${idx >= 2 ? `<button class="absolute top-4 right-4 text-error" onclick="cdRemoveMember(${idx})"><i class="fa-solid fa-trash"></i></button>` : ''}
            <h4 class="font-bold mb-4 text-success">Thành viên ${idx + 1}</h4>
            <div class="grid-2" style="gap: var(--space-4);">
                <div class="col-span-2">
                    <button class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0; color: var(--success); border-color: var(--success);" onclick="triggerInlineOCR_CD1TV('cd_tv_${idx}', event)"><i class="fa-solid fa-id-card"></i> Quét VNeID/CCCD</button>
                </div>
                ${cdRenderInput('Họ và tên', `cd_tv_${idx}_ho_ten`, m.ho_ten, '', 'cdSaveMembers()')}
                ${cdRenderInput('Số CCCD', `cd_tv_${idx}_cccd`, m.cccd, '', 'cdSaveMembers()')}
                ${cdRenderInput('Ngày sinh', `cd_tv_${idx}_ngay_sinh`, m.ngay_sinh, '', 'cdSaveMembers()')}
                ${cdRenderInput('Giới tính', `cd_tv_${idx}_gioi_tinh`, m.gioi_tinh, '', 'cdSaveMembers()')}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ thường trú</label>
                    <input type="text" id="cd_tv_${idx}_dia_chi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${m.dia_chi}" onchange="cdSaveMembers()">
                </div>
                <div>
                    <label class="text-sm text-muted font-bold text-warning mb-1 block">Vốn góp mới (VNĐ)</label>
                    <input type="text" id="cd_tv_${idx}_von" class="input border-warning" style="width: 100%; background: transparent; border: 1px solid var(--warning); color: white; padding: 8px 12px; border-radius: 4px;" placeholder="VD: 500.000.000" value="${m.von}" oninput="formatCurrencyInput(this); cdSaveMembers()">
                </div>
                <div>
                    <label class="text-sm text-muted font-bold text-warning mb-1 block">Tỷ lệ (%)</label>
                    <input type="text" id="cd_tv_${idx}_ty_le" class="input border-warning" style="width: 100%; background: transparent; border: 1px solid var(--warning); color: white; padding: 8px 12px; border-radius: 4px;" placeholder="VD: 50" value="${m.ty_le}" onchange="cdSaveMembers()">
                </div>
            </div>
        </div>
    `;
}

window.cdAddMember = function() {
    cdSaveMembers();
    window.cd1tv2tvState.members.push({ id: window.cd1tv2tvState.members.length + 1, ho_ten: '', cccd: '', ngay_sinh: '', dia_chi: '', gioi_tinh: '', von: '', ty_le: '', nhan_cn: '' });
    document.getElementById('cd-members-list').innerHTML = window.cd1tv2tvState.members.map((m, idx) => renderCDMemberCard(idx)).join('');
};

window.cdRemoveMember = function(idx) {
    cdSaveMembers();
    window.cd1tv2tvState.members.splice(idx, 1);
    document.getElementById('cd-members-list').innerHTML = window.cd1tv2tvState.members.map((m, i) => renderCDMemberCard(i)).join('');
};

window.cdSaveMembers = function() {
    window.cd1tv2tvState.members.forEach((m, idx) => {
        m.ho_ten = document.getElementById(`cd_tv_${idx}_ho_ten`)?.value || '';
        m.cccd = document.getElementById(`cd_tv_${idx}_cccd`)?.value || '';
        m.ngay_sinh = document.getElementById(`cd_tv_${idx}_ngay_sinh`)?.value || '';
        m.gioi_tinh = document.getElementById(`cd_tv_${idx}_gioi_tinh`)?.value || '';
        m.dia_chi = document.getElementById(`cd_tv_${idx}_dia_chi`)?.value || '';
        m.von = document.getElementById(`cd_tv_${idx}_von`)?.value || '';
        m.ty_le = document.getElementById(`cd_tv_${idx}_ty_le`)?.value || '';
    });
};

function renderCDStep3() {
    cdSaveMembers();
    let html = `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--warning); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;">
            <h3 class="font-bold text-warning mb-2"><i class="fa-solid fa-handshake"></i> Hợp đồng chuyển nhượng</h3>
            <p class="text-sm text-muted mb-4">Chủ sở hữu cũ sẽ là <b>Bên Bán</b>. Nhập số tiền vốn chuyển nhượng cho từng thành viên bên dưới để tạo Hợp đồng. Bỏ trống hoặc nhập 0 nếu không có giao dịch với thành viên đó.</p>
    `;
    
    window.cd1tv2tvState.members.forEach((m, idx) => {
        html += `
            <div class="bg-gray-800 p-3 rounded mb-3 flex items-center justify-between border border-gray-700">
                <div>
                    <div class="font-bold text-success">${m.ho_ten || `Thành viên ${idx + 1}`}</div>
                    <div class="text-xs text-muted">CCCD: ${m.cccd || '---'}</div>
                </div>
                <div class="text-right">
                    <label class="text-xs text-muted block mb-1">Số vốn nhận CN (VNĐ)</label>
                    <input type="text" id="cd_tv_${idx}_nhan_cn" class="input input-sm border-warning" style="background: transparent; border: 1px solid var(--warning); color: white; padding: 4px 8px; border-radius: 4px; width: 150px;" placeholder="VD: 100.000.000" value="${m.nhan_cn || ''}" oninput="formatCurrencyInput(this); cdSaveCN(${idx}, this.value)">
                </div>
            </div>
        `;
    });
    
    html += `</div>`;
    return html;
}

window.cdSaveCN = function(idx, val) {
    window.cd1tv2tvState.members[idx].nhan_cn = val;
};

window.lookupCDMst = async function() {
    const mst = document.getElementById('cd_mst').value;
    if(!mst) return;
    try {
        const res = await fetch(`/api/mst/${mst}`);
        const data = await res.json();
        if(data.success && data.data) {
            document.getElementById('cd_ten_cty').value = data.data.name;
            document.getElementById('cd_dia_chi_cty').value = data.data.address;
        }
    } catch(e) {}
};

window.triggerInlineOCR_CD1TV = function(prefix, event) {
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

            const elHoTen = document.getElementById(`${prefix}_ho_ten`);
            const elCCCD = document.getElementById(`${prefix}_cccd`);
            const elNgaySinh = document.getElementById(`${prefix}_ngay_sinh`);
            const elGioiTinh = document.getElementById(`${prefix}_gioi_tinh`);
            const elDiaChi = document.getElementById(`${prefix}_dia_chi`);

            if (elHoTen) elHoTen.value = result.data.ho_ten || '';
            if (elCCCD) elCCCD.value = result.data.so_cccd || '';
            if (elNgaySinh) elNgaySinh.value = result.data.ngay_sinh || '';
            if (elGioiTinh) elGioiTinh.value = gt;
            if (elDiaChi) elDiaChi.value = result.data.dia_chi || '';

            if (prefix.startsWith('cd_tv_')) cdSaveMembers();

            btn.innerHTML = oldHTML;
            btn.disabled = false;
        } catch(err) {
            console.error(err);
            alert('Lỗi trích xuất: ' + err.message);
            btn.innerHTML = oldHTML;
            btn.disabled = false;
        }
    };
    fileInput.click();
};

window.collectCD1TV2TVData = function() {
    cdSaveMembers();
    
    // Save to formData format so backend can use it
    window.wizardState.formData = {
        TEN_CONG_TY_VN_CU: document.getElementById('cd_ten_cty')?.value || '',
        MA_SO_THUE: document.getElementById('cd_mst')?.value || '',
        DIA_CHI_CTY_CU: document.getElementById('cd_dia_chi_cty')?.value || '',
        VON_CU: document.getElementById('cd_von_cu')?.value || '',
        
        TEN_CONG_TY_VN: document.getElementById('cd_ten_cty_moi')?.value || document.getElementById('cd_ten_cty')?.value || '',
        TEN_CONG_TY_EN: document.getElementById('cd_ten_en')?.value || '',
        TEN_CONG_TY_VIET_TAT: document.getElementById('cd_ten_vt')?.value || '',
        SDT_CONG_TY: document.getElementById('cd_sdt')?.value || '',
        EMAIL_CONG_TY: document.getElementById('cd_email')?.value || '',
    };
    
    window.wizardState.cd1tv2tvData = {
        csh: {
            HO_TEN: document.getElementById('csh_ho_ten')?.value,
            CCCD: document.getElementById('csh_cccd')?.value,
            NGAY_SINH: document.getElementById('csh_ngay_sinh')?.value,
            GIOI_TINH: document.getElementById('csh_gioi_tinh')?.value,
            DIA_CHI: document.getElementById('csh_dia_chi')?.value,
        },
        ddplCu: {
            HO_TEN: document.getElementById('ddpl_cu_ho_ten')?.value,
            CCCD: document.getElementById('ddpl_cu_cccd')?.value,
            NGAY_SINH: document.getElementById('ddpl_cu_ngay_sinh')?.value,
            GIOI_TINH: document.getElementById('ddpl_cu_gioi_tinh')?.value,
            DIA_CHI: document.getElementById('ddpl_cu_dia_chi')?.value,
        },
        ddplMoi: {
            HO_TEN: document.getElementById('ddpl_moi_ho_ten')?.value,
            CCCD: document.getElementById('ddpl_moi_cccd')?.value,
            NGAY_SINH: document.getElementById('ddpl_moi_ngay_sinh')?.value,
            GIOI_TINH: document.getElementById('ddpl_moi_gioi_tinh')?.value,
            DIA_CHI: document.getElementById('ddpl_moi_dia_chi')?.value,
        },
        members: window.cd1tv2tvState.members
    };
    
    return true;
};
