/**
 * reports.js - Trang báo cáo & thống kê
 */
window.CRM = window.CRM || {};
CRM.Pages = CRM.Pages || {};

CRM.Pages.Reports = (() => {
  let charts = [];
  let currentTab = 'finance';
  let filters = { period: 'monthly', year: new Date().getFullYear(), month: new Date().getMonth() + 1, quarter: Math.ceil((new Date().getMonth() + 1) / 3) };

  function render() {
    CRM.App.setPageTitle('Báo cáo', 'Báo cáo & Thống kê');
    const content = document.getElementById('page-content');
    content.innerHTML = `
      <div class="tabs">
        <div class="tab-item active" data-tab="finance">💰 Tài chính</div>
        <div class="tab-item" data-tab="records">📋 Hồ sơ</div>
      </div>
      <div class="filter-bar" id="report-filters"></div>
      <div id="report-content">
        <div class="loading-container"><div class="spinner spinner-lg"></div></div>
      </div>
    `;

    content.querySelectorAll('.tab-item').forEach(tab => {
      tab.addEventListener('click', () => {
        content.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentTab = tab.dataset.tab;
        renderFilters();
        loadReport();
      });
    });

    renderFilters();
    loadReport();
  }

  function renderFilters() {
    const container = document.getElementById('report-filters');
    const yearOptions = Array.from({length: 5}, (_, i) => {
      const y = new Date().getFullYear() - i;
      return `<option value="${y}" ${y === filters.year ? 'selected' : ''}>${y}</option>`;
    }).join('');

    const monthOptions = Array.from({length: 12}, (_, i) => {
      const m = i + 1;
      return `<option value="${m}" ${m === filters.month ? 'selected' : ''}>Tháng ${m}</option>`;
    }).join('');

    container.innerHTML = `
      <div class="filter-group">
        <label>Kỳ báo cáo</label>
        <select class="form-control" id="rpt-period">
          <option value="monthly" ${filters.period === 'monthly' ? 'selected' : ''}>Theo tháng</option>
          <option value="quarterly" ${filters.period === 'quarterly' ? 'selected' : ''}>Theo quý</option>
          <option value="yearly" ${filters.period === 'yearly' ? 'selected' : ''}>Theo năm</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Năm</label>
        <select class="form-control" id="rpt-year">${yearOptions}</select>
      </div>
      <div class="filter-group" id="rpt-month-group">
        <label>Tháng</label>
        <select class="form-control" id="rpt-month">${monthOptions}</select>
      </div>
      <div class="filter-group" style="align-self:flex-end">
        <button class="btn btn-primary" id="rpt-export-excel"><i class="fa-solid fa-file-excel"></i> Xuất Excel</button>
      </div>
      <div class="filter-group" style="align-self:flex-end">
        <button class="btn btn-secondary" id="rpt-export-pdf"><i class="fa-solid fa-file-pdf"></i> Xuất PDF</button>
      </div>
    `;

    document.getElementById('rpt-period').addEventListener('change', e => {
      filters.period = e.target.value;
      const monthGroup = document.getElementById('rpt-month-group');
      monthGroup.style.display = filters.period === 'yearly' ? 'none' : 'flex';
      loadReport();
    });
    document.getElementById('rpt-year').addEventListener('change', e => { filters.year = parseInt(e.target.value); loadReport(); });
    document.getElementById('rpt-month').addEventListener('change', e => { filters.month = parseInt(e.target.value); loadReport(); });
    document.getElementById('rpt-export-excel').addEventListener('click', exportExcel);
    document.getElementById('rpt-export-pdf').addEventListener('click', exportPDF);

    if (filters.period === 'yearly') {
      document.getElementById('rpt-month-group').style.display = 'none';
    }
  }

  async function loadReport() {
    destroyCharts();
    const rc = document.getElementById('report-content');
    rc.innerHTML = '<div class="loading-container"><div class="spinner spinner-lg"></div></div>';

    try {
      if (currentTab === 'finance') {
        await loadFinanceReport();
      } else {
        await loadRecordsReport();
      }
    } catch (err) {
      CRM.Toast.error(err.message);
      rc.innerHTML = '<div class="empty-state"><div class="empty-state-title">Lỗi tải báo cáo</div></div>';
    }
  }

  async function loadFinanceReport() {
    const params = new URLSearchParams({ period: filters.period, year: filters.year, month: filters.month });
    const res = await CRM.API.get(`/api/reports/finance?${params}`);
    const d = res.data;
    const rc = document.getElementById('report-content');

    rc.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card green"><div class="stat-icon"><i class="fa-solid fa-arrow-trend-up"></i></div><div class="stat-info"><div class="stat-value">${CRM.Utils.formatCurrency(d.summary?.revenue || 0)}</div><div class="stat-label">Doanh thu</div></div></div>
        <div class="stat-card red"><div class="stat-icon"><i class="fa-solid fa-arrow-trend-down"></i></div><div class="stat-info"><div class="stat-value">${CRM.Utils.formatCurrency(d.summary?.expense || 0)}</div><div class="stat-label">Chi phí</div></div></div>
        <div class="stat-card blue"><div class="stat-icon"><i class="fa-solid fa-scale-balanced"></i></div><div class="stat-info"><div class="stat-value">${CRM.Utils.formatCurrency(d.summary?.profit || 0)}</div><div class="stat-label">Lợi nhuận</div></div></div>
      </div>
      <div class="chart-grid">
        <div class="card"><div class="card-header"><div class="card-title"><i class="fa-solid fa-chart-column"></i> Thu/Chi theo tháng</div></div><div class="card-body"><div class="chart-container"><canvas id="chart-finance-monthly"></canvas></div></div></div>
        <div class="card"><div class="card-header"><div class="card-title"><i class="fa-solid fa-chart-pie"></i> Chi phí theo danh mục</div></div><div class="card-body"><div class="chart-container"><canvas id="chart-finance-category"></canvas></div></div></div>
      </div>
      <div class="card mt-3">
        <div class="card-header"><div class="card-title"><i class="fa-solid fa-list"></i> Chi tiết giao dịch</div></div>
        <div class="card-body no-padding" id="rpt-tx-table"></div>
      </div>
    `;

    // Monthly chart
    const monthlyData = d.by_month || [];
    const monthlyChart = new Chart(document.getElementById('chart-finance-monthly'), {
      type: 'bar',
      data: {
        labels: monthlyData.map(m => `T${m.month}`),
        datasets: [
          { label: 'Thu', data: monthlyData.map(m => m.revenue || 0), backgroundColor: 'rgba(16,185,129,0.6)', borderRadius: 6 },
          { label: 'Chi', data: monthlyData.map(m => m.expense || 0), backgroundColor: 'rgba(239,68,68,0.6)', borderRadius: 6 }
        ]
      },
      options: getChartOptions('Thu/Chi')
    });
    charts.push(monthlyChart);

    // Category chart
    const catData = d.by_category || [];
    const catColors = ['#667eea','#f59e0b','#10b981','#ef4444','#8b5cf6','#3b82f6','#ec4899'];
    const catChart = new Chart(document.getElementById('chart-finance-category'), {
      type: 'doughnut',
      data: {
        labels: catData.map(c => CRM.Utils.getCategoryLabel(c.category)),
        datasets: [{ data: catData.map(c => c.total || 0), backgroundColor: catColors.slice(0, catData.length), borderWidth: 0 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 16, font: { size: 12 } } } } }
    });
    charts.push(catChart);

    // Transactions table
    const txData = (d.transactions || []).map(t => ({
      ...t,
      type_label: t.type === 'thu' ? '<span class="badge badge-success">Thu</span>' : '<span class="badge badge-danger">Chi</span>'
    }));
    CRM.Table.render('rpt-tx-table', {
      columns: [
        { key: 'code', label: 'Mã GD' },
        { key: 'type_label', label: 'Loại', render: v => v },
        { key: 'category', label: 'Danh mục', render: v => CRM.Utils.getCategoryLabel(v) },
        { key: 'amount', label: 'Số tiền', render: v => CRM.Utils.formatCurrency(v) },
        { key: 'transaction_date', label: 'Ngày', render: v => CRM.Utils.formatDate(v) },
        { key: 'customer_name', label: 'Khách hàng', render: v => v || '—' }
      ],
      data: txData,
      emptyMessage: 'Không có giao dịch trong kỳ này'
    });
  }

  async function loadRecordsReport() {
    const params = new URLSearchParams({ year: filters.year });
    const res = await CRM.API.get(`/api/reports/records?${params}`);
    const d = res.data;
    const rc = document.getElementById('report-content');

    rc.innerHTML = `
      <div class="chart-grid">
        <div class="card"><div class="card-header"><div class="card-title"><i class="fa-solid fa-chart-column"></i> Hồ sơ theo tháng</div></div><div class="card-body"><div class="chart-container"><canvas id="chart-records-monthly"></canvas></div></div></div>
        <div class="card"><div class="card-header"><div class="card-title"><i class="fa-solid fa-chart-pie"></i> Hồ sơ theo loại</div></div><div class="card-body"><div class="chart-container"><canvas id="chart-records-type"></canvas></div></div></div>
      </div>
      <div class="card mt-3">
        <div class="card-header"><div class="card-title"><i class="fa-solid fa-users"></i> Hiệu suất nhân viên</div></div>
        <div class="card-body"><div class="chart-container" style="min-height:200px"><canvas id="chart-employee"></canvas></div></div>
      </div>
    `;

    // Monthly
    const byMonth = d.by_month || [];
    charts.push(new Chart(document.getElementById('chart-records-monthly'), {
      type: 'bar',
      data: {
        labels: byMonth.map(m => `T${m.month}`),
        datasets: [{ label: 'Số hồ sơ', data: byMonth.map(m => m.count), backgroundColor: 'rgba(102,126,234,0.6)', borderRadius: 6 }]
      },
      options: getChartOptions('Hồ sơ')
    }));

    // By type
    const byType = d.by_type || [];
    const typeColors = ['#667eea','#f59e0b','#10b981','#ef4444','#8b5cf6','#3b82f6','#ec4899','#06b6d4','#84cc16','#f97316'];
    charts.push(new Chart(document.getElementById('chart-records-type'), {
      type: 'doughnut',
      data: {
        labels: byType.map(t => CRM.Utils.getRecordTypeLabel(t.type)),
        datasets: [{ data: byType.map(t => t.count), backgroundColor: typeColors.slice(0, byType.length), borderWidth: 0 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 12, font: { size: 11 } } } } }
    }));

    // Employee performance
    const byEmp = d.by_employee || [];
    charts.push(new Chart(document.getElementById('chart-employee'), {
      type: 'bar',
      data: {
        labels: byEmp.map(e => e.name || 'N/A'),
        datasets: [
          { label: 'Hoàn thành', data: byEmp.map(e => e.completed || 0), backgroundColor: 'rgba(16,185,129,0.6)', borderRadius: 6 },
          { label: 'Đang xử lý', data: byEmp.map(e => e.in_progress || 0), backgroundColor: 'rgba(245,158,11,0.6)', borderRadius: 6 }
        ]
      },
      options: { ...getChartOptions('Nhân viên'), indexAxis: 'y' }
    }));
  }

  function getChartOptions(title) {
    return {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 11 } } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 11 } }, beginAtZero: true }
      },
      plugins: { legend: { labels: { color: '#94a3b8', font: { size: 12 } } }, tooltip: { backgroundColor: '#1a1a2e', borderColor: '#667eea', borderWidth: 1 } }
    };
  }

  function exportExcel() {
    try {
      // Gather visible table data
      const table = document.querySelector('#rpt-tx-table .data-table');
      if (!table) { CRM.Toast.warning('Không có dữ liệu để xuất'); return; }
      const wb = XLSX.utils.table_to_book(table, { sheet: 'Báo cáo' });
      XLSX.writeFile(wb, `bao_cao_${currentTab}_${filters.year}_T${filters.month}.xlsx`);
      CRM.Toast.success('Đã xuất file Excel');
    } catch (e) { CRM.Toast.error('Lỗi xuất Excel: ' + e.message); }
  }

  function exportPDF() {
    try {
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF();
      doc.setFontSize(16);
      doc.text('BAO CAO ' + (currentTab === 'finance' ? 'TAI CHINH' : 'HO SO'), 14, 20);
      doc.setFontSize(10);
      doc.text(`Nam: ${filters.year} - Thang: ${filters.month}`, 14, 28);
      doc.text('Cong ty TNHH Dich vu Tu Van NAC', 14, 34);

      const table = document.querySelector('#rpt-tx-table .data-table');
      if (table) {
        doc.autoTable({ html: table, startY: 42, theme: 'grid', headStyles: { fillColor: [102, 126, 234] }, styles: { fontSize: 8 } });
      }
      doc.save(`bao_cao_${currentTab}_${filters.year}_T${filters.month}.pdf`);
      CRM.Toast.success('Đã xuất file PDF');
    } catch (e) { CRM.Toast.error('Lỗi xuất PDF: ' + e.message); }
  }

  function destroyCharts() {
    charts.forEach(c => { try { c.destroy(); } catch(e) {} });
    charts = [];
  }

  function destroy() { destroyCharts(); }

  return { render, destroy };
})();
