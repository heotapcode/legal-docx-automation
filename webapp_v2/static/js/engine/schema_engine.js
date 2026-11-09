/**
 * Lõi đọc _schema.json v2 phía trình duyệt: điều kiện hiển thị và kiểm tra dữ liệu.
 *
 * Hành vi PHẢI giống hệt services/schema_engine.py (backend). Cả hai bản chạy cùng bộ ca kiểm thử
 * tests/engine_cases.json (tests/test_schema_engine.py), nên sửa một bên thì sửa cả bên kia.
 * Dùng được trong trình duyệt (window.SchemaEngine) và Node.js (require).
 *
 * Đặc tả: docs/schema-v2.md (mục 3.2 validate, 3.3 rules, 4 điều kiện).
 */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) module.exports = factory();
    else root.SchemaEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
    'use strict';

    const LIST_TYPES = new Set(['list', 'person_list']);

    // ---------- Giá trị ----------

    function isBlank(v) {
        if (v === null || v === undefined) return true;
        if (Array.isArray(v)) return v.length === 0;
        if (typeof v === 'object') return Object.keys(v).length === 0;
        return String(v).trim() === '';
    }

    /** '1,000,000' / '1.000.000' / '33.33' / 5 -> số; không đọc được -> null. */
    function toNumber(v) {
        if (v === null || v === undefined || typeof v === 'boolean') return null;
        if (typeof v === 'number') return Number.isFinite(v) ? v : null;
        let s = String(v).trim().replace(/ /g, '');
        if (!s) return null;
        const neg = s.startsWith('-');
        s = s.replace(/^[+-]+/, '');
        if (/^\d{1,3}([.,]\d{3})+$/.test(s)) s = s.replace(/[.,]/g, '');
        else s = s.replace(/,/g, '.');
        if (!/^(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(s)) return null;
        const n = Number(s);
        if (!Number.isFinite(n)) return null;
        return neg ? -n : n;
    }

    /** 'DD/MM/YYYY' hoặc 'YYYY-MM-DD' -> {y, m, d}; ngày không hợp lệ -> null. */
    function parseDate(v) {
        const s = String(v === null || v === undefined ? '' : v).trim();
        let y, m, d, mt;
        if ((mt = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(s))) { d = +mt[1]; m = +mt[2]; y = +mt[3]; }
        else if ((mt = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s))) { y = +mt[1]; m = +mt[2]; d = +mt[3]; }
        else return null;
        const dt = new Date(Date.UTC(y, m - 1, d));
        if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== d) return null;
        return { y, m, d };
    }

    function sameValue(a, b) {
        if (a === b) return true;
        if (typeof a === 'object' || typeof b === 'object') return JSON.stringify(a) === JSON.stringify(b);
        return false;
    }

    // ---------- Điều kiện ----------

    /** Điều kiện rỗng/null -> true. Xem docs/schema-v2.md mục 4. */
    function evalCondition(cond, data) {
        if (!cond || Object.keys(cond).length === 0) return true;
        data = data || {};
        if ('all' in cond) return cond.all.every(c => evalCondition(c, data));
        if ('any' in cond) return cond.any.some(c => evalCondition(c, data));
        const value = Object.prototype.hasOwnProperty.call(data, cond.field) ? data[cond.field] : null;
        if ('equals' in cond && !sameValue(value, cond.equals)) return false;
        if ('not_equals' in cond && sameValue(value, cond.not_equals)) return false;
        if ('contains' in cond && !(Array.isArray(value) && value.some(x => sameValue(x, cond.contains)))) return false;
        if ('in' in cond && !cond.in.some(x => sameValue(x, value))) return false;
        if ('not_empty' in cond && (!isBlank(value)) !== Boolean(cond.not_empty)) return false;
        return true;
    }

    function visibleSteps(schema, data) {
        return ((schema && schema.steps) || []).filter(s => evalCondition(s.show_if, data));
    }

    function visibleFields(schema, data) {
        const out = [];
        visibleSteps(schema, data).forEach(step => (step.fields || []).forEach(f => {
            if (evalCondition(f.show_if, data)) out.push(f);
        }));
        return out;
    }

    // ---------- Kiểm tra dữ liệu ----------

    function fmt(n) { return String(+n.toPrecision(6)); }

    function err(errors, key, label, code, message, index) {
        const e = { key, label, code, message };
        if (index !== undefined && index !== null) e.index = index;
        errors.push(e);
    }

    /** Giá trị của select có options_from là số thứ tự (0, 1, ...) của phần tử trong list nguồn. */
    function refIndex(value, items) {
        const s = String(value).trim();
        if (!/^\d+$/.test(s)) return null;
        const i = parseInt(s, 10);
        return Array.isArray(items) && i < items.length ? i : null;
    }

    function checkValue(field, value, scope, errors, today, index, prefix, root) {
        const key = field.key, label = (prefix || '') + (field.label || field.key);
        if (isBlank(value) && 'default' in field) value = field.default;  // bỏ trống -> dùng giá trị mặc định
        if (isBlank(value)) {
            if (field.required) {
                err(errors, key, label, 'required',
                    field.type === 'checkbox_group' ? `${label}: chọn ít nhất 1 mục` : `${label}: bắt buộc nhập`, index);
            }
            return;
        }
        const rules = field.validate || {};
        const msg = rules.message;
        const sv = String(value).trim();
        if (field.options_from) {
            const source = (root || scope || {})[field.options_from];
            if (refIndex(value, source) === null) err(errors, key, label, 'options_from', msg || `${label}: chọn một mục trong danh sách`, index);
        }
        if (field.type === 'cccd' && !('pattern' in rules) && !/^\d{12}$/.test(sv)) {
            err(errors, key, label, 'pattern', msg || `${label}: số CCCD phải gồm 12 chữ số`, index);
        }
        if ('pattern' in rules && !new RegExp('^(?:' + rules.pattern + ')$').test(sv)) {
            err(errors, key, label, 'pattern', msg || `${label}: không đúng định dạng`, index);
        }
        const num = toNumber(value);
        if ('min' in rules && (num === null || num < rules.min)) err(errors, key, label, 'min', msg || `${label}: tối thiểu ${fmt(rules.min)}`, index);
        if ('max' in rules && (num === null || num > rules.max)) err(errors, key, label, 'max', msg || `${label}: tối đa ${fmt(rules.max)}`, index);
        [['greater_than', (a, b) => a > b, 'lớn hơn'], ['less_than', (a, b) => a < b, 'nhỏ hơn']].forEach(([code, op, word]) => {
            if (code in rules) {
                const other = toNumber(scope ? scope[rules[code]] : null);
                if (num !== null && other !== null && !op(num, other)) err(errors, key, label, code, msg || `${label}: phải ${word} ${rules[code]}`, index);
            }
        });
        if ('min_age' in rules) {
            const d = parseDate(value);
            let age = null;
            if (d) {
                age = today.y - d.y - ((today.m < d.m || (today.m === d.m && today.d < d.d)) ? 1 : 0);
            }
            if (age === null || age < rules.min_age) err(errors, key, label, 'min_age', msg || `${label}: chưa đủ ${rules.min_age} tuổi`, index);
        }
    }

    function checkList(field, items, root, errors, today) {
        const key = field.key, label = field.label || field.key;
        items = Array.isArray(items) ? items : [];
        const start = errors.length;
        const lo = 'min' in field ? field.min : (field.required ? 1 : 0);
        if (items.length < lo) err(errors, key, label, 'min_items', `${label}: cần ít nhất ${lo} (hiện có ${items.length})`);
        if ('max' in field && items.length > field.max) err(errors, key, label, 'max_items', `${label}: tối đa ${field.max} (hiện có ${items.length})`);
        let subs = (field.item || []).concat(field.extra_fields || []);
        if (field.type === 'person_list' && !subs.some(sub => sub.key === 'ho_ten')) {
            subs = [{ key: 'ho_ten', label: 'Họ và tên', type: 'text', required: true }].concat(subs);
        }
        items.forEach((raw, i) => {
            const item = raw && typeof raw === 'object' && !Array.isArray(raw) ? raw : {};
            subs.forEach(sub => {
                if (evalCondition(sub.show_if, item)) checkValue(sub, item[sub.key], item, errors, today, i, `${label} #${i + 1}: `, root);
            });
        });
        const subLabel = k => { const s = subs.find(x => x.key === k); return s ? (s.label || k) : k; };
        (field.rules || []).forEach(rule => {
            if ('sum' in rule) {
                const total = items.reduce((acc, it) => acc + ((it && typeof it === 'object' && toNumber(it[rule.sum])) || 0), 0);
                const target = rule.equals;
                // equals là số, hoặc tên một trường ở cấp gốc (vd "von_dieu_le_so")
                const targetN = (typeof target === 'string' && Object.prototype.hasOwnProperty.call(root, target))
                    ? toNumber(root[target]) : toNumber(target);
                if (targetN !== null && Math.abs(total - targetN) > 1e-6) {
                    err(errors, key, label, 'sum', rule.message || `${label}: tổng ${subLabel(rule.sum)} phải bằng ${fmt(targetN)} (hiện ${fmt(total)})`);
                }
            }
            if ('unique' in rule) {
                const seen = {};
                items.forEach((it, i) => {
                    const v = it && typeof it === 'object' ? it[rule.unique] : null;
                    if (isBlank(v)) return;
                    const k = String(v).trim();
                    if (k in seen) err(errors, key, label, 'unique', rule.message || `${label}: ${subLabel(rule.unique)} bị trùng (#${seen[k] + 1} và #${i + 1})`, i);
                    else seen[k] = i;
                });
            }
        });
        // Lỗi của một phần tử: ghi kèm danh sách chứa nó
        errors.slice(start).forEach(e => { if (e.index !== undefined) e.list = key; });
    }

    /** Danh sách lỗi [{key, label, code, message, index?}] cho các trường đang hiển thị. */
    function validate(schema, data, today) {
        data = data || {};
        if (typeof today === 'string') today = parseDate(today);
        if (!today) { const n = new Date(); today = { y: n.getFullYear(), m: n.getMonth() + 1, d: n.getDate() }; }
        const errors = [];
        visibleFields(schema, data).forEach(f => {
            if (LIST_TYPES.has(f.type)) checkList(f, data[f.key], data, errors, today);
            else if (f.type === 'person') {
                // Kiểu cũ: dữ liệu phẳng <key>_ho_ten, <key>_so_cccd...
                if (f.required) {
                    [['_ho_ten', 'Họ và tên'], ['_so_cccd', 'Số CCCD']].forEach(([suffix, subLabel]) => {
                        checkValue({ key: f.key + suffix, label: `${f.label || f.key}: ${subLabel}`, required: true },
                                   data[f.key + suffix], data, errors, today);
                    });
                }
            } else checkValue(f, data[f.key], data, errors, today);
        });
        return errors;
    }

    return { isBlank, toNumber, parseDate, evalCondition, visibleSteps, visibleFields, validate };
});
