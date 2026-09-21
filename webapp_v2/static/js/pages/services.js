function renderServices() {
    return `
        <!-- Navbar -->
        <nav class="navbar scrolled">
            <div class="container navbar-container">
                <a href="#/" class="navbar-brand">
                    <i class="fa-solid fa-building text-gradient"></i> NAC
                </a>
                <div class="navbar-menu">
                    <a href="#/services" style="color: #fff;">Dịch vụ</a>
                    <a href="#/pricing">Bảng giá</a>
                    <a href="#/about">Về chúng tôi</a>
                    <a href="#/contact">Liên hệ</a>
                </div>
                <a href="#/wizard" class="btn btn-primary btn-sm">Tạo hồ sơ ngay</a>
            </div>
        </nav>

        <section class="section" style="padding-top: var(--space-24);">
            <div class="container">
                <div class="text-center mb-12 animate-on-scroll">
                    <h1 class="text-5xl font-bold mb-4">Dịch Vụ <span class="text-gradient">Chuyên Nghiệp</span></h1>
                    <p class="text-secondary text-lg">NAC cung cấp giải pháp trọn gói, đồng hành cùng sự phát triển của doanh nghiệp bạn.</p>
                </div>
                
                <div class="grid-2">
                    <div class="card animate-on-scroll">
                        <h2 class="text-2xl font-bold mb-4 text-gradient">1. Đăng ký Doanh nghiệp</h2>
                        <ul class="text-secondary" style="line-height: 2;">
                            <li>- Thành lập công ty TNHH, Cổ phần</li>
                            <li>- Thay đổi ĐKKD (địa chỉ, vốn, ngành nghề)</li>
                            <li>- Chuyển đổi loại hình doanh nghiệp</li>
                            <li>- Giải thể doanh nghiệp trọn gói</li>
                        </ul>
                        <div class="mt-6 pt-6" style="border-top: 1px solid var(--border-glass); margin-top: 1.5rem; padding-top: 1.5rem;">
                            <a href="#/contact" class="btn btn-outline">Tư vấn báo giá &rarr;</a>
                        </div>
                    </div>
                    
                    <div class="card animate-on-scroll delay-100">
                        <h2 class="text-2xl font-bold mb-4 text-gradient" style="background: linear-gradient(135deg, var(--success), #34d399); -webkit-background-clip: text;">2. Kế toán Thuế</h2>
                        <ul class="text-secondary" style="line-height: 2;">
                            <li>- Dịch vụ kế toán trọn gói hàng tháng</li>
                            <li>- Báo cáo tài chính cuối năm</li>
                            <li>- Quyết toán thuế TNCN, TNDN</li>
                            <li>- Dọn dẹp, hoàn thiện sổ sách kế toán</li>
                        </ul>
                        <div class="mt-6 pt-6" style="border-top: 1px solid var(--border-glass); margin-top: 1.5rem; padding-top: 1.5rem;">
                            <a href="#/contact" class="btn btn-outline">Tư vấn báo giá &rarr;</a>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Footer (Short) -->
        <footer style="background: #05070a; padding: var(--space-8) 0; border-top: 1px solid var(--border-glass); text-align: center; color: var(--text-muted); font-size: var(--font-size-sm);">
            <div class="container">
                &copy; 2026 NAC. All rights reserved.
            </div>
        </footer>
    `;
}
