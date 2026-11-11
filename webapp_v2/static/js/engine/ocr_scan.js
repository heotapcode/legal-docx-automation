/**
 * Quét CCCD/VNeID: gửi ảnh lên /api/ocr/vneid rồi điền vào thẻ một người (handleOcrUpload), một thành viên
 * (handleMemberOcrUpload) hoặc một phần tử của danh sách kiểu list (handleListOcrUpload).
 * Ô cần rà lại được viền cam (can_kiem_tra do máy chủ trả về).
 * Phụ thuộc: pages/wizard.js (wizardState, collectFormData, renderStep2Form).
 */
/** Gửi ảnh CCCD/VNeID lên máy chủ. Luôn trả {success, data?, message?}; lỗi mạng / lỗi HTTP có thông báo rõ. */
async function ocrRequest(fd) {
    let res;
    try {
        res = await fetch('/api/ocr/vneid', { method: 'POST', body: fd });
    } catch (err) {
        return { success: false, message: 'Không kết nối được máy chủ để đọc ảnh. Kiểm tra máy chủ còn chạy không rồi thử lại.' };
    }
    let body = null;
    try { body = await res.json(); } catch (err) { body = null; }
    if (!res.ok) {
        const detail = body && (body.message || (typeof body.detail === 'string' ? body.detail : ''));
        return { success: false, message: detail || `Máy chủ báo lỗi ${res.status} khi đọc ảnh. Vui lòng thử lại hoặc nhập tay.` };
    }
    return body || { success: false, message: 'Máy chủ trả về dữ liệu không đọc được. Vui lòng thử lại hoặc nhập tay.' };
}

window.handleOcrUpload = async function(fileInput, targetKey) {
    const file = fileInput.files[0];
    if (!file) return;

    // Lưu dữ liệu form hiện thời trước khi xử lý
    collectFormData();

    const btn = fileInput.nextElementSibling;
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang đọc VNeID...';
        btn.disabled = true;
    }

    try {
        const fd = new FormData();
        fd.append('image', file);
        fd.append('target', targetKey);

        const resData = await ocrRequest(fd);

        if (resData.success && resData.data) {
            const data = resData.data;
            const pfx = targetKey + '_';

            // Chuẩn hóa giới tính
            let gt = (data.gioi_tinh || '').trim();
            if (gt.toLowerCase() === 'nữ' || gt.toLowerCase() === 'nu' || gt.toLowerCase().includes('nữ')) {
                gt = 'Nữ';
            } else {
                gt = 'Nam';
            }

            // Populate inputs
            const mapProps = {
                ho_ten: data.ho_ten || '',
                gioi_tinh: gt,
                ngay_sinh: data.ngay_sinh || '',
                so_cccd: data.so_cccd || '',
                dia_chi_so_nha: data.dia_chi_so_nha || '',
                dia_chi_xa_phuong: data.dia_chi_xa_phuong || '',
                dia_chi_tinh_thanh: data.dia_chi_tinh_thanh || '',
                dia_chi_day_du: data.dia_chi || ''
            };

            for (const [k, v] of Object.entries(mapProps)) {
                const el = document.getElementById(`input-${pfx}${k}`);
                if (el) {
                    el.value = v || '';
                    el.style.borderColor = 'var(--accent-green)';
                }
                window.wizardState.formData[pfx + k] = v || '';
            }

            markOcrReview(data, k => document.getElementById(`input-${pfx}${k}`));

            if (data.dia_chi) {
                window.wizardState.formData[pfx + 'dia_chi_day_du'] = data.dia_chi;
            }

            if (btn) {
                btn.innerHTML = ocrDoneLabel(data);
                btn.disabled = false;
            }
        } else {
            alert(resData.message || 'Không nhận diện được thông tin từ ảnh VNeID. Vui lòng kiểm tra lại ảnh.');
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    } catch (err) {
        console.error('Lỗi OCR:', err);
        alert('Có lỗi xảy ra khi xử lý ảnh VNeID.');
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    } finally {
        fileInput.value = '';
        if (btn) btn.disabled = false;
    }
};

// Ô cần người dùng rà lại sau khi đọc CCCD (đọc OCR có thể sai dấu, hoặc dữ liệu không khớp)
function markOcrReview(data, getEl) {
    const keys = data.can_kiem_tra || [];
    // Biểu mẫu chỉ có một ô địa chỉ đầy đủ thì cờ của các phần địa chỉ dồn về ô đó
    keys.concat(keys.some(k => k.startsWith('dia_chi')) ? ['dia_chi_day_du'] : []).forEach(k => {
        const el = getEl(k);
        if (el) el.style.borderColor = 'var(--accent-orange)';
    });
}

function ocrDoneLabel(data) {
    const source = data.nguon === 'qr' ? 'QR' : 'OCR';
    return (data.can_kiem_tra || []).length
        ? `<i class="fa-solid fa-triangle-exclamation"></i> Đã đọc ${source}, hãy rà ô viền cam`
        : `<i class="fa-solid fa-check text-success"></i> Đã nhận diện (${source})`;
}

window.handleMemberOcrUpload = async function(fileInput, memberIdx) {
    const file = fileInput.files[0];
    if (!file) return;

    // Lưu ngay toàn bộ dữ liệu form hiện thời (thông tin công ty, ĐDPL, các thành viên khác)
    collectFormData();

    const btn = fileInput.nextElementSibling;
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang đọc VNeID...';
        btn.disabled = true;
    }

    try {
        const fd = new FormData();
        fd.append('image', file);
        fd.append('target', `member_${memberIdx}`);

        const resData = await ocrRequest(fd);

        if (resData.success && resData.data) {
            const data = resData.data;
            const targetMember = window.wizardState.thanhVienList[memberIdx];
            if (targetMember) {
                targetMember.ho_ten = data.ho_ten || '';
                targetMember.gioi_tinh = data.gioi_tinh || 'Nam';
                targetMember.ngay_sinh = data.ngay_sinh || '';
                targetMember.so_cccd = data.so_cccd || '';
                targetMember.dia_chi_so_nha = data.dia_chi_so_nha || '';
                targetMember.dia_chi_xa_phuong = data.dia_chi_xa_phuong || '';
                targetMember.dia_chi_tinh_thanh = data.dia_chi_tinh_thanh || '';
            }

            // Điền trực tiếp vào DOM của thẻ thành viên tương ứng, tránh re-render làm mất thông tin công ty
            const card = document.getElementById(`member-card-${memberIdx}`);
            if (card) {
                const mapProps = {
                    ho_ten: data.ho_ten || '',
                    gioi_tinh: data.gioi_tinh || 'Nam',
                    ngay_sinh: data.ngay_sinh || '',
                    so_cccd: data.so_cccd || '',
                    dia_chi_so_nha: data.dia_chi_so_nha || '',
                    dia_chi_xa_phuong: data.dia_chi_xa_phuong || '',
                    dia_chi_tinh_thanh: data.dia_chi_tinh_thanh || ''
                };
                for (const [prop, val] of Object.entries(mapProps)) {
                    const el = card.querySelector(`[data-prop="${prop}"]`);
                    if (el) {
                        el.value = val;
                        el.style.borderColor = 'var(--accent-green)';
                    }
                }
                markOcrReview(data, k => card.querySelector(`[data-prop="${k}"]`));
            }

            if (btn) {
                btn.innerHTML = ocrDoneLabel(data);
                btn.disabled = false;
            }
        } else {
            alert(resData.message || 'Không thể nhận diện ảnh VNeID. Vui lòng thử lại.');
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    } catch (err) {
        console.error('Lỗi OCR member:', err);
        alert('Có lỗi xảy ra khi xử lý ảnh VNeID.');
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    } finally {
        fileInput.value = '';
    }
};

// Quét CCCD cho một phần tử của danh sách kiểu `list` (vd Thành viên cũ)
window.handleListOcrUpload = async function(fileInput, listKey, idx) {
    const file = fileInput.files[0];
    if (!file) return;
    collectFormData();

    const btn = fileInput.nextElementSibling;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang đọc VNeID...';
    btn.disabled = true;

    try {
        const fd = new FormData();
        fd.append('image', file);
        fd.append('target', `${listKey}_${idx}`);
        const resData = await ocrRequest(fd);
        if (!resData.success || !resData.data) {
            alert(resData.message || 'Không thể nhận diện ảnh VNeID. Vui lòng thử lại.');
            btn.innerHTML = originalText;
            return;
        }

        const data = resData.data;
        const getEl = k => document.querySelector(`.lf-field[data-list="${CSS.escape(listKey)}"][data-idx="${idx}"][data-key="${k}"]`);
        const values = {
            ho_ten: data.ho_ten, gioi_tinh: data.gioi_tinh, ngay_sinh: data.ngay_sinh,
            so_cccd: data.so_cccd, dia_chi_day_du: data.dia_chi
        };
        for (const [k, v] of Object.entries(values)) {
            const el = getEl(k);
            if (el && v) {
                el.value = v;
                el.style.borderColor = 'var(--accent-green)';
            }
        }
        markOcrReview(data, getEl);
        btn.innerHTML = ocrDoneLabel(data);
        // Để form thu dữ liệu, xóa báo lỗi và cập nhật danh sách chọn bên chuyển nhượng
        const nameEl = getEl('ho_ten');
        if (nameEl) nameEl.dispatchEvent(new Event('change', { bubbles: true }));
    } catch (err) {
        console.error('Lỗi OCR danh sách:', err);
        alert('Có lỗi xảy ra khi xử lý ảnh VNeID.');
        btn.innerHTML = originalText;
    } finally {
        fileInput.value = '';
        btn.disabled = false;
    }
};
