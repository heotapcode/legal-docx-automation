function renderLanding() {
    return `
        <!-- Navbar -->
        <nav class="navbar">
            <div class="container navbar-container">
                <a href="#/" class="navbar-brand">
                    <i class="fa-solid fa-building text-gradient"></i> NAC
                </a>
                <div class="navbar-menu">
                    <a href="#/services">Dịch vụ</a>
                    <a href="#/pricing">Bảng giá</a>
                    <a href="#/about">Về chúng tôi</a>
                    <a href="#/contact">Liên hệ</a>
                </div>
                <a href="#/wizard" class="btn btn-primary btn-sm">Tạo hồ sơ ngay</a>
            </div>
        </nav>

        <!-- Hero -->
        <section class="hero">
            <div class="blob blob-1"></div>
            <div class="blob blob-2"></div>
            
            <div class="container grid-2" style="align-items: center;">
                <div class="hero-content">
                    <span class="badge mb-4">🚀 Công nghệ AI Mới Nhất 2026</span>
                    <h1 class="mb-4" style="font-size: var(--font-size-5xl); font-weight: 800; line-height: 1.2; margin-bottom: var(--space-6);">
                        Tạo Hồ Sơ Doanh Nghiệp<br>
                        <span class="text-gradient">Trong 5 Phút Với AI</span>
                    </h1>
                    <p class="text-secondary text-lg mb-8" style="margin-bottom: var(--space-8); max-width: 90%;">
                        Chỉ cần chụp ảnh VNeID — AI tự động điền thông tin. Hỗ trợ 17+ loại thủ tục ĐKKD. Tải ngay bộ hồ sơ hoàn chỉnh.
                    </p>
                    <div class="hero-cta" style="display: flex; gap: var(--space-4); margin-bottom: var(--space-12);">
                        <a href="#/wizard" class="btn btn-primary">
                            <i class="fa-solid fa-robot"></i> Tự Tạo Hồ Sơ — Từ 99K
                        </a>
                        <a href="#/contact" class="btn btn-secondary">
                            <i class="fa-solid fa-briefcase"></i> NAC Làm Hộ — Trọn Gói
                        </a>
                    </div>
                    
                    <div class="stats grid-3 text-center" style="border-top: 1px solid var(--border-glass); padding-top: var(--space-6);">
                        <div>
                            <div class="text-2xl font-bold text-gradient">1,200+</div>
                            <div class="text-sm text-muted">Hồ sơ đã tạo</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-gradient">5 phút</div>
                            <div class="text-sm text-muted">Thời gian TB</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-gradient">17+</div>
                            <div class="text-sm text-muted">Loại thủ tục</div>
                        </div>
                    </div>
                </div>
                
                <div class="hero-visual" style="animation: float 6s ease-in-out infinite;">
                    <!-- Simple Glassmorphism App Mockup -->
                    <div class="card-glass" style="position: relative; height: 500px; border-radius: var(--radius-2xl); overflow: hidden; padding: 0;">
                        <div style="background: rgba(0,0,0,0.3); padding: var(--space-4); border-bottom: 1px solid var(--border-glass); display: flex; gap: var(--space-2);">
                            <div style="width: 12px; height: 12px; border-radius: 50%; background: #ef4444;"></div>
                            <div style="width: 12px; height: 12px; border-radius: 50%; background: #f59e0b;"></div>
                            <div style="width: 12px; height: 12px; border-radius: 50%; background: #10b981;"></div>
                        </div>
                        <div style="padding: var(--space-6);">
                            <div style="height: 40px; background: rgba(255,255,255,0.05); border-radius: var(--radius-md); margin-bottom: var(--space-4);"></div>
                            <div style="height: 120px; background: rgba(255,255,255,0.05); border-radius: var(--radius-md); margin-bottom: var(--space-4); display: flex; align-items: center; justify-content: center; border: 2px dashed rgba(255,255,255,0.2);">
                                <span class="text-muted"><i class="fa-solid fa-camera"></i> Kéo thả ảnh VNeID vào đây</span>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
                                <div style="height: 30px; background: rgba(255,255,255,0.05); border-radius: var(--radius-sm);"></div>
                                <div style="height: 30px; background: rgba(255,255,255,0.05); border-radius: var(--radius-sm);"></div>
                                <div style="height: 30px; background: rgba(255,255,255,0.05); border-radius: var(--radius-sm);"></div>
                                <div style="height: 30px; background: rgba(255,255,255,0.05); border-radius: var(--radius-sm);"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- How it works -->
        <section class="section">
            <div class="container">
                <div class="text-center mb-12 animate-on-scroll" style="margin-bottom: var(--space-12);">
                    <h2 class="text-4xl font-bold mb-4" style="margin-bottom: var(--space-4);">Cách Thức <span class="text-gradient">Hoạt Động</span></h2>
                    <p class="text-secondary text-lg">Đơn giản hóa quy trình đăng ký doanh nghiệp với sức mạnh của AI.</p>
                </div>
                
                <div class="grid-3">
                    <div class="card text-center animate-on-scroll">
                        <div style="font-size: 3rem; color: var(--accent-primary); margin-bottom: var(--space-4);"><i class="fa-solid fa-id-card"></i></div>
                        <h3 class="text-xl font-bold mb-2" style="margin-bottom: var(--space-2);">1. Chụp ảnh VNeID</h3>
                        <p class="text-secondary">Hệ thống AI tự động trích xuất thông tin CMND/CCCD chính xác tuyệt đối.</p>
                    </div>
                    <div class="card text-center animate-on-scroll delay-100">
                        <div style="font-size: 3rem; color: var(--accent-secondary); margin-bottom: var(--space-4);"><i class="fa-solid fa-pen-to-square"></i></div>
                        <h3 class="text-xl font-bold mb-2" style="margin-bottom: var(--space-2);">2. Điền thông tin</h3>
                        <p class="text-secondary">Chỉ cần nhập MST hoặc tên công ty dự kiến, các biểu mẫu sẽ tự động điền.</p>
                    </div>
                    <div class="card text-center animate-on-scroll delay-200">
                        <div style="font-size: 3rem; color: var(--success); margin-bottom: var(--space-4);"><i class="fa-solid fa-file-arrow-down"></i></div>
                        <h3 class="text-xl font-bold mb-2" style="margin-bottom: var(--space-2);">3. Tải hồ sơ Word</h3>
                        <p class="text-secondary">Nhận ngay trọn bộ hồ sơ chuẩn chỉnh, đúng quy định pháp luật hiện hành.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Services -->
        <section class="section" style="background: var(--bg-secondary);">
            <div class="container">
                <div class="text-center mb-12 animate-on-scroll" style="margin-bottom: var(--space-12);">
                    <div class="badge mb-4">Không chỉ là công cụ</div>
                    <h2 class="text-4xl font-bold mb-4" style="margin-bottom: var(--space-4);">NAC là <span class="text-gradient">Đối Tác Kinh Doanh</span> của bạn</h2>
                </div>
                
                <div class="grid-2">
                    <div class="card card-glass animate-on-scroll">
                        <div style="display: flex; gap: var(--space-4); align-items: flex-start;">
                            <div style="font-size: 2.5rem; color: var(--accent-primary);"><i class="fa-solid fa-file-signature"></i></div>
                            <div>
                                <h3 class="text-xl font-bold mb-2">Đăng ký Doanh nghiệp</h3>
                                <div class="text-sm text-gradient font-bold mb-2">Từ 1.5 triệu trọn gói</div>
                                <p class="text-secondary mb-4" style="margin-bottom: var(--space-4);">Thành lập mới, thay đổi nội dung ĐKKD, giải thể, chuyển nhượng cổ phần uy tín.</p>
                                <a href="#/services" class="btn btn-outline btn-sm">Tư vấn ngay &rarr;</a>
                            </div>
                        </div>
                    </div>
                    <div class="card card-glass animate-on-scroll delay-100">
                        <div style="display: flex; gap: var(--space-4); align-items: flex-start;">
                            <div style="font-size: 2.5rem; color: var(--success);"><i class="fa-solid fa-chart-pie"></i></div>
                            <div>
                                <h3 class="text-xl font-bold mb-2">Kế toán Thuế</h3>
                                <div class="text-sm text-gradient font-bold mb-2">Từ 2 triệu/tháng</div>
                                <p class="text-secondary mb-4" style="margin-bottom: var(--space-4);">Chuyên nghiệp, chính xác. Báo cáo thuế đúng hạn, dọn dẹp sổ sách, quyết toán thuế.</p>
                                <a href="#/services" class="btn btn-outline btn-sm">Tư vấn ngay &rarr;</a>
                            </div>
                        </div>
                    </div>
                    <div class="card card-glass animate-on-scroll">
                        <div style="display: flex; gap: var(--space-4); align-items: flex-start;">
                            <div style="font-size: 2.5rem; color: var(--warning);"><i class="fa-solid fa-pen-nib"></i></div>
                            <div>
                                <h3 class="text-xl font-bold mb-2">Chữ ký số</h3>
                                <div class="text-sm text-gradient font-bold mb-2">Từ 1.5 triệu/năm</div>
                                <p class="text-secondary mb-4" style="margin-bottom: var(--space-4);">Token USB chính hãng, bảo mật cao. Hỗ trợ cài đặt tận nơi, khai báo thuế nhanh chóng.</p>
                                <a href="#/services" class="btn btn-outline btn-sm">Đặt mua ngay &rarr;</a>
                            </div>
                        </div>
                    </div>
                    <div class="card card-glass animate-on-scroll delay-100">
                        <div style="display: flex; gap: var(--space-4); align-items: flex-start;">
                            <div style="font-size: 2.5rem; color: var(--info);"><i class="fa-solid fa-file-invoice"></i></div>
                            <div>
                                <h3 class="text-xl font-bold mb-2">Hóa đơn điện tử</h3>
                                <div class="text-sm text-gradient font-bold mb-2">Từ 800K/năm</div>
                                <p class="text-secondary mb-4" style="margin-bottom: var(--space-4);">Đầy đủ tính năng, giao diện dễ dùng. Kết nối phần mềm kế toán mượt mà.</p>
                                <a href="#/services" class="btn btn-outline btn-sm">Đăng ký ngay &rarr;</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Starter Pack Upsell -->
        <section class="section" style="padding: var(--space-8) 0;">
            <div class="container animate-on-scroll">
                <div style="background: var(--accent-gradient); border-radius: var(--radius-2xl); padding: var(--space-8); display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: var(--space-6);">
                    <div>
                        <div class="badge mb-2" style="background: rgba(255,255,255,0.2); color: white; border: none;">🎁 GÓI KHỞI NGHIỆP</div>
                        <h2 class="text-3xl font-bold text-white mb-2">Chỉ 4.5 Triệu Đồng</h2>
                        <p class="text-white" style="opacity: 0.9;">ĐKDN + Khắc dấu + Chữ ký số + HĐĐT + Biển hiệu. Tiết kiệm 2 triệu so với mua lẻ!</p>
                    </div>
                    <a href="#/contact" class="btn" style="background: white; color: var(--accent-primary);">ĐĂNG KÝ GÓI KHỞI NGHIỆP &rarr;</a>
                </div>
            </div>
        </section>

        <!-- Pricing -->
        <section class="section" id="pricing">
            <div class="container">
                <div class="text-center mb-12 animate-on-scroll" style="margin-bottom: var(--space-12);">
                    <h2 class="text-4xl font-bold mb-4" style="margin-bottom: var(--space-4);">Bảng Giá <span class="text-gradient">Phần Mềm</span></h2>
                    <p class="text-secondary text-lg">Lựa chọn gói phù hợp với nhu cầu tạo hồ sơ tự động của bạn.</p>
                </div>
                
                <div class="grid-3" style="align-items: center;">
                    <!-- Basic -->
                    <div class="card animate-on-scroll">
                        <div class="text-center mb-6">
                            <h3 class="text-xl font-bold mb-2">Cơ bản</h3>
                            <div class="text-4xl font-bold mb-2">FREE</div>
                            <p class="text-muted text-sm">Cho cá nhân trải nghiệm</p>
                        </div>
                        <ul style="margin-bottom: var(--space-8);">
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> 2 bộ HS đơn giản/tháng</li>
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> Tra mã ngành 5 lần/ngày</li>
                            <li class="text-muted"><i class="fa-solid fa-xmark" style="margin-right: var(--space-2);"></i> Không hỗ trợ Auto-fill VNeID</li>
                        </ul>
                        <button class="btn btn-secondary" style="width: 100%;">Bắt đầu miễn phí</button>
                    </div>
                    
                    <!-- Pro -->
                    <div class="card pricing-card highlight animate-on-scroll delay-100">
                        <div style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--accent-gradient); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase;">Phổ biến nhất</div>
                        <div class="text-center mb-6">
                            <h3 class="text-xl font-bold mb-2">Professional</h3>
                            <div class="text-4xl font-bold mb-2 text-gradient">499K<span class="text-lg text-muted">/tháng</span></div>
                            <p class="text-muted text-sm">Cho văn phòng luật & dịch vụ</p>
                        </div>
                        <ul style="margin-bottom: var(--space-8);">
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> <b>Không giới hạn</b> bộ hồ sơ</li>
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> OCR VNeID không giới hạn</li>
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> Tra MST auto-fill</li>
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> Lưu profile công ty</li>
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> Ưu tiên hỗ trợ</li>
                        </ul>
                        <button class="btn btn-primary" style="width: 100%;">Đăng ký ngay</button>
                    </div>
                    
                    <!-- Standard -->
                    <div class="card animate-on-scroll delay-200">
                        <div class="text-center mb-6">
                            <h3 class="text-xl font-bold mb-2">Standard</h3>
                            <div class="text-4xl font-bold mb-2">199K<span class="text-lg text-muted">/tháng</span></div>
                            <p class="text-muted text-sm">Cho doanh nghiệp nhỏ</p>
                        </div>
                        <ul style="margin-bottom: var(--space-8);">
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> 10 bộ HS bất kỳ/tháng</li>
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> OCR VNeID không giới hạn</li>
                            <li style="margin-bottom: var(--space-3);"><i class="fa-solid fa-check text-success" style="margin-right: var(--space-2);"></i> Tra MST auto-fill</li>
                        </ul>
                        <button class="btn btn-secondary" style="width: 100%;">Đăng ký ngay</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- CTA Final -->
        <section class="section">
            <div class="container">
                <div class="card text-center animate-on-scroll" style="background: var(--bg-secondary);">
                    <h2 class="text-4xl font-bold mb-4">Sẵn Sàng Mở Công Ty?</h2>
                    <p class="text-secondary text-lg mb-8" style="margin-bottom: var(--space-8);">Đội ngũ NAC luôn sẵn sàng hỗ trợ bạn từ A-Z, cả online lẫn offline.</p>
                    <div style="display: flex; gap: var(--space-4); justify-content: center; margin-bottom: var(--space-8); flex-wrap: wrap;">
                        <a href="#/wizard" class="btn btn-primary">🤖 Tự Tạo Hồ Sơ Ngay</a>
                        <a href="#/contact" class="btn btn-secondary">💼 NAC Làm Hộ Trọn Gói</a>
                    </div>
                    <div class="text-muted">
                        Hotline: <b>0988.xxx.xxx</b> | Zalo: <b>0988.xxx.xxx</b>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer style="background: #05070a; padding: var(--space-12) 0; border-top: 1px solid var(--border-glass);">
            <div class="container grid-4">
                <div>
                    <a href="#/" class="navbar-brand mb-4" style="display: block; margin-bottom: var(--space-4);">
                        <i class="fa-solid fa-building text-gradient"></i> NAC
                    </a>
                    <p class="text-muted text-sm">Đối tác tin cậy về Kế toán Thuế và Đăng ký Doanh nghiệp.</p>
                </div>
                <div>
                    <h4 class="font-bold mb-4" style="margin-bottom: var(--space-4);">Dịch vụ</h4>
                    <ul class="text-muted text-sm" style="display: flex; flex-direction: column; gap: var(--space-2);">
                        <li><a href="#/services">Đăng ký doanh nghiệp</a></li>
                        <li><a href="#/services">Kế toán thuế</a></li>
                        <li><a href="#/services">Chữ ký số</a></li>
                        <li><a href="#/services">Hóa đơn điện tử</a></li>
                    </ul>
                </div>
                <div>
                    <h4 class="font-bold mb-4" style="margin-bottom: var(--space-4);">Phần mềm</h4>
                    <ul class="text-muted text-sm" style="display: flex; flex-direction: column; gap: var(--space-2);">
                        <li><a href="#/wizard">Tạo hồ sơ AI</a></li>
                        <li><a href="#/pricing">Bảng giá</a></li>
                        <li><a href="#">Hướng dẫn</a></li>
                    </ul>
                </div>
                <div>
                    <h4 class="font-bold mb-4" style="margin-bottom: var(--space-4);">Liên hệ</h4>
                    <ul class="text-muted text-sm" style="display: flex; flex-direction: column; gap: var(--space-2);">
                        <li><i class="fa-solid fa-location-dot"></i> Hà Nội, Việt Nam</li>
                        <li><i class="fa-solid fa-phone"></i> 0988.xxx.xxx</li>
                        <li><i class="fa-solid fa-envelope"></i> contact@nac.vn</li>
                    </ul>
                </div>
            </div>
            <div class="container mt-8 pt-8 text-center text-muted text-sm" style="border-top: 1px solid var(--border-glass); margin-top: var(--space-8); padding-top: var(--space-8);">
                &copy; 2026 NAC. All rights reserved.
            </div>
        </footer>
    `;
}
