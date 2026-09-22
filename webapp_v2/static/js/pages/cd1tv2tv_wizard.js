// Specialized Dynamic Wizard for Chuyển đổi loại hình 1TV sang 2 TV

function getInitialCD1TV2TVState() {
    return {
        step: 1,
        hinhThucCN: 'mot_phan', // 'mot_phan' (CSH giữ lại vốn làm TV1) hoặc 'toan_bo' (CSH thoái 100% vốn)
        oldCompany: {
            mst: '',
            name: '',
            address: '',
            von: ''
        },
        csh: {
            HO_TEN: '',
            CCCD: '',
            NGAY_SINH: '',
            GIOI_TINH: 'Nam',
            DIA_CHI: ''
        },
        ddplCu: {
            HO_TEN: '',
            CCCD: '',
            NGAY_SINH: '',
            GIOI_TINH: 'Nam',
            DIA_CHI: ''
        },
        newCompany: {
            nameVn: '',
            nameEn: '',
            nameShort: '',
            phone: '',
            email: ''
        },
        ddplMoi: {
            HO_TEN: '',
            CCCD: '',
            NGAY_SINH: '',
            GIOI_TINH: 'Nam',
            DIA_CHI: ''
        },
        members: [
            { id: 1, ho_ten: '', cccd: '', ngay_sinh: '', dia_chi: '', gioi_tinh: 'Nam', von: '', ty_le: '', nhan_cn: '' },
            { id: 2, ho_ten: '', cccd: '', ngay_sinh: '', dia_chi: '', gioi_tinh: 'Nam', von: '', ty_le: '', nhan_cn: '' }
        ]
    };
}

window.cd1tv2tvState = window.cd1tv2tvState || getInitialCD1TV2TVState();

function cdRenderInput(label, id, val, placeholder = '', oninput = '') {
    return `
        <div>
            <label class="text-sm text-muted mb-1 block">${label}</label>
            <input type="text" id="${id}" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${val || ''}" placeholder="${placeholder}" oninput="${oninput}">
        </div>
    `;
}

window.cdSetHinhThucCN = function(mode) {
    window.cdSyncFromDOM();
    const s = window.cd1tv2tvState;
    const oldMode = s.hinhThucCN || 'mot_phan';
    s.hinhThucCN = mode;

    if (mode === 'toan_bo' && oldMode !== 'toan_bo') {
        // Nếu Thành viên 1 đang mang dữ liệu của CSH cũ thì reset để người dùng nhập Người mua mới 1
        if (s.members[0] && s.csh.CCCD && (s.members[0].cccd === s.csh.CCCD || s.members[0].ho_ten === s.csh.HO_TEN)) {
            s.members[0].ho_ten = '';
            s.members[0].cccd = '';
            s.members[0].ngay_sinh = '';
            s.members[0].gioi_tinh = 'Nam';
            s.members[0].dia_chi = '';
        }
    } else if (mode === 'mot_phan' && oldMode !== 'mot_phan') {
        // Nếu chuyển lại một phần, tự động điền CSH vào TV1 nếu TV1 đang trống
        if (s.members[0] && !s.members[0].ho_ten && s.csh.HO_TEN) {
            s.members[0].ho_ten = s.csh.HO_TEN;
            s.members[0].cccd = s.csh.CCCD;
            s.members[0].ngay_sinh = s.csh.NGAY_SINH;
            s.members[0].gioi_tinh = s.csh.GIOI_TINH;
            s.members[0].dia_chi = s.csh.DIA_CHI;
        }
    }

    const c2 = document.getElementById('cd-step2-container');
    if (c2) c2.innerHTML = renderCDStep2();
};

window.cdCopyCSHToMember1 = function() {
    window.cdSyncFromDOM();
    const s = window.cd1tv2tvState;
    if (!s.members[0]) return;
    s.members[0].ho_ten = s.csh.HO_TEN || '';
    s.members[0].cccd = s.csh.CCCD || '';
    s.members[0].ngay_sinh = s.csh.NGAY_SINH || '';
    s.members[0].gioi_tinh = s.csh.GIOI_TINH || 'Nam';
    s.members[0].dia_chi = s.csh.DIA_CHI || '';

    const elH = document.getElementById('cd_tv_0_ho_ten'); if (elH) elH.value = s.members[0].ho_ten;
    const elC = document.getElementById('cd_tv_0_cccd'); if (elC) elC.value = s.members[0].cccd;
    const elN = document.getElementById('cd_tv_0_ngay_sinh'); if (elN) elN.value = s.members[0].ngay_sinh;
    const elG = document.getElementById('cd_tv_0_gioi_tinh'); if (elG) elG.value = s.members[0].gioi_tinh;
    const elD = document.getElementById('cd_tv_0_dia_chi'); if (elD) elD.value = s.members[0].dia_chi;
};

window.cdCopyMemberToDDPL = function(memberIdx) {
    window.cdSyncFromDOM();
    const s = window.cd1tv2tvState;
    const m = s.members[memberIdx];
    if (!m) return;
    s.ddplMoi.HO_TEN = m.ho_ten || '';
    s.ddplMoi.CCCD = m.cccd || '';
    s.ddplMoi.NGAY_SINH = m.ngay_sinh || '';
    s.ddplMoi.GIOI_TINH = m.gioi_tinh || 'Nam';
    s.ddplMoi.DIA_CHI = m.dia_chi || '';

    const elH = document.getElementById('ddpl_moi_ho_ten'); if (elH) elH.value = s.ddplMoi.HO_TEN;
    const elC = document.getElementById('ddpl_moi_cccd'); if (elC) elC.value = s.ddplMoi.CCCD;
    const elN = document.getElementById('ddpl_moi_ngay_sinh'); if (elN) elN.value = s.ddplMoi.NGAY_SINH;
    const elG = document.getElementById('ddpl_moi_gioi_tinh'); if (elG) elG.value = s.ddplMoi.GIOI_TINH;
    const elD = document.getElementById('ddpl_moi_dia_chi'); if (elD) elD.value = s.ddplMoi.DIA_CHI;
};

window.cdCopyCSHToDDPL = function() {
    window.cdSyncFromDOM();
    const s = window.cd1tv2tvState;
    s.ddplMoi.HO_TEN = s.csh.HO_TEN || '';
    s.ddplMoi.CCCD = s.csh.CCCD || '';
    s.ddplMoi.NGAY_SINH = s.csh.NGAY_SINH || '';
    s.ddplMoi.GIOI_TINH = s.csh.GIOI_TINH || 'Nam';
    s.ddplMoi.DIA_CHI = s.csh.DIA_CHI || '';

    const elH = document.getElementById('ddpl_moi_ho_ten'); if (elH) elH.value = s.ddplMoi.HO_TEN;
    const elC = document.getElementById('ddpl_moi_cccd'); if (elC) elC.value = s.ddplMoi.CCCD;
    const elN = document.getElementById('ddpl_moi_ngay_sinh'); if (elN) elN.value = s.ddplMoi.NGAY_SINH;
    const elG = document.getElementById('ddpl_moi_gioi_tinh'); if (elG) elG.value = s.ddplMoi.GIOI_TINH;
    const elD = document.getElementById('ddpl_moi_dia_chi'); if (elD) elD.value = s.ddplMoi.DIA_CHI;
};

window.renderCD1TV2TVWizard = function(container) {
    if (!window.cd1tv2tvState) {
        window.cd1tv2tvState = getInitialCD1TV2TVState();
    }
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
            const getVal = (id) => document.getElementById(id)?.value || '';
            const setVal = (id, v) => {
                const el = document.getElementById(id);
                if (el) el.value = v;
            };
            setVal('ddpl_cu_ho_ten', getVal('csh_ho_ten'));
            setVal('ddpl_cu_cccd', getVal('csh_cccd'));
            setVal('ddpl_cu_ngay_sinh', getVal('csh_ngay_sinh'));
            setVal('ddpl_cu_gioi_tinh', getVal('csh_gioi_tinh'));
            setVal('ddpl_cu_dia_chi', getVal('csh_dia_chi'));
        }
    });
};

window.cdSyncFromDOM = function() {
    if (!window.cd1tv2tvState) {
        window.cd1tv2tvState = getInitialCD1TV2TVState();
    }
    const s = window.cd1tv2tvState;
    const getVal = (id) => {
        const el = document.getElementById(id);
        return el ? el.value : null;
    };

    // Old company
    let v = getVal('cd_mst'); if (v !== null) s.oldCompany.mst = v;
    v = getVal('cd_ten_cty'); if (v !== null) s.oldCompany.name = v;
    v = getVal('cd_dia_chi_cty'); if (v !== null) s.oldCompany.address = v;
    v = getVal('cd_von_cu'); if (v !== null) s.oldCompany.von = v;

    // CSH
    v = getVal('csh_ho_ten'); if (v !== null) s.csh.HO_TEN = v;
    v = getVal('csh_cccd'); if (v !== null) s.csh.CCCD = v;
    v = getVal('csh_ngay_sinh'); if (v !== null) s.csh.NGAY_SINH = v;
    v = getVal('csh_gioi_tinh'); if (v !== null) s.csh.GIOI_TINH = v;
    v = getVal('csh_dia_chi'); if (v !== null) s.csh.DIA_CHI = v;

    // DDPL Cu
    v = getVal('ddpl_cu_ho_ten'); if (v !== null) s.ddplCu.HO_TEN = v;
    v = getVal('ddpl_cu_cccd'); if (v !== null) s.ddplCu.CCCD = v;
    v = getVal('ddpl_cu_ngay_sinh'); if (v !== null) s.ddplCu.NGAY_SINH = v;
    v = getVal('ddpl_cu_gioi_tinh'); if (v !== null) s.ddplCu.GIOI_TINH = v;
    v = getVal('ddpl_cu_dia_chi'); if (v !== null) s.ddplCu.DIA_CHI = v;

    // New company
    v = getVal('cd_ten_cty_moi'); if (v !== null) s.newCompany.nameVn = v;
    v = getVal('cd_ten_en'); if (v !== null) s.newCompany.nameEn = v;
    v = getVal('cd_ten_vt'); if (v !== null) s.newCompany.nameShort = v;
    v = getVal('cd_sdt'); if (v !== null) s.newCompany.phone = v;
    v = getVal('cd_email'); if (v !== null) s.newCompany.email = v;

    // DDPL Moi
    v = getVal('ddpl_moi_ho_ten'); if (v !== null) s.ddplMoi.HO_TEN = v;
    v = getVal('ddpl_moi_cccd'); if (v !== null) s.ddplMoi.CCCD = v;
    v = getVal('ddpl_moi_ngay_sinh'); if (v !== null) s.ddplMoi.NGAY_SINH = v;
    v = getVal('ddpl_moi_gioi_tinh'); if (v !== null) s.ddplMoi.GIOI_TINH = v;
    v = getVal('ddpl_moi_dia_chi'); if (v !== null) s.ddplMoi.DIA_CHI = v;

    // Members
    s.members.forEach((m, idx) => {
        let val = getVal(`cd_tv_${idx}_ho_ten`); if (val !== null) m.ho_ten = val;
        val = getVal(`cd_tv_${idx}_cccd`); if (val !== null) m.cccd = val;
        val = getVal(`cd_tv_${idx}_ngay_sinh`); if (val !== null) m.ngay_sinh = val;
        val = getVal(`cd_tv_${idx}_gioi_tinh`); if (val !== null) m.gioi_tinh = val;
        val = getVal(`cd_tv_${idx}_dia_chi`); if (val !== null) m.dia_chi = val;
        val = getVal(`cd_tv_${idx}_von`); if (val !== null) m.von = val;
        val = getVal(`cd_tv_${idx}_ty_le`); if (val !== null) m.ty_le = val;
        val = getVal(`cd_tv_${idx}_nhan_cn`); if (val !== null) m.nhan_cn = val;
    });
};

window.cd1tv2tvGotoStep = function(step) {
    window.cdSyncFromDOM();
    window.cd1tv2tvState.step = step;

    const s1 = document.getElementById('cd-step-1');
    const s2 = document.getElementById('cd-step-2');
    const s3 = document.getElementById('cd-step-3');
    if (s1) s1.className = step === 1 ? 'font-bold text-accent' : 'text-muted';
    if (s2) s2.className = step === 2 ? 'font-bold text-accent' : 'text-muted';
    if (s3) s3.className = step === 3 ? 'font-bold text-accent' : 'text-muted';

    const c1 = document.getElementById('cd-step1-container');
    const c2 = document.getElementById('cd-step2-container');
    const c3 = document.getElementById('cd-step3-container');

    if (c1) c1.style.display = step === 1 ? 'block' : 'none';
    if (c2) {
        c2.style.display = step === 2 ? 'block' : 'none';
        if (step === 2) c2.innerHTML = renderCDStep2();
    }

    if (step === 3) {
        if (c3) {
            c3.innerHTML = renderCDStep3();
            c3.style.display = 'block';
        }
    } else {
        if (c3) c3.style.display = 'none';
    }

    window.collectCD1TV2TVData();
};

function renderCDStep1() {
    const s = window.cd1tv2tvState;
    return `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;">
            <h3 class="font-bold text-info mb-4"><i class="fa-solid fa-building"></i> Công ty 1TV cũ</h3>
            <div class="grid-2" style="gap: var(--space-4);">
                <div>
                    <label class="text-sm text-muted mb-1 block">Mã số thuế</label>
                    <input type="text" id="cd_mst" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" placeholder="Nhập MST (VD: 0109942993)" value="${s.oldCompany.mst || ''}" onkeydown="if(event.key==='Enter'){event.preventDefault();window.lookupCDMst(event);}">
                    <div class="mt-2 flex items-center gap-2">
                        <button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0;" onclick="window.lookupCDMst(event)"><i class="fa-solid fa-magnifying-glass"></i> Tra cứu</button>
                        <span id="cd_mst_status" class="text-xs"></span>
                    </div>
                </div>
                ${cdRenderInput('Tên công ty tiếng Việt', 'cd_ten_cty', s.oldCompany.name, 'Tự động điền')}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ trụ sở chính</label>
                    <input type="text" id="cd_dia_chi_cty" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" placeholder="Tự động điền" value="${s.oldCompany.address || ''}">
                </div>
                ${cdRenderInput('Vốn điều lệ cũ (VNĐ)', 'cd_von_cu', s.oldCompany.von, 'VD: 1.000.000.000', 'formatCurrencyInput(this)')}
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;">
            <h3 class="font-bold text-warning mb-4"><i class="fa-solid fa-user-tag"></i> Chủ sở hữu cũ (Bên bán vốn)</h3>
            <div class="grid-2" style="gap: var(--space-4);">
                <div class="col-span-2">
                    <button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0; color: var(--success); border-color: var(--success);" onclick="triggerInlineOCR_CD1TV('csh', event)"><i class="fa-solid fa-id-card"></i> Quét VNeID/CCCD</button>
                </div>
                ${cdRenderInput('Họ và tên', 'csh_ho_ten', s.csh.HO_TEN)}
                ${cdRenderInput('Số CCCD', 'csh_cccd', s.csh.CCCD)}
                ${cdRenderInput('Ngày sinh', 'csh_ngay_sinh', s.csh.NGAY_SINH)}
                ${cdRenderInput('Giới tính', 'csh_gioi_tinh', s.csh.GIOI_TINH)}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ thường trú</label>
                    <input type="text" id="csh_dia_chi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${s.csh.DIA_CHI || ''}">
                </div>
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;">
            <div class="flex justify-between items-center mb-4">
                <h3 class="font-bold text-muted"><i class="fa-solid fa-user-shield"></i> Đại diện pháp luật cũ (nếu khác CSH)</h3>
                <label class="flex items-center gap-2 cursor-pointer text-sm">
                    <input type="checkbox" id="cd-csh-is-ddpl" checked> Kiêm ĐDPL cũ
                </label>
            </div>
            <div class="grid-2" style="gap: var(--space-4);">
                <div class="col-span-2">
                    <button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0; color: var(--success); border-color: var(--success);" onclick="triggerInlineOCR_CD1TV('ddpl_cu', event)"><i class="fa-solid fa-id-card"></i> Quét VNeID/CCCD</button>
                </div>
                ${cdRenderInput('Họ và tên', 'ddpl_cu_ho_ten', s.ddplCu.HO_TEN)}
                ${cdRenderInput('Số CCCD', 'ddpl_cu_cccd', s.ddplCu.CCCD)}
                ${cdRenderInput('Ngày sinh', 'ddpl_cu_ngay_sinh', s.ddplCu.NGAY_SINH)}
                ${cdRenderInput('Giới tính', 'ddpl_cu_gioi_tinh', s.ddplCu.GIOI_TINH)}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ thường trú</label>
                    <input type="text" id="ddpl_cu_dia_chi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${s.ddplCu.DIA_CHI || ''}">
                </div>
            </div>
        </div>
    `;
}

function renderCDStep2() {
    const s = window.cd1tv2tvState;
    const isToanBo = s.hinhThucCN === 'toan_bo';
    return `
        <!-- HÌNH THỨC CHUYỂN NHƯỢNG CỦA CSH -->
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--accent); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1.25rem;">
            <h3 class="font-bold text-accent mb-2"><i class="fa-solid fa-arrows-split-up-and-left"></i> Hình thức chuyển nhượng của Chủ sở hữu cũ</h3>
            <div class="grid-2" style="gap: 1rem;">
                <label class="p-3 rounded border cursor-pointer flex items-start gap-3 transition-all" style="border-color: ${!isToanBo ? 'var(--accent)' : 'var(--border-glass)'}; background: ${!isToanBo ? 'rgba(59, 130, 246, 0.1)' : 'transparent'};">
                    <input type="radio" name="cd_hinh_thuc_cn" value="mot_phan" ${!isToanBo ? 'checked' : ''} onchange="window.cdSetHinhThucCN('mot_phan')" style="margin-top: 3px;">
                    <div>
                        <div class="font-bold text-white">Chuyển nhượng MỘT PHẦN vốn</div>
                        <div class="text-xs text-muted mt-1">Chủ sở hữu cũ giữ lại một phần vốn và tiếp tục là <b>Thành viên #1</b> trong công ty mới.</div>
                    </div>
                </label>
                <label class="p-3 rounded border cursor-pointer flex items-start gap-3 transition-all" style="border-color: ${isToanBo ? 'var(--warning)' : 'var(--border-glass)'}; background: ${isToanBo ? 'rgba(234, 179, 8, 0.1)' : 'transparent'};">
                    <input type="radio" name="cd_hinh_thuc_cn" value="toan_bo" ${isToanBo ? 'checked' : ''} onchange="window.cdSetHinhThucCN('toan_bo')" style="margin-top: 3px;">
                    <div>
                        <div class="font-bold text-warning">Chuyển nhượng TOÀN BỘ vốn (Thoái vốn 100%)</div>
                        <div class="text-xs text-muted mt-1">Chủ sở hữu cũ chuyển hết vốn cho các thành viên mới và <b>rút khỏi công ty</b> (không còn là thành viên).</div>
                    </div>
                </label>
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;">
            <h3 class="font-bold text-info mb-4"><i class="fa-solid fa-building-circle-arrow-right"></i> Công ty 2TV mới</h3>
            <div class="grid-2" style="gap: var(--space-4);">
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Tên công ty tiếng Việt mới (nếu có đổi)</label>
                    <input type="text" id="cd_ten_cty_moi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" placeholder="VD: CÔNG TY TNHH HAI THÀNH VIÊN..." value="${s.newCompany.nameVn || ''}">
                </div>
                ${cdRenderInput('Tên tiếng Anh', 'cd_ten_en', s.newCompany.nameEn)}
                ${cdRenderInput('Tên viết tắt', 'cd_ten_vt', s.newCompany.nameShort)}
                ${cdRenderInput('Số điện thoại', 'cd_sdt', s.newCompany.phone)}
                ${cdRenderInput('Email', 'cd_email', s.newCompany.email)}
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem; border-color: var(--accent);">
            <div class="flex justify-between items-center mb-3">
                <h3 class="font-bold text-accent"><i class="fa-solid fa-user-tie"></i> Đại diện pháp luật mới</h3>
            </div>
            <div class="grid-2" style="gap: var(--space-4);">
                <div class="col-span-2 flex gap-2 flex-wrap items-center">
                    <button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0; color: var(--success); border-color: var(--success);" onclick="triggerInlineOCR_CD1TV('ddpl_moi', event)"><i class="fa-solid fa-id-card"></i> Quét VNeID/CCCD</button>
                    <button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0;" onclick="window.cdCopyMemberToDDPL(0)"><i class="fa-solid fa-user-check"></i> Lấy theo TV #1</button>
                    <button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0;" onclick="window.cdCopyMemberToDDPL(1)"><i class="fa-solid fa-user-check"></i> Lấy theo TV #2</button>
                    ${!isToanBo ? '<button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0;" onclick="window.cdCopyCSHToDDPL()"><i class="fa-solid fa-user-tie"></i> Giữ nguyên CSH cũ</button>' : ''}
                </div>
                ${cdRenderInput('Họ và tên', 'ddpl_moi_ho_ten', s.ddplMoi.HO_TEN)}
                ${cdRenderInput('Số CCCD', 'ddpl_moi_cccd', s.ddplMoi.CCCD)}
                ${cdRenderInput('Ngày sinh', 'ddpl_moi_ngay_sinh', s.ddplMoi.NGAY_SINH)}
                ${cdRenderInput('Giới tính', 'ddpl_moi_gioi_tinh', s.ddplMoi.GIOI_TINH)}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ thường trú</label>
                    <input type="text" id="ddpl_moi_dia_chi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${s.ddplMoi.DIA_CHI || ''}">
                </div>
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;">
            <div class="flex justify-between items-center mb-4">
                <div>
                    <h3 class="font-bold text-success"><i class="fa-solid fa-users"></i> Danh sách thành viên công ty mới</h3>
                    <p class="text-xs text-muted">${isToanBo ? 'Chủ sở hữu cũ thoái 100% vốn. Vui lòng nhập tối thiểu 2 thành viên mới nhận chuyển nhượng vốn để thành lập công ty 2TV trở lên.' : 'Thành viên 1 là Chủ sở hữu cũ (tiếp tục giữ lại vốn). Thêm thành viên mới nhận chuyển nhượng để công ty đạt từ 2 TV trở lên.'}</p>
                </div>
                <button type="button" class="btn btn-sm btn-primary" onclick="cdAddMember()"><i class="fa-solid fa-plus"></i> Thêm thành viên</button>
            </div>
            
            <div id="cd-members-list">
                ${s.members.map((m, idx) => renderCDMemberCard(idx)).join('')}
            </div>
        </div>
    `;
}

function renderCDMemberCard(idx) {
    const s = window.cd1tv2tvState;
    const m = s.members[idx];
    const isToanBo = s.hinhThucCN === 'toan_bo';
    const isFirst = idx === 0;

    let headerTitle = '';
    let headerAction = '';

    if (isFirst) {
        if (isToanBo) {
            headerTitle = `<span class="font-bold text-sm text-success">Thành viên mới #1 (Bên nhận chuyển nhượng vốn 1)</span>`;
            headerAction = `<span class="badge badge-success" style="font-size: 11px; padding: 2px 6px;">Thành viên mới</span>`;
        } else {
            headerTitle = `<span class="font-bold text-sm text-warning">Thành viên #1: ${m.ho_ten || 'Chủ sở hữu cũ'} (Giữ lại vốn)</span>`;
            headerAction = `
                <span class="badge badge-warning" style="font-size: 11px; padding: 2px 6px; margin-right: 6px;">CSH giữ lại vốn</span>
                <button type="button" class="btn btn-outline" style="font-size: 10px; padding: 2px 6px; height: auto; min-height: 0;" onclick="window.cdCopyCSHToMember1()"><i class="fa-solid fa-arrows-rotate"></i> Đồng bộ CSH</button>
            `;
        }
    } else {
        const numLabel = isToanBo ? idx + 1 : idx;
        headerTitle = `<span class="font-bold text-sm text-info">Thành viên mới #${idx + 1} (Bên nhận chuyển nhượng vốn ${numLabel})</span>`;
        headerAction = `<button type="button" class="btn btn-sm btn-danger" style="padding: 2px 8px; font-size: 11px; height: auto;" onclick="cdRemoveMember(${idx})"><i class="fa-solid fa-trash"></i> Xóa</button>`;
    }

    return `
        <div class="p-4 mb-4 rounded border border-gray-700 bg-gray-900 bg-opacity-40" style="background: rgba(255,255,255,0.02); margin-bottom: 1rem;">
            <div class="flex justify-between items-center mb-3">
                <div>${headerTitle}</div>
                <div class="flex items-center">${headerAction}</div>
            </div>
            <div class="grid-2" style="gap: var(--space-3);">
                <div class="col-span-2">
                    <button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0; color: var(--success); border-color: var(--success);" onclick="triggerInlineOCR_CD1TV('cd_tv_${idx}', event)"><i class="fa-solid fa-id-card"></i> Quét VNeID/CCCD</button>
                </div>
                ${cdRenderInput('Họ và tên', `cd_tv_${idx}_ho_ten`, m.ho_ten)}
                ${cdRenderInput('Số CCCD', `cd_tv_${idx}_cccd`, m.cccd)}
                ${cdRenderInput('Ngày sinh', `cd_tv_${idx}_ngay_sinh`, m.ngay_sinh)}
                ${cdRenderInput('Giới tính', `cd_tv_${idx}_gioi_tinh`, m.gioi_tinh)}
                <div class="col-span-2">
                    <label class="text-sm text-muted mb-1 block">Địa chỉ thường trú</label>
                    <input type="text" id="cd_tv_${idx}_dia_chi" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${m.dia_chi || ''}">
                </div>
                ${cdRenderInput('Vốn góp mới (VNĐ)', `cd_tv_${idx}_von`, m.von, 'VD: 500.000.000', 'formatCurrencyInput(this)')}
                ${cdRenderInput('Tỷ lệ vốn (%)', `cd_tv_${idx}_ty_le`, m.ty_le, 'VD: 50')}
            </div>
        </div>
    `;
}

window.cdAddMember = function() {
    window.cdSyncFromDOM();
    window.cd1tv2tvState.members.push({
        id: window.cd1tv2tvState.members.length + 1,
        ho_ten: '',
        cccd: '',
        ngay_sinh: '',
        dia_chi: '',
        gioi_tinh: 'Nam',
        von: '',
        ty_le: '',
        nhan_cn: ''
    });
    const el = document.getElementById('cd-members-list');
    if (el) el.innerHTML = window.cd1tv2tvState.members.map((m, idx) => renderCDMemberCard(idx)).join('');
};

window.cdRemoveMember = function(idx) {
    window.cdSyncFromDOM();
    if (window.cd1tv2tvState.members.length <= 2) {
        alert('Công ty TNHH 2 thành viên trở lên phải có tối thiểu 2 thành viên!');
        return;
    }
    window.cd1tv2tvState.members.splice(idx, 1);
    const el = document.getElementById('cd-members-list');
    if (el) el.innerHTML = window.cd1tv2tvState.members.map((m, i) => renderCDMemberCard(i)).join('');
};

function renderCDStep3() {
    window.cdSyncFromDOM();
    const s = window.cd1tv2tvState;
    const isToanBo = s.hinhThucCN === 'toan_bo';
    const cshName = s.csh.HO_TEN || 'Chủ sở hữu cũ';
    const vonCuClean = (s.oldCompany.von || '').toString().replace(/[^0-9]/g, '');
    const vonCuNum = parseInt(vonCuClean, 10) || 0;

    let totalCN = 0;
    s.members.forEach((m, idx) => {
        if (isToanBo || idx > 0) {
            if (m.nhan_cn === undefined || m.nhan_cn === null || m.nhan_cn === '') {
                m.nhan_cn = m.von || '';
            }
            const cleanVal = (m.nhan_cn || '').toString().replace(/[^0-9]/g, '');
            totalCN += (parseInt(cleanVal, 10) || 0);
        } else {
            m.nhan_cn = ''; // CSH giữ lại vốn
        }
    });

    const isMatch = vonCuNum > 0 && totalCN === vonCuNum;
    const diff = vonCuNum - totalCN;

    let html = `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--warning); border-radius: var(--radius-lg); padding: var(--space-4); margin-bottom: 1rem;">
            <div class="flex justify-between items-start mb-2">
                <h3 class="font-bold text-warning"><i class="fa-solid fa-handshake"></i> Hợp đồng chuyển nhượng vốn</h3>
                <span class="badge ${isToanBo ? 'badge-warning' : 'badge-info'}" style="font-size: 11px; padding: 2px 8px;">
                    ${isToanBo ? 'Thoái vốn 100%' : 'Chuyển nhượng 1 phần'}
                </span>
            </div>
            <p class="text-sm text-muted mb-4">
                ${isToanBo ? 
                    `Chủ sở hữu cũ (<b>${cshName}</b>) là <b>Bên Bán (Bên A)</b> chuyển nhượng <b>toàn bộ 100% vốn</b> cho tất cả các thành viên mới bên dưới. Mỗi thành viên sẽ được tạo <b>1 Hợp đồng chuyển nhượng + Biên bản thanh lý riêng biệt</b>.` : 
                    `Chủ sở hữu cũ (<b>${cshName}</b>) là <b>Bên Bán (Bên A)</b> chuyển nhượng <b>một phần vốn</b> cho các thành viên bên dưới. Thành viên #1 (CSH cũ) tiếp tục giữ lại vốn.`}
            </p>

            <!-- TỔNG KẾT ĐỐI CHIẾU VỐN -->
            <div class="p-3 rounded mb-4" style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-glass);">
                <div class="flex justify-between items-center text-xs">
                    <div>
                        <span class="text-muted">Vốn cũ CSH:</span> <b class="text-white">${vonCuNum ? vonCuNum.toLocaleString('vi-VN') : '0'} VNĐ</b>
                        <span class="mx-2 text-muted">|</span>
                        <span class="text-muted">Tổng vốn nhận CN:</span> <b class="${isMatch ? 'text-success' : 'text-warning'}">${totalCN ? totalCN.toLocaleString('vi-VN') : '0'} VNĐ</b>
                    </div>
                    <div>
                        ${isToanBo ? (isMatch ? 
                            '<span class="text-success font-bold"><i class="fa-solid fa-check-circle"></i> Khớp 100% vốn cũ</span>' : 
                            `<span class="text-danger font-bold"><i class="fa-solid fa-triangle-exclamation"></i> Lệch ${Math.abs(diff).toLocaleString('vi-VN')} VNĐ</span>`) : 
                            '<span class="text-info"><i class="fa-solid fa-info-circle"></i> Đã trừ phần CSH giữ lại</span>'}
                    </div>
                </div>
            </div>
    `;

    s.members.forEach((m, idx) => {
        const isFirst = idx === 0;

        if (!isToanBo && isFirst) {
            html += `
                <div class="p-3 rounded mb-3 flex items-center justify-between" style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);">
                    <div style="flex: 1;">
                        <div class="font-bold text-warning">Thành viên #1: ${m.ho_ten || 'Chủ sở hữu cũ'} (CSH giữ lại vốn)</div>
                        <div class="text-xs text-muted mt-1">CCCD: ${m.cccd || '---'} | Vốn giữ lại: ${m.von || '0'} VNĐ (${m.ty_le || '0'}%)</div>
                        <div class="text-xs text-muted mt-1"><i>Chủ sở hữu cũ là Bên Bán vốn. Phần vốn này tự giữ lại, không lập Hợp đồng chuyển nhượng.</i></div>
                    </div>
                    <div class="text-right">
                        <span class="badge badge-outline" style="font-size: 11px; opacity: 0.7;">Không tạo HĐ</span>
                    </div>
                </div>
            `;
        } else {
            const numLabel = isToanBo ? idx + 1 : idx;
            html += `
                <div class="p-3 rounded mb-3 flex items-center justify-between" style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-glass);">
                    <div style="flex: 1;">
                        <div class="font-bold text-success">Thành viên mới #${idx + 1}: ${m.ho_ten || `Bên nhận CN ${numLabel}`}</div>
                        <div class="text-xs text-muted mt-1">CCCD: ${m.cccd || '---'} | Vốn góp mới: ${m.von || '0'} VNĐ (${m.ty_le || '0'}%)</div>
                        <div class="text-xs text-info mt-1">Sẽ tạo: 1 Hợp đồng chuyển nhượng + 1 Biên bản thanh lý (từ ${cshName})</div>
                    </div>
                    <div class="text-right" style="min-width: 220px;">
                        <label class="text-xs text-muted block mb-1">Số vốn nhận CN từ CSH (VNĐ)</label>
                        <input type="text" id="cd_tv_${idx}_nhan_cn" class="input input-sm" style="background: transparent; border: 1px solid var(--warning); color: white; padding: 6px 10px; border-radius: 4px; width: 180px; text-align: right;" placeholder="VD: 500.000.000" value="${m.nhan_cn || ''}" oninput="formatCurrencyInput(this); cdSaveCN(${idx}, this.value)">
                    </div>
                </div>
            `;
        }
    });

    html += `</div>`;
    return html;
}

window.cdSaveCN = function(idx, val) {
    if (window.cd1tv2tvState.members[idx]) {
        window.cd1tv2tvState.members[idx].nhan_cn = val;
    }
};

window.lookupCDMst = async function(event) {
    if(event) event.preventDefault();
    const btn = event && event.currentTarget ? event.currentTarget : document.querySelector('#cd_mst ~ div button');
    const oldHTML = btn ? btn.innerHTML : '';
    const mstInput = document.getElementById('cd_mst');
    const mst = mstInput?.value?.trim();
    const statusEl = document.getElementById('cd_mst_status');

    if(!mst) {
        alert('Vui lòng nhập Mã số thuế trước khi tra cứu.');
        return;
    }

    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang tra cứu...';
        btn.disabled = true;
    }
    if (statusEl) {
        statusEl.innerHTML = '<span class="text-muted"><i class="fa-solid fa-spinner fa-spin"></i> Đang kết nối CSDL Thuế...</span>';
    }

    try {
        const res = await fetch(`/api/mst/${encodeURIComponent(mst)}`);
        const result = await res.json();
        if(result.success && result.data && (result.data.name || result.data.ten_cong_ty)) {
            const c = result.data;
            const ten = c.name || c.ten_cong_ty || '';
            const diaChi = c.address || c.dia_chi || '';

            const elTen = document.getElementById('cd_ten_cty');
            const elDiaChi = document.getElementById('cd_dia_chi_cty');
            if (elTen) {
                elTen.value = ten;
                elTen.style.borderColor = 'var(--accent-green)';
            }
            if (elDiaChi) {
                elDiaChi.value = diaChi;
                elDiaChi.style.borderColor = 'var(--accent-green)';
            }
            if (statusEl) {
                statusEl.innerHTML = `<span class="text-success"><i class="fa-solid fa-check"></i> Đã tìm thấy: <b>${ten}</b></span>`;
            }
            window.cdSyncFromDOM();
        } else {
            if (statusEl) {
                statusEl.innerHTML = '<span class="text-danger"><i class="fa-solid fa-triangle-exclamation"></i> Không tìm thấy</span>';
            }
            alert('Không tìm thấy thông tin doanh nghiệp với mã số thuế này trên Cổng Thuế.');
        }
    } catch(e) {
        console.error('MST Lookup error:', e);
        if (statusEl) {
            statusEl.innerHTML = '<span class="text-danger">Lỗi kết nối</span>';
        }
        alert('Lỗi khi tra cứu mã số thuế: ' + e.message);
    } finally {
        if (btn) {
            btn.innerHTML = oldHTML;
            btn.disabled = false;
        }
    }
};

window.triggerInlineOCR_CD1TV = function(prefix, event) {
    if(event) event.preventDefault();
    const btn = event ? event.currentTarget : null;
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';

    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if(!file) return;

        const oldHTML = btn ? btn.innerHTML : '';
        if (btn) {
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang đọc...';
            btn.disabled = true;
        }

        const formData = new FormData();
        formData.append('image', file);
        formData.append('file', file);

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

            window.cdSyncFromDOM();

            if (btn) {
                btn.innerHTML = oldHTML;
                btn.disabled = false;
            }
        } catch(err) {
            console.error(err);
            alert('Lỗi trích xuất: ' + err.message);
            if (btn) {
                btn.innerHTML = oldHTML;
                btn.disabled = false;
            }
        }
    };
    fileInput.click();
};

window.collectCD1TV2TVData = function() {
    window.cdSyncFromDOM();
    const s = window.cd1tv2tvState;
    const isToanBo = s.hinhThucCN === 'toan_bo';

    // Build form data
    window.wizardState.formData = {
        TEN_CONG_TY_VN_CU: s.oldCompany.name || '',
        MA_SO_THUE: s.oldCompany.mst || '',
        DIA_CHI_CTY_CU: s.oldCompany.address || '',
        VON_CU: s.oldCompany.von || '',

        TEN_CONG_TY_VN: s.newCompany.nameVn || s.oldCompany.name || '',
        TEN_CONG_TY_EN: s.newCompany.nameEn || '',
        TEN_CONG_TY_VIET_TAT: s.newCompany.nameShort || '',
        SDT_CONG_TY: s.newCompany.phone || '',
        EMAIL_CONG_TY: s.newCompany.email || '',

        HINH_THUC_CN: s.hinhThucCN || 'mot_phan'
    };

    // Auto sync CSH with Member 1 ONLY when mot_phan and Member 1 ho_ten is empty
    if (!isToanBo && s.members.length > 0 && !s.members[0].ho_ten && s.csh.HO_TEN) {
        s.members[0].ho_ten = s.csh.HO_TEN;
        s.members[0].cccd = s.csh.CCCD;
        s.members[0].ngay_sinh = s.csh.NGAY_SINH;
        s.members[0].gioi_tinh = s.csh.GIOI_TINH;
        s.members[0].dia_chi = s.csh.DIA_CHI;
    }

    // Build contracts based on transactions
    const contracts = [];
    s.members.forEach((m, idx) => {
        // Nếu chuyển nhượng 1 phần, Thành viên 1 giữ lại vốn, không nhận chuyển nhượng
        if (!isToanBo && idx === 0) return;

        const cleanVal = (m.nhan_cn || '').toString().replace(/[^0-9]/g, '');
        const valNum = parseInt(cleanVal, 10) || 0;
        const vonNum = parseInt((m.von || '').toString().replace(/[^0-9]/g, ''), 10) || 0;

        const amt = valNum > 0 ? cleanVal : (vonNum > 0 ? (m.von || '').toString() : '');
        if (amt && parseInt(amt.replace(/[^0-9]/g, ''), 10) > 0) {
            contracts.push({
                ben_a: {
                    ho_ten: s.csh.HO_TEN || '',
                    so_cccd: s.csh.CCCD || '',
                    ngay_sinh: s.csh.NGAY_SINH || '',
                    gioi_tinh: s.csh.GIOI_TINH || 'Nam',
                    dia_chi_day_du: s.csh.DIA_CHI || ''
                },
                ben_b: {
                    ho_ten: m.ho_ten || '',
                    so_cccd: m.cccd || '',
                    ngay_sinh: m.ngay_sinh || '',
                    gioi_tinh: m.gioi_tinh || 'Nam',
                    dia_chi_day_du: m.dia_chi || ''
                },
                von_cn_so: amt,
                gia_tri_cn_so: amt,
                ty_le_cn: m.ty_le || ''
            });
        }
    });

    window.wizardState.transferList = contracts;

    window.wizardState.cd1tv2tvData = {
        hinhThucCN: s.hinhThucCN || 'mot_phan',
        hinh_thuc_cn: s.hinhThucCN || 'mot_phan',
        oldCompany: { ...s.oldCompany },
        csh: { ...s.csh },
        ddplCu: { ...s.ddplCu },
        newCompany: { ...s.newCompany },
        ddplMoi: { ...s.ddplMoi },
        members: s.members.map(m => ({ ...m })),
        chuyen_nhuong: contracts
    };

    return true;
};
