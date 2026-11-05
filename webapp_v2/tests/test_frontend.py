"""Test giao diện bằng trình duyệt thật (Playwright): chống XSS và kiểm tra trường bắt buộc.

Tự động bỏ qua nếu chưa cài Playwright / Chromium. Cài đặt:
    pip install playwright && python -m playwright install chromium
Có thể chỉ định trình duyệt có sẵn qua biến PLAYWRIGHT_CHROMIUM_EXECUTABLE.
"""
import os
import socket
import threading
import time

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")

XSS = '"><img src=x onerror="window.__xss=(window.__xss||0)+1">'


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def base_url():
    import uvicorn
    from main import app

    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    t.join(timeout=5)


@pytest.fixture(scope="module")
def browser():
    with playwright_api.sync_playwright() as p:
        kwargs = {}
        exe = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        if exe:
            kwargs["executable_path"] = exe
        try:
            b = p.chromium.launch(**kwargs)
        except Exception as e:  # trình duyệt chưa được cài
            pytest.skip(f"Không khởi động được Chromium: {e}")
        yield b
        b.close()


@pytest.fixture
def page(browser, base_url):
    pg = browser.new_page()
    pg.dialogs = []

    def on_dialog(d):
        pg.dialogs.append(d.message)
        d.dismiss()

    pg.on("dialog", on_dialog)
    # Chặn tài nguyên bên ngoài (CDN font/icon) để test nhanh và không phụ thuộc mạng
    pg.route("**/*", lambda route: route.continue_() if route.request.url.startswith(base_url) else route.abort())
    yield pg
    pg.close()


def open_template(page, base_url, name):
    page.goto(f"{base_url}/#/wizard")
    # Chờ initWizard() (bất đồng bộ) tải xong danh sách mẫu, tránh nó vẽ đè lên form
    page.wait_for_function("window.wizardState && (window.wizardState.templatesList || []).length > 0")
    page.wait_for_load_state("networkidle")
    page.evaluate("n => selectTemplate(n)", name)
    page.wait_for_function("window.wizardState.schema && window.wizardState.step === 2 && document.querySelector('input[name]')")
    page.wait_for_load_state("networkidle")


def test_escape_html_helper(page, base_url):
    page.goto(base_url)
    assert page.evaluate("escapeHtml('<a href=\"x\">&\\'</a>')") == "&lt;a href=&quot;x&quot;&gt;&amp;&#39;&lt;/a&gt;"
    assert page.evaluate("escapeHtml(0)") == "0"
    assert page.evaluate("escapeHtml(null)") == ""
    assert page.evaluate("escapeHtml(undefined)") == ""


@pytest.mark.parametrize("template", [
    "Tạm dừng công ty TNHH 1 TV",
    "Thành lập mới công ty TNHH 2 TV",
    "Tăng vốn công ty TNHH 2 TV",
])
def test_form_values_are_escaped(page, base_url, template):
    open_template(page, base_url, template)
    # Điền payload XSS vào mọi ô và vào dữ liệu thành viên, rồi buộc vẽ lại form
    for el in page.query_selector_all("input[name]:not([type=file]):not([type=checkbox]), input[data-prop]"):
        try:
            el.fill(XSS, timeout=500)
        except Exception:
            pass
    page.evaluate("""xss => {
        const s = window.wizardState;
        s.thanhVienList.forEach(m => { m.ho_ten = xss; m.so_cccd = xss; });
        if (typeof collectFormData === 'function' && !window.tv2Sync) collectFormData();
        if (window.tv2Sync) window.tv2Sync();
        for (const k of Object.keys(s.formData)) s.formData[k] = xss;
        renderCurrentStep();
    }""", XSS)
    page.wait_for_timeout(300)
    assert page.evaluate("window.__xss || 0") == 0, "Mã chèn qua ô nhập đã được thực thi"
    assert page.query_selector('img[src="x"]') is None
    # Giá trị vẫn hiển thị đúng nguyên văn trong ô nhập
    values = page.eval_on_selector_all("input[name]:not([type=file])", "els => els.map(e => e.value)")
    assert XSS in values


def test_required_fields_block_next_step(page, base_url):
    open_template(page, base_url, "Tạm dừng công ty TNHH 1 TV")
    assert page.evaluate("window.wizardState.step") == 2
    page.evaluate("nextStep()")
    assert page.evaluate("window.wizardState.step") == 2, "Form trống không được phép sang bước tiếp theo"
    assert page.dialogs and "bắt buộc" in page.dialogs[-1]
    assert page.query_selector(".input-invalid") is not None

    # Điền đủ các trường bắt buộc theo schema thì được đi tiếp
    page.evaluate("""() => {
        const s = window.wizardState;
        s.schema.steps.forEach(st => st.fields.forEach(f => {
            const set = (n, v) => { const el = document.querySelector(`[name="${n}"]`); if (el) el.value = v; };
            if (f.type === 'person') { set(f.key + '_ho_ten', 'NGUYỄN VĂN A'); set(f.key + '_so_cccd', '001090001234'); }
            else if (f.required) set(f.key, f.type === 'money' ? '1,000,000' : 'Giá trị');
        }));
    }""")
    page.evaluate("nextStep()")
    assert page.evaluate("window.wizardState.step") == 4


def test_required_member_fields(page, base_url):
    open_template(page, base_url, "Thành lập mới công ty TNHH 2 TV")
    errors = page.evaluate("validateRequiredFields(window.wizardState.schema).map(e => e.label)")
    assert any("Họ và tên" in e for e in errors)
    assert page.evaluate("validateRequiredFields(window.wizardState.schema).total") >= len(errors)


def test_tang_von_completeness_reflects_real_state(page, base_url):
    open_template(page, base_url, "Tăng vốn công ty TNHH 2 TV")
    page.wait_for_selector("#tv2-completeness-score")
    assert page.inner_text("#tv2-completeness-score") != "100%"
    assert "Thiếu" in page.inner_text(".tv2-doc-badge")

    # Bấm tải hồ sơ khi còn thiếu dữ liệu -> bị chặn, không gọi API
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "/api/documents/generate" in r.url else None)
    page.evaluate("tv2GenerateAll()")
    page.wait_for_timeout(300)
    assert not requests
    assert page.dialogs and "bắt buộc" in page.dialogs[-1]


def _template_names():
    from conftest import list_template_names
    return list_template_names()


@pytest.mark.parametrize("template", _template_names())
def test_every_wizard_renders_without_js_errors(browser, base_url, template):
    pg = browser.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.dismiss())
    pg.route("**/*", lambda route: route.continue_() if route.request.url.startswith(base_url) else route.abort())
    try:
        pg.goto(f"{base_url}/#/wizard")
        pg.wait_for_function("window.wizardState && (window.wizardState.templatesList || []).length > 0")
        pg.wait_for_load_state("networkidle")
        pg.evaluate("n => selectTemplate(n)", template)
        pg.wait_for_function("window.wizardState.schema && window.wizardState.step === 2")
        pg.wait_for_load_state("networkidle")
        pg.wait_for_function("document.querySelectorAll('#wizard-content input:not([type=file])').length > 0", timeout=5000)
        assert not errors, errors
    finally:
        pg.close()
