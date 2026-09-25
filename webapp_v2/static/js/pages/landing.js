// ==============================================================================
// NAC v2 - Harvey Legal Tech Executive Landing Portal
// Mẫu 1: The Executive Law & Finance Suite + Form Đặt Lịch Hẹn Tư Vấn
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

    // HARVEY LEGAL TECH EXECUTIVE PORTAL (SUITE + BOOKING CONSULTATION)
    return `
        <div class="harvey-app-shell">
            <!-- 1. Left Executive Navigation Sidebar -->
            <aside class="harvey-sidebar">
                <div class="harvey-sidebar-brand">
                    <div class="harvey-seal-logo"><i class="fa-solid fa-scale-balanced"></i></div>
                    <div style="display: flex; flex-direction: column;">
                        <span class="harvey-brand-title">HARVEY LEGAL OS</span>
                        <span class="harvey-brand-tag">Law & Finance Suite</span>
                    </div>
                </div>

                <nav class="harvey-sidebar-nav" id="landing-sidebar-nav">
                    <div class="nav-group-title">Trung tâm Dịch vụ</div>
                    <a class="harvey-nav-item active" href="#/">
                        <i class="fa-solid fa-layer-group"></i>
                        <span>Tổng quan 4 Trụ cột</span>
                    </a>
                    <a class="harvey-nav-item" href="#/wizard">
                        <i class="fa-solid fa-wand-magic-sparkles"></i>
                        <span>Tự soạn thảo hồ sơ AI</span>
                        <span class="harvey-nav-badge">19 Mẫu</span>
                    </a>
                    <a class="harvey-nav-item" onclick="scrollToBooking()">
                        <i class="fa-solid fa-calendar-check"></i>
                        <span>Đặt lịch tư vấn</span>
                    </a>

                    <div class="nav-group-title">Chuyên mục Dịch vụ</div>
                    <a class="harvey-nav-item" onclick="scrollToSection('pillar-p1')">
                        <i class="fa-solid fa-landmark"></i>
                        <span>1. Pháp lý & ĐKKD</span>
                    </a>
                    <a class="harvey-nav-item" onclick="scrollToSection('pillar-p2')">
                        <i class="fa-solid fa-calculator"></i>
                        <span>2. Kế toán & Thuế</span>
                    </a>
                    <a class="harvey-nav-item" onclick="scrollToSection('pillar-p3')">
                        <i class="fa-solid fa-key"></i>
                        <span>3. Hạ tầng số & Hóa đơn</span>
                    </a>
                    <a class="harvey-nav-item" onclick="scrollToSection('pillar-p4')">
                        <i class="fa-solid fa-certificate"></i>
                        <span>4. Giấy phép & SHTT</span>
                    </a>

                    <div class="nav-group-title" style="margin-top: 14px;">Quy trình Thủ tục (19 bộ)</div>
                    <div id="landing-procedures-sidebar-list">
                        <!-- Dynamically filled with templates -->
                    </div>
                </nav>

                <div class="harvey-sidebar-footer">
                    <div class="harvey-pulse-dot"></div>
                    <div style="font-size: 11.5px;">
                        <div style="color: var(--gold-light); font-weight: 600;">Jinja2 Engine Active</div>
                        <div style="color: var(--harvey-text-muted); font-size: 10.5px;">Cổng 8002 &bull; Hãng luật số</div>
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
                        <span style="color: var(--harvey-text-heading); font-weight: 600;">Tổ Hợp Dịch Vụ Pháp Lý & Kế Toán Doanh Nghiệp</span>
                    </div>

                    <div class="harvey-search-bar" onclick="const inp = document.getElementById('landing-global-search'); if(inp) inp.focus();">
                        <i class="fa-solid fa-magnifying-glass" style="color: var(--gold-primary);"></i>
                        <input type="text" id="landing-global-search" placeholder="Tra cứu dịch vụ, mã số thuế, thủ tục..." style="background: transparent; border: none; outline: none; color: #fff; width: 100%; font-size: 12.5px;" onkeyup="filterLandingCards(this.value)">
                        <span style="font-family: var(--font-mono); font-size: 10.5px; background: rgba(212, 175, 55, 0.1); color: var(--gold-primary); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(212, 175, 55, 0.25);">⌘K</span>
                    </div>

                    <div style="display: flex; align-items: center; gap: 12px;">
                        <button type="button" class="btn harvey-btn-ghost btn-sm" onclick="toggleGlobalUIMode()" title="Chuyển về giao diện giới thiệu cũ">
                            <i class="fa-solid fa-rotate-left"></i> Giao diện cũ
                        </button>
                        <a href="#/wizard" class="btn harvey-btn-gold btn-sm"><i class="fa-solid fa-bolt"></i> Soạn thảo AI ngay</a>
                    </div>
                </header>

                <!-- Workspace Scroll Body -->
                <main class="workspace-scroll" id="landing-scroll-body" style="flex: 1; overflow-y: auto; padding: 28px 34px 80px 34px;">
                    <!-- Hero Section -->
                    <div class="hero-banner-line" style="margin-bottom: 30px;">
                        <div>
                            <div class="hero-citation">
                                <i class="fa-solid fa-award"></i> TỔ HỢP TƯ VẤN PHÁP LÝ & QUẢN TRỊ THUẾ CHUYÊN NGHIỆP
                            </div>
                            <h1 class="hero-heading" style="font-size: 32px; line-height: 1.25; margin-bottom: 12px;">
                                Đồng Hành Pháp Lý & Quản Trị Thuế Doanh Nghiệp Toàn Diện
                            </h1>
                            <p class="hero-subtext" style="max-width: 880px; font-size: 14.5px; line-height: 1.6; margin-bottom: 22px;">
                                Từ khởi sự kinh doanh, kế toán thuế định kỳ đến tái cấu trúc doanh nghiệp quy mô lớn. 
                                Hệ thống tích hợp công nghệ AI soạn thảo hồ sơ Word chuẩn xác 100% theo quy định Sở KH&ĐT, 
                                kết hợp đội ngũ chuyên viên & luật sư hỗ trợ trọn gói tận nơi.
                            </p>
                            <div style="display: flex; gap: 14px; flex-wrap: wrap;">
                                <a href="#/wizard" class="btn harvey-btn-gold"><i class="fa-solid fa-wand-magic-sparkles"></i> Tự Soạn Thảo Bằng AI (0.85s)</a>
                                <button class="btn harvey-btn-ghost" onclick="scrollToBooking()"><i class="fa-solid fa-calendar-check"></i> Đặt Lịch Hẹn Tư Vấn Trực Tuyến</button>
                            </div>
                        </div>
                    </div>

                    <!-- 4 Core Pillars Grid -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
                        <div>
                            <h3 style="font-family: var(--font-serif); font-size: 22px; color: var(--gold-light); margin: 0;">4 Trụ Cột Dịch Vụ Doanh Nghiệp Cốt Lõi</h3>
                            <p style="font-size: 12.5px; color: var(--harvey-text-muted); margin: 2px 0 0 0;">Cung cấp giải pháp pháp lý toàn diện từ khởi sự đến mở rộng và thoái vốn</p>
                        </div>
                        <span class="legal-seal-badge"><i class="fa-solid fa-shield-check"></i> ĐẦY ĐỦ THẨM QUYỀN & TRÁCH NHIỆM</span>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 22px; margin-bottom: 34px;">
                        <!-- Pillar 1 -->
                        <div class="harvey-card" id="pillar-p1" style="display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <div class="card-header-bar">
                                    <div class="card-title">
                                        <i class="fa-solid fa-landmark"></i>
                                        <span>1. Pháp Lý & Đăng Ký Doanh Nghiệp</span>
                                    </div>
                                    <span class="legal-seal-badge">19 QUY TRÌNH</span>
                                </div>
                                <p style="font-size: 13px; color: var(--harvey-text-body); margin-bottom: 16px; line-height: 1.6;">
                                    Xử lý toàn diện mọi thủ tục hành chính tại Sở Kế hoạch & Đầu tư với thời gian thẩm định và cấp phép nhanh nhất.
                                </p>
                                <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px;">
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Thành lập mới công ty TNHH 1TV, 2TV, Công ty Cổ phần</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Thay đổi ĐKKD: Tăng vốn, đổi địa chỉ, đổi người ĐDPL</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Chuyển nhượng vốn góp, chuyển đổi loại hình 1TV sang 2TV</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Tạm ngừng kinh doanh, giải thể công ty không nợ đọng thuế</span>
                                    </div>
                                </div>
                            </div>
                            <div style="display: flex; gap: 10px;">
                                <a href="#/wizard" class="btn harvey-btn-gold" style="flex: 1; justify-content: center; font-size: 12.5px;">Tự Soạn Thảo AI &rarr;</a>
                                <button class="btn harvey-btn-ghost" style="font-size: 12.5px;" onclick="selectBookingService('Pháp lý & ĐKKD')">Tư Vấn Trọn Gói</button>
                            </div>
                        </div>

                        <!-- Pillar 2 -->
                        <div class="harvey-card" id="pillar-p2" style="display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <div class="card-header-bar">
                                    <div class="card-title">
                                        <i class="fa-solid fa-calculator"></i>
                                        <span>2. Kế Toán, Thuế & Báo Cáo Tài Chính</span>
                                    </div>
                                    <span class="legal-seal-badge">ĐẠI LÝ THUẾ</span>
                                </div>
                                <p style="font-size: 13px; color: var(--harvey-text-body); margin-bottom: 16px; line-height: 1.6;">
                                    Bảo vệ an toàn nghĩa vụ thuế, tối ưu chi phí hợp pháp và đại diện làm việc trực tiếp trước cơ quan thuế.
                                </p>
                                <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px;">
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Đại lý thuế trọn gói: Kê khai thuế GTGT, TNCN, TNDN định kỳ</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Lập Báo cáo tài chính (BCTC) & Quyết toán thuế cuối năm</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Rà soát sổ sách kế toán, tối ưu chi phí trước thanh kiểm tra</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Tư vấn pháp luật thuế chuyên sâu và hoàn thuế GTGT</span>
                                    </div>
                                </div>
                            </div>
                            <div style="display: flex; gap: 10px;">
                                <button class="btn harvey-btn-gold" style="flex: 1; justify-content: center; font-size: 12.5px;" onclick="selectBookingService('Kế toán & Đại lý thuế')">Đăng Ký Đại Lý Thuế &rarr;</button>
                                <button class="btn harvey-btn-ghost" style="font-size: 12.5px;" onclick="selectBookingService('Rà soát sổ sách BCTC')">Rà Soát Sổ Sách</button>
                            </div>
                        </div>

                        <!-- Pillar 3 -->
                        <div class="harvey-card" id="pillar-p3" style="display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <div class="card-header-bar">
                                    <div class="card-title">
                                        <i class="fa-solid fa-key"></i>
                                        <span>3. Hạ Tầng Doanh Nghiệp Số</span>
                                    </div>
                                    <span class="legal-seal-badge">SỐ HÓA 100%</span>
                                </div>
                                <p style="font-size: 13px; color: var(--harvey-text-body); margin-bottom: 16px; line-height: 1.6;">
                                    Trang bị đầy đủ công cụ kỹ thuật số thiết yếu để doanh nghiệp vận hành ngay sau khi nhận Giấy chứng nhận ĐKKD.
                                </p>
                                <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px;">
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Chữ ký số điện tử HSM / USB Token bảo mật cao</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Hóa đơn điện tử có mã cơ quan thuế (VNPT, Viettel, MISA)</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Khắc con dấu pháp nhân công nghệ laser sắc nét lấy ngay</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Mở tài khoản ngân hàng số đẹp & đăng ký nộp thuế điện tử</span>
                                    </div>
                                </div>
                            </div>
                            <div style="display: flex; gap: 10px;">
                                <button class="btn harvey-btn-gold" style="flex: 1; justify-content: center; font-size: 12.5px;" onclick="selectBookingService('Chữ ký số & Hóa đơn')">Đăng Ký Gói Số Hóa &rarr;</button>
                                <button class="btn harvey-btn-ghost" style="font-size: 12.5px;" onclick="selectBookingService('Khắc con dấu pháp nhân')">Khắc Con Dấu</button>
                            </div>
                        </div>

                        <!-- Pillar 4 -->
                        <div class="harvey-card" id="pillar-p4" style="display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <div class="card-header-bar">
                                    <div class="card-title">
                                        <i class="fa-solid fa-certificate"></i>
                                        <span>4. Giấy Phép Con & Sở Hữu Trí Tuệ</span>
                                    </div>
                                    <span class="legal-seal-badge">BẢO HỘ ĐỘC QUYỀN</span>
                                </div>
                                <p style="font-size: 13px; color: var(--harvey-text-body); margin-bottom: 16px; line-height: 1.6;">
                                    Bảo vệ thương hiệu tài sản trí tuệ và xin cấp các giấy phép ngành nghề đặc thù có điều kiện.
                                </p>
                                <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px;">
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Đăng ký bảo hộ nhãn hiệu độc quyền tại Cục Sở hữu trí tuệ</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Giấy chứng nhận PCCC, An toàn vệ sinh thực phẩm (ATTP)</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Giấy phép bưu chính, trung tâm ngoại ngữ, phòng khám y tế</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: #fff; display: flex; align-items: center; gap: 8px;">
                                        <i class="fa-solid fa-circle-check" style="color: var(--gold-primary); font-size: 11px;"></i>
                                        <span>Giấy phép bán buôn/lẻ rượu, thuốc lá, kinh doanh vận tải</span>
                                    </div>
                                </div>
                            </div>
                            <div style="display: flex; gap: 10px;">
                                <button class="btn harvey-btn-gold" style="flex: 1; justify-content: center; font-size: 12.5px;" onclick="selectBookingService('Giấy phép con & Nhãn hiệu')">Tư Vấn Giấy Phép &rarr;</button>
                                <button class="btn harvey-btn-ghost" style="font-size: 12.5px;" onclick="selectBookingService('Đăng ký nhãn hiệu')">Bảo Hộ Nhãn Hiệu</button>
                            </div>
                        </div>
                    </div>

                    <!-- Dual Mode Section -->
                    <div class="harvey-card" style="margin-bottom: 34px; background: rgba(13, 21, 42, 0.7);">
                        <div class="card-header-bar" style="margin-bottom: 14px;">
                            <div class="card-title">
                                <i class="fa-solid fa-sliders"></i>
                                <span>Linh Hoạt Lựa Chọn: 2 Chế Độ Phù Hợp Mọi Khách Hàng</span>
                            </div>
                            <span class="legal-seal-badge">CHỦ ĐỘNG TIẾT KIỆM</span>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px;">
                            <div style="background: rgba(6, 10, 20, 0.55); border: 1px solid var(--gold-border-subtle); border-radius: var(--radius-md); padding: 22px;">
                                <div style="font-size: 11.5px; font-family: var(--font-mono); color: var(--gold-primary); margin-bottom: 6px;">CHẾ ĐỘ 1 &bull; SELF-SERVICE AI</div>
                                <h4 style="font-family: var(--font-serif); font-size: 17.5px; color: #fff; margin-bottom: 8px;">Tự Soạn Thảo Bằng AI Siêu Tốc</h4>
                                <p style="font-size: 12.5px; color: var(--harvey-text-body); margin-bottom: 16px; line-height: 1.6;">
                                    Phù hợp chủ doanh nghiệp hoặc kế toán muốn tự nộp hồ sơ lên Cổng thông tin Quốc gia. Nhập liệu nhanh, tự động kiểm tra tỷ lệ vốn điều lệ và xuất trọn bộ file Word (.docx) chuẩn trong đúng 0.85 giây.
                                </p>
                                <a href="#/wizard" class="btn harvey-btn-gold" style="font-size: 12.5px; padding: 7px 16px;">Bắt đầu soạn thảo &rarr;</a>
                            </div>

                            <div style="background: rgba(6, 10, 20, 0.55); border: 1px solid var(--gold-border-subtle); border-radius: var(--radius-md); padding: 22px;">
                                <div style="font-size: 11.5px; font-family: var(--font-mono); color: var(--gold-primary); margin-bottom: 6px;">CHẾ ĐỘ 2 &bull; FULL CONCIERGE</div>
                                <h4 style="font-family: var(--font-serif); font-size: 17.5px; color: #fff; margin-bottom: 8px;">Dịch Vụ Pháp Lý Trọn Gói A-Z</h4>
                                <p style="font-size: 12.5px; color: var(--harvey-text-body); margin-bottom: 16px; line-height: 1.6;">
                                    Đội ngũ chuyên viên & luật sư đại diện soạn thảo, nộp hồ sơ, làm việc với Sở KH&ĐT, nhận kết quả và bàn giao Giấy chứng nhận ĐKKD + Con dấu pháp nhân tận tay quý khách.
                                </p>
                                <button class="btn harvey-btn-ghost" style="font-size: 12.5px; padding: 7px 16px;" onclick="scrollToBooking()">Yêu cầu tư vấn trọn gói &rarr;</button>
                            </div>
                        </div>
                    </div>

                    <!-- FORM ĐẶT LỊCH HẸN TƯ VẤN TRỰC TUYẾN (HIGHLIGHT COMPONENT) -->
                    <div id="booking-section" class="harvey-card" style="margin-bottom: 34px; padding: 30px; border-color: rgba(212, 175, 55, 0.45); background: linear-gradient(135deg, rgba(13, 21, 42, 0.95) 0%, rgba(6, 10, 20, 0.98) 100%);">
                        <div style="display: grid; grid-template-columns: 1fr 440px; gap: 32px; align-items: start;">
                            <!-- Left: Trách nhiệm & Cam kết -->
                            <div>
                                <div class="hero-citation">
                                    <i class="fa-solid fa-handshake"></i> ĐỒNG HÀNH & BẢO CHỨNG PHÁP LÝ
                                </div>
                                <h3 style="font-family: var(--font-serif); font-size: 24px; color: var(--gold-light); margin-bottom: 12px;">
                                    Đặt Lịch Hẹn Tư Vấn Chuyên Sâu
                                </h3>
                                <p style="font-size: 13.5px; color: var(--harvey-text-body); line-height: 1.6; margin-bottom: 22px;">
                                    Mỗi khách hàng đều được phụ trách bởi một Chuyên viên Trưởng giàu kinh nghiệm. Chúng tôi cam kết bảo mật thông tin tuyệt đối và đồng hành pháp lý dài hạn:
                                </p>

                                <div style="display: flex; flex-direction: column; gap: 16px;">
                                    <div style="display: flex; gap: 14px; align-items: flex-start;">
                                        <div style="color: var(--gold-primary); font-size: 17px; margin-top: 2px;"><i class="fa-solid fa-shield-halved"></i></div>
                                        <div>
                                            <div style="font-size: 14px; font-weight: 600; color: #fff;">Chịu Trách Nhiệm 100% Về Hồ Sơ</div>
                                            <div style="font-size: 12.5px; color: var(--harvey-text-body);">Mọi văn bản đều được rà soát đối chiếu chặt chẽ với Nghị định 01/2021/NĐ-CP và Luật Doanh nghiệp trước khi phát hành.</div>
                                        </div>
                                    </div>

                                    <div style="display: flex; gap: 14px; align-items: flex-start;">
                                        <div style="color: var(--gold-primary); font-size: 17px; margin-top: 2px;"><i class="fa-solid fa-clock"></i></div>
                                        <div>
                                            <div style="font-size: 14px; font-weight: 600; color: #fff;">Cam Kết Thời Hạn SLA Rõ Ràng</div>
                                            <div style="font-size: 12.5px; color: var(--harvey-text-body);">Thành lập mới & Thay đổi ĐKKD hoàn tất trong đúng 3 ngày làm việc. Báo cáo kế toán thuế đúng hạn ngày 15 hàng tháng.</div>
                                        </div>
                                    </div>

                                    <div style="display: flex; gap: 14px; align-items: flex-start;">
                                        <div style="color: var(--gold-primary); font-size: 17px; margin-top: 2px;"><i class="fa-solid fa-lock"></i></div>
                                        <div>
                                            <div style="font-size: 14px; font-weight: 600; color: #fff;">Bảo Mật Thông Tin & Tài Chính</div>
                                            <div style="font-size: 12.5px; color: var(--harvey-text-body);">Dữ liệu thành viên, tỷ lệ sở hữu vốn và số liệu kế toán thuế được bảo mật theo tiêu chuẩn hãng luật chuyên nghiệp.</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Right: Booking Form -->
                            <div style="background: rgba(6, 10, 20, 0.75); border: 1px solid var(--gold-border); border-radius: var(--radius-lg); padding: 26px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                                <h4 style="font-family: var(--font-serif); font-size: 17px; color: var(--gold-light); margin-bottom: 4px;">
                                    <i class="fa-solid fa-calendar-check" style="color: var(--gold-primary);"></i> Thông Tin Đặt Lịch Tư Vấn
                                </h4>
                                <p style="font-size: 12px; color: var(--harvey-text-muted); margin-bottom: 16px;">
                                    Chuyên viên tư vấn sẽ liên hệ lại với quý khách trong vòng 15 phút.
                                </p>

                                <form id="consultation-form" onsubmit="handleConsultationSubmit(event)">
                                    <div class="form-group" style="margin-bottom: 12px;">
                                        <label class="form-label" style="font-size: 12px;">Họ và tên của bạn <span class="req">*</span></label>
                                        <input type="text" class="exec-input" id="b_name" required placeholder="Nguyễn Văn A">
                                    </div>

                                    <div class="form-group" style="margin-bottom: 12px;">
                                        <label class="form-label" style="font-size: 12px;">Số điện thoại liên hệ <span class="req">*</span></label>
                                        <input type="tel" class="exec-input font-mono" id="b_phone" required placeholder="0908xxxxxx">
                                    </div>

                                    <div class="form-group" style="margin-bottom: 12px;">
                                        <label class="form-label" style="font-size: 12px;">Tên doanh nghiệp / Mã số thuế (nếu có)</label>
                                        <input type="text" class="exec-input" id="b_company" placeholder="Công ty TNHH...">
                                    </div>

                                    <div class="form-group" style="margin-bottom: 16px;">
                                        <label class="form-label" style="font-size: 12px;">Nhu cầu tư vấn chính <span class="req">*</span></label>
                                        <select class="exec-input" id="b_service">
                                            <option value="Thành lập mới doanh nghiệp">Thành lập mới doanh nghiệp (1TV, 2TV, CP)</option>
                                            <option value="Thay đổi nội dung ĐKKD & Tăng vốn">Thay đổi nội dung ĐKKD & Tăng vốn</option>
                                            <option value="Chuyển nhượng vốn góp / Tái cấu trúc">Chuyển nhượng vốn góp / Tái cấu trúc M&A</option>
                                            <option value="Dịch vụ Kế toán & Đại lý thuế">Dịch vụ Kế toán & Đại lý thuế trọn gói</option>
                                            <option value="Hạ tầng số: Chữ ký số & Hóa đơn">Hạ tầng số: Chữ ký số & Hóa đơn điện tử</option>
                                            <option value="Giấy phép con & Nhãn hiệu độc quyền">Giấy phép con & Nhãn hiệu độc quyền</option>
                                            <option value="Tạm dừng / Giải thể doanh nghiệp">Tạm dừng / Giải thể doanh nghiệp</option>
                                        </select>
                                    </div>

                                    <button type="submit" class="btn harvey-btn-gold" style="width: 100%; justify-content: center; padding: 11px;">
                                        <i class="fa-solid fa-paper-plane"></i> Gửi Yêu Cầu Tư Vấn Ngay
                                    </button>
                                </form>
                                <div id="booking-success-msg" style="display: none; margin-top: 14px; padding: 10px; background: rgba(16, 185, 129, 0.15); border: 1px solid var(--status-green); border-radius: var(--radius-sm); color: var(--status-green); font-size: 12.5px; text-align: center;">
                                    <i class="fa-solid fa-circle-check"></i> Đã tiếp nhận yêu cầu! Chuyên viên sẽ gọi lại trong 15 phút.
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Quick Links to 19 Procedures -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <div>
                            <h4 style="font-family: var(--font-serif); font-size: 19px; color: var(--gold-light); margin: 0;">Danh Mục 19 Quy Trình Soạn Thảo Hồ Sơ AI</h4>
                            <p style="font-size: 12.5px; color: var(--harvey-text-muted); margin: 2px 0 0 0;">Bấm vào bất kỳ thủ tục nào để bắt đầu nhập liệu tự động</p>
                        </div>
                        <a href="#/wizard" class="btn harvey-btn-ghost btn-sm">Xem tất cả trên Wizard &rarr;</a>
                    </div>

                    <div id="landing-procedures-quick-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px;">
                        <!-- Dynamically filled with templates -->
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
            renderLandingQuickGrid(data.templates);
            renderLandingSidebarList(data.templates);
        }
    } catch (err) {
        console.error('Lỗi nạp danh mục thủ tục tại trang chủ:', err);
    }
};

function renderLandingSidebarList(templates) {
    const container = document.getElementById('landing-procedures-sidebar-list');
    if (!container || !templates) return;

    let html = '';
    templates.slice(0, 10).forEach(item => {
        html += `
            <a class="harvey-nav-item" onclick="startProcedure('${escapeHtml(item.name)}')">
                <i class="fa-solid fa-file-contract"></i>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(item.display_name)}</span>
                <span class="harvey-nav-badge">${item.file_count || 5}</span>
            </a>
        `;
    });
    if (templates.length > 10) {
        html += `
            <a class="harvey-nav-item" href="#/wizard" style="color: var(--gold-primary);">
                <i class="fa-solid fa-ellipsis"></i>
                <span>Xem thêm ${templates.length - 10} thủ tục...</span>
            </a>
        `;
    }
    container.innerHTML = html;
}

function renderLandingQuickGrid(templates) {
    const grid = document.getElementById('landing-procedures-quick-grid');
    if (!grid || !templates) return;

    let html = '';
    templates.forEach(item => {
        html += `
            <div class="harvey-card tpl-item" style="padding: 16px 18px; cursor: pointer; display: flex; flex-direction: column; justify-content: space-between;" onclick="startProcedure('${escapeHtml(item.name)}')">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <h5 style="font-family: var(--font-serif); font-size: 14px; font-weight: 600; color: #fff; margin: 0; line-height: 1.4;">${escapeHtml(item.display_name)}</h5>
                    <span class="legal-seal-badge" style="font-size: 10px; margin-left: 6px;">${item.file_count || 5} docs</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; border-top: 1px solid var(--gold-border-subtle); padding-top: 8px;">
                    <span style="font-size: 11px; color: var(--gold-primary);">${item.category || 'ĐKKD'}</span>
                    <span style="font-size: 11px; color: var(--gold-light);">Soạn thảo &rarr;</span>
                </div>
            </div>
        `;
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

window.scrollToBooking = function() {
    const el = document.getElementById('booking-section');
    if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
        setTimeout(() => {
            const input = document.getElementById('b_name');
            if (input) input.focus();
        }, 500);
    }
};

window.scrollToSection = function(id) {
    const el = document.getElementById(id);
    if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
    }
};

window.selectBookingService = function(serviceName) {
    window.scrollToBooking();
    const select = document.getElementById('b_service');
    if (select) {
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].text.includes(serviceName) || select.options[i].value.includes(serviceName)) {
                select.selectedIndex = i;
                break;
            }
        }
    }
};

window.handleConsultationSubmit = function(e) {
    e.preventDefault();
    const name = document.getElementById('b_name').value;
    const phone = document.getElementById('b_phone').value;
    const service = document.getElementById('b_service').value;

    const msg = document.getElementById('booking-success-msg');
    if (msg) {
        msg.style.display = 'block';
        msg.innerHTML = `<i class="fa-solid fa-circle-check"></i> Cảm ơn ${escapeHtml(name)} (${phone})! Chuyên viên trưởng mảng <b>${escapeHtml(service)}</b> sẽ liên hệ lại với bạn trong 15 phút.`;
    }

    // Save lead locally to localStorage for reference
    try {
        const leads = JSON.parse(localStorage.getItem('consultation_leads') || '[]');
        leads.push({
            name,
            phone,
            company: document.getElementById('b_company').value,
            service,
            timestamp: new Date().toISOString()
        });
        localStorage.setItem('consultation_leads', JSON.stringify(leads));
    } catch(err) {}
};

window.filterLandingCards = function(query) {
    const q = query.toLowerCase().trim();
    const items = document.querySelectorAll('#landing-procedures-quick-grid .tpl-item');
    items.forEach(el => {
        const txt = el.innerText.toLowerCase();
        el.style.display = txt.includes(q) ? 'flex' : 'none';
    });
};
