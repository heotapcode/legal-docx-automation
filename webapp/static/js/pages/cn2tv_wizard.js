window.renderCN2TVWizard = function(container) {
    let state = {
        company: {
            TEN_CONG_TY_VN: '',
            MA_SO_THUE: '',
            VON_DIEU_LE_SO: '',
            VON_DIEU_LE_CHU: ''
        },
        ddplCu: { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: '' },
        ddplCuIsTv: true,
        tvCu1: { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: '', VON_GOP: '', TY_LE: '' },
        tvCu2: { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: '', VON_GOP: '', TY_LE: '' },
        
        ddplMoi: { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: '' },
        ddplMoiIsTv: true,
        tvMoi1: { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: '', VON_GOP: '', TY_LE: '' },
        tvMoi2: { HO_TEN: '', NGAY_SINH: '', SO_CCCD: '', DIA_CHI: '', GIOI_TINH: '', VON_GOP: '', TY_LE: '' },

        contracts: []
    };

    function renderInput(label, id, value, type='text', placeholder='', onchange='') {
        return `
            <div>
                <label class="text-sm text-muted mb-1 block">${label}</label>
                <input type="${type}" id="${id}" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${value}" placeholder="${placeholder}" onchange="${onchange}">
            </div>
        `;
    }

    function renderPersonForm(prefix, title, person, showCapital=false) {
        let html = `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-md); padding: var(--space-4); margin-bottom: var(--space-4);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-3);">
                    <h4 class="font-bold" style="color: var(--accent-secondary); margin: 0;">${title}</h4>
                    <button class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0; color: var(--success); border-color: var(--success);" onclick="triggerInlineOCR_CN2TV('${prefix}', event)"><i class="fa-solid fa-id-card"></i> Quét VNeID/CCCD</button>
                </div>
                <div class="grid-2" style="gap: var(--space-3);">
                    ${renderInput('Họ và tên', `${prefix}_HO_TEN`, person.HO_TEN, 'text', '', 'updateCN2TVState()')}
                    ${renderInput('Số CCCD', `${prefix}_SO_CCCD`, person.SO_CCCD, 'text', '', 'updateCN2TVState()')}
                    ${renderInput('Ngày sinh', `${prefix}_NGAY_SINH`, person.NGAY_SINH, 'text', '', 'updateCN2TVState()')}
                    ${renderInput('Giới tính', `${prefix}_GIOI_TINH`, person.GIOI_TINH, 'text', 'Nam/Nữ', 'updateCN2TVState()')}
                    ${renderInput('Địa chỉ đầy đủ', `${prefix}_DIA_CHI`, person.DIA_CHI, 'text', '', 'updateCN2TVState()')}
        `;
        if (showCapital) {
            html += `
                    ${renderInput('Vốn góp (VNĐ)', `${prefix}_VON_GOP`, person.VON_GOP, 'text', 'VD: 10000000', 'updateCN2TVState()')}
                    ${renderInput('Tỷ lệ (%)', `${prefix}_TY_LE`, person.TY_LE, 'number', 'VD: 50', 'updateCN2TVState()')}
            `;
        }
        html += `</div></div>`;
        return html;
    }

    window.lookupMST_CN2TV = async function(event) {
        const mstInput = document.getElementById('COMP_MA_SO_THUE');
        if(!mstInput || !mstInput.value) {
            alert("Vui lòng nhập Mã số thuế trước khi tra cứu.");
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
                state.company.TEN_CONG_TY_VN = result.data.name;
                // Don't auto fill address for company because CN2TV doesn't have COMP_DIA_CHI
                // Re-render
                reRenderCN2TV();
            } else {
                alert('Không tìm thấy thông tin công ty.');
            }
        } catch(err) {
            console.error(err);
            alert('Lỗi tra cứu MST: ' + err.message);
        }
        
        btn.innerHTML = oldHTML;
        btn.disabled = false;
    };

    window.updateCN2TVState = function() {
        // Collect Company
        ['TEN_CONG_TY_VN', 'MA_SO_THUE', 'VON_DIEU_LE_SO', 'VON_DIEU_LE_CHU'].forEach(k => {
            const el = document.getElementById(`COMP_${k}`);
            if(el) state.company[k] = el.value;
        });

        // Collect DDPL Cu
        ['HO_TEN', 'NGAY_SINH', 'SO_CCCD', 'DIA_CHI', 'GIOI_TINH'].forEach(k => {
            const el = document.getElementById(`D_CU_${k}`);
            if(el) state.ddplCu[k] = el.value;
        });

        state.ddplCuIsTv = document.getElementById('D_CU_IS_TV').checked;
        
        ['HO_TEN', 'NGAY_SINH', 'SO_CCCD', 'DIA_CHI', 'GIOI_TINH', 'VON_GOP', 'TY_LE'].forEach(k => {
            const el1 = document.getElementById(`T_CU1_${k}`);
            if(el1) state.tvCu1[k] = el1.value;
            const el2 = document.getElementById(`T_CU2_${k}`);
            if(el2) state.tvCu2[k] = el2.value;
        });

        // Collect DDPL Moi
        ['HO_TEN', 'NGAY_SINH', 'SO_CCCD', 'DIA_CHI', 'GIOI_TINH'].forEach(k => {
            const el = document.getElementById(`D_MOI_${k}`);
            if(el) state.ddplMoi[k] = el.value;
        });

        state.ddplMoiIsTv = document.getElementById('D_MOI_IS_TV').checked;
        
        ['HO_TEN', 'NGAY_SINH', 'SO_CCCD', 'DIA_CHI', 'GIOI_TINH', 'VON_GOP', 'TY_LE'].forEach(k => {
            const el1 = document.getElementById(`T_MOI1_${k}`);
            if(el1) state.tvMoi1[k] = el1.value;
            const el2 = document.getElementById(`T_MOI2_${k}`);
            if(el2) state.tvMoi2[k] = el2.value;
        });

        reRenderCN2TV();
    };

    window.addContract = function() {
        state.contracts.push({ ben_a: 0, ben_b: 0, von: '', ty_le: '' });
        reRenderCN2TV();
    };

    window.removeContract = function(idx) {
        state.contracts.splice(idx, 1);
        reRenderCN2TV();
    };

    window.updateContract = function(idx, field, val) {
        state.contracts[idx][field] = val;
    };

    function reRenderCN2TV() {
        let html = `<div style="display: flex; flex-direction: column; gap: var(--space-6);">`;

        // 1. Company
        html += `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4);">
                <h3 class="font-bold mb-4" style="color: var(--info);"><i class="fa-solid fa-building"></i> 1. Thông tin Công ty</h3>
                <div class="grid-2" style="gap: var(--space-4);">
                    ${renderInput('Tên công ty', 'COMP_TEN_CONG_TY_VN', state.company.TEN_CONG_TY_VN, 'text', '', 'updateCN2TVState()')}
                    <div>
                        <label class="text-sm text-muted mb-1 block">Mã số thuế</label>
                        <input type="text" id="COMP_MA_SO_THUE" class="input" style="width: 100%; background: transparent; border: 1px solid var(--border-glass); color: white; padding: 8px 12px; border-radius: 4px;" value="${state.company.MA_SO_THUE}" placeholder="" onchange="updateCN2TVState()">
                        <div class="mt-2"><button type="button" class="btn btn-outline" style="font-size: 11px; padding: 4px 8px; height: auto; min-height: 0;" onclick="lookupMST_CN2TV(event)"><i class="fa-solid fa-magnifying-glass"></i> Tra cứu tự động</button></div>
                    </div>
                    ${renderInput('Vốn điều lệ (Số)', 'COMP_VON_DIEU_LE_SO', state.company.VON_DIEU_LE_SO, 'text', 'VD: 10000000', 'updateCN2TVState()')}
                    ${renderInput('Vốn điều lệ (Chữ)', 'COMP_VON_DIEU_LE_CHU', state.company.VON_DIEU_LE_CHU, 'text', 'VD: Mười triệu đồng', 'updateCN2TVState()')}
                </div>
            </div>
        `;

        // 2. OLD MEMBERS
        html += `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4);">
                <h3 class="font-bold mb-4" style="color: var(--warning);"><i class="fa-solid fa-user-clock"></i> 2. Bên chuyển nhượng (CŨ)</h3>
                ${renderPersonForm('D_CU', 'Đại diện pháp luật CŨ', state.ddplCu, false)}
                
                <div class="mb-4">
                    <label style="display: flex; gap: 8px; cursor: pointer; align-items: center; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;">
                        <input type="checkbox" id="D_CU_IS_TV" onchange="updateCN2TVState()" ${state.ddplCuIsTv ? 'checked' : ''}>
                        <span class="font-bold">Đại diện pháp luật cũ ĐỒNG THỜI là Thành viên góp vốn</span>
                    </label>
                </div>
        `;

        if (state.ddplCuIsTv) {
            state.tvCu1.HO_TEN = state.ddplCu.HO_TEN;
            state.tvCu1.NGAY_SINH = state.ddplCu.NGAY_SINH;
            state.tvCu1.SO_CCCD = state.ddplCu.SO_CCCD;
            state.tvCu1.DIA_CHI = state.ddplCu.DIA_CHI;
            
            html += `
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--radius-md); padding: var(--space-4); margin-bottom: var(--space-4);">
                    <h4 class="font-bold mb-3 text-success">Thành viên 1 (Lấy từ ĐDPL Cũ)</h4>
                    <div class="grid-2" style="gap: var(--space-3);">
                        ${renderInput('Vốn góp hiện tại (VNĐ)', 'T_CU1_VON_GOP', state.tvCu1.VON_GOP, 'text', '', 'updateCN2TVState()')}
                        ${renderInput('Tỷ lệ (%)', 'T_CU1_TY_LE', state.tvCu1.TY_LE, 'number', '', 'updateCN2TVState()')}
                    </div>
                </div>
            `;
        } else {
            html += renderPersonForm('T_CU1', 'Thành viên 1', state.tvCu1, true);
        }
        
        html += renderPersonForm('T_CU2', 'Thành viên 2', state.tvCu2, true);
        html += `</div>`;


        // 3. NEW MEMBERS
        html += `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4);">
                <h3 class="font-bold mb-4" style="color: var(--success);"><i class="fa-solid fa-user-tie"></i> 3. Bên nhận chuyển nhượng (MỚI)</h3>
                ${renderPersonForm('D_MOI', 'Đại diện pháp luật MỚI', state.ddplMoi, false)}
                
                <div class="mb-4">
                    <label style="display: flex; gap: 8px; cursor: pointer; align-items: center; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;">
                        <input type="checkbox" id="D_MOI_IS_TV" onchange="updateCN2TVState()" ${state.ddplMoiIsTv ? 'checked' : ''}>
                        <span class="font-bold">Đại diện pháp luật mới ĐỒNG THỜI là Thành viên góp vốn</span>
                    </label>
                </div>
        `;

        if (state.ddplMoiIsTv) {
            state.tvMoi1.HO_TEN = state.ddplMoi.HO_TEN;
            state.tvMoi1.NGAY_SINH = state.ddplMoi.NGAY_SINH;
            state.tvMoi1.SO_CCCD = state.ddplMoi.SO_CCCD;
            state.tvMoi1.DIA_CHI = state.ddplMoi.DIA_CHI;
            
            html += `
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--radius-md); padding: var(--space-4); margin-bottom: var(--space-4);">
                    <h4 class="font-bold mb-3 text-success">Thành viên 1 (Lấy từ ĐDPL Mới)</h4>
                    <div class="grid-2" style="gap: var(--space-3);">
                        ${renderInput('Vốn góp mới (VNĐ)', 'T_MOI1_VON_GOP', state.tvMoi1.VON_GOP, 'text', '', 'updateCN2TVState()')}
                        ${renderInput('Tỷ lệ mới (%)', 'T_MOI1_TY_LE', state.tvMoi1.TY_LE, 'number', '', 'updateCN2TVState()')}
                    </div>
                </div>
            `;
        } else {
            html += renderPersonForm('T_MOI1', 'Thành viên 1', state.tvMoi1, true);
        }
        
        html += renderPersonForm('T_MOI2', 'Thành viên 2', state.tvMoi2, true);
        html += `</div>`;

        // 4. CONTRACTS
        html += `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-lg); padding: var(--space-4);">
                <div style="display: flex; justify-content: space-between; align-items: center; mb-4">
                    <h3 class="font-bold mb-4" style="color: var(--accent-primary);"><i class="fa-solid fa-file-contract"></i> 4. Hợp đồng chuyển nhượng</h3>
                    <button class="btn btn-outline btn-sm" onclick="addContract()">+ Thêm giao dịch</button>
                </div>
        `;

        if (state.contracts.length === 0) {
            html += `<div class="text-center text-muted py-4">Chưa có giao dịch chuyển nhượng nào. Vui lòng thêm giao dịch!</div>`;
        }

        const cuOpts = `<option value="0">${state.tvCu1.HO_TEN || 'Thành viên cũ 1'}</option><option value="1">${state.tvCu2.HO_TEN || 'Thành viên cũ 2'}</option>`;
        const moiOpts = `<option value="0">${state.tvMoi1.HO_TEN || 'Thành viên mới 1'}</option><option value="1">${state.tvMoi2.HO_TEN || 'Thành viên mới 2'}</option>`;

        state.contracts.forEach((cn, idx) => {
            html += `
                <div style="background: rgba(0,0,0,0.2); border: 1px dashed var(--border-glass); border-radius: var(--radius-md); padding: var(--space-3); margin-bottom: var(--space-3);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <h4 class="font-bold text-sm">Giao dịch #${idx + 1}</h4>
                        <button class="btn btn-ghost" style="color: var(--error); padding: 2px 8px; min-height: 0; height: auto;" onclick="removeContract(${idx})"><i class="fa-solid fa-trash"></i></button>
                    </div>
                    <div class="grid-2" style="gap: var(--space-3);">
                        <div>
                            <label class="text-xs text-muted block mb-1">Bên bán (Cũ)</label>
                            <select class="input" style="width: 100%; padding: 6px; background: transparent; border: 1px solid var(--border-glass); color: white; border-radius: 4px;" onchange="updateContract(${idx}, 'ben_a', this.value)">
                                <option style="color: black;" value="0" ${cn.ben_a == 0 ? 'selected' : ''}>${state.tvCu1.HO_TEN || 'Thành viên cũ 1'}</option>
                                <option style="color: black;" value="1" ${cn.ben_a == 1 ? 'selected' : ''}>${state.tvCu2.HO_TEN || 'Thành viên cũ 2'}</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs text-muted block mb-1">Bên mua (Mới)</label>
                            <select class="input" style="width: 100%; padding: 6px; background: transparent; border: 1px solid var(--border-glass); color: white; border-radius: 4px;" onchange="updateContract(${idx}, 'ben_b', this.value)">
                                <option style="color: black;" value="0" ${cn.ben_b == 0 ? 'selected' : ''}>${state.tvMoi1.HO_TEN || 'Thành viên mới 1'}</option>
                                <option style="color: black;" value="1" ${cn.ben_b == 1 ? 'selected' : ''}>${state.tvMoi2.HO_TEN || 'Thành viên mới 2'}</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs text-muted block mb-1">Giá trị chuyển nhượng (VNĐ)</label>
                            <input type="text" class="input" style="width: 100%; padding: 6px; background: transparent; border: 1px solid var(--border-glass); color: white; border-radius: 4px;" value="${cn.von}" onchange="updateContract(${idx}, 'von', this.value)">
                        </div>
                        <div>
                            <label class="text-xs text-muted block mb-1">Tỷ lệ chuyển (%)</label>
                            <input type="number" class="input" style="width: 100%; padding: 6px; background: transparent; border: 1px solid var(--border-glass); color: white; border-radius: 4px;" value="${cn.ty_le}" onchange="updateContract(${idx}, 'ty_le', this.value)">
                        </div>
                    </div>
                </div>
            `;
        });

        html += `</div></div>`; // End section 4
        
        container.innerHTML = html;
        
        // Ensure values are collected so nextStep passes validation correctly
        window.wizardState.cn2tvData = {
            company: state.company,
            ddpl_cu: state.ddplCu,
            ddpl_moi: state.ddplMoi,
            tv_cu: [state.tvCu1, state.tvCu2],
            tv_moi: [state.tvMoi1, state.tvMoi2],
            chuyen_nhuong: state.contracts
        };
    }

    // Initial render
    reRenderCN2TV();

    window.collectCN2TVData = function() {
        if (!state.company.TEN_CONG_TY_VN) {
            alert('Vui lòng nhập tên công ty!');
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
            tv_cu: [state.tvCu1, state.tvCu2],
            tv_moi: [state.tvMoi1, state.tvMoi2],
            chuyen_nhuong: state.contracts
        };
        return true;
    };

    window.triggerInlineOCR_CN2TV = function(prefix, event) {
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

                // Update state directly
                let targetObj;
                if(prefix === 'D_CU') targetObj = state.ddplCu;
                else if(prefix === 'T_CU1') targetObj = state.tvCu1;
                else if(prefix === 'T_CU2') targetObj = state.tvCu2;
                else if(prefix === 'D_MOI') targetObj = state.ddplMoi;
                else if(prefix === 'T_MOI1') targetObj = state.tvMoi1;
                else if(prefix === 'T_MOI2') targetObj = state.tvMoi2;

                if (targetObj) {
                    targetObj.HO_TEN = result.data.ho_ten || '';
                    targetObj.SO_CCCD = result.data.so_cccd || '';
                    targetObj.NGAY_SINH = result.data.ngay_sinh || '';
                    
                    let gioiTinh = result.data.gioi_tinh || '';
                    if (gioiTinh.toLowerCase().includes('việt nam')) gioiTinh = '';
                    targetObj.GIOI_TINH = gioiTinh;

                    targetObj.DIA_CHI = result.data.dia_chi || '';
                    reRenderCN2TV();
                }
            } catch(err) {
                console.error(err);
                alert('Lỗi trích xuất: ' + err.message);
                btn.innerHTML = oldHTML;
                btn.disabled = false;
            }
        };
        
        fileInput.click();
    };
};
