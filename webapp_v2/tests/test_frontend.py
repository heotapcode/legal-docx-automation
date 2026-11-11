"""Test giao diện bằng trình duyệt thật (Playwright): chống XSS và kiểm tra trường bắt buộc.

Tự động bỏ qua nếu chưa cài Playwright / Chromium. Cài đặt:
    pip install playwright && python -m playwright install chromium
Có thể chỉ định trình duyệt có sẵn qua biến PLAYWRIGHT_CHROMIUM_EXECUTABLE.
"""
import os
import urllib.error
import urllib.parse
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
            else if (f.required && f.type !== 'select') set(f.key, f.type === 'money' ? '1,000,000' : 'Giá trị');  // ô chọn đã có mặc định
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
    """% hoàn thiện tính theo lõi kiểm tra dữ liệu (không phải đếm ô đã gõ) và tăng khi nhập đúng."""
    open_template(page, base_url, "Tăng vốn công ty TNHH 2 TV")
    page.wait_for_selector("#universal-completeness-score")
    before = int(page.inner_text("#universal-completeness-score").rstrip("%"))
    assert before < 100
    page.fill('input[name="ten_cong_ty_vn"]', "CÔNG TY TNHH A")
    page.fill('input[name="ma_so_thue"]', "0101234567")
    after = int(page.inner_text("#universal-completeness-score").rstrip("%"))
    assert after > before

    # Bấm tải hồ sơ khi còn thiếu dữ liệu -> bị chặn, không gọi API
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "/api/documents/generate" in r.url else None)
    page.evaluate("window.wizardState.step = 4; generateDocuments()")
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


# ---------- Ô chọn tỉnh/thành phố nơi đăng ký ----------

def open_wizard_until(page, base_url, template, selector):
    page.goto(f"{base_url}/#/wizard")
    page.wait_for_function("window.wizardState && (window.wizardState.templatesList || []).length > 0")
    page.wait_for_load_state("networkidle")
    page.evaluate("n => selectTemplate(n)", template)
    page.wait_for_selector(selector, state="attached", timeout=5000)


@pytest.mark.parametrize("template", [
    "Tạm dừng công ty TNHH 1 TV",          # wizard chung
    "Tăng vốn công ty TNHH 2 TV",          # wizard chung
    "Chuyển nhượng Công ty TNHH 2 TV",     # wizard chung (list + options_from)
    "Chuyển đổi loại hình 1TV sang 2 TV",  # wizard chung (show_if theo hình thức chuyển nhượng)
])
def test_province_select_present(page, base_url, template):
    open_wizard_until(page, base_url, template, "select#input-tinh_dang_ky")
    sel = page.query_selector("select#input-tinh_dang_ky")
    options = sel.eval_on_selector_all("option", "els => els.map(e => [e.value, e.textContent])")
    assert len(options) == 34
    assert sel.input_value() == "Hà Nội"
    assert ["Bắc Ninh", "Tỉnh Bắc Ninh"] in options
    sel.select_option("Bắc Ninh")
    if template == "Tạm dừng công ty TNHH 1 TV":
        page.evaluate("collectFormData()")
    assert page.evaluate("window.wizardState.formData.tinh_dang_ky") == "Bắc Ninh"


def test_selected_province_is_sent_when_generating(page, base_url):
    open_wizard_until(page, base_url, "Tạm dừng công ty TNHH 1 TV", "select#input-tinh_dang_ky")
    page.select_option("select#input-tinh_dang_ky", "Hồ Chí Minh")
    page.evaluate("""() => {
        const set = (n, v) => { const el = document.querySelector(`[name="${n}"]`); if (el) el.value = v; };
        set('ten_cong_ty_vn', 'CÔNG TY TNHH A'); set('ma_so_thue', '0101234567');
        set('ddpl_ho_ten', 'NGUYỄN VĂN A'); set('ddpl_so_cccd', '001090001234');
    }""")
    page.evaluate("nextStep()")
    assert page.evaluate("window.wizardState.step") == 4
    with page.expect_request(lambda r: "/api/documents/generate" in r.url) as req_info:
        page.evaluate("generateDocuments()")
    body = req_info.value.post_data_json
    assert body["data"]["tinh_dang_ky"] == "Hồ Chí Minh"


def test_browser_and_api_report_same_errors(page, base_url):
    """Lõi kiểm tra trong trình duyệt và API trả cùng danh sách lỗi cho cùng dữ liệu."""
    import json as _json
    import urllib.request

    data = {"ten_cong_ty_vn": "CÔNG TY A", "thanh_vien": [{"ho_ten": "A", "von_gop": "1", "ty_le": ""}]}
    name = "Thành lập mới công ty TNHH 2 TV"
    page.goto(base_url)
    page.wait_for_function("window.SchemaEngine && typeof SchemaEngine.validate === 'function'")
    schema = _json.loads(urllib.request.urlopen(f"{base_url}/api/templates/{urllib.parse.quote(name)}/schema").read())
    in_browser = page.evaluate("([s, d]) => SchemaEngine.validate(s, d).map(e => [e.key, e.code, e.index ?? -1])",
                               [schema, data])
    req = urllib.request.Request(f"{base_url}/api/documents/generate", method="POST",
                                 data=_json.dumps({"template_name": name, "data": data}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        raise AssertionError("API phải trả 422")
    except urllib.error.HTTPError as e:
        assert e.code == 422
        api = [[x["key"], x["code"], x.get("index", -1)] for x in _json.loads(e.read())["errors"]]
    assert in_browser == api and len(api) >= 3


# ---------- Bộ vẽ form chung (static/js/engine/form_renderer.js) ----------

DEMO_SCHEMA = {
    "id": "demo-form-renderer", "name": "Demo", "display_name": "Demo bộ vẽ form", "has_nganh": False,
    "steps": [
        {"id": "chon", "title": "Chọn nội dung", "fields": [
            {"key": "thay_doi", "label": "Nội dung thay đổi", "type": "checkbox_group", "required": True,
             "options": [{"value": "A1", "label": "Đổi tên"}, {"value": "A2", "label": "Đổi địa chỉ"}]},
            {"key": "ten_moi", "label": "Tên mới", "type": "text", "required": True,
             "show_if": {"field": "thay_doi", "contains": "A1"}}]},
        {"id": "dia_chi", "title": "Địa chỉ mới", "show_if": {"field": "thay_doi", "contains": "A2"}, "fields": [
            {"key": "dia_chi_moi", "label": "Địa chỉ mới", "type": "address", "required": True}]},
        {"id": "nguoi", "title": "Người liên hệ", "fields": [
            {"key": "lh_cccd", "label": "CCCD", "type": "cccd", "required": True},
            {"key": "lh_ngay_sinh", "label": "Ngày sinh", "type": "date", "validate": {"min_age": 18}},
            {"key": "co_dong", "label": "Cổ đông", "type": "list", "min": 1, "max": 2,
             "item": [{"key": "ho_ten", "label": "Họ tên", "type": "text", "required": True},
                      {"key": "ty_le", "label": "Tỷ lệ", "type": "percent", "required": True}],
             "rules": [{"sum": "ty_le", "equals": 100}]}]},
    ],
}


def open_demo(page, base_url, mode):
    page.goto(f"{base_url}/#/wizard")
    page.wait_for_function("window.wizardState && (window.wizardState.templatesList || []).length > 0")
    page.wait_for_load_state("networkidle")
    page.evaluate("""([schema, mode]) => {
        localStorage.setItem('global_ui_mode', mode);
        const s = window.wizardState;
        s.template = { name: schema.name, display_name: schema.display_name };
        s.schema = schema; s.step = 2; s.formData = {}; s.thanhVienList = []; s.dkkdSelected = [];
        FormRenderer.resetTouched();
        renderStep2Form(schema);
    }""", [DEMO_SCHEMA, mode])
    page.wait_for_selector("#dynamic-form-container .fr-step")


def visible(page, selector):
    return page.eval_on_selector(selector, "el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)")


@pytest.mark.parametrize("mode", ["modern", "legacy"])
def test_renderer_show_if_steps_and_fields(page, base_url, mode):
    open_demo(page, base_url, mode)
    assert not visible(page, '.fr-step[data-step-id="dia_chi"]')
    assert not visible(page, '.fr-field[data-field-key="ten_moi"]')
    page.check('.dkkd-cb[value="A2"]')
    assert visible(page, '.fr-step[data-step-id="dia_chi"]')
    assert not visible(page, '.fr-field[data-field-key="ten_moi"]')
    page.check('.dkkd-cb[value="A1"]')
    assert visible(page, '.fr-field[data-field-key="ten_moi"]')
    page.uncheck('.dkkd-cb[value="A2"]')
    assert not visible(page, '.fr-step[data-step-id="dia_chi"]')
    # Bước bị ẩn không bị bắt buộc nhập
    keys = page.evaluate("validateRequiredFields(window.wizardState.schema).map(e => e.name || e.prop)")
    assert "dia_chi_moi" not in keys and "ten_moi" in keys


@pytest.mark.parametrize("mode", ["modern", "legacy"])
def test_renderer_list_add_remove_and_collect(page, base_url, mode):
    open_demo(page, base_url, mode)
    assert page.locator('.fr-list-item[data-list-item="co_dong"]').count() == 1
    page.fill('.lf-field[data-list="co_dong"][data-idx="0"][data-key="ho_ten"]', "Nguyễn A")
    page.fill('.lf-field[data-list="co_dong"][data-idx="0"][data-key="ty_le"]', "60")
    page.click('button:has-text("+ Thêm")')
    assert page.locator('.fr-list-item[data-list-item="co_dong"]').count() == 2
    # Giữ dữ liệu đã nhập sau khi vẽ lại; tối đa 2 dòng -> hết nút Thêm
    assert page.input_value('.lf-field[data-list="co_dong"][data-idx="0"][data-key="ho_ten"]') == "Nguyễn A"
    assert page.locator('button:has-text("+ Thêm")').count() == 0
    page.fill('.lf-field[data-list="co_dong"][data-idx="1"][data-key="ho_ten"]', "Trần B")
    page.fill('.lf-field[data-list="co_dong"][data-idx="1"][data-key="ty_le"]', "40")
    page.evaluate("collectFormData()")
    data = page.evaluate("wizardDataForSchema(window.wizardState.schema, false).co_dong")
    assert data == [{"ho_ten": "Nguyễn A", "ty_le": "60"}, {"ho_ten": "Trần B", "ty_le": "40"}]
    assert not any("co_dong" in (e.get("name") or "") for e in page.evaluate("validateRequiredFields(window.wizardState.schema)"))
    page.click('.fr-list-item[data-idx="0"] button:has-text("Xóa")')
    assert page.evaluate("window.wizardState.formData.co_dong.map(x => x.ho_ten)") == ["Trần B"]


def test_renderer_inline_errors_on_blur(page, base_url):
    open_demo(page, base_url, "modern")
    page.fill('input[name="lh_cccd"]', "123")
    page.fill('input[name="lh_ngay_sinh"]', "01/01/2015")
    page.focus('.lf-field[data-key="ho_ten"]')  # rời khỏi ô ngày sinh
    assert "12 chữ số" in page.inner_text('.fr-error[data-error-for="lh_cccd"]')
    assert "18 tuổi" in page.inner_text('.fr-error[data-error-for="lh_ngay_sinh"]')
    # Ô chưa chạm vào thì chưa báo lỗi; bấm Tiếp thì báo hết
    assert page.inner_text('.fr-error[data-error-for="co_dong.0.ty_le"]') == ""
    page.evaluate("ensureRequiredFields()")
    assert "bắt buộc" in page.inner_text('.fr-error[data-error-for="co_dong.0.ty_le"]')
    page.fill('input[name="lh_cccd"]', "001090001234")
    page.focus('input[name="lh_ngay_sinh"]')
    assert page.inner_text('.fr-error[data-error-for="lh_cccd"]') == ""


def test_renderer_escapes_list_values(page, base_url):
    open_demo(page, base_url, "modern")
    page.evaluate("""xss => { window.wizardState.formData.co_dong = [{ho_ten: xss, ty_le: xss}];
                              window.wizardState.formData.lh_cccd = xss; renderStep2Form(window.wizardState.schema); }""", XSS)
    page.wait_for_timeout(200)
    assert page.evaluate("window.__xss || 0") == 0
    assert page.input_value('.lf-field[data-key="ho_ten"]') == XSS


def test_renderer_payload_uses_schema_keys(page, base_url):
    """Dữ liệu gửi lên dùng đúng key của schema: checkbox_group 'thay_doi' và list 'co_dong'."""
    open_demo(page, base_url, "modern")
    page.check('.dkkd-cb[value="A2"]')
    page.fill('input[name="dia_chi_moi"]', "Số 2 Phố B")
    page.fill('input[name="lh_cccd"]', "001090001234")
    page.fill('.lf-field[data-key="ho_ten"]', "Nguyễn A")
    page.fill('.lf-field[data-key="ty_le"]', "100")
    page.evaluate("collectFormData(); window.wizardState.step = 4;")
    assert page.evaluate("validateRequiredFields(window.wizardState.schema).length") == 0
    with page.expect_request(lambda r: "/api/documents/generate" in r.url) as req:
        page.evaluate("generateDocuments()")
    data = req.value.post_data_json["data"]
    assert data["thay_doi"] == ["A2"]
    assert data["co_dong"][0]["ho_ten"] == "Nguyễn A"


def test_chuyen_nhuong_2tv_on_generic_form(page, base_url):
    """Chuyển nhượng 2 TV chạy trên bộ máy chung: bên A/B chọn từ danh sách thành viên cũ/mới."""
    open_template(page, base_url, "Chuyển nhượng Công ty TNHH 2 TV")
    page.evaluate("""() => {
        const set = (n, v) => { const el = document.querySelector(`[name="${n}"]`); el.value = v; };
        set('ten_cong_ty_vn', 'CÔNG TY TNHH A'); set('ma_so_thue', '0101234567');
        set('ddpl_cu_ho_ten', 'NGƯỜI CŨ'); set('ddpl_cu_so_cccd', '001090000100');
        set('ddpl_ho_ten', 'NGƯỜI MỚI'); set('ddpl_so_cccd', '001090000200');
    }""")
    lf = 'xpath=//*[@data-list="{0}" and @data-idx="{1}" and @data-key="{2}"]'
    for i, (name, cccd) in enumerate([("CŨ MỘT", "001090000001"), ("CŨ HAI", "001090000002")]):
        page.fill(lf.format("tv_cu", i, "ho_ten"), name)
        page.fill(lf.format("tv_cu", i, "so_cccd"), cccd)
        page.fill(lf.format("tv_cu", i, "dia_chi_day_du"), f"Số {i + 1} Phố Huế, Phường Hai Bà Trưng, Thành phố Hà Nội")
    for i, name in enumerate(["MỚI MỘT", "MỚI HAI"]):
        page.fill(f'.m-field[data-idx="{i}"][data-prop="ho_ten"]', name)
        page.fill(f'.m-field[data-idx="{i}"][data-prop="von_gop"]', "500000000")
        page.fill(f'.m-field[data-idx="{i}"][data-prop="ty_le"]', "50")
    # Ô chọn bên A/B cập nhật theo họ tên vừa nhập
    ben_a = lf.format("chuyen_nhuong", 0, "ben_a")
    labels = page.eval_on_selector(ben_a, "s => [...s.options].map(o => o.textContent)")
    assert labels == ["-- Chọn --", "#1: CŨ MỘT", "#2: CŨ HAI"]
    page.select_option(ben_a, "1")
    page.select_option(lf.format("chuyen_nhuong", 0, "ben_b"), "0")
    page.fill(lf.format("chuyen_nhuong", 0, "gia_tri_so"), "250000000")
    assert page.input_value(lf.format("chuyen_nhuong", 0, "gia_tri_so")) == "250.000.000"
    page.evaluate("collectFormData()")
    assert page.evaluate("validateRequiredFields(window.wizardState.schema).map(e => e.label)") == []
    page.evaluate("nextStep()")
    assert page.evaluate("window.wizardState.step") == 4
    with page.expect_response(lambda r: "/api/documents/generate" in r.url) as resp:
        page.evaluate("generateDocuments()")
    body = resp.value.request.post_data_json["data"]
    assert body["chuyen_nhuong"][0]["ben_a"] == "1" and body["chuyen_nhuong"][0]["ben_b"] == "0"
    assert resp.value.status == 200, resp.value.text()


def test_list_errors_point_to_their_own_list(page, base_url):
    """Hai danh sách cùng có ô 'ho_ten': lỗi của tv_cu không được tô đỏ ô của danh sách khác."""
    open_template(page, base_url, "Chuyển nhượng Công ty TNHH 2 TV")
    page.evaluate("ensureRequiredFields()")
    lf = '[data-list="tv_cu"][data-idx="0"][data-key="ho_ten"]'
    assert page.eval_on_selector(f".lf-field{lf}", "el => el.classList.contains('input-invalid')")
    assert "bắt buộc" in page.inner_text('.fr-error[data-error-for="tv_cu.0.ho_ten"]')
    assert "bắt buộc" in page.inner_text('.fr-error[data-error-for="chuyen_nhuong.0.ben_a"]')


def test_chuyen_doi_on_generic_form(page, base_url):
    """Chuyển đổi 1TV -> 2TV chạy trên bộ máy chung: ô vốn giữ lại chỉ hiện khi chuyển nhượng một phần."""
    open_template(page, base_url, "Chuyển đổi loại hình 1TV sang 2 TV")
    giu_lai = '.fr-field[data-field-key="csh_von_giu_lai"]'
    assert visible(page, giu_lai)
    page.select_option('select[name="hinh_thuc_cn"]', "toan_bo")
    assert not visible(page, giu_lai)
    page.select_option('select[name="hinh_thuc_cn"]', "mot_phan")
    page.evaluate("""() => {
        const set = (n, v) => { const el = document.querySelector(`[name="${n}"]`); el.value = v; };
        set('ma_so_thue', '0101234567'); set('ten_cong_ty_vn_cu', 'CÔNG TY TNHH MỘT THÀNH VIÊN A');
        set('dia_chi_so_nha', 'Số 1 Phố Huế'); set('dia_chi_xa_phuong', 'Phường Hai Bà Trưng');
        set('dia_chi_tinh_thanh', 'Thành phố Hà Nội'); set('von_dieu_le_so', '1.000.000.000');
        set('csh_ho_ten', 'CHỦ CŨ'); set('csh_so_cccd', '001080000011');
        set('csh_von_giu_lai', '600.000.000'); set('csh_ty_le', '60');
        set('ddpl_ho_ten', 'CHỦ CŨ'); set('ddpl_so_cccd', '001080000011');
    }""")
    page.fill('.m-field[data-idx="0"][data-prop="ho_ten"]', "THÀNH VIÊN MỚI")
    page.fill('.m-field[data-idx="0"][data-prop="so_cccd"]', "001190000022")
    page.fill('.m-field[data-idx="0"][data-prop="von_gop"]', "400000000")
    page.fill('.m-field[data-idx="0"][data-prop="ty_le"]', "40")
    page.evaluate("collectFormData()")
    assert page.evaluate("validateRequiredFields(window.wizardState.schema).map(e => e.label)") == []
    page.evaluate("window.wizardState.step = 4")
    with page.expect_response(lambda r: "/api/documents/generate" in r.url) as resp:
        page.evaluate("generateDocuments()")
    assert resp.value.status == 200, resp.value.text()
    body = resp.value.request.post_data_json
    assert body["data"]["hinh_thuc_cn"] == "mot_phan" and "cd1tv2tv_data" not in body["special_payload"]


# ---------- Trang quản trị (Mục 10.1) ----------

def test_admin_login_logout_page(page, base_url, tmp_path, monkeypatch):
    import config
    from services import auth

    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")
    auth.create_user(XSS, "mat-khau-thu-nghiem-123")  # tên đăng nhập có ký tự HTML: phải được escape
    page.goto(f"{base_url}/#/admin")
    page.wait_for_selector("#admin-login-form")
    page.fill("#admin-username", XSS)
    page.fill("#admin-password", "sai-mat-khau-000")
    page.click("#admin-login-form button[type=submit]")
    page.wait_for_function("document.getElementById('admin-login-error') && "
                           "document.getElementById('admin-login-error').textContent.includes('Sai')")
    page.fill("#admin-username", XSS)
    page.fill("#admin-password", "mat-khau-thu-nghiem-123")
    page.click("#admin-login-form button[type=submit]")
    page.wait_for_selector("#admin-current-user")
    assert page.inner_text("#admin-current-user") == XSS
    assert page.evaluate("window.__xss || 0") == 0
    # Tải lại trang: vẫn đăng nhập (cookie phiên), JS không đọc được cookie (HttpOnly)
    page.reload()
    page.wait_for_selector("#admin-current-user")
    assert "nac_admin_session" not in page.evaluate("document.cookie")
    page.click("#admin-logout")
    page.wait_for_selector("#admin-login-form")


def test_admin_edit_power_of_attorney_recipient(page, base_url, tmp_path, monkeypatch):
    """Trang quản trị: sửa người nhận ủy quyền (Bên B của mọi Giấy ủy quyền), giá trị có ký tự HTML được escape."""
    import config
    from services import auth, uy_quyen

    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")
    auth.create_user("quantri", "mat-khau-thu-nghiem-123")
    page.goto(f"{base_url}/#/admin")
    page.wait_for_selector("#admin-login-form")
    page.fill("#admin-username", "quantri")
    page.fill("#admin-password", "mat-khau-thu-nghiem-123")
    page.click("#admin-login-form button[type=submit]")
    page.click("#admin-open-uy-quyen")
    page.wait_for_selector("#uq-ho_ten")
    assert page.input_value("#uq-so_cccd") == uy_quyen.defaults()["so_cccd"]
    page.fill("#uq-ho_ten", "Trần Thị Nhận Thử")
    page.fill("#uq-gioi_tinh", "Nữ")
    page.fill("#uq-so_cccd", "123")
    page.click('[data-action="save-uy-quyen"]')
    page.wait_for_function("document.getElementById('admin-message').textContent.includes('12 chữ số')")
    page.fill("#uq-so_cccd", "001191000099")
    page.fill("#uq-dia_chi", XSS)
    page.click('[data-action="save-uy-quyen"]')
    page.wait_for_function("document.getElementById('admin-message').textContent.includes('Đã lưu')")
    assert page.input_value("#uq-dia_chi") == XSS and page.evaluate("window.__xss || 0") == 0
    saved = uy_quyen.get()
    assert saved["ho_ten"] == "Trần Thị Nhận Thử" and saved["so_cccd"] == "001191000099"
    assert uy_quyen.context_values()["uq_danh_xung"] == "Bà"


# ---------- Quản lý bộ mẫu trên trang quản trị (Mục 10.2, 10.4) ----------

def test_admin_draft_publish_rollback_flow(page, base_url, tmp_path, monkeypatch):
    """Trên giao diện: tạo bản nháp, tải file Word, quét, xuất bản, quay lại bản cũ (bản sao tạm của bộ mẫu)."""
    import io
    import json as _json
    import shutil

    import docx

    import config
    from services import auth, render_service

    name = "Tạm dừng công ty TNHH 1 TV"
    root = tmp_path / "templates"
    shutil.copytree(config.TEMPLATES_DIR / name, root / name)
    for mod in (config, render_service):
        monkeypatch.setattr(mod, "TEMPLATES_DIR", root)
    monkeypatch.setattr(config, "TEMPLATE_DRAFTS_DIR", tmp_path / "drafts")
    monkeypatch.setattr(config, "TEMPLATE_VERSIONS_DIR", tmp_path / "versions")
    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")
    auth.create_user("quantri", "mat-khau-thu-nghiem-123")
    tid = _json.loads((root / name / "_schema.json").read_text(encoding="utf-8"))["id"]

    page.goto(f"{base_url}/#/admin")
    page.wait_for_selector("#admin-login-form")
    page.fill("#admin-username", "quantri")
    page.fill("#admin-password", "mat-khau-thu-nghiem-123")
    page.click("#admin-login-form button[type=submit]")
    page.wait_for_selector("#admin-templates")
    assert "v1" in page.inner_text("#admin-templates")
    page.click(f'[data-action="open-template"][data-id="{tid}"]')
    page.wait_for_selector('[data-action="new-draft"]')
    page.click('[data-action="new-draft"]')
    page.wait_for_selector("#admin-draft-files")

    # Tải lên bản sửa của một file Word (cùng tên -> thay file cũ)
    target = sorted((root / name).glob("*.docx"))[0]
    d = docx.Document(str(target))
    d.add_paragraph("NỘI DUNG MỚI TỪ TRANG QUẢN TRỊ")
    buf = io.BytesIO()
    d.save(buf)
    page.set_input_files("#admin-upload", files=[{"name": target.name, "buffer": buf.getvalue(),
                                                   "mimeType": "application/octet-stream"}])
    page.wait_for_function("document.getElementById('admin-message') && "
                           "document.getElementById('admin-message').textContent.includes('Đã tải lên')")

    page.click('[data-action="lint"]')
    page.wait_for_function("document.getElementById('admin-lint').textContent.includes('0 lỗi')")
    with page.expect_download() as dl:
        page.click('[data-action="preview"]')
    assert dl.value.suggested_filename == "ban_nhap_sinh_thu.zip"

    page.fill("#admin-note", "Thêm đoạn nội dung mới")
    page.click("#admin-publish-form button[type=submit]")
    page.wait_for_selector("#admin-versions")
    assert "Đã xuất bản phiên bản v2" in page.inner_text("#admin-message")
    assert "NỘI DUNG MỚI TỪ TRANG QUẢN TRỊ" in "\n".join(p.text for p in docx.Document(str(root / name / target.name)).paragraphs)

    # Quay lại v1
    page.evaluate("window.confirm = () => true")  # fixture `page` tự đóng hộp thoại; ở đây đồng ý xác nhận
    page.click('[data-action="rollback"][data-version="1"]')
    page.wait_for_function("document.getElementById('admin-message').textContent.includes('v3')")
    assert "NỘI DUNG MỚI TỪ TRANG QUẢN TRỊ" not in "\n".join(p.text for p in docx.Document(str(root / name / target.name)).paragraphs)
    assert page.locator('#admin-versions tbody tr').count() == 3


def test_admin_suggest_fields_ui(page, base_url, tmp_path, monkeypatch):
    """Trang bản nháp: tải mẫu có biến mới -> Gợi ý trường còn thiếu -> Thêm vào cấu hình."""
    import io
    import shutil

    import docx

    import config
    from services import auth, render_service, template_store

    name = "Tạm dừng công ty TNHH 1 TV"
    root = tmp_path / "templates"
    shutil.copytree(config.TEMPLATES_DIR / name, root / name)
    for mod in (config, render_service):
        monkeypatch.setattr(mod, "TEMPLATES_DIR", root)
    monkeypatch.setattr(config, "TEMPLATE_DRAFTS_DIR", tmp_path / "drafts")
    monkeypatch.setattr(config, "TEMPLATE_VERSIONS_DIR", tmp_path / "versions")
    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")
    auth.create_user("quantri", "mat-khau-thu-nghiem-123")
    user = {"id": 1}
    tid = template_store.list_templates()[0]["id"]
    draft = template_store.create_draft(tid, user)
    target = sorted((root / name).glob("*.docx"))[0]
    d = docx.Document(str(target))
    d.add_paragraph("Ký ngày {{ ngay_ky_hop_dong }}, liên hệ {{ nguoi_lien_he_ho_ten }} - {{ nguoi_lien_he_so_cccd }}")
    buf = io.BytesIO()
    d.save(buf)
    template_store.put_docx(draft["id"], target.name, buf.getvalue(), user)

    page.goto(f"{base_url}/#/admin")
    page.wait_for_selector("#admin-login-form")
    page.fill("#admin-username", "quantri")
    page.fill("#admin-password", "mat-khau-thu-nghiem-123")
    page.click("#admin-login-form button[type=submit]")
    page.wait_for_selector("#admin-templates")
    page.click(f'[data-action="open-template"][data-id="{tid}"]')
    page.wait_for_selector(f'[data-action="open-draft"][data-id="{draft["id"]}"]')
    page.click(f'[data-action="open-draft"][data-id="{draft["id"]}"]')
    page.wait_for_selector('[data-action="suggest"]')
    page.click('[data-action="suggest"]')
    page.wait_for_selector("#admin-suggest-table")
    assert page.locator(".admin-suggest-cb").evaluate_all("els => els.map(e => e.value)") == \
        ["ngay_ky_hop_dong", "nguoi_lien_he"]
    page.click('[data-action="apply-suggestions"]')
    page.wait_for_function("document.getElementById('admin-message') && "
                           "document.getElementById('admin-message').textContent.includes('Đã thêm 2 trường')")
    assert '"bo_sung"' in page.input_value("#admin-schema")
    page.click('[data-action="suggest"]')
    page.wait_for_function("document.getElementById('admin-suggestions').textContent.includes('đều đã có ô nhập')")


OCR_FAKE = {
    "success": True,
    "data": {
        "ho_ten": "TRẦN THỊ MAI", "gioi_tinh": "Nữ", "ngay_sinh": "02/03/1985", "so_cccd": "034185012345",
        "dia_chi": "Tổ 1, Phường Tây Hồ, Thành phố Hà Nội", "dia_chi_so_nha": "Tổ 1",
        "dia_chi_xa_phuong": "Phường Tây Hồ", "dia_chi_quan_huyen": "", "dia_chi_tinh_thanh": "Thành Phố Hà Nội",
        "nguon": "ocr", "can_kiem_tra": ["ho_ten", "dia_chi_so_nha"],
    },
}
PNG_FILE = {"name": "a.png", "mimeType": "image/png", "buffer": b"\x89PNG\r\n\x1a\n"}


def stub_ocr(page):
    import json
    page.route("**/api/ocr/vneid", lambda r: r.fulfill(content_type="application/json", body=json.dumps(OCR_FAKE)))


def test_scan_fills_only_that_list_item(page, base_url):
    open_template(page, base_url, "Chuyển nhượng Công ty TNHH 2 TV")
    stub_ocr(page)
    page.locator("#ocr-tv_cu-0").set_input_files(PNG_FILE)
    field = lambda i, k: page.locator(f'.lf-field[data-list="tv_cu"][data-idx="{i}"][data-key="{k}"]')
    page.wait_for_function("""document.querySelector('.lf-field[data-list="tv_cu"][data-idx="0"][data-key="ho_ten"]').value !== ''""")
    assert field(0, "so_cccd").input_value() == "034185012345"
    assert field(0, "dia_chi_day_du").input_value() == "Tổ 1, Phường Tây Hồ, Thành phố Hà Nội"
    assert field(0, "gioi_tinh").input_value() == "Nữ"
    assert field(1, "ho_ten").input_value() == ""
    assert page.evaluate("wizardState.formData.tv_cu[0].ho_ten") == "TRẦN THỊ MAI"
    assert field(0, "dia_chi_day_du").evaluate("e => e.style.borderColor") == "var(--accent-orange)"


@pytest.mark.parametrize("template,prefix", [
    ("Tăng vốn công ty TNHH 1 TV", "ddpl"),
    ("Thay đổi địa chỉ và thuế TNHH 2 TV", "ktt"),
])
def test_scan_fills_loose_person_fields(page, base_url, template, prefix):
    open_template(page, base_url, template)
    stub_ocr(page)
    page.locator(f"#ocr-file-{prefix}").set_input_files(PNG_FILE)
    page.wait_for_function("p => document.getElementById(`input-${p}_so_cccd`).value !== ''", arg=prefix)
    assert page.locator(f"#input-{prefix}_ho_ten").input_value() == "TRẦN THỊ MAI"
    assert page.evaluate("p => wizardState.formData[`${p}_so_cccd`]", prefix) == "034185012345"


# ---------- Mục 8.3: lối tắt sang thủ tục gộp ----------

def test_shortcut_opens_combined_procedure_with_data(page, base_url):
    """Từ Tăng vốn TNHH 1 TV: nút lối tắt mở thủ tục gộp, giữ dữ liệu, đặt sẵn loại hình và nội dung A4."""
    open_template(page, base_url, "Tăng vốn công ty TNHH 1 TV")
    page.fill('[name="ma_so_thue"]', "0101234567")
    page.fill('[name="ten_cong_ty_vn"]', "CÔNG TY TNHH MỘT THÀNH VIÊN A")
    page.fill('[name="von_moi_so"]', "2.000.000.000")
    page.fill('[name="csh_ho_ten"]', "CHỦ SỞ HỮU")
    page.click("#btn-combined-shortcut")
    page.wait_for_function("window.wizardState.schema && window.wizardState.schema.name === 'Thay đổi nội dung ĐKKD'"
                           " && document.querySelector('[name=\"loai_hinh\"]')")
    page.wait_for_load_state("networkidle")
    assert page.input_value('[name="ma_so_thue"]') == "0101234567"
    assert page.input_value('[name="ten_cong_ty_vn"]') == "CÔNG TY TNHH MỘT THÀNH VIÊN A"
    assert page.input_value('[name="loai_hinh"]') == "tnhh_1tv"
    assert page.input_value('[name="hinh_thuc_thay_doi_von"]') == "tang"
    assert page.input_value('[name="von_dieu_le_so"]') == "2.000.000.000"
    assert page.input_value('[name="chu_tich_ho_ten"]') == "CHỦ SỞ HỮU"
    checked = page.evaluate("Array.from(document.querySelectorAll('.dkkd-cb:checked')).map(c => c.value)")
    assert checked == ["A4"]
    assert visible(page, '[name="von_dieu_le_so"]')
    # Bộ đích không có lối tắt
    assert page.locator("#btn-combined-shortcut").count() == 0


@pytest.mark.parametrize("template", ["Tạm dừng công ty TNHH 1 TV", "Thành lập mới công ty TNHH 2 TV"])
def test_no_shortcut_without_config(page, base_url, template):
    open_template(page, base_url, template)
    assert page.locator("#btn-combined-shortcut").count() == 0
