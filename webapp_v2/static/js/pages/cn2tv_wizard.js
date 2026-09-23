// Specialized Dynamic Wizard for Chuyển nhượng Công ty TNHH 2 TV
// Supports N Old Members and N New Members dynamically

window.formatMoneyInput = window.formatMoneyInput || function(input) {
    if (!input) return;
    const raw = String(input.value || '').replace(/\D/g, '');
    input.value = raw ? Number(raw).toLocaleString('vi-VN') : '';
};
window.formatCurrencyInput = window.formatMoneyInput;
window.formatMoneyStr = window.formatMoneyStr || function(val) {
    if (!val) return '';
    const raw = String(val).replace(/\D/g, '');
    return raw ? Number(raw).toLocaleString('vi-VN') : '';
};

window.docSoThanhChu = window.docSoThanhChu || function(s) {
    if (!s) return '';
    const digits = String(s).replace(/\D/g, '');
    if (!digits) return '';
    let n;
    try { n = BigInt(digits); } catch(e) { n = parseInt(digits, 10); }
    if (n === 0n || n === 0) return 'Không đồng';

    const donVi = ['', 'nghìn', 'triệu', 'tỷ', 'nghìn tỷ', 'triệu tỷ'];
    const chuSo = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín'];

    function docBaChuSo(val, isHighest) {
        val = Number(val);
        const tram = Math.floor(val / 100);
        const chuc = Math.floor((val % 100) / 10);
        const dv = val % 10;
        let res = '';
        if (tram > 0 || !isHighest) {
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

    let groups = [];
    let temp = BigInt(digits);
    while (temp > 0n) {
        groups.push(Number(temp % 1000n));
        temp = temp / 1000n;
    }

    let chuoi = '';
    for (let i = 0; i < groups.length; i++) {
        const val = groups[i];
        if (val > 0) {
            const isHighest = (i === groups.length - 1);
            const doc = docBaChuSo(val, isHighest);
            if (doc) {
                const dv = donVi[i] || '';
                chuoi = doc + (dv ? ' ' + dv : '') + (chuoi ? ' ' + chuoi : '');
            }
        }
    }
    chuoi = chuoi.trim();
    if (!chuoi) return '';
    return chuoi.charAt(0).toUpperCase() + chuoi.slice(1) + ' đồng';
};

window.handleCN2TVCompanyMoney = function(input) {
    if (window.formatMoneyInput) window.formatMoneyInput(input);
    const raw = String(input.value || '').replace(/\D/g, '');
    const words = raw && window.docSoThanhChu ? window.docSoThanhChu(raw) : '';
    const chuEl = document.getElementById('COMP_VON_DIEU_LE_CHU');
    if (chuEl && words) {
        chuEl.value = words;
    }
    if (window.cn2tvState && window.cn2tvState.company) {
        window.cn2tvState.company.VON_DIEU_LE_SO = input.value;
        if (words) window.cn2tvState.company.VON_DIEU_LE_CHU = words;
    }
    if (window.updateCN2TVState) window.updateCN2TVState();
};

function getInitialCN2TVState() {
    return {
        company: {
            TEN_CONG_TY_VN: '',
            MA_SO_THUE: '',
            VON_DIEU_LE_SO: '',
            VON_DIEU_LE_CHU: ''
        },
        ddplCu: { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: 'Nam' },
        ddplCuIsTv: true,
        tvCu: [
            { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: 'Nam', VON_GOP: '', TY_LE: '' },
            { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: 'Nam', VON_GOP: '', TY_LE: '' }
        ],
        ddplMoi: { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: 'Nam' },
        ddplMoiIsTv: true,
        tvMoi: [
            { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: 'Nam', VON_GOP: '', TY_LE: '' },
            { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: 'Nam', VON_GOP: '', TY_LE: '' }
        ],
        contracts: [
            { ben_a: 0, ben_b: 0, von: '', gia_tri: '', ty_le: '' }
        ]
    };
}

window.cn2tvState = window.cn2tvState || getInitialCN2TVState();

window.renderCN2TVWizard = function(container) {
    const parentContainer = container.closest('.container');
    if (parentContainer) {
        parentContainer.style.maxWidth = '1540px';
        parentContainer.style.width = '96%';
        parentContainer.style.padding = '0 16px';
    }
    if (!window.cn2tvState) {
        window.cn2tvState = getInitialCN2TVState();
    }
    let state = window.cn2tvState;

    function renderInput(label, id, value, type='text', placeholder='', onchange='', oninput='') {
        const inp = oninput || 'updateCN2TVState()';
        const chg = onchange || 'updateCN2TVState()';
        return `
            <div class="form-group">
                <label class="form-label">${label}</label>
                <input type="${type}" id="${id}" class="form-control" value="${value || ''}" placeholder="${placeholder}" onchange="${chg}" oninput="${inp}">
            </div>
        `;
    }

    function renderPersonForm(prefix, title, person, showCapital=false, canDelete=false, deleteHandler='', isMoi=false, idx=0) {
        let html = `
            <div class="person-card mb-4" id="card-${prefix}">
                <div class="person-card-header">
                    <h4 class="font-bold text-sm" style="color: ${isMoi ? 'var(--accent-green)' : 'var(--accent-orange)'}; margin: 0;">
                        <i class="fa-solid fa-user"></i> ${title}
                    </h4>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        <button type="button" class="btn btn-ocr" onclick="triggerInlineOCR_CN2TV('${prefix}', event)">
                            <i class="fa-solid fa-id-card"></i> Quét VNeID
                        </button>
                        ${canDelete ? `
                            <button type="button" class="btn btn-ghost btn-sm text-error" onclick="${deleteHandler}">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
                <div class="grid-form-2">
                    ${renderInput('Họ và tên *', `${prefix}_HO_TEN`, person.HO_TEN, 'text', 'NGUYỄN VĂN A', 'updateCN2TVState()', 'updateCN2TVState()')}
                    <div class="grid-form-2">
                        <div class="form-group">
                            <label class="form-label">Giới tính</label>
                            <select id="${prefix}_GIOI_TINH" class="form-control" onchange="updateCN2TVState()">
                                <option value="Nam" ${person.GIOI_TINH === 'Nam' ? 'selected' : ''}>Nam</option>
                                <option value="Nữ" ${person.GIOI_TINH === 'Nữ' ? 'selected' : ''}>Nữ</option>
                            </select>
                        </div>
                        ${renderInput('Ngày sinh', `${prefix}_NGAY_SINH`, person.NGAY_SINH, 'text', 'DD/MM/YYYY', 'updateCN2TVState()', 'updateCN2TVState()')}
                    </div>
                </div>
                <div class="grid-form-2">
                    ${renderInput('Số CCCD (12 số) *', `${prefix}_SO_CCCD`, person.SO_CCCD, 'text', '001090001234', 'updateCN2TVState()', 'updateCN2TVState()')}
                    ${renderInput('Địa chỉ thường trú đầy đủ', `${prefix}_DIA_CHI`, person.DIA_CHI, 'text', 'Số nhà, Phường/Xã, Tỉnh/Thành', 'updateCN2TVState()', 'updateCN2TVState()')}
                </div>
        `;
        if (showCapital) {
            html += `
                <div class="grid-form-2 mt-2 pt-2" style="border-top: 1px dashed rgba(255,255,255,0.08);">
                    ${renderInput('Vốn góp (VNĐ)', `${prefix}_VON_GOP`, person.VON_GOP, 'text', 'VD: 500,000,000', 'updateCN2TVState()', 'formatMoneyInput(this); updateCN2TVState()')}
                    ${renderInput('Tỷ lệ (%)', `${prefix}_TY_LE`, person.TY_LE, 'number', 'VD: 50', 'updateCN2TVState()', 'updateCN2TVState()')}
                </div>
            `;
        }
        html += `</div>`;
        return html;
    }

    // --- LOOKUP MST HANDLER ---
    window.lookupMST_CN2TV = async function() {
        const mstInput = document.getElementById('COMP_MA_SO_THUE');
        const btn = document.getElementById('btn-lookup-mst-cn2tv');
        if (!mstInput || !mstInput.value.trim()) {
            alert('Vui lòng nhập Mã số thuế để tra cứu!');
            return;
        }

        const oldHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Tra cứu...';
        btn.disabled = true;

        try {
            const response = await fetch(`/api/mst/${encodeURIComponent(mstInput.value.trim())}`);
            const result = await response.json();

            if (result.success && result.data && result.data.name) {
                state.company.TEN_CONG_TY_VN = result.data.name;
                const nameEl = document.getElementById('COMP_TEN_CONG_TY_VN');
                if (nameEl) {
                    nameEl.value = result.data.name;
                    nameEl.style.borderColor = 'var(--accent-green)';
                }
            } else {
                alert('Không tìm thấy thông tin mã số thuế.');
            }
        } catch (err) {
            console.error(err);
            alert('Lỗi tra cứu MST: ' + err.message);
        }

        btn.innerHTML = oldHTML;
        btn.disabled = false;
    };

    function updateContractSelectOptions() {
        if (!state.contracts) return;
        state.contracts.forEach((c, idx) => {
            const selA = document.getElementById(`C_${idx}_BEN_A`);
            if (selA) {
                const curVal = isNaN(parseInt(selA.value)) ? c.ben_a : parseInt(selA.value);
                selA.innerHTML = state.tvCu.map((m, i) => `
                    <option value="${i}" ${curVal === i ? 'selected' : ''}>
                        Thành viên Cũ #${i + 1}: ${m.HO_TEN ? m.HO_TEN : '(Chưa nhập tên)'}
                    </option>
                `).join('');
            }

            const selB = document.getElementById(`C_${idx}_BEN_B`);
            if (selB) {
                const curVal = isNaN(parseInt(selB.value)) ? c.ben_b : parseInt(selB.value);
                selB.innerHTML = state.tvMoi.map((m, i) => `
                    <option value="${i}" ${curVal === i ? 'selected' : ''}>
                        Thành viên Mới #${i + 1}: ${m.HO_TEN ? m.HO_TEN : '(Chưa nhập tên)'}
                    </option>
                `).join('');
            }
        });

        // Update badge headers in DOM
        const badgeCu1 = document.getElementById('BADGE_TV_CU_1');
        if (badgeCu1 && state.tvCu[0]) {
            badgeCu1.textContent = state.tvCu[0].HO_TEN || 'Chưa nhập họ tên';
        }
        const badgeMoi1 = document.getElementById('BADGE_TV_MOI_1');
        if (badgeMoi1 && state.tvMoi[0]) {
            badgeMoi1.textContent = state.tvMoi[0].HO_TEN || 'Chưa nhập họ tên';
        }
    }

    window.updateCN2TVState = function() {
        if (!window.cn2tvState) {
            window.cn2tvState = getInitialCN2TVState();
        }
        state = window.cn2tvState;
        // 1. Collect Company
        ['TEN_CONG_TY_VN', 'MA_SO_THUE', 'VON_DIEU_LE_SO', 'VON_DIEU_LE_CHU'].forEach(k => {
            const el = document.getElementById(`COMP_${k}`);
            if (el) state.company[k] = el.value;
        });

        // 2. Collect DDPL Cu
        ['HO_TEN', 'NGAY_SINH', 'SO_CCCD', 'DIA_CHI', 'GIOI_TINH'].forEach(k => {
            const el = document.getElementById(`D_CU_${k}`);
            if (el) state.ddplCu[k] = el.value;
        });

        const ddplCuCb = document.getElementById('D_CU_IS_TV');
        if (ddplCuCb) state.ddplCuIsTv = ddplCuCb.checked;

        // Sync DDPL Cu to TV Cu #1 if linked
        if (state.ddplCuIsTv && state.tvCu.length > 0) {
            state.tvCu[0].HO_TEN = state.ddplCu.HO_TEN;
            state.tvCu[0].NGAY_SINH = state.ddplCu.NGAY_SINH;
            state.tvCu[0].SO_CCCD = state.ddplCu.SO_CCCD;
            state.tvCu[0].DIA_CHI = state.ddplCu.DIA_CHI;
            state.tvCu[0].GIOI_TINH = state.ddplCu.GIOI_TINH;
        }

        // 3. Collect Old Members
        state.tvCu.forEach((m, idx) => {
            const pre = `T_CU${idx + 1}`;
            if (idx === 0 && state.ddplCuIsTv) {
                const vg = document.getElementById(`${pre}_VON_GOP`);
                const tl = document.getElementById(`${pre}_TY_LE`);
                if (vg) m.VON_GOP = vg.value;
                if (tl) m.TY_LE = tl.value;
            } else {
                ['HO_TEN', 'NGAY_SINH', 'SO_CCCD', 'DIA_CHI', 'GIOI_TINH', 'VON_GOP', 'TY_LE'].forEach(k => {
                    const el = document.getElementById(`${pre}_${k}`);
                    if (el) m[k] = el.value;
                });
            }
        });

        // 4. Collect DDPL Moi
        ['HO_TEN', 'NGAY_SINH', 'SO_CCCD', 'DIA_CHI', 'GIOI_TINH'].forEach(k => {
            const el = document.getElementById(`D_MOI_${k}`);
            if (el) state.ddplMoi[k] = el.value;
        });

        const ddplMoiCb = document.getElementById('D_MOI_IS_TV');
        if (ddplMoiCb) state.ddplMoiIsTv = ddplMoiCb.checked;

        // Sync DDPL Moi to TV Moi #1 if linked
        if (state.ddplMoiIsTv && state.tvMoi.length > 0) {
            state.tvMoi[0].HO_TEN = state.ddplMoi.HO_TEN;
            state.tvMoi[0].NGAY_SINH = state.ddplMoi.NGAY_SINH;
            state.tvMoi[0].SO_CCCD = state.ddplMoi.SO_CCCD;
            state.tvMoi[0].DIA_CHI = state.ddplMoi.DIA_CHI;
            state.tvMoi[0].GIOI_TINH = state.ddplMoi.GIOI_TINH;
        }

        // 5. Collect New Members
        state.tvMoi.forEach((m, idx) => {
            const pre = `T_MOI${idx + 1}`;
            if (idx === 0 && state.ddplMoiIsTv) {
                const vg = document.getElementById(`${pre}_VON_GOP`);
                const tl = document.getElementById(`${pre}_TY_LE`);
                if (vg) m.VON_GOP = vg.value;
                if (tl) m.TY_LE = tl.value;
            } else {
                ['HO_TEN', 'NGAY_SINH', 'SO_CCCD', 'DIA_CHI', 'GIOI_TINH', 'VON_GOP', 'TY_LE'].forEach(k => {
                    const el = document.getElementById(`${pre}_${k}`);
                    if (el) m[k] = el.value;
                });
            }
        });

        // 6. Collect Contracts
        state.contracts.forEach((c, idx) => {
            const a = document.getElementById(`C_${idx}_BEN_A`);
            const b = document.getElementById(`C_${idx}_BEN_B`);
            const v = document.getElementById(`C_${idx}_VON`);
            const gt = document.getElementById(`C_${idx}_GIA_TRI`);
            const tl = document.getElementById(`C_${idx}_TY_LE`);

            if (a) c.ben_a = parseInt(a.value);
            if (b) c.ben_b = parseInt(b.value);
            if (v) c.von = v.value;
            if (gt) c.gia_tri = gt.value;
            if (tl) c.ty_le = tl.value;
        });

        // 7. Update dropdown options in Section 4 in real-time
        updateContractSelectOptions();
    };

    window.toggleDDPLCu_CN2TV = function() {
        window.updateCN2TVState();
        reRenderCN2TV();
    };

    window.toggleDDPLMoi_CN2TV = function() {
        window.updateCN2TVState();
        reRenderCN2TV();
    };

    // --- DYNAMIC ADD / REMOVE OLD MEMBERS ---
    window.addOldMember_CN2TV = function() {
        window.updateCN2TVState();
        state.tvCu.push({
            HO_TEN: '',
            NGAY_SINH: '',
            SO_CCCD: '',
            DIA_CHI: '',
            GIOI_TINH: 'Nam',
            VON_GOP: '',
            TY_LE: ''
        });
        reRenderCN2TV();
    };

    window.removeOldMember_CN2TV = function(idx) {
        window.updateCN2TVState();
        if (state.tvCu.length <= 2) {
            alert('Công ty TNHH 2 thành viên trở lên phải có tối thiểu 2 thành viên cũ!');
            return;
        }
        state.tvCu.splice(idx, 1);
        reRenderCN2TV();
    };

    // --- DYNAMIC ADD / REMOVE NEW MEMBERS ---
    window.addNewMember_CN2TV = function() {
        window.updateCN2TVState();
        state.tvMoi.push({
            HO_TEN: '',
            NGAY_SINH: '',
            SO_CCCD: '',
            DIA_CHI: '',
            GIOI_TINH: 'Nam',
            VON_GOP: '',
            TY_LE: ''
        });
        reRenderCN2TV();
    };

    window.removeNewMember_CN2TV = function(idx) {
        window.updateCN2TVState();
        if (state.tvMoi.length <= 2) {
            alert('Công ty TNHH 2 thành viên trở lên phải có tối thiểu 2 thành viên mới!');
            return;
        }
        state.tvMoi.splice(idx, 1);
        reRenderCN2TV();
    };

    // --- CONTRACT MANAGEMENT ---
    window.addContract_CN2TV = function() {
        window.updateCN2TVState();
        state.contracts.push({ ben_a: 0, ben_b: 0, von: '', gia_tri: '', ty_le: '' });
        reRenderCN2TV();
    };

    window.removeContract_CN2TV = function(idx) {
        window.updateCN2TVState();
        if (state.contracts.length <= 1) {
            alert('Phải có ít nhất 1 giao dịch chuyển nhượng!');
            return;
        }
        state.contracts.splice(idx, 1);
        reRenderCN2TV();
    };

    function reRenderCN2TV() {
        let html = `
            <div style="display: flex; flex-direction: column; gap: var(--space-6);">
                <div class="text-xs text-muted" style="background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-glass);">
                    <i class="fa-solid fa-circle-info text-cyan"></i> Form chuyên biệt hỗ trợ linh hoạt <b>N Thành viên Cũ</b> chuyển nhượng cho <b>N Thành viên Mới</b> và phân bổ nhiều Hợp đồng chuyển nhượng.
                </div>

                <!-- 1. COMPANY INFO -->
                <div class="card card-sub" style="border-left: 4px solid var(--accent-cyan);">
                    <h3 class="font-bold text-lg mb-4 text-cyan"><i class="fa-solid fa-building"></i> 1. Thông tin Công ty</h3>
                    <div class="grid-form-2">
                        <div class="form-group">
                            <label class="form-label">Mã số thuế doanh nghiệp *</label>
                            <div style="display: flex; gap: 8px;">
                                <input type="text" id="COMP_MA_SO_THUE" class="form-control font-mono" value="${state.company.MA_SO_THUE}" placeholder="VD: 0101234567" onchange="updateCN2TVState()" oninput="updateCN2TVState()">
                                <button type="button" class="btn btn-secondary" id="btn-lookup-mst-cn2tv" onclick="lookupMST_CN2TV()">
                                    <i class="fa-solid fa-magnifying-glass"></i> Tra cứu
                                </button>
                            </div>
                        </div>
                        ${renderInput('Tên công ty (tiếng Việt) *', 'COMP_TEN_CONG_TY_VN', state.company.TEN_CONG_TY_VN, 'text', 'CÔNG TY TNHH...', 'updateCN2TVState()', 'updateCN2TVState()')}
                    </div>
                    <div class="grid-form-2 mt-2">
                        ${renderInput('Vốn điều lệ (Số)', 'COMP_VON_DIEU_LE_SO', state.company.VON_DIEU_LE_SO, 'text', 'VD: 1,000,000,000', 'handleCN2TVCompanyMoney(this)', 'handleCN2TVCompanyMoney(this)')}
                        ${renderInput('Vốn điều lệ (Chữ)', 'COMP_VON_DIEU_LE_CHU', state.company.VON_DIEU_LE_CHU, 'text', 'VD: Một tỷ đồng', 'updateCN2TVState()', 'updateCN2TVState()')}
                    </div>
                </div>

                <!-- 2. OLD MEMBERS (SELLER SIDE) -->
                <div class="card card-sub" style="border-left: 4px solid var(--accent-orange);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4);">
                        <h3 class="font-bold text-lg text-warning"><i class="fa-solid fa-users"></i> 2. Bên chuyển nhượng (Thành viên CŨ: ${state.tvCu.length} người)</h3>
                        <button type="button" class="btn btn-secondary btn-sm" onclick="addOldMember_CN2TV()">
                            <i class="fa-solid fa-user-plus"></i> Thêm thành viên cũ
                        </button>
                    </div>

                    ${renderPersonForm('D_CU', 'Người đại diện theo pháp luật CŨ', state.ddplCu, false, false, '', false)}

                    <div class="mb-4" style="background: rgba(0,0,0,0.25); padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-glass);">
                        <label style="display: flex; gap: 10px; cursor: pointer; align-items: center;">
                            <input type="checkbox" id="D_CU_IS_TV" ${state.ddplCuIsTv ? 'checked' : ''} onchange="toggleDDPLCu_CN2TV()">
                            <span class="text-sm font-medium">Người ĐDPL Cũ đồng thời là Thành viên Cũ #1 (Bên chuyển nhượng vốn)</span>
                        </label>
                    </div>
        `;

        state.tvCu.forEach((m, idx) => {
            if (idx === 0 && state.ddplCuIsTv) {
                m.HO_TEN = state.ddplCu.HO_TEN;
                m.NGAY_SINH = state.ddplCu.NGAY_SINH;
                m.SO_CCCD = state.ddplCu.SO_CCCD;
                m.DIA_CHI = state.ddplCu.DIA_CHI;
                m.GIOI_TINH = state.ddplCu.GIOI_TINH;

                html += `
                    <div class="person-card mb-4" style="background: rgba(255, 184, 108, 0.05); border: 1px solid rgba(255, 184, 108, 0.2);">
                        <div class="person-card-header">
                            <h4 class="font-bold text-sm text-warning"><i class="fa-solid fa-link"></i> Thành viên Cũ #1 (Tự động liên kết từ ĐDPL Cũ)</h4>
                            <span id="BADGE_TV_CU_1" class="badge badge-warning text-xs">${m.HO_TEN || 'Chưa nhập họ tên'}</span>
                        </div>
                        <div class="grid-form-2">
                            ${renderInput('Vốn góp cũ (VNĐ)', 'T_CU1_VON_GOP', m.VON_GOP, 'text', 'VD: 500,000,000', 'updateCN2TVState()', 'formatMoneyInput(this); updateCN2TVState()')}
                            ${renderInput('Tỷ lệ vốn cũ (%)', 'T_CU1_TY_LE', m.TY_LE, 'number', 'VD: 50', 'updateCN2TVState()', 'updateCN2TVState()')}
                        </div>
                    </div>
                `;
            } else {
                const canDel = state.tvCu.length > 2;
                html += renderPersonForm(`T_CU${idx + 1}`, `Thành viên Cũ #${idx + 1}`, m, true, canDel, `removeOldMember_CN2TV(${idx})`, false, idx);
            }
        });

        html += `</div>`;

        // 3. NEW MEMBERS (BUYER SIDE)
        html += `
            <div class="card card-sub" style="border-left: 4px solid var(--accent-green);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4);">
                    <h3 class="font-bold text-lg text-success"><i class="fa-solid fa-user-plus"></i> 3. Bên nhận chuyển nhượng (Thành viên MỚI: ${state.tvMoi.length} người)</h3>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="addNewMember_CN2TV()">
                        <i class="fa-solid fa-user-plus"></i> Thêm thành viên mới
                    </button>
                </div>

                ${renderPersonForm('D_MOI', 'Người đại diện theo pháp luật MỚI', state.ddplMoi, false, false, '', true)}

                <div class="mb-4" style="background: rgba(0,0,0,0.25); padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-glass);">
                    <label style="display: flex; gap: 10px; cursor: pointer; align-items: center;">
                        <input type="checkbox" id="D_MOI_IS_TV" ${state.ddplMoiIsTv ? 'checked' : ''} onchange="toggleDDPLMoi_CN2TV()">
                        <span class="text-sm font-medium">Người ĐDPL Mới đồng thời là Thành viên Mới #1 (Bên nhận chuyển nhượng vốn)</span>
                    </label>
                </div>
        `;

        state.tvMoi.forEach((m, idx) => {
            if (idx === 0 && state.ddplMoiIsTv) {
                m.HO_TEN = state.ddplMoi.HO_TEN;
                m.NGAY_SINH = state.ddplMoi.NGAY_SINH;
                m.SO_CCCD = state.ddplMoi.SO_CCCD;
                m.DIA_CHI = state.ddplMoi.DIA_CHI;
                m.GIOI_TINH = state.ddplMoi.GIOI_TINH;

                html += `
                    <div class="person-card mb-4" style="background: rgba(80, 250, 123, 0.05); border: 1px solid rgba(80, 250, 123, 0.2);">
                        <div class="person-card-header">
                            <h4 class="font-bold text-sm text-success"><i class="fa-solid fa-link"></i> Thành viên Mới #1 (Tự động liên kết từ ĐDPL Mới)</h4>
                            <span id="BADGE_TV_MOI_1" class="badge badge-green text-xs">${m.HO_TEN || 'Chưa nhập họ tên'}</span>
                        </div>
                        <div class="grid-form-2">
                            ${renderInput('Vốn góp mới (VNĐ)', 'T_MOI1_VON_GOP', m.VON_GOP, 'text', 'VD: 500,000,000', 'updateCN2TVState()', 'formatMoneyInput(this); updateCN2TVState()')}
                            ${renderInput('Tỷ lệ vốn mới (%)', 'T_MOI1_TY_LE', m.TY_LE, 'number', 'VD: 50', 'updateCN2TVState()', 'updateCN2TVState()')}
                        </div>
                    </div>
                `;
            } else {
                const canDel = state.tvMoi.length > 2;
                html += renderPersonForm(`T_MOI${idx + 1}`, `Thành viên Mới #${idx + 1}`, m, true, canDel, `removeNewMember_CN2TV(${idx})`, true, idx);
            }
        });

        html += `</div>`;

        // 4. CONTRACT MATRIX
        html += `
            <div class="card card-sub" style="border-left: 4px solid var(--accent-primary);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4);">
                    <h3 class="font-bold text-lg text-cyan"><i class="fa-solid fa-file-contract"></i> 4. Các giao dịch chuyển nhượng (${state.contracts.length} hợp đồng)</h3>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="addContract_CN2TV()">
                        <i class="fa-solid fa-plus"></i> Thêm giao dịch
                    </button>
                </div>
        `;

        state.contracts.forEach((c, idx) => {
            const optBenA = state.tvCu.map((m, i) => `
                <option value="${i}" ${c.ben_a === i ? 'selected' : ''}>
                    Thành viên Cũ #${i + 1}: ${m.HO_TEN ? m.HO_TEN : '(Chưa nhập tên)'}
                </option>
            `).join('');

            const optBenB = state.tvMoi.map((m, i) => `
                <option value="${i}" ${c.ben_b === i ? 'selected' : ''}>
                    Thành viên Mới #${i + 1}: ${m.HO_TEN ? m.HO_TEN : '(Chưa nhập tên)'}
                </option>
            `).join('');

            html += `
                <div class="person-card mb-4" style="background: rgba(189, 147, 249, 0.05); border: 1px solid rgba(189, 147, 249, 0.2);">
                    <div class="person-card-header">
                        <span class="font-bold text-sm text-cyan">Giao dịch #${idx + 1}</span>
                        ${state.contracts.length > 1 ? `
                            <button type="button" class="btn btn-ghost btn-sm text-error" onclick="removeContract_CN2TV(${idx})">
                                <i class="fa-solid fa-trash"></i> Xóa
                            </button>
                        ` : ''}
                    </div>
                    <div class="grid-form-2">
                        <div class="form-group">
                            <label class="form-label">Bên chuyển nhượng (Bên A)</label>
                            <select id="C_${idx}_BEN_A" class="form-control" onchange="updateCN2TVState()">
                                ${optBenA}
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Bên nhận chuyển nhượng (Bên B)</label>
                            <select id="C_${idx}_BEN_B" class="form-control" onchange="updateCN2TVState()">
                                ${optBenB}
                            </select>
                        </div>
                    </div>
                    <div class="grid-form-3 mt-2">
                        ${renderInput('Phần vốn chuyển nhượng (VNĐ)', `C_${idx}_VON`, c.von, 'text', '500,000,000', 'updateCN2TVState()', 'formatMoneyInput(this); updateCN2TVState()')}
                        ${renderInput('Giá chuyển nhượng (VNĐ)', `C_${idx}_GIA_TRI`, c.gia_tri, 'text', '500,000,000', 'updateCN2TVState()', 'formatMoneyInput(this); updateCN2TVState()')}
                        ${renderInput('Tỷ lệ vốn (%)', `C_${idx}_TY_LE`, c.ty_le, 'number', '50', 'updateCN2TVState()', 'updateCN2TVState()')}
                    </div>
                </div>
            `;
        });

        html += `</div></div>`;
        container.innerHTML = html;
    }

    // Initial render
    reRenderCN2TV();

    window.collectCN2TVData = function() {
        window.updateCN2TVState();

        if (!state.company.TEN_CONG_TY_VN) {
            alert('Vui lòng nhập Tên công ty!');
            return false;
        }
        if (state.contracts.length === 0) {
            alert('Phải có ít nhất 1 giao dịch chuyển nhượng!');
            return false;
        }

        window.wizardState.cn2tvData = {
            company: state.company,
            ddpl_cu: state.ddplCu,
            ddpl_moi: state.ddplMoi,
            tv_cu: state.tvCu,
            tv_moi: state.tvMoi,
            chuyen_nhuong: state.contracts
        };
        return true;
    };

    window.triggerInlineOCR_CN2TV = function(prefix, event) {
        const btn = event.currentTarget;
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/png, image/jpeg, image/webp';

        fileInput.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const oldHTML = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang quét...';
            btn.disabled = true;

            const formData = new FormData();
            formData.append('image', file);
            formData.append('file', file);
            formData.append('target', prefix);

            try {
                const response = await fetch('/api/ocr/vneid', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (!result.success) throw new Error(result.message);

                const data = result.data;
                const setVal = (k, v) => {
                    const el = document.getElementById(`${prefix}_${k}`);
                    if (el) {
                        el.value = v || '';
                        el.style.borderColor = 'var(--accent-green)';
                    }
                };

                setVal('HO_TEN', data.ho_ten);
                setVal('NGAY_SINH', data.ngay_sinh);
                setVal('SO_CCCD', data.so_cccd);
                setVal('GIOI_TINH', data.gioi_tinh);
                setVal('DIA_CHI', data.dia_chi);

                window.updateCN2TVState();
                btn.innerHTML = '<i class="fa-solid fa-check text-success"></i> Xong';
                setTimeout(() => { btn.innerHTML = oldHTML; btn.disabled = false; }, 2000);
            } catch (err) {
                console.error(err);
                alert('Lỗi quét VNeID: ' + err.message);
                btn.innerHTML = oldHTML;
                btn.disabled = false;
            }
        };

        fileInput.click();
    };
};
