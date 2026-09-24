// ==============================================================================
// NAC v2 - Harvey Legal Tech Executive Landing Portal (With Navigation Sidebar)
// ==============================================================================

function renderLanding() {
    const isHarvey = window.isGlobalModernUI ? window.isGlobalModernUI() : true;

    if (!isHarvey) {
        // Legacy marketing landing page
        return `
            <nav class="navbar">
                <div class="container navbar-container">
                    <a href="#/" class="navbar-brand">
                        <i class="fa-solid fa-building text-gradient"></i> NAC
                    </a>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <button type="button" class="btn btn-secondary btn-sm" onclick="toggleGlobalUIMode()">
                            <i class="fa-solid fa-scale-balanced" style="color: #d4af37;"></i> Dùng giao diện Harvey
                        </button>
                        <a href="#/wizard" class="btn btn-primary btn-sm">Tạo hồ sơ ngay</a>
                    </div>
                </div>
            </nav>

            <section class="hero" style="min-height: 85vh; display: flex; align-items: center;">
                <div class="container grid-2" style="align-items: center;">
                    <div class="hero-content">
                        <span class="badge mb-4">🚀 Công nghệ AI Mới Nhất 2026</span>
                        <h1 class="mb-4" style="font-size: var(--font-size-5xl); font-weight: 800; line-height: 1.2;">
                            Tạo Hồ Sơ Doanh Nghiệp<br>
                            <span class="text-gradient">Trong 5 Phút Với AI</span>
                        </h1>
                        <p class="text-secondary text-lg mb-8" style="max-width: 90%;">
                            Chỉ cần chụp ảnh VNeID — AI tự động điền thông tin. Hỗ trợ 19 loại thủ tục ĐKKD. Tải ngay bộ hồ sơ hoàn chỉnh.
                        </p>
                        <div style="display: flex; gap: var(--space-4); margin-bottom: var(--space-8);">
                            <a href="#/wizard" class="btn btn-primary">
                                <i class="fa-solid fa-robot"></i> Bắt đầu soạn thảo
                            </a>
                        </div>
                    </div>
                </div>
            </section>
        `;
    }

    // HARVEY LEGAL TECH EXECUTIVE PORTAL WITH NAVIGATION SIDEBAR
    return `
        <div class="harvey-app-shell">
            <!-- 1. Left Executive Navigation Sidebar -->
            <aside class="harvey-sidebar">
                <div class="harvey-sidebar-brand">
                    <div class="harvey-seal-logo"><i class="fa-solid fa-scale-balanced"></i></div>
                    <div style="display: flex; flex-direction: column;">
                        <span class="harvey-brand-title">HARVEY LEGAL OS</span>
                        <span class="harvey-brand-tag">Executive Studio</span>
                    </div>
                </div>

                <nav class="harvey-sidebar-nav" id="landing-sidebar-nav">
                    <div class="text-center py-6 text-sm" style="color: var(--harvey-text-muted);">
                        <i class="fa-solid fa-spinner fa-spin"></i> Đang nạp danh mục...
                    </div>
                </nav>

                <div class="harvey-sidebar-footer">
                    <div class="harvey-pulse-dot"></div>
                    <div style="font-size: 11.5px;">
                        <div style="color: var(--gold-light); font-weight: 600;">Jinja2 Engine Active</div>
                        <div style="color: var(--harvey-text-muted); font-size: 10.5px;">Cổng 8002 &bull; Thẩm định tự động</div>
                    </div>
                </div>
            </aside>

            <!-- 2. Main Executive App Area -->
            <div class="harvey-main-area">
                <!-- Top Command Bar -->
                <header class="harvey-topbar">
                    <div class="harvey-breadcrumbs">
                        <span style="color: var(--harvey-text-muted);">Pháp nhân</span>
                        <span style="color: var(--gold-primary);">/</span>
                        <span style="color: var(--harvey-text-heading); font-weight: 600;">Trung tâm Điều hành Pháp lý Doanh nghiệp</span>
                    </div>

                    <div class="harvey-search-bar" onclick="const inp = document.getElementById('landing-global-search'); if(inp) inp.focus();">
                        <i class="fa-solid fa-magnifying-glass" style="color: var(--gold-primary);"></i>
                        <input type="text" id="landing-global-search" placeholder="Tra cứu thủ tục, MST, mã ngành..." style="background: transparent; border: none; outline: none; color: #fff; width: 100%; font-size: 12.5px;" onkeyup="filterLandingProcedures(this.value)">
                        <span style="font-family: var(--font-mono); font-size: 10.5px; background: rgba(212, 175, 55, 0.1); color: var(--gold-primary); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(212, 175, 55, 0.25);">⌘K</span>
                    </div>

                    <div style="display: flex; align-items: center; gap: 12px;">
                        <button type="button" class="btn harvey-btn-ghost btn-sm" onclick="toggleGlobalUIMode()" title="Chuyển về giao diện giới thiệu cũ">
                            <i class="fa-solid fa-rotate-left"></i> Giao diện cũ
                        </button>
                        <a href="#/wizard" class="btn harvey-btn-gold btn-sm"><i class="fa-solid fa-wand-magic-sparkles"></i> Tạo hồ sơ ngay</a>
                    </div>
                </header>

                <!-- Workspace Scroll Body -->
                <main class="harvey-workspace">
                    <!-- Executive Hero Banner -->
                    <div class="hero-banner-line">
                        <div>
                            <div class="hero-citation">
                                <i class="fa-solid fa-certificate"></i> NGHỊ ĐỊNH 01/2021/NĐ-CP &bull; LUẬT DOANH NGHIỆP 2020
                            </div>
                            <h1 class="hero-heading" style="font-size: 28px;">Trung Tâm Soạn Thảo & Thẩm Định Hồ Sơ Doanh Nghiệp</h1>
                            <p class="hero-subtext">Hệ thống pháp lý tự động hóa cao cấp: tra cứu Tổng cục Thuế, nhận diện thẻ VNeID, tự động cân đối vốn điều lệ và khởi tạo trọn bộ hồ sơ Word (.docx) chuẩn hóa.</p>
                        </div>
                        <div>
                            <span class="legal-seal-badge" style="padding: 6px 14px; font-size: 11.5px;">
                                <i class="fa-solid fa-award"></i> 19 BỘ THỦ TỤC ĐÃ ĐƯỢC CHUẨN HÓA
                            </span>
                        </div>
                    </div>

                    <!-- Executive KPI Strip -->
                    <div class="harvey-kpi-grid">
                        <div class="harvey-kpi-card">
                            <div>
                                <div class="kpi-label">QUY TRÌNH DOANH NGHIỆP</div>
                                <div class="harvey-kpi-num">19 Bộ Thủ Tục</div>
                                <div style="font-size: 11px; color: var(--status-green); margin-top: 3px;"><i class="fa-solid fa-check"></i> Đầy đủ biểu mẫu Sở KH&ĐT</div>
                            </div>
                            <div class="kpi-icon-box" style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: rgba(212, 175, 55, 0.08); border: 1px solid var(--gold-border-subtle); display: flex; align-items: center; justify-content: center; color: var(--gold-primary); font-size: 15px;"><i class="fa-solid fa-folder-tree"></i></div>
                        </div>

                        <div class="harvey-kpi-card">
                            <div>
                                <div class="kpi-label">TỐC ĐỘ BIÊN DỊCH</div>
                                <div class="harvey-kpi-num">~0.85s / Bộ</div>
                                <div style="font-size: 11px; color: var(--gold-primary); margin-top: 3px;"><i class="fa-solid fa-bolt"></i> docxtpl Jinja2 siêu tốc</div>
                            </div>
                            <div class="kpi-icon-box" style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: rgba(212, 175, 55, 0.08); border: 1px solid var(--gold-border-subtle); display: flex; align-items: center; justify-content: center; color: var(--gold-primary); font-size: 15px;"><i class="fa-solid fa-gauge-high"></i></div>
                        </div>

                        <div class="harvey-kpi-card">
                            <div>
                                <div class="kpi-label">CHUẨN MỰC PHÁP LÝ</div>
                                <div class="harvey-kpi-num">100% Khớp Luật</div>
                                <div style="font-size: 11px; color: var(--status-green); margin-top: 3px;"><i class="fa-solid fa-shield-halved"></i> Căn cứ Nghị định 01/2021</div>
                            </div>
                            <div class="kpi-icon-box" style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: rgba(212, 175, 55, 0.08); border: 1px solid var(--gold-border-subtle); display: flex; align-items: center; justify-content: center; color: var(--gold-primary); font-size: 15px;"><i class="fa-solid fa-scale-balanced"></i></div>
                        </div>

                        <div class="harvey-kpi-card">
                            <div>
                                <div class="kpi-label">XÁC THỰC DANH TÍNH</div>
                                <div class="harvey-kpi-num">VNeID / CCCD</div>
                                <div style="font-size: 11px; color: var(--gold-primary); margin-top: 3px;"><i class="fa-solid fa-id-card"></i> AI OCR chống lỗi sai</div>
                            </div>
                            <div class="kpi-icon-box" style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: rgba(212, 175, 55, 0.08); border: 1px solid var(--gold-border-subtle); display: flex; align-items: center; justify-content: center; color: var(--gold-primary); font-size: 15px;"><i class="fa-solid fa-fingerprint"></i></div>
                        </div>
                    </div>

                    <!-- Executive 3-Step Workflow -->
                    <div class="harvey-card" style="margin-bottom: 28px; background: rgba(13, 21, 42, 0.7);">
                        <div class="card-header-bar" style="margin-bottom: 16px;">
                            <div class="card-title">
                                <i class="fa-solid fa-diagram-project"></i>
                                <span>Quy Trình Tự Động Hóa 3 Bước Chuẩn Harvey</span>
                            </div>
                            <span class="legal-seal-badge">EXECUTIVE WORKFLOW</span>
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                            <div style="background: rgba(6, 10, 20, 0.5); padding: 18px 20px; border-radius: var(--radius-md); border: 1px solid var(--gold-border-subtle);">
                                <div style="font-size: 12px; font-weight: 700; color: var(--gold-primary); margin-bottom: 6px; font-family: var(--font-mono);">BƯỚC 01 &bull; KHỞI TẠO</div>
                                <h4 style="font-family: var(--font-serif); font-size: 15.5px; color: #fff; margin-bottom: 6px;">Tra cứu Thuế & Quét VNeID</h4>
                                <p style="font-size: 12.5px; color: var(--harvey-text-body); margin: 0;">Nhập mã số thuế để đồng bộ tên công ty, địa chỉ từ Tổng cục Thuế. Quét thẻ CCCD để tự động điền ĐDPL và các thành viên sáng lập.</p>
                            </div>

                            <div style="background: rgba(6, 10, 20, 0.5); padding: 18px 20px; border-radius: var(--radius-md); border: 1px solid var(--gold-border-subtle);">
                                <div style="font-size: 12px; font-weight: 700; color: var(--gold-primary); margin-bottom: 6px; font-family: var(--font-mono);">BƯỚC 02 &bull; CÂN ĐỐI</div>
                                <h4 style="font-family: var(--font-serif); font-size: 15.5px; color: #fff; margin-bottom: 6px;">Cân Đối Vốn & Thẩm Định</h4>
                                <p style="font-size: 12.5px; color: var(--harvey-text-body); margin: 0;">Thanh phân bổ vốn thông minh tự động tính tỷ lệ % sở hữu, kiểm tra chéo tính hợp lệ 100% của vốn điều lệ trước khi tạo file.</p>
                            </div>

                            <div style="background: rgba(6, 10, 20, 0.5); padding: 18px 20px; border-radius: var(--radius-md); border: 1px solid var(--gold-border-subtle);">
                                <div style="font-size: 12px; font-weight: 700; color: var(--gold-primary); margin-bottom: 6px; font-family: var(--font-mono);">BƯỚC 03 &bull; BIÊN DỊCH</div>
                                <h4 style="font-family: var(--font-serif); font-size: 15.5px; color: #fff; margin-bottom: 6px;">Xuất Bộ Hồ Sơ Word (.ZIP)</h4>
                                <p style="font-size: 12.5px; color: var(--harvey-text-body); margin: 0;">Engine docxtpl tạo ngay toàn bộ các văn bản Word (.docx) chuẩn hóa (Điều lệ, Thông báo, Biên bản họp...) và đóng gói thành 1 file ZIP duy nhất.</p>
                            </div>
                        </div>
                    </div>

                    <!-- Procedures Directory Section -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
                        <div>
                            <h3 style="font-family: var(--font-serif); font-size: 20px; font-weight: 600; color: var(--gold-light); margin: 0;">Bảng Danh Mục 19 Quy Trình Thủ Tục ĐKKD</h3>
                            <p style="font-size: 12.5px; color: var(--harvey-text-muted); margin: 2px 0 0 0;">Chọn thủ tục bất kỳ bên dưới hoặc từ thanh Sidebar để bắt đầu soạn thảo</p>
                        </div>
                        <a href="#/wizard" class="btn harvey-btn-gold"><i class="fa-solid fa-play"></i> Bắt đầu soạn thảo &rarr;</a>
                    </div>

                    <div id="landing-procedures-grid" style="display: flex; flex-direction: column; gap: 20px;">
                        <div class="text-center py-10" style="color: var(--harvey-text-muted);">
                            <i class="fa-solid fa-spinner fa-spin fa-2x" style="color: var(--gold-primary);"></i>
                            <div class="mt-3">Đang đồng bộ 19 bộ thủ tục...</div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    `;
}

window.initLandingHarvey = async function() {
    if (!window.isGlobalModernUI || !window.isGlobalModernUI()) return;

    try {
        const res = await fetch('/api/templates');
        if (res.ok) {
            const data = await res.json();
            window.allTemplatesCache = data.templates || [];
            renderLandingProcedures(data.templates);
            renderLandingSidebar(data.templates);
        }
    } catch (err) {
        console.error('Lỗi nạp danh mục thủ tục tại trang chủ:', err);
    }
};

function renderLandingSidebar(templates) {
    const nav = document.getElementById('landing-sidebar-nav');
    if (!nav || !templates) return;

    const categories = [...new Set(templates.map(t => t.category || 'Khác'))];
    let html = '';

    categories.forEach(cat => {
        const items = templates.filter(t => (t.category || 'Khác') === cat);
        html += `<div class="harvey-nav-group-title">${cat}</div>`;
        items.forEach(item => {
            html += `
                <a class="harvey-nav-item" onclick="startProcedure('${escapeHtml(item.name)}')">
                    <i class="fa-solid fa-file-contract"></i>
                    <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(item.display_name)}</span>
                    <span class="harvey-nav-badge">${item.file_count || 5}</span>
                </a>
            `;
        });
    });

    html += `
        <div class="harvey-nav-group-title" style="margin-top: 14px;">Quản trị Pháp lý</div>
        <a class="harvey-nav-item" onclick="if (window.showToast) window.showToast('Kho dữ liệu Doanh nghiệp & CCCD'); else alert('Kho dữ liệu Doanh nghiệp');">
            <i class="fa-solid fa-building-user"></i>
            <span>Kho Pháp nhân & CCCD</span>
        </a>
        <a class="harvey-nav-item" onclick="if (window.showToast) window.showToast('19 bộ biểu mẫu chuẩn hóa ĐKKD'); else alert('19 bộ biểu mẫu chuẩn hóa ĐKKD');">
            <i class="fa-solid fa-file-word"></i>
            <span>Mẫu biểu chuẩn (19 bộ)</span>
        </a>
    `;

    nav.innerHTML = html;
}

function renderLandingProcedures(templates) {
    const grid = document.getElementById('landing-procedures-grid');
    if (!grid || !templates) return;

    const categories = [...new Set(templates.map(t => t.category || 'Khác'))];
    let html = '';

    categories.forEach(cat => {
        const items = templates.filter(t => (t.category || 'Khác') === cat);
        html += `
            <div class="landing-cat-group">
                <div style="font-family: var(--font-serif); font-size: 16px; font-weight: 600; color: var(--gold-light); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-folder-open" style="color: var(--gold-primary);"></i>
                    <span>${cat}</span>
                    <span style="font-size: 12px; font-family: var(--font-mono); color: var(--harvey-text-muted); font-weight: normal;">(${items.length} thủ tục)</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px;">
        `;

        items.forEach(item => {
            html += `
                <div class="harvey-card tpl-item" style="cursor: pointer; padding: 20px 22px; display: flex; flex-direction: column; justify-content: space-between;" onclick="startProcedure('${escapeHtml(item.name)}')">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                            <h4 style="font-family: var(--font-serif); font-size: 15px; font-weight: 600; color: #fff; margin: 0; line-height: 1.4;">${escapeHtml(item.display_name)}</h4>
                            <span class="legal-seal-badge" style="white-space: nowrap; margin-left: 8px;">${item.file_count || 5} docs</span>
                        </div>
                        <p style="font-size: 12.5px; color: var(--harvey-text-body); margin-bottom: 16px; line-height: 1.5;">${escapeHtml(item.description || 'Bộ hồ sơ đầy đủ các văn bản pháp lý theo Nghị định 01/2021/NĐ-CP.')}</p>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--gold-border-subtle); padding-top: 12px;">
                        <span style="font-size: 11.5px; color: var(--gold-primary); font-family: var(--font-mono);"><i class="fa-solid fa-stamp"></i> Chuẩn Sở KH&ĐT</span>
                        <span class="btn harvey-btn-ghost btn-sm" style="padding: 4px 10px; font-size: 11.5px;">Bắt đầu &rarr;</span>
                    </div>
                </div>
            `;
        });

        html += `</div></div>`;
    });

    grid.innerHTML = html;
}

window.startProcedure = function(name) {
    window.location.hash = '#/wizard';
    setTimeout(() => {
        if (window.selectTemplate) {
            window.selectTemplate(name);
        }
    }, 100);
};

window.filterLandingProcedures = function(query) {
    const q = query.toLowerCase().trim();
    const items = document.querySelectorAll('#landing-procedures-grid .tpl-item');
    items.forEach(el => {
        const txt = el.innerText.toLowerCase();
        el.style.display = txt.includes(q) ? 'flex' : 'none';
    });
};
