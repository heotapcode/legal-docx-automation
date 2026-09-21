/**
 * modal.js - Component Modal cho NAC CRM
 */
window.CRM = window.CRM || {};

CRM.Modal = (() => {
  let onCloseCallback = null;

  function getOverlay() { return document.getElementById('modal-overlay'); }

  function show({ title, body, footer = '', onClose = null, size = '' }) {
    const overlay = getOverlay();
    if (!overlay) return;

    onCloseCallback = onClose;
    const sizeClass = size ? `modal-${size}` : '';

    overlay.className = `modal-overlay ${sizeClass}`;
    overlay.innerHTML = `
      <div class="modal-container">
        <div class="modal-header">
          <h3 class="modal-title">${title}</h3>
          <button class="modal-close" id="modal-close-btn"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <div class="modal-body">${body}</div>
        ${footer ? `<div class="modal-footer">${footer}</div>` : ''}
      </div>
    `;

    requestAnimationFrame(() => overlay.classList.add('active'));

    // Close handlers
    document.getElementById('modal-close-btn').addEventListener('click', close);
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) close();
    });

    // ESC key
    document.addEventListener('keydown', handleEsc);
  }

  function confirm({ title, message, onConfirm, confirmText = 'Xác nhận', confirmClass = 'btn-danger' }) {
    show({
      title: title || 'Xác nhận',
      body: `<p style="color:var(--text-secondary);font-size:14px;line-height:1.7">${message}</p>`,
      footer: `
        <button class="btn btn-secondary" onclick="CRM.Modal.close()">Hủy</button>
        <button class="btn ${confirmClass}" id="modal-confirm-btn">${confirmText}</button>
      `
    });

    setTimeout(() => {
      const btn = document.getElementById('modal-confirm-btn');
      if (btn) {
        btn.addEventListener('click', () => {
          close();
          if (onConfirm) onConfirm();
        });
      }
    }, 50);
  }

  function close() {
    const overlay = getOverlay();
    if (!overlay) return;
    overlay.classList.remove('active');
    document.removeEventListener('keydown', handleEsc);
    if (onCloseCallback) {
      onCloseCallback();
      onCloseCallback = null;
    }
  }

  function handleEsc(e) {
    if (e.key === 'Escape') close();
  }

  return { show, confirm, close };
})();
