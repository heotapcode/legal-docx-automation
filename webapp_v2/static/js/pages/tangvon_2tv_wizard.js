// ==============================================================================
// NAC v2 - Giao diện Tăng vốn công ty TNHH 2 TV (Split-Screen & Live Dossier)
// Module độc lập - Thiết kế màn hình rộng rãi, hiển thị đầy đủ thông tin
// ==============================================================================

(function() {
    window.tangvon2tvState = {
        activeDocPreview: null
    };

    // Kiểm tra chế độ UI ưu tiên (mặc định là true nếu chưa set)
    window.isTangVon2TVNewUI = function() {
        return localStorage.getItem('tangvon_ui_mode') !== 'legacy';
    };

    window.toggleTangVonUIMode = function() {
        const current = window.isTangVon2TVNewUI();
        localStorage.setItem('tangvon_ui_mode', current ? 'legacy' : 'modern');
        
        // Điều chỉnh lại độ rộng container phù hợp với chế độ được chọn
        const parentContainer = document.getElementById('wizard-content')?.closest('.container');
        if (parentContainer) {
            if (!current) { // chuẩn bị chuyển sang modern
                parentContainer.style.maxWidth = '1520px';
                parentContainer.style.width = '96%';
            } else { // chuẩn bị chuyển sang legacy
                parentContainer.style.maxWidth = '950px';
                parentContainer.style.width = '100%';
            }
        }

        // Re-render
        if (window.wizardState && window.wizardState.step === 2) {
            const content = document.getElementById('wizard-content');
            if (content) {
                if (window.isTangVon2TVNewUI()) {
                    window.renderTangVon2TVWizard(content);
                } else {
                    if (window.wizardState.schema) {
                        window.renderStep2Form(window.wizardState.schema);
                    } else {
                        window.loadStep2Schema();
                    }
                }
            }
        }
    };

    // Hàm render chính được gọi từ wizard.js
    window.renderTangVon2TVWizard = function(container) {
        if (!container) return;

        // Mở rộng container bao ngoài để giao diện hiển thị rộng rãi, không bị gò bó 950px
        const parentContainer = container.closest('.container');
        if (parentContainer) {
            parentContainer.style.maxWidth = '1540px';
            parentContainer.style.width = '96%';
            parentContainer.style.padding = '0 20px';
        }

        // Khởi tạo dữ liệu mặc định nếu chưa có
        const fd = window.wizardState.formData = window.wizardState.formData || {};
        if (!window.wizardState.thanhVienList || window.wizardState.thanhVienList.length === 0) {
            window.wizardState.thanhVienList = [
                {
                    stt: 1,
                    ho_ten: fd.ddpl_ho_ten || '',
                    gioi_tinh: fd.ddpl_gioi_tinh || 'Nam',
                    ngay_sinh: fd.ddpl_ngay_sinh || '',
                    so_cccd: fd.ddpl_so_cccd || '',
                    dia_chi_so_nha: fd.ddpl_dia_chi_so_nha || '',
                    dia_chi_xa_phuong: fd.ddpl_dia_chi_xa_phuong || '',
                    dia_chi_tinh_thanh: fd.ddpl_dia_chi_tinh_thanh || '',
                    von_gop: '',
                    ty_le: ''
                },
                {
                    stt: 2,
                    ho_ten: '',
                    gioi_tinh: 'Nam',
                    ngay_sinh: '',
                    so_cccd: '',
                    dia_chi_so_nha: '',
                    dia_chi_xa_phuong: '',
                    dia_chi_tinh_thanh: '',
                    von_gop: '',
                    ty_le: ''
                }
            ];
        }

        const stepText = document.getElementById('wizard-step-text');
        if (stepText) {
            stepText.innerHTML = `<span>Thủ tục: <b>Tăng vốn công ty TNHH 2 TV</b> (Chế độ Split-Screen mở rộng)</span>`;
        }

        const tvList = window.wizardState.thanhVienList;

        container.innerHTML = `
            <div id="tv2-wrapper" class="tv2-container">
                <!-- Header Toolbar -->
                <div class="tv2-header-toolbar">
                    <div class="tv2-title-cluster">
                        <div class="tv2-badge"><i class="fa-solid fa-chart-line"></i> THỦ TỤC ĐĂNG KÝ TĂNG VỐN ĐIỀU LỆ</div>
                        <h2 class="tv2-main-title">Công ty TNHH Hai thành viên trở lên</h2>
                    </div>
                    <div class="tv2-actions">
                        <button type="button" class="btn btn-ghost btn-sm tv2-switch-btn" onclick="toggleTangVonUIMode()" title="Chuyển về giao diện form truyền thống">
                            <i class="fa-solid fa-rotate-left"></i> Dùng giao diện cũ
                        </button>
                    </div>
                </div>

                <!-- Split-screen Workspace -->
                <div class="tv2-workspace">
                    <!-- Left Column: Smart Form (Chiếm toàn bộ không gian rộng rãi) -->
                    <div class="tv2-form-col">
                        
                        <!-- Card 1: Doanh nghiệp & Vốn điều lệ -->
                        <div class="tv2-card">
                            <div class="tv2-card-header">
                                <div class="tv2-card-title">
                                    <i class="fa-solid fa-building text-gradient"></i>
                                    Thông tin Doanh nghiệp & Vốn điều lệ
                                </div>
                                <span class="tv2-pill-tag"><i class="fa-solid fa-bolt"></i> Tra cứu MST tự động</span>
                            </div>

                            <div class="tv2-grid-2">
                                <div class="tv2-field col-span-2">
                                    <label class="tv2-label">Mã số thuế doanh nghiệp <span class="text-error">*</span></label>
                                    <div style="display: flex; gap: 10px; align-items: center;">
                                        <input type="text" id="tv2_mst" name="ma_so_thue" value="${escapeHtml(fd.ma_so_thue || '')}" class="form-control font-mono font-bold" style="max-width: 340px; font-size: 15px;" placeholder="Nhập mã số thuế (10 hoặc 13 số)..." onkeyup="tv2Sync()">
                                        <button type="button" class="btn btn-secondary" onclick="tv2LookupMST()" id="btn-tv2-mst" style="white-space: nowrap; padding: 10px 20px; font-weight: 600;">
                                            <i class="fa-solid fa-magnifying-glass"></i> Tra cứu Tổng cục Thuế
                                        </button>
                                    </div>
                                    <div id="tv2-mst-status" style="font-size: 12.5px; margin-top: 4px;"></div>
                                </div>

                                <div class="tv2-field col-span-2">
                                    <label class="tv2-label">Tên công ty (tiếng Việt) <span class="text-error">*</span></label>
                                    <input type="text" id="tv2_ten_cong_ty" name="ten_cong_ty_vn" value="${escapeHtml(fd.ten_cong_ty_vn || '')}" class="form-control tv2-input-lg font-bold" placeholder="CÔNG TY TNHH..." onkeyup="tv2Sync()">
                                </div>

                                <div class="tv2-field col-span-2">
                                    <label class="tv2-label">Số nhà, tên đường (Trụ sở chính) <span class="text-error">*</span></label>
                                    <input type="text" id="tv2_so_nha" name="dia_chi_so_nha" value="${escapeHtml(fd.dia_chi_so_nha || '')}" class="form-control tv2-input-lg" placeholder="Số 123 đường..." onkeyup="tv2Sync()">
                                </div>

                                <div class="tv2-field">
                                    <label class="tv2-label">Xã / Phường <span class="text-error">*</span></label>
                                    <input type="text" id="tv2_xa_phuong" name="dia_chi_xa_phuong" value="${escapeHtml(fd.dia_chi_xa_phuong || '')}" class="form-control tv2-input-lg" placeholder="Phường..." onkeyup="tv2Sync()">
                                </div>

                                <div class="tv2-field">
                                    <label class="tv2-label">Tỉnh / Thành phố <span class="text-error">*</span></label>
                                    <input type="text" id="tv2_tinh_thanh" name="dia_chi_tinh_thanh" value="${escapeHtml(fd.dia_chi_tinh_thanh || '')}" class="form-control tv2-input-lg" placeholder="Thành phố..." onkeyup="tv2Sync()">
                                </div>

                                <div class="tv2-field">
                                    <label class="tv2-label">Vốn điều lệ đang đăng ký (cũ) <span class="text-error">*</span></label>
                                    <input type="text" id="tv2_von_cu" name="von_cu_so" value="${escapeHtml(fd.von_cu_so ? formatMoneyStr(fd.von_cu_so) : '')}" class="form-control font-mono tv2-input-lg" placeholder="Ví dụ: 1,000,000,000" onkeyup="handleMoneyChange(this, 'spellout-tv2-von-cu'); tv2Sync()">
                                    <div id="spellout-tv2-von-cu" class="money-spellout tv2-spellout">${fd.von_cu_so ? 'Bằng chữ: ' + (window.docSoThanhChu ? window.docSoThanhChu(fd.von_cu_so) : numToVietnameseWords(fd.von_cu_so)) : ''}</div>
                                </div>

                                <div class="tv2-field">
                                    <label class="tv2-label">Vốn điều lệ mới sau khi tăng <span class="text-error">*</span></label>
                                    <input type="text" id="tv2_von_moi" name="von_dieu_le_so" value="${escapeHtml(fd.von_dieu_le_so ? formatMoneyStr(fd.von_dieu_le_so) : '')}" class="form-control font-mono font-bold tv2-input-lg" style="border-color: var(--accent-primary);" placeholder="Ví dụ: 3,000,000,000" onkeyup="handleMoneyChange(this, 'spellout-tv2-von-moi'); tv2UpdateCapitalDistribution(); tv2Sync()">
                                    <div id="spellout-tv2-von-moi" class="money-spellout tv2-spellout" style="color: var(--accent-orange); font-weight: 600;">${fd.von_dieu_le_so ? 'Bằng chữ: ' + (window.docSoThanhChu ? window.docSoThanhChu(fd.von_dieu_le_so) : numToVietnameseWords(fd.von_dieu_le_so)) : ''}</div>
                                </div>
                            </div>

                            <!-- Live Capital Distribution Bar -->
                            <div class="tv2-distribution-wrap">
                                <div class="tv2-dist-header">
                                    <span style="font-size: 13px;">Cơ cấu vốn sau tăng: <b id="tv2-dist-total" style="color: var(--accent-primary); font-size: 14px;">0 VNĐ</b></span>
                                    <span id="tv2-dist-ratios" style="font-family: var(--font-mono); font-weight: 600; font-size: 13px; color: var(--accent-green);">Đang tính toán...</span>
                                </div>
                                <div class="tv2-bar-track" id="tv2-bar-track">
                                    <!-- Dynamic segments -->
                                </div>
                            </div>
                        </div>

                        <!-- Card 2: Người đại diện theo pháp luật -->
                        <div class="tv2-card" id="card-ddpl">
                            <div class="tv2-card-header">
                                <div class="tv2-card-title">
                                    <i class="fa-solid fa-user-tie text-gradient"></i>
                                    Người đại diện theo pháp luật
                                </div>
                                <div style="display: flex; gap: 8px; align-items: center;">
                                    <input type="file" id="tv2-ocr-ddpl-file" accept="image/*" style="display: none;" onchange="handleOcrUpload(this, 'ddpl')">
                                    <button type="button" class="btn btn-ocr" onclick="document.getElementById('tv2-ocr-ddpl-file').click()">
                                        <i class="fa-solid fa-id-card"></i> Quét ảnh VNeID
                                    </button>
                                </div>
                            </div>

                            <div class="tv2-grid-2">
                                <div class="tv2-field">
                                    <label class="tv2-label">Họ và tên <span class="text-error">*</span></label>
                                    <input type="text" name="ddpl_ho_ten" id="input-ddpl_ho_ten" value="${escapeHtml(fd.ddpl_ho_ten || '')}" class="form-control tv2-input-lg font-bold" placeholder="NGUYỄN VĂN A" onkeyup="tv2Sync()">
                                </div>

                                <div class="tv2-grid-2">
                                    <div class="tv2-field">
                                        <label class="tv2-label">Giới tính</label>
                                        <select name="ddpl_gioi_tinh" id="input-ddpl_gioi_tinh" class="form-control tv2-input-lg" onchange="tv2Sync()">
                                            <option value="Nam" ${(fd.ddpl_gioi_tinh || 'Nam') === 'Nam' ? 'selected' : ''}>Nam</option>
                                            <option value="Nữ" ${(fd.ddpl_gioi_tinh || '') === 'Nữ' ? 'selected' : ''}>Nữ</option>
                                        </select>
                                    </div>
                                    <div class="tv2-field">
                                        <label class="tv2-label">Ngày sinh</label>
                                        <input type="text" name="ddpl_ngay_sinh" id="input-ddpl_ngay_sinh" value="${escapeHtml(fd.ddpl_ngay_sinh || '')}" class="form-control tv2-input-lg" placeholder="DD/MM/YYYY" onkeyup="tv2Sync()">
                                    </div>
                                </div>

                                <div class="tv2-field">
                                    <label class="tv2-label">Số CCCD (12 số) <span class="text-error">*</span></label>
                                    <input type="text" name="ddpl_so_cccd" id="input-ddpl_so_cccd" value="${escapeHtml(fd.ddpl_so_cccd || '')}" class="form-control font-mono tv2-input-lg" placeholder="001090001234" onkeyup="tv2Sync()">
                                </div>

                                <div class="tv2-field">
                                    <label class="tv2-label">Số nhà, đường (Thường trú)</label>
                                    <input type="text" name="ddpl_dia_chi_so_nha" id="input-ddpl_dia_chi_so_nha" value="${escapeHtml(fd.ddpl_dia_chi_so_nha || '')}" class="form-control tv2-input-lg" placeholder="Số 12, đường..." onkeyup="tv2Sync()">
                                </div>

                                <div class="tv2-field">
                                    <label class="tv2-label">Xã / Phường</label>
                                    <input type="text" name="ddpl_dia_chi_xa_phuong" id="input-ddpl_dia_chi_xa_phuong" value="${escapeHtml(fd.ddpl_dia_chi_xa_phuong || '')}" class="form-control tv2-input-lg" placeholder="Xã/Phường" onkeyup="tv2Sync()">
                                </div>

                                <div class="tv2-field">
                                    <label class="tv2-label">Tỉnh / Thành phố</label>
                                    <input type="text" name="ddpl_dia_chi_tinh_thanh" id="input-ddpl_dia_chi_tinh_thanh" value="${escapeHtml(fd.ddpl_dia_chi_tinh_thanh || '')}" class="form-control tv2-input-lg" placeholder="Tỉnh/Thành phố" onkeyup="tv2Sync()">
                                </div>
                            </div>
                        </div>

                        <!-- Card 3: Danh sách Thành viên sau tăng vốn -->
                        <div class="tv2-card">
                            <div class="tv2-card-header">
                                <div class="tv2-card-title">
                                    <i class="fa-solid fa-users text-gradient"></i>
                                    Danh sách Thành viên sau tăng vốn (<span id="tv2-member-count">${tvList.length}</span>)
                                </div>
                                <button type="button" class="btn btn-secondary btn-sm" onclick="tv2AddMember()">
                                    <i class="fa-solid fa-plus"></i> Thêm thành viên
                                </button>
                            </div>

                            <div id="tv2-members-container" style="display: flex; flex-direction: column; gap: 16px;">
                                ${tvList.map((m, idx) => renderTV2MemberCard(m, idx)).join('')}
                            </div>
                        </div>
                    </div>

                    <!-- Right Column: Live Dossier Inspector (Sticky 380px) -->
                    <div class="tv2-dossier-col">
                        <div class="tv2-dossier-card">
                            <div class="tv2-dossier-header">
                                <span class="tv2-dossier-title"><i class="fa-solid fa-file-shield text-cyan"></i> Kiểm soát hồ sơ</span>
                                <span class="tv2-score" id="tv2-completeness-score">100%</span>
                            </div>

                            <!-- Progress Meter -->
                            <div class="tv2-progress-track">
                                <div class="tv2-progress-fill" id="tv2-progress-fill" style="width: 100%;"></div>
                            </div>
                            <div style="font-size: 11.5px; color: var(--text-muted); margin-bottom: 16px;">
                                Sẵn sàng tạo trọn bộ 7 văn bản hành chính theo Luật Doanh nghiệp 2020.
                            </div>

                            <!-- Document Items -->
                            <div class="tv2-doc-list">
                                <div class="tv2-doc-item" onclick="tv2PreviewDoc('01. Thông báo thay đổi ĐKKD.docx')">
                                    <div class="tv2-doc-left">
                                        <div class="tv2-doc-icon"><i class="fa-solid fa-file-word"></i></div>
                                        <div>
                                            <div class="tv2-doc-name">01. Thông báo thay đổi ĐKKD</div>
                                            <div class="tv2-doc-meta" id="tv2-meta-01">Phụ lục II-1 • Vốn sau tăng</div>
                                        </div>
                                    </div>
                                    <span class="tv2-doc-badge ready"><i class="fa-solid fa-check"></i> Đủ</span>
                                </div>

                                <div class="tv2-doc-item" onclick="tv2PreviewDoc('02. Biên bản họp.docx')">
                                    <div class="tv2-doc-left">
                                        <div class="tv2-doc-icon"><i class="fa-solid fa-file-word"></i></div>
                                        <div>
                                            <div class="tv2-doc-name">02. Biên bản họp HĐTV</div>
                                            <div class="tv2-doc-meta" id="tv2-meta-02">Biểu quyết theo tỷ lệ thành viên</div>
                                        </div>
                                    </div>
                                    <span class="tv2-doc-badge ready"><i class="fa-solid fa-check"></i> Đủ</span>
                                </div>

                                <div class="tv2-doc-item" onclick="tv2PreviewDoc('03. Quyết định.docx')">
                                    <div class="tv2-doc-left">
                                        <div class="tv2-doc-icon"><i class="fa-solid fa-file-word"></i></div>
                                        <div>
                                            <div class="tv2-doc-name">03. Quyết định HĐTV</div>
                                            <div class="tv2-doc-meta">Sửa đổi Điều 1 & Điều 6 Điều lệ</div>
                                        </div>
                                    </div>
                                    <span class="tv2-doc-badge ready"><i class="fa-solid fa-check"></i> Đủ</span>
                                </div>

                                <div class="tv2-doc-item" onclick="tv2PreviewDoc('04. Giấy ủy quyền.docx')">
                                    <div class="tv2-doc-left">
                                        <div class="tv2-doc-icon"><i class="fa-solid fa-file-word"></i></div>
                                        <div>
                                            <div class="tv2-doc-name">04. Giấy ủy quyền</div>
                                            <div class="tv2-doc-meta">Người nhận: Đỗ Quang Hiếu</div>
                                        </div>
                                    </div>
                                    <span class="tv2-doc-badge ready"><i class="fa-solid fa-check"></i> Đủ</span>
                                </div>

                                <div class="tv2-doc-item" onclick="tv2PreviewDoc('05. Danh sách chủ sở hữu hưởng lợi.docx')">
                                    <div class="tv2-doc-left">
                                        <div class="tv2-doc-icon"><i class="fa-solid fa-file-word"></i></div>
                                        <div>
                                            <div class="tv2-doc-name">05. Danh sách CSH hưởng lợi</div>
                                            <div class="tv2-doc-meta" id="tv2-meta-05">Tự động sinh theo số thành viên</div>
                                        </div>
                                    </div>
                                    <span class="tv2-doc-badge ready"><i class="fa-solid fa-check"></i> Đủ</span>
                                </div>

                                <div class="tv2-doc-item" onclick="tv2PreviewDoc('06. Danh sách thành viên.docx')">
                                    <div class="tv2-doc-left">
                                        <div class="tv2-doc-icon"><i class="fa-solid fa-file-word"></i></div>
                                        <div>
                                            <div class="tv2-doc-name">06. Danh sách thành viên</div>
                                            <div class="tv2-doc-meta">Thời hạn góp vốn: …/…/2026</div>
                                        </div>
                                    </div>
                                    <span class="tv2-doc-badge ready"><i class="fa-solid fa-check"></i> Đủ</span>
                                </div>

                                <div class="tv2-doc-item" onclick="tv2PreviewDoc('07. Giấy chứng nhận góp vốn.docx')">
                                    <div class="tv2-doc-left">
                                        <div class="tv2-doc-icon"><i class="fa-solid fa-copy"></i></div>
                                        <div>
                                            <div class="tv2-doc-name">07. GCN phần vốn góp</div>
                                            <div class="tv2-doc-meta" id="tv2-meta-07">Tách riêng từng thành viên (_a, _b...)</div>
                                        </div>
                                    </div>
                                    <span class="tv2-doc-badge ready"><i class="fa-solid fa-check"></i> Đủ</span>
                                </div>
                            </div>

                            <!-- Fast Download CTA -->
                            <button type="button" class="btn btn-primary tv2-download-btn" id="btn-tv2-generate" onclick="tv2GenerateAll()">
                                <i class="fa-solid fa-download"></i>
                                Tải trọn bộ hồ sơ (.ZIP)
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Áp dụng styles CSS mở rộng
        injectTangVonStyles();

        // Kích hoạt tính toán ban đầu
        tv2UpdateCapitalDistribution();
        tv2UpdateMeta();
    };

    // Render từng Card thành viên
    function renderTV2MemberCard(m, idx) {
        return `
            <div class="tv2-member-card" id="member-card-${idx}">
                <div class="tv2-member-header">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="tv2-member-idx">${idx + 1}</span>
                        <span style="font-weight: 700; font-size: 14px; color: var(--text-primary);">
                            Thành viên #${idx + 1} ${idx === 0 ? '<span style="font-size: 12px; color: var(--accent-primary); font-weight: normal;">(ĐDPL)</span>' : ''}
                        </span>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <input type="file" id="ocr-member-${idx}" accept="image/*" style="display: none;" onchange="handleMemberOcrUpload(this, ${idx})">
                        <button type="button" class="btn btn-ocr btn-sm" onclick="document.getElementById('ocr-member-${idx}').click()" style="padding: 4px 10px; font-size: 12px;">
                            <i class="fa-solid fa-id-card"></i> VNeID
                        </button>
                        ${idx >= 2 ? `
                            <button type="button" class="btn btn-ghost btn-sm text-error" onclick="tv2RemoveMember(${idx})" style="padding: 4px 8px;">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>

                <div class="tv2-grid-2">
                    <div class="tv2-field">
                        <label class="tv2-label">Họ và tên <span class="text-error">*</span></label>
                        <input type="text" class="form-control m-field tv2-input-lg font-bold" data-idx="${idx}" data-prop="ho_ten" value="${escapeHtml(m.ho_ten || '')}" placeholder="NGUYỄN VĂN A" onkeyup="tv2Sync()">
                    </div>

                    <div class="tv2-grid-2">
                        <div class="tv2-field">
                            <label class="tv2-label">Giới tính</label>
                            <select class="form-control m-field tv2-input-lg" data-idx="${idx}" data-prop="gioi_tinh" onchange="tv2Sync()">
                                <option value="Nam" ${(m.gioi_tinh || 'Nam') === 'Nam' ? 'selected' : ''}>Nam</option>
                                <option value="Nữ" ${(m.gioi_tinh || '') === 'Nữ' ? 'selected' : ''}>Nữ</option>
                            </select>
                        </div>
                        <div class="tv2-field">
                            <label class="tv2-label">Ngày sinh</label>
                            <input type="text" class="form-control m-field tv2-input-lg" data-idx="${idx}" data-prop="ngay_sinh" value="${escapeHtml(m.ngay_sinh || '')}" placeholder="DD/MM/YYYY" onkeyup="tv2Sync()">
                        </div>
                    </div>

                    <div class="tv2-field">
                        <label class="tv2-label">Số CCCD (12 số) <span class="text-error">*</span></label>
                        <input type="text" class="form-control m-field font-mono tv2-input-lg" data-idx="${idx}" data-prop="so_cccd" value="${escapeHtml(m.so_cccd || '')}" placeholder="001090001234" onkeyup="tv2Sync()">
                    </div>

                    <div class="tv2-field">
                        <label class="tv2-label">Số nhà, tên đường</label>
                        <input type="text" class="form-control m-field tv2-input-lg" data-idx="${idx}" data-prop="dia_chi_so_nha" value="${escapeHtml(m.dia_chi_so_nha || '')}" placeholder="Số nhà..." onkeyup="tv2Sync()">
                    </div>

                    <div class="tv2-field">
                        <label class="tv2-label">Xã / Phường</label>
                        <input type="text" class="form-control m-field tv2-input-lg" data-idx="${idx}" data-prop="dia_chi_xa_phuong" value="${escapeHtml(m.dia_chi_xa_phuong || '')}" placeholder="Xã/Phường" onkeyup="tv2Sync()">
                    </div>

                    <div class="tv2-field">
                        <label class="tv2-label">Tỉnh / Thành phố</label>
                        <input type="text" class="form-control m-field tv2-input-lg" data-idx="${idx}" data-prop="dia_chi_tinh_thanh" value="${escapeHtml(m.dia_chi_tinh_thanh || '')}" placeholder="Tỉnh/Thành phố" onkeyup="tv2Sync()">
                    </div>

                    <div class="tv2-field">
                        <label class="tv2-label">Vốn góp mới (VNĐ) <span class="text-error">*</span></label>
                        <input type="text" class="form-control m-field font-mono tv2-input-lg font-bold" data-idx="${idx}" data-prop="von_gop" value="${escapeHtml(m.von_gop ? formatMoneyStr(m.von_gop) : '')}" placeholder="1,000,000,000" onkeyup="handleMemberMoneyChange(this); tv2RecalcRatio(${idx}); tv2Sync()">
                    </div>

                    <div class="tv2-field">
                        <label class="tv2-label">Tỷ lệ góp vốn (%) <span class="text-error">*</span></label>
                        <input type="number" class="form-control m-field font-mono tv2-input-lg font-bold" data-idx="${idx}" data-prop="ty_le" value="${escapeHtml(m.ty_le || '')}" placeholder="Tỷ lệ %" onkeyup="tv2UpdateCapitalDistribution(); tv2Sync()">
                    </div>
                </div>
            </div>
        `;
    }

    // Tra cứu MST tự động
    window.tv2LookupMST = async function() {
        const mstInp = document.getElementById('tv2_mst');
        const statusEl = document.getElementById('tv2-mst-status');
        const btn = document.getElementById('btn-tv2-mst');
        if (!mstInp || !mstInp.value) {
            alert('Vui lòng nhập Mã số thuế trước khi tra cứu.');
            return;
        }

        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Tra cứu...';
        btn.disabled = true;

        try {
            const res = await fetch(`/api/mst/${encodeURIComponent(mstInp.value.trim())}`);
            const result = await res.json();
            if (result.success && result.data && result.data.name) {
                const data = result.data;
                statusEl.innerHTML = `<span class="text-success"><i class="fa-solid fa-check"></i> Đã tìm thấy: <b>${escapeHtml(data.name)}</b></span>`;

                const nameEl = document.getElementById('tv2_ten_cong_ty');
                if (nameEl) {
                    nameEl.value = data.name;
                    nameEl.style.borderColor = 'var(--accent-green)';
                }

                if (data.address) {
                    const parts = data.address.split(',').map(p => p.trim());
                    const tinh = parts.length > 0 ? parts.pop() : '';
                    const xa = parts.length > 0 ? parts.pop() : '';
                    const sonha = parts.join(', ');

                    const snEl = document.getElementById('tv2_so_nha');
                    const xpEl = document.getElementById('tv2_xa_phuong');
                    const ttEl = document.getElementById('tv2_tinh_thanh');

                    if (snEl) snEl.value = sonha;
                    if (xpEl) xpEl.value = xa;
                    if (ttEl) ttEl.value = tinh;
                }

                tv2Sync();
            } else {
                statusEl.innerHTML = `<span class="text-warning"><i class="fa-solid fa-circle-exclamation"></i> Không tìm thấy dữ liệu từ Tổng cục Thuế. Vui lòng điền tay.</span>`;
            }
        } catch (err) {
            console.error(err);
            statusEl.innerHTML = `<span class="text-error">Lỗi kết nối tra cứu MST.</span>`;
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    };

    // Tự động tính tỷ lệ % khi nhập vốn góp của thành viên
    window.tv2RecalcRatio = function(idx) {
        const vonMoiEl = document.getElementById('tv2_von_moi');
        if (!vonMoiEl) return;
        const totalNum = parseInt(vonMoiEl.value.replace(/\D/g, '') || 0, 10);
        if (totalNum > 0) {
            const mCard = document.getElementById(`member-card-${idx}`);
            if (mCard) {
                const vgInp = mCard.querySelector('[data-prop="von_gop"]');
                const tlInp = mCard.querySelector('[data-prop="ty_le"]');
                if (vgInp && tlInp) {
                    const vgNum = parseInt(vgInp.value.replace(/\D/g, '') || 0, 10);
                    if (vgNum > 0) {
                        const r = ((vgNum / totalNum) * 100).toFixed(1).replace('.0', '');
                        tlInp.value = r;
                    }
                }
            }
        }
        tv2UpdateCapitalDistribution();
    };

    // Cập nhật thanh phân bổ vốn trực quan
    window.tv2UpdateCapitalDistribution = function() {
        const vonMoiEl = document.getElementById('tv2_von_moi');
        const track = document.getElementById('tv2-bar-track');
        const totalText = document.getElementById('tv2-dist-total');
        const ratiosText = document.getElementById('tv2-dist-ratios');
        if (!vonMoiEl || !track) return;

        const totalNum = parseInt(vonMoiEl.value.replace(/\D/g, '') || 0, 10);
        totalText.innerText = totalNum > 0 ? Number(totalNum).toLocaleString('vi-VN') + ' VNĐ' : '0 VNĐ';

        const mCards = document.querySelectorAll('.tv2-member-card');
        const colors = ['#f97316', '#10b981', '#0ea5e9', '#8b5cf6', '#ec4899', '#f59e0b'];
        let segmentsHtml = '';
        let ratioStrings = [];

        mCards.forEach((c, idx) => {
            const tlInp = c.querySelector('[data-prop="ty_le"]');
            const nameInp = c.querySelector('[data-prop="ho_ten"]');
            const val = parseFloat(tlInp ? tlInp.value : 0) || 0;
            const name = nameInp && nameInp.value ? nameInp.value.trim() : `TV #${idx + 1}`;
            const color = colors[idx % colors.length];

            if (val > 0) {
                segmentsHtml += `<div style="width: ${val}%; height: 100%; background: ${color}; transition: width 0.3s;" title="${name}: ${val}%"></div>`;
                ratioStrings.push(`<span style="color: ${color};">${val}% ${name}</span>`);
            }
        });

        track.innerHTML = segmentsHtml || `<div style="width: 100%; height: 100%; background: var(--border-glass);"></div>`;
        ratiosText.innerHTML = ratioStrings.join(' — ') || 'Chưa nhập đủ tỷ lệ';
        tv2UpdateMeta();
    };

    // Thêm thành viên động
    window.tv2AddMember = function() {
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
        const container = document.getElementById('wizard-content');
        if (container) {
            window.renderTangVon2TVWizard(container);
        }
    };

    // Xóa thành viên
    window.tv2RemoveMember = function(idx) {
        collectFormData();
        window.wizardState.thanhVienList.splice(idx, 1);
        const container = document.getElementById('wizard-content');
        if (container) {
            window.renderTangVon2TVWizard(container);
        }
    };

    // Đồng bộ tức thời dữ liệu sang wizardState.formData và wizardState.thanhVienList
    window.tv2Sync = function() {
        const fd = window.wizardState.formData;
        const setVal = (id, prop) => {
            const el = document.getElementById(id);
            if (el) fd[prop] = el.value;
        };

        setVal('tv2_mst', 'ma_so_thue');
        setVal('tv2_ten_cong_ty', 'ten_cong_ty_vn');
        setVal('tv2_so_nha', 'dia_chi_so_nha');
        setVal('tv2_xa_phuong', 'dia_chi_xa_phuong');
        setVal('tv2_tinh_thanh', 'dia_chi_tinh_thanh');
        setVal('tv2_von_cu', 'von_cu_so');
        setVal('tv2_von_moi', 'von_dieu_le_so');

        setVal('input-ddpl_ho_ten', 'ddpl_ho_ten');
        setVal('input-ddpl_gioi_tinh', 'ddpl_gioi_tinh');
        setVal('input-ddpl_ngay_sinh', 'ddpl_ngay_sinh');
        setVal('input-ddpl_so_cccd', 'ddpl_so_cccd');
        setVal('input-ddpl_dia_chi_so_nha', 'ddpl_dia_chi_so_nha');
        setVal('input-ddpl_dia_chi_xa_phuong', 'ddpl_dia_chi_xa_phuong');
        setVal('input-ddpl_dia_chi_tinh_thanh', 'ddpl_dia_chi_tinh_thanh');

        // Đồng bộ thành viên
        const mCards = document.querySelectorAll('.tv2-member-card');
        mCards.forEach((c, idx) => {
            if (window.wizardState.thanhVienList[idx]) {
                const props = ['ho_ten', 'gioi_tinh', 'ngay_sinh', 'so_cccd', 'dia_chi_so_nha', 'dia_chi_xa_phuong', 'dia_chi_tinh_thanh', 'von_gop', 'ty_le'];
                props.forEach(p => {
                    const inp = c.querySelector(`[data-prop="${p}"]`);
                    if (inp) {
                        window.wizardState.thanhVienList[idx][p] = inp.value;
                    }
                });
            }
        });

        tv2UpdateMeta();
    };

    function tv2UpdateMeta() {
        const vm = document.getElementById('tv2_von_moi');
        const meta01 = document.getElementById('tv2-meta-01');
        if (meta01 && vm) {
            meta01.innerText = `Phụ lục II-1 • Vốn sau tăng: ${vm.value || 'Chưa nhập'}`;
        }
        const mCount = window.wizardState.thanhVienList.length;
        const meta05 = document.getElementById('tv2-meta-05');
        if (meta05) meta05.innerText = `Tự động sinh ${mCount} dòng CSHHL`;
        const meta07 = document.getElementById('tv2-meta-07');
        if (meta07) meta07.innerText = `Tách riêng ${mCount} file GCN (_a, _b...)`;
        tv2UpdateCompleteness();
    }

    // Tính % hoàn thiện thật từ các trường bắt buộc trong _schema.json
    function tv2UpdateCompleteness() {
        if (!window.validateRequiredFields) return;
        const errors = window.validateRequiredFields(window.wizardState.schema);
        const total = errors.total || 0;
        const pct = total ? Math.round(((total - errors.length) / total) * 100) : 100;
        const score = document.getElementById('tv2-completeness-score');
        const fill = document.getElementById('tv2-progress-fill');
        if (score) score.innerText = `${pct}%`;
        if (fill) fill.style.width = `${pct}%`;
        const ready = errors.length === 0;
        document.querySelectorAll('.tv2-doc-badge').forEach(b => {
            b.classList.toggle('ready', ready);
            b.classList.toggle('pending', !ready);
            b.innerHTML = ready ? '<i class="fa-solid fa-check"></i> Đủ' : '<i class="fa-solid fa-hourglass-half"></i> Thiếu';
        });
    }
    window.tv2UpdateCompleteness = tv2UpdateCompleteness;

    // Xem trước thông tin tài liệu
    window.tv2PreviewDoc = function(docName) {
        tv2Sync();
        const fd = window.wizardState.formData;
        const cty = fd.ten_cong_ty_vn || '(Chưa nhập tên công ty)';
        const von = fd.von_dieu_le_so || '(Chưa nhập vốn mới)';
        alert(`THÔNG TIN VĂN BẢN: ${docName}\n\n- Doanh nghiệp: ${cty}\n- Vốn mới: ${von} VNĐ\n- Thành viên: ${window.wizardState.thanhVienList.length} người\n- Trạng thái: Sẵn sàng render 100%`);
    };

    // Tải trọn bộ hồ sơ ZIP trực tiếp
    window.tv2GenerateAll = async function() {
        tv2Sync();
        if (window.ensureRequiredFields && !window.ensureRequiredFields()) return;
        const btn = document.getElementById('btn-tv2-generate');
        const oldText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang khởi tạo hồ sơ...';
        btn.disabled = true;

        try {
            const payload = {
                template_name: 'Tăng vốn công ty TNHH 2 TV',
                data: {
                    ...window.wizardState.formData,
                    thanh_vien: window.wizardState.thanhVienList
                },
                ma_nganh: [],
                special_payload: {}
            };

            const res = await fetch('/api/documents/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Lỗi khi tạo tài liệu');
            }

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Ho_so_Tang_von_cong_ty_TNHH_2_TV.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            btn.innerHTML = '<i class="fa-solid fa-circle-check text-success"></i> Đã tải hồ sơ thành công!';
            setTimeout(() => {
                btn.innerHTML = oldText;
                btn.disabled = false;
            }, 3000);
        } catch (err) {
            console.error(err);
            alert('Có lỗi khi tạo tài liệu: ' + err.message);
            btn.innerHTML = oldText;
            btn.disabled = false;
        }
    };

    // Tự động inject CSS cho giao diện mới
    function injectTangVonStyles() {
        if (document.getElementById('tv2-custom-styles')) return;
        const style = document.createElement('style');
        style.id = 'tv2-custom-styles';
        style.textContent = `
            .tv2-container {
                width: 100%;
                max-width: 100%;
                margin: 0 auto;
                padding-bottom: 60px;
            }
            .tv2-header-toolbar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 22px;
                padding: 14px 22px;
                background: var(--bg-card);
                border: 1px solid var(--border-glass);
                border-radius: var(--radius-lg);
            }
            .tv2-title-cluster {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .tv2-badge {
                font-size: 11px;
                font-weight: 800;
                color: var(--accent-primary);
                text-transform: uppercase;
                letter-spacing: 0.6px;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            .tv2-main-title {
                font-size: 19px;
                font-weight: 800;
                color: var(--text-primary);
                margin: 0;
            }
            .tv2-workspace {
                display: grid;
                grid-template-columns: minmax(0, 1fr) 380px;
                gap: 28px;
                align-items: start;
            }
            @media (max-width: 1100px) {
                .tv2-workspace { grid-template-columns: 1fr; }
                .tv2-dossier-col { position: static; }
            }
            .tv2-form-col {
                display: flex;
                flex-direction: column;
                gap: 22px;
            }
            .tv2-card {
                background: var(--bg-card);
                border: 1px solid var(--border-glass);
                border-radius: var(--radius-lg);
                padding: 26px 28px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.25);
            }
            .tv2-card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
                padding-bottom: 14px;
                border-bottom: 1px solid var(--border-glass);
            }
            .tv2-card-title {
                font-size: 16px;
                font-weight: 700;
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .tv2-pill-tag {
                background: rgba(16, 185, 129, 0.15);
                color: var(--accent-green);
                font-size: 11.5px;
                font-weight: 700;
                padding: 4px 10px;
                border-radius: var(--radius-full);
            }
            .tv2-grid-2 {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px 20px;
            }
            .tv2-field {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            .tv2-label {
                font-size: 13.5px;
                font-weight: 600;
                color: var(--text-secondary);
                letter-spacing: 0.2px;
            }
            .tv2-input-lg {
                padding: 11px 15px !important;
                font-size: 14.5px !important;
                border-radius: var(--radius-md) !important;
            }
            .tv2-spellout {
                font-size: 12.5px;
                margin-top: 4px;
            }
            .tv2-distribution-wrap {
                margin-top: 18px;
                background: rgba(0,0,0,0.25);
                border: 1px solid var(--border-glass);
                border-radius: var(--radius-md);
                padding: 14px 18px;
            }
            .tv2-dist-header {
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 10px;
            }
            .tv2-bar-track {
                height: 12px;
                background: rgba(255,255,255,0.06);
                border-radius: var(--radius-full);
                overflow: hidden;
                display: flex;
            }
            .tv2-member-card {
                background: rgba(0,0,0,0.22);
                border: 1px solid var(--border-glass);
                border-radius: var(--radius-md);
                padding: 18px 20px;
            }
            .tv2-member-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 14px;
            }
            .tv2-member-idx {
                background: var(--accent-primary);
                color: #fff;
                width: 24px;
                height: 24px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border-radius: var(--radius-full);
                font-size: 12px;
                font-weight: 800;
            }
            .tv2-dossier-col {
                position: sticky;
                top: 80px;
                height: fit-content;
            }
            .tv2-dossier-card {
                background: var(--bg-card);
                border: 1px solid var(--border-glass);
                border-radius: var(--radius-lg);
                padding: 22px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.3);
            }
            .tv2-dossier-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            .tv2-dossier-title {
                font-size: 15px;
                font-weight: 700;
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .tv2-score {
                font-family: var(--font-mono);
                font-size: 15px;
                font-weight: 700;
                color: var(--accent-green);
            }
            .tv2-progress-track {
                height: 7px;
                background: rgba(255,255,255,0.08);
                border-radius: var(--radius-full);
                overflow: hidden;
                margin-bottom: 8px;
            }
            .tv2-progress-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--accent-green) 0%, #34d399 100%);
                border-radius: var(--radius-full);
            }
            .tv2-doc-list {
                display: flex;
                flex-direction: column;
                gap: 9px;
                margin-top: 14px;
                margin-bottom: 18px;
            }
            .tv2-doc-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 11px 13px;
                background: rgba(0,0,0,0.22);
                border: 1px solid var(--border-glass);
                border-radius: var(--radius-sm);
                cursor: pointer;
                transition: all 0.2s;
            }
            .tv2-doc-item:hover {
                border-color: var(--accent-primary);
                background: rgba(249, 115, 22, 0.08);
                transform: translateX(4px);
            }
            .tv2-doc-left {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            .tv2-doc-icon {
                color: #38bdf8;
                font-size: 15px;
            }
            .tv2-doc-name {
                font-size: 12.5px;
                font-weight: 600;
                color: var(--text-primary);
            }
            .tv2-doc-meta {
                font-size: 11px;
                color: var(--text-muted);
            }
            .tv2-doc-badge {
                font-size: 10.5px;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: var(--radius-full);
            }
            .tv2-doc-badge.pending {
                background: rgba(245, 158, 11, 0.15);
                color: var(--accent-yellow, #f59e0b);
            }
            .tv2-doc-badge.ready {
                background: rgba(16, 185, 129, 0.15);
                color: var(--accent-green);
            }
            .tv2-download-btn {
                width: 100%;
                padding: 14px;
                font-weight: 700;
                font-size: 14.5px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                box-shadow: 0 4px 18px rgba(249, 115, 22, 0.35);
            }
        `;
        document.head.appendChild(style);
    }
})();
