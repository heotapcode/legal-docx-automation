/**
 * table.js - Component bảng dữ liệu có phân trang, sắp xếp
 */
window.CRM = window.CRM || {};

CRM.Table = (() => {
  function render(containerId, options) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const {
      columns = [], data = [], actions = [],
      pagination = null, onPageChange = null,
      emptyMessage = 'Không có dữ liệu', emptyIcon = 'fa-inbox'
    } = options;

    if (!data || data.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid ${emptyIcon} empty-state-icon"></i>
          <div class="empty-state-title">${emptyMessage}</div>
        </div>
      `;
      return;
    }

    // Build header
    let headerHtml = '<tr>';
    columns.forEach(col => {
      const widthStyle = col.width ? `style="width:${col.width}"` : '';
      headerHtml += `<th ${widthStyle}>${col.label}</th>`;
    });
    if (actions.length) headerHtml += '<th style="width:100px">Thao tác</th>';
    headerHtml += '</tr>';

    // Build rows
    let bodyHtml = '';
    data.forEach((row, idx) => {
      bodyHtml += `<tr data-index="${idx}">`;
      columns.forEach(col => {
        const value = row[col.key];
        const display = col.render ? col.render(value, row) : (value != null ? value : '—');
        bodyHtml += `<td>${display}</td>`;
      });
      if (actions.length) {
        bodyHtml += '<td><div class="table-actions">';
        actions.forEach((action, aIdx) => {
          const cls = action.className || 'btn-secondary';
          const title = action.label || '';
          bodyHtml += `<button class="btn btn-icon btn-sm ${cls}" data-action="${aIdx}" data-row="${idx}" title="${title}">
            <i class="fa-solid ${action.icon}"></i>
          </button>`;
        });
        bodyHtml += '</div></td>';
      }
      bodyHtml += '</tr>';
    });

    // Build pagination
    let paginationHtml = '';
    if (pagination && pagination.total_pages > 1) {
      const { page, total_pages, total } = pagination;
      paginationHtml = '<div class="pagination">';
      paginationHtml += `<button class="pagination-btn" data-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}><i class="fa-solid fa-chevron-left"></i></button>`;

      const range = getPageRange(page, total_pages);
      range.forEach(p => {
        if (p === '...') {
          paginationHtml += `<span class="pagination-info">...</span>`;
        } else {
          paginationHtml += `<button class="pagination-btn ${p === page ? 'active' : ''}" data-page="${p}">${p}</button>`;
        }
      });

      paginationHtml += `<button class="pagination-btn" data-page="${page + 1}" ${page >= total_pages ? 'disabled' : ''}><i class="fa-solid fa-chevron-right"></i></button>`;
      paginationHtml += `<span class="pagination-info">(${total} kết quả)</span>`;
      paginationHtml += '</div>';
    }

    container.innerHTML = `
      <div class="table-container">
        <table class="data-table">
          <thead>${headerHtml}</thead>
          <tbody>${bodyHtml}</tbody>
        </table>
      </div>
      ${paginationHtml}
    `;

    // Bind action clicks
    container.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const aIdx = parseInt(btn.dataset.action);
        const rIdx = parseInt(btn.dataset.row);
        if (actions[aIdx] && actions[aIdx].onClick) {
          actions[aIdx].onClick(data[rIdx]);
        }
      });
    });

    // Bind pagination clicks
    if (onPageChange) {
      container.querySelectorAll('.pagination-btn[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
          const p = parseInt(btn.dataset.page);
          if (!isNaN(p)) onPageChange(p);
        });
      });
    }
  }

  function getPageRange(current, total) {
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
    const pages = [];
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i);
      pages.push('...', total);
    } else if (current >= total - 3) {
      pages.push(1, '...');
      for (let i = total - 4; i <= total; i++) pages.push(i);
    } else {
      pages.push(1, '...', current - 1, current, current + 1, '...', total);
    }
    return pages;
  }

  return { render };
})();
