/**
 * Bộ vẽ form chung theo _schema.json v2 (Mục 9, bước 4).
 *
 * - Vẽ các bước/ô theo schema; mỗi bước và mỗi ô có show_if được bọc trong phần tử có
 *   data-show-if, ẩn/hiện ngay khi dữ liệu thay đổi (không vẽ lại cả form nên không mất focus).
 * - Kiểu ô mới: date, cccd, percent, number, address, list (danh sách lặp tổng quát).
 *   Trong list: select có options_from = chọn một phần tử của list khác (giá trị là số thứ tự 0, 1...),
 *   money tự định dạng khi gõ.
 *   Kiểu cũ (text, money, mst_lookup, phone, email, select, person, person_list, transfer_list,
 *   checkbox_group) dùng lại renderField() của wizard.js để giữ OCR, tra MST, định dạng tiền.
 * - Báo lỗi ngay dưới ô khi người dùng rời khỏi ô (dùng SchemaEngine, cùng kết quả với backend).
 *
 * Dữ liệu: ô thường lưu ở wizardState.formData[key]; danh sách `list` lưu ở formData[key] (mảng).
 * Phụ thuộc: utils.js (escapeHtml, renderSelectOptions), engine/schema_engine.js, pages/wizard.js.
 */
(function (root) {
    'use strict';

    const NEW_TYPES = new Set(['date', 'cccd', 'percent', 'number', 'address', 'list']);
    const touched = new Set();

    function state() { return window.wizardState; }
    function fd() { return state().formData; }

    function showIfAttr(cond) {
        return cond ? ` data-show-if="${escapeHtml(JSON.stringify(cond))}"` : '';
    }

    function reqBadge(f) { return f.required ? ' <span class="text-error">*</span>' : ''; }

    // ---------- Ô kiểu mới ----------

    function inputAttrs(type) {
        switch (type) {
            case 'date': return { type: 'text', placeholder: 'DD/MM/YYYY', extra: 'inputmode="numeric" maxlength="10"' };
            case 'cccd': return { type: 'text', placeholder: '12 chữ số', extra: 'inputmode="numeric" maxlength="12"' };
            case 'percent': return { type: 'number', placeholder: '%', extra: 'step="0.01" min="0" max="100"' };
            case 'number': return { type: 'number', placeholder: '', extra: 'step="any"' };
            case 'money': return { type: 'text', placeholder: 'VD: 500.000.000', extra: '' };
            default: return { type: 'text', placeholder: '', extra: '' };
        }
    }

    /** Ô đơn (không phải list). `nameAttr` cho ô thường; ô trong list dùng data-list/data-idx/data-key. */
    function simpleInput(field, value, nameAttr) {
        const a = inputAttrs(field.type);
        const ph = field.placeholder || a.placeholder;
        return `<input type="${a.type}" ${nameAttr} value="${escapeHtml(value)}" class="form-control" ` +
            `placeholder="${escapeHtml(ph)}" ${a.extra}>`;
    }

    function fieldShell(field, inner, keyForError) {
        const help = field.help ? `<div class="text-xs text-secondary mt-1">${escapeHtml(field.help)}</div>` : '';
        return `
            <div class="form-group">
                <label class="form-label">${escapeHtml(field.label)}${reqBadge(field)}</label>
                ${inner}
                ${help}
                <div class="fr-error text-xs text-error mt-1" data-error-for="${escapeHtml(keyForError)}"></div>
            </div>`;
    }

    /** Lựa chọn của select có options_from: các phần tử hiện có của list nguồn, giá trị là số thứ tự. */
    function refOptions(sub) {
        const source = currentData()[sub.options_from];
        return (Array.isArray(source) ? source : []).map((it, i) => ({
            value: String(i),
            label: `#${i + 1}: ${(it && (it.ho_ten || it.HO_TEN)) || '(chưa nhập tên)'}`,
        }));
    }

    function refSelect(sub, attrs, value) {
        const cur = value === undefined || value === null ? '' : String(value);
        return `<select ${attrs} data-options-from="${escapeHtml(sub.options_from)}">` +
            `<option value="">-- Chọn --</option>${renderSelectOptions(refOptions(sub), cur)}</select>`;
    }

    /** Cập nhật lại nhãn các lựa chọn options_from khi list nguồn đổi (vd vừa sửa họ tên thành viên). */
    function refreshRefOptions(container) {
        (container || document).querySelectorAll('select[data-options-from]').forEach(sel => {
            const opts = refOptions({ options_from: sel.getAttribute('data-options-from') });
            const cur = sel.value;
            const html = `<option value="">-- Chọn --</option>${renderSelectOptions(opts, cur)}`;
            if (sel.__lastOptions !== html) { sel.innerHTML = html; sel.__lastOptions = html; }
        });
    }

    function formatMoney(el) {
        const raw = String(el.value || '').replace(/\D/g, '');
        el.value = raw ? Number(raw).toLocaleString('vi-VN') : '';
    }

    /** Nút quét CCCD/VNeID; handler lấy nút ngay sau input làm nơi báo trạng thái. */
    function scanControl(inputId, onchange) {
        return `<input type="file" id="${inputId}" accept="image/*" style="display: none;" onchange="${onchange}">` +
            `<button type="button" class="btn btn-ocr" onclick="document.getElementById('${inputId}').click()">` +
            `<i class="fa-solid fa-id-card"></i> Quét ảnh VNeID</button>`;
    }

    function isPersonItem(field) {
        const keys = (field.item || []).map(sub => sub.key);
        return keys.includes('ho_ten') && keys.includes('so_cccd');
    }

    /** Nút quét cho nhóm ô rời cùng tiền tố (vd ddpl_ho_ten + ddpl_so_cccd), đặt ngay trên ô họ tên. */
    function flatGroupScan(field, step) {
        const m = /^(.+)_ho_ten$/.exec(field.key);
        if (!m || !(step.fields || []).some(f => f.key === `${m[1]}_so_cccd`)) return '';
        const prefix = escapeHtml(m[1]);
        return `<div style="display: flex; justify-content: flex-end; margin-bottom: 6px;">` +
            scanControl(`ocr-file-${prefix}`, `handleOcrUpload(this, '${prefix}')`) + `</div>`;
    }

    function renderListField(field) {
        const key = field.key;
        const items = Array.isArray(fd()[key]) ? fd()[key] : (fd()[key] = []);
        const min = field.min || 0;
        while (items.length < min) items.push({});
        const cards = items.map((item, i) => {
            const subs = (field.item || []).map(sub => {
                const attrs = `data-list="${escapeHtml(key)}" data-idx="${i}" data-key="${escapeHtml(sub.key)}" class="form-control lf-field"`;
                let input;
                if (sub.type === 'select' && sub.options_from) {
                    input = refSelect(sub, attrs, item[sub.key]);
                } else if (sub.type === 'select') {
                    const opts = (window.getCatalogOptions ? getCatalogOptions(sub) : (sub.options || []));
                    input = `<select ${attrs}>${renderSelectOptions(opts, item[sub.key] || sub.default || '')}</select>`;
                } else {
                    const a = inputAttrs(sub.type);
                    const money = sub.type === 'money' ? ' data-money="1" inputmode="numeric"' : '';
                    input = `<input type="${a.type}" ${attrs}${money} value="${escapeHtml(item[sub.key])}" ` +
                        `placeholder="${escapeHtml(sub.placeholder || a.placeholder)}" ${a.extra}>`;
                }
                return `<div${showIfAttr(sub.show_if)} data-scope-list="${escapeHtml(key)}" data-scope-idx="${i}">` +
                    fieldShell(sub, input, `${key}.${i}.${sub.key}`) + `</div>`;
            }).join('');
            const canRemove = items.length > min;
            return `
                <div class="person-card fr-list-item" data-list-item="${escapeHtml(key)}" data-idx="${i}">
                    <div class="person-card-header">
                        <span class="font-bold text-sm">${escapeHtml(field.label)} #${i + 1}</span>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            ${isPersonItem(field) ? scanControl(`ocr-${escapeHtml(key)}-${i}`, `handleListOcrUpload(this, '${escapeHtml(key)}', ${i})`) : ''}
                            ${canRemove ? `<button type="button" class="btn btn-secondary btn-sm" onclick="FormRenderer.removeListItem('${escapeHtml(key)}', ${i})">Xóa</button>` : ''}
                        </div>
                    </div>
                    <div class="grid-form-2">${subs}</div>
                </div>`;
        }).join('');
        const canAdd = !field.max || items.length < field.max;
        return `
            <div class="form-group">
                <label class="form-label">${escapeHtml(field.label)}${reqBadge(field)}</label>
                <div class="fr-list" data-list="${escapeHtml(key)}">${cards}</div>
                ${canAdd ? `<button type="button" class="btn btn-secondary btn-sm mt-2" onclick="FormRenderer.addListItem('${escapeHtml(key)}')">+ Thêm</button>` : ''}
                <div class="fr-error text-xs text-error mt-1" data-error-for="${escapeHtml(key)}"></div>
            </div>`;
    }

    /** HTML của một ô (kiểu mới tự vẽ, kiểu cũ dùng renderField của wizard.js). */
    function renderOne(field) {
        if (!NEW_TYPES.has(field.type)) return window.renderField(field);
        if (field.type === 'list') return renderListField(field);
        const value = fd()[field.key] !== undefined ? fd()[field.key] : (field.default || '');
        return fieldShell(field, simpleInput(field, value, `name="${escapeHtml(field.key)}" id="input-${escapeHtml(field.key)}"`), field.key);
    }

    /**
     * HTML cho mọi bước của schema. wrapStep(step, index, total, innerHtml) trả HTML khung của một bước
     * (mỗi giao diện có khung riêng); bước/ô có show_if được bọc để ẩn/hiện.
     */
    function renderSteps(schema, wrapStep) {
        const steps = (schema && schema.steps) || [];
        return steps.map((step, i) => {
            const inner = (step.fields || []).map(f =>
                `<div class="fr-field" data-field-key="${escapeHtml(f.key)}"${showIfAttr(f.show_if)}>${flatGroupScan(f, step)}${renderOne(f)}</div>`
            ).join('');
            return `<div class="fr-step" data-step-id="${escapeHtml(step.id)}"${showIfAttr(step.show_if)}>${wrapStep(step, i, steps.length, inner)}</div>`;
        }).join('');
    }

    // ---------- Dữ liệu ----------

    /** Gom giá trị các ô trong danh sách `list` vào formData[key][idx][subkey]. */
    function collectLists(container) {
        (container || document).querySelectorAll('.lf-field').forEach(el => {
            const list = el.getAttribute('data-list');
            const idx = parseInt(el.getAttribute('data-idx'), 10);
            const key = el.getAttribute('data-key');
            if (!Array.isArray(fd()[list])) fd()[list] = [];
            if (!fd()[list][idx]) fd()[list][idx] = {};
            fd()[list][idx][key] = el.value;
        });
    }

    function currentData() {
        return window.wizardDataForSchema ? wizardDataForSchema(state().schema, false) : Object.assign({}, fd());
    }

    /** Ẩn/hiện bước và ô theo show_if trên dữ liệu hiện tại. */
    function applyVisibility(container) {
        const root = container || document;
        const data = currentData();
        root.querySelectorAll('[data-show-if]').forEach(el => {
            let cond = null;
            try { cond = JSON.parse(el.getAttribute('data-show-if')); } catch (e) { cond = null; }
            const listKey = el.getAttribute('data-scope-list');
            let scope = data;
            if (listKey !== null) {
                const items = data[listKey] || [];
                scope = items[parseInt(el.getAttribute('data-scope-idx'), 10)] || {};
            }
            el.style.display = SchemaEngine.evalCondition(cond, scope) ? '' : 'none';
        });
    }

    // ---------- Báo lỗi ngay ----------

    /** Lỗi thuộc một phần tử của `list` (kiểu mới) -> khóa danh sách; ngược lại null. */
    function listOfError(e) {
        if (e.index === undefined || !e.list) return null;
        const steps = (state().schema && state().schema.steps) || [];
        for (const st of steps) for (const f of (st.fields || [])) {
            if (f.key === e.list && f.type === 'list') return f.key;
        }
        return null;
    }

    function errorKey(e) {
        const list = listOfError(e);
        return list ? `${list}.${e.index}.${e.key}` : e.key;
    }

    /** Hiện lỗi dưới các ô người dùng đã rời khỏi (touched); `all` = hiện mọi lỗi (khi bấm Tiếp/Tải). */
    function showInlineErrors(container, all) {
        const root = container || document;
        root.querySelectorAll('.fr-error').forEach(el => { el.textContent = ''; });
        const errors = SchemaEngine.validate(state().schema, currentData());
        errors.forEach(e => {
            const k = errorKey(e);
            // Đã bấm Tiếp/Tải: coi mọi ô lỗi là đã chạm, để lỗi không biến mất khi ô mất focus
            if (all) touched.add(k);
            if (!all && !touched.has(k) && !touched.has(e.key)) return;
            const box = root.querySelector(`.fr-error[data-error-for="${CSS.escape(k)}"]`);
            if (box && !box.textContent) box.textContent = e.message;
        });
        return errors;
    }

    function keyOfInput(el) {
        if (el.classList.contains('lf-field')) return `${el.getAttribute('data-list')}.${el.getAttribute('data-idx')}.${el.getAttribute('data-key')}`;
        return el.getAttribute('name') || '';
    }

    /** Gắn sự kiện cho vùng form: thu dữ liệu, ẩn/hiện theo điều kiện, báo lỗi ngay. */
    function attach(container) {
        if (!container || container.__frAttached) return;
        container.__frAttached = true;
        const refresh = () => {
            if (window.collectFormData) collectFormData();
            applyVisibility(container);
            refreshRefOptions(container);
            showInlineErrors(container, false);
        };
        container.addEventListener('change', refresh);
        container.addEventListener('input', ev => {
            if (ev.target && ev.target.getAttribute && ev.target.getAttribute('data-money')) formatMoney(ev.target);
            if (window.collectFormData) collectFormData();
            applyVisibility(container);
            refreshRefOptions(container);
        });
        container.addEventListener('focusout', ev => {
            const k = ev.target && keyOfInput(ev.target);
            if (k) touched.add(k);
            refresh();
        });
        applyVisibility(container);
        refreshRefOptions(container);
    }

    function resetTouched() { touched.clear(); }

    // ---------- Thêm/xóa phần tử danh sách ----------

    /**
     * Thu dữ liệu, rồi gỡ các ô danh sách khỏi giao diện cũ trước khi vẽ lại: renderStep2Form có thể
     * gọi collectFormData() khi giao diện cũ còn trên trang, làm dòng vừa xóa bị ghi lại.
     */
    function mutateList(key, change) {
        if (window.collectFormData) collectFormData();
        if (!Array.isArray(fd()[key])) fd()[key] = [];
        change(fd()[key]);
        document.querySelectorAll('.lf-field').forEach(el => el.remove());
        if (window.renderStep2Form) renderStep2Form(state().schema);
    }

    function addListItem(key) { mutateList(key, list => list.push({})); }

    function removeListItem(key, idx) { mutateList(key, list => list.splice(idx, 1)); }

    root.FormRenderer = {
        NEW_TYPES, renderSteps, renderOne, collectLists, applyVisibility, showInlineErrors,
        attach, resetTouched, addListItem, removeListItem, listOfError, refreshRefOptions,
    };
})(typeof self !== 'undefined' ? self : this);
