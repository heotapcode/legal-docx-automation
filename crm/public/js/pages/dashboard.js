/**
 * CRM.Pages.Dashboard
 * Trang tổng quan hệ thống - Dashboard
 * Hiển thị thống kê, biểu đồ, hồ sơ sắp hết hạn, hoạt động gần đây
 */
;(function () {
  'use strict';

  // ── Biến module ──────────────────────────────────────────────
  let _refreshInterval = null;
  let _chartBar = null;
  let _chartDoughnut = null;
  let _chartLine = null;
  const REFRESH_MS = 60000; // 60 giây

  // ── Màu sắc biểu đồ ─────────────────────────────────────────
  const CHART_COLORS = [
    '#667eea', '#764ba2', '#f59e0b', '#10b981',
    '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899',
    '#06b6d4', '#84cc16', '#f97316', '#14b8a6'
  ];

  // ── Helpers ──────────────────────────────────────────────────

  /**
   * Tạo gradient cho canvas Chart.js
   */
  function createGradient(ctx, colorTop, colorBottom, height) {
    const gradient = ctx.createLinearGradient(0, 0, 0, height || 300);
    gradient.addColorStop(0, colorTop);
    gradient.addColorStop(1, colorBottom);
    return gradient;
  }

  /**
   * Tính số ngày còn lại đến deadline
   */
  function daysUntil(dateStr) {
    if (!dateStr) return Infinity;
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const target = new Date(dateStr);
    target.setHours(0, 0, 0, 0);
    return Math.ceil((target - now) / (1000 * 60 * 60 * 24));
  }

  /**
   * Lấy chữ cái đầu từ tên
   */
  function getInitial(name) {
    if (!name) return '?';
    return name.trim().charAt(0).toUpperCase();
  }

  /**
   * Format số gọn (1.2M, 500K, ...)
   */
  function shortNumber(n) {
    if (n >= 1e9) return (n / 1e9).toFixed(1).replace(/\.0$/, '') + 'B';
    if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, '') + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, '') + 'K';
    return String(n);
  }

  // ── Cấu hình Chart.js chung (Dark theme) ─────────────────────
  const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#94a3b8',
          font: { family: 'Inter', size: 12 },
          padding: 16,
          usePointStyle: true,
          pointStyleWidth: 10
        }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 15, 35, 0.95)',
        titleColor: '#e2e8f0',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        titleFont: { family: 'Inter', weight: '600' },
        bodyFont: { family: 'Inter' },
        displayColors: true,
        boxPadding: 4
      }
    },
    scales: {
      x: {
        ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false }
      },
      y: {
        ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } },
        grid: { color: 'rgba(255,255,255,0.06)', drawBorder: false },
        beginAtZero: true
      }
    }
  };

  // ── Render HTML chính ────────────────────────────────────────

  function buildPageHTML() {
    return `
      <!-- Stats Grid -->
      <div class="stats-grid" id="dash-stats-grid">
        ${buildStatCard('fa-folder-open', 'linear-gradient(135deg, #667eea, #764ba2)', '—', 'Tổng hồ sơ', '', 'stat-total')}
        ${buildStatCard('fa-spinner', 'linear-gradient(135deg, #f59e0b, #ed8936)', '—', 'Đang xử lý', '', 'stat-active')}
        ${buildStatCard('fa-check-circle', 'linear-gradient(135deg, #10b981, #059669)', '—', 'Hoàn thành', '', 'stat-completed')}
        ${buildStatCard('fa-chart-line', 'linear-gradient(135deg, #8b5cf6, #7c3aed)', '—', 'Doanh thu tháng', '', 'stat-revenue')}
      </div>

      <!-- Biểu đồ 2 cột -->
      <div class="chart-grid" style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title"><i class="fas fa-chart-bar" style="color:#667eea; margin-right:8px;"></i>Số hồ sơ theo tháng</h3>
          </div>
          <div class="card-body" style="padding: 16px 20px;">
            <div style="height: 300px; position: relative;">
              <canvas id="chart-bar-records"></canvas>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <h3 class="card-title"><i class="fas fa-chart-pie" style="color:#8b5cf6; margin-right:8px;"></i>Hồ sơ theo loại</h3>
          </div>
          <div class="card-body" style="padding: 16px 20px;">
            <div style="height: 300px; position: relative;">
              <canvas id="chart-doughnut-types"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- Biểu đồ Thu/Chi -->
      <div class="card" style="margin-top: 20px;">
        <div class="card-header">
          <h3 class="card-title"><i class="fas fa-money-bill-trend-up" style="color:#10b981; margin-right:8px;"></i>Thu / Chi theo tháng</h3>
        </div>
        <div class="card-body" style="padding: 16px 20px;">
          <div style="height: 350px; position: relative;">
            <canvas id="chart-line-finance"></canvas>
          </div>
        </div>
      </div>

      <!-- Hồ sơ sắp hết hạn + Hoạt động gần đây -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title"><i class="fas fa-clock" style="color:#f59e0b; margin-right:8px;"></i>Hồ sơ sắp hết hạn</h3>
          </div>
          <div class="card-body" style="padding: 0;" id="dash-deadlines">
            <div class="empty-state" style="padding: 32px;"><i class="fas fa-check-circle" style="font-size:32px; margin-bottom:12px; color:#10b981;"></i><p>Không có hồ sơ sắp hết hạn</p></div>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <h3 class="card-title"><i class="fas fa-history" style="color:#3b82f6; margin-right:8px;"></i>Hoạt động gần đây</h3>
          </div>
          <div class="card-body" style="padding: 0; max-height: 420px; overflow-y: auto;" id="dash-activities">
            <div class="empty-state" style="padding: 32px;"><i class="fas fa-inbox" style="font-size:32px; margin-bottom:12px;"></i><p>Chưa có hoạt động</p></div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Tạo HTML cho 1 stat card
   */
  function buildStatCard(icon, gradient, value, label, trend, id) {
    return `
      <div class="stat-card" id="${id}">
        <div class="stat-icon" style="background: ${gradient}; width:56px; height:56px; border-radius:16px; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
          <i class="fas ${icon}" style="font-size:22px; color:#fff;"></i>
        </div>
        <div style="flex:1; min-width:0;">
          <div class="stat-value" style="font-size:28px; font-weight:700; color:var(--text-primary); line-height:1.2;">${value}</div>
          <div class="stat-label" style="font-size:13px; color:var(--text-secondary); margin-top:4px;">${label}</div>
          ${trend ? `<div class="stat-trend" style="font-size:12px; margin-top:4px;">${trend}</div>` : ''}
        </div>
      </div>
    `;
  }

  // ── Cập nhật Stats Grid ──────────────────────────────────────

  function updateStats(data) {
    // Tổng hồ sơ
    const elTotal = document.getElementById('stat-total');
    if (elTotal) {
      elTotal.querySelector('.stat-value').textContent = data.total_records || 0;
      const overdue = data.overdue_records || 0;
      const trendEl = elTotal.querySelector('.stat-trend');
      if (overdue > 0) {
        if (trendEl) {
          trendEl.innerHTML = `<span style="color:#ef4444;"><i class="fas fa-exclamation-triangle"></i> ${overdue} quá hạn</span>`;
        } else {
          elTotal.querySelector('.stat-label').insertAdjacentHTML('afterend',
            `<div class="stat-trend" style="font-size:12px; margin-top:4px;"><span style="color:#ef4444;"><i class="fas fa-exclamation-triangle"></i> ${overdue} quá hạn</span></div>`
          );
        }
      }
    }

    // Đang xử lý
    const elActive = document.getElementById('stat-active');
    if (elActive) elActive.querySelector('.stat-value').textContent = data.active_records || 0;

    // Hoàn thành
    const elCompleted = document.getElementById('stat-completed');
    if (elCompleted) elCompleted.querySelector('.stat-value').textContent = data.completed_records || 0;

    // Doanh thu tháng
    const elRevenue = document.getElementById('stat-revenue');
    if (elRevenue) {
      elRevenue.querySelector('.stat-value').textContent = CRM.Utils.formatCurrency(data.monthly_revenue || 0);
    }
  }

  // ── Render biểu đồ cột – Hồ sơ theo tháng ──────────────────

  function renderBarChart(monthlyData) {
    const canvas = document.getElementById('chart-bar-records');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Hủy chart cũ nếu có
    if (_chartBar) { _chartBar.destroy(); _chartBar = null; }

    const labels = (monthlyData || []).map(m => m.month || '');
    const values = (monthlyData || []).map(m => m.records_count || 0);

    // Gradient fill
    const gradientFill = createGradient(ctx, 'rgba(102, 126, 234, 0.7)', 'rgba(118, 75, 162, 0.1)', 300);

    _chartBar = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Số hồ sơ',
          data: values,
          backgroundColor: gradientFill,
          borderColor: '#667eea',
          borderWidth: 1,
          borderRadius: 6,
          borderSkipped: false,
          maxBarThickness: 40
        }]
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: {
          ...CHART_DEFAULTS.plugins,
          legend: { display: false }
        },
        scales: {
          ...CHART_DEFAULTS.scales,
          y: {
            ...CHART_DEFAULTS.scales.y,
            ticks: {
              ...CHART_DEFAULTS.scales.y.ticks,
              stepSize: 1,
              callback: v => Number.isInteger(v) ? v : ''
            }
          }
        }
      }
    });
  }

  // ── Render biểu đồ tròn – Hồ sơ theo loại ──────────────────

  function renderDoughnutChart(byType) {
    const canvas = document.getElementById('chart-doughnut-types');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (_chartDoughnut) { _chartDoughnut.destroy(); _chartDoughnut = null; }

    const items = (byType || []).filter(t => t.count > 0).slice(0, 8);
    const labels = items.map(t => CRM.Utils.getRecordTypeLabel(t.type) || t.type);
    const values = items.map(t => t.count);
    const colors = items.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]);

    _chartDoughnut = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderColor: 'rgba(30, 30, 60, 0.8)',
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          ...CHART_DEFAULTS.plugins,
          legend: {
            position: 'right',
            labels: {
              color: '#94a3b8',
              font: { family: 'Inter', size: 11 },
              padding: 12,
              usePointStyle: true,
              pointStyleWidth: 8,
              boxWidth: 8
            }
          }
        }
      }
    });
  }

  // ── Render biểu đồ đường – Thu/Chi theo tháng ───────────────

  function renderLineChart(monthlyData) {
    const canvas = document.getElementById('chart-line-finance');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (_chartLine) { _chartLine.destroy(); _chartLine = null; }

    const labels = (monthlyData || []).map(m => m.month || '');
    const revenue = (monthlyData || []).map(m => m.revenue || 0);
    const expense = (monthlyData || []).map(m => m.expense || 0);

    // Gradient fills
    const gradRevenue = createGradient(ctx, 'rgba(16, 185, 129, 0.3)', 'rgba(16, 185, 129, 0.02)', 350);
    const gradExpense = createGradient(ctx, 'rgba(239, 68, 68, 0.25)', 'rgba(239, 68, 68, 0.02)', 350);

    _chartLine = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Doanh thu',
            data: revenue,
            borderColor: '#10b981',
            backgroundColor: gradRevenue,
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#10b981',
            pointBorderColor: '#0f0f23',
            pointBorderWidth: 2,
            borderWidth: 2.5
          },
          {
            label: 'Chi phí',
            data: expense,
            borderColor: '#ef4444',
            backgroundColor: gradExpense,
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#ef4444',
            pointBorderColor: '#0f0f23',
            pointBorderWidth: 2,
            borderWidth: 2.5
          }
        ]
      },
      options: {
        ...CHART_DEFAULTS,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          ...CHART_DEFAULTS.plugins,
          tooltip: {
            ...CHART_DEFAULTS.plugins.tooltip,
            callbacks: {
              label: function (context) {
                return context.dataset.label + ': ' + CRM.Utils.formatCurrency(context.raw);
              }
            }
          }
        },
        scales: {
          ...CHART_DEFAULTS.scales,
          y: {
            ...CHART_DEFAULTS.scales.y,
            ticks: {
              ...CHART_DEFAULTS.scales.y.ticks,
              callback: v => shortNumber(v) + ' ₫'
            }
          }
        }
      }
    });
  }

  // ── Render bảng Hồ sơ sắp hết hạn ───────────────────────────

  function renderDeadlines(deadlines) {
    const container = document.getElementById('dash-deadlines');
    if (!container) return;

    if (!deadlines || deadlines.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="padding: 32px;">
          <i class="fas fa-check-circle" style="font-size:32px; margin-bottom:12px; color:#10b981;"></i>
          <p>Không có hồ sơ sắp hết hạn</p>
        </div>`;
      return;
    }

    let rows = '';
    deadlines.forEach(r => {
      const days = daysUntil(r.deadline);
      const isUrgent = days <= 3;
      const isOverdue = days < 0;
      const rowBg = isOverdue
        ? 'background: rgba(239,68,68,0.08);'
        : (isUrgent ? 'background: rgba(245,158,11,0.08);' : '');
      const deadlineColor = isOverdue
        ? 'color: #ef4444; font-weight: 600;'
        : (isUrgent ? 'color: #f59e0b; font-weight: 600;' : 'color: var(--text-primary);');
      const deadlineText = r.deadline ? CRM.Utils.formatDate(r.deadline) : '—';
      const daysText = isOverdue
        ? `<span style="color:#ef4444; font-size:11px; margin-left:4px;">(quá ${Math.abs(days)} ngày)</span>`
        : (isUrgent ? `<span style="color:#f59e0b; font-size:11px; margin-left:4px;">(còn ${days} ngày)</span>` : '');

      rows += `
        <tr style="${rowBg}">
          <td style="padding:10px 16px; font-weight:500; color:var(--accent-primary); font-size:13px;">${r.code || ''}</td>
          <td style="padding:10px 16px; font-size:13px; color:var(--text-primary); max-width:160px;" class="text-truncate">${r.customer_name || ''}</td>
          <td style="padding:10px 16px; font-size:12px; color:var(--text-secondary);">${CRM.Utils.getRecordTypeLabel(r.type) || ''}</td>
          <td style="padding:10px 16px; font-size:13px; ${deadlineColor}">${deadlineText}${daysText}</td>
          <td style="padding:10px 16px;">${CRM.Utils.getStatusBadge(r.status)}</td>
        </tr>`;
    });

    container.innerHTML = `
      <div class="table-container">
        <table class="data-table" style="margin:0;">
          <thead>
            <tr>
              <th style="padding:10px 16px;">Mã HS</th>
              <th style="padding:10px 16px;">Khách hàng</th>
              <th style="padding:10px 16px;">Loại</th>
              <th style="padding:10px 16px;">Hạn nộp</th>
              <th style="padding:10px 16px;">Trạng thái</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  // ── Render Timeline Hoạt động gần đây ────────────────────────

  function renderActivities(activities) {
    const container = document.getElementById('dash-activities');
    if (!container) return;

    if (!activities || activities.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="padding: 32px;">
          <i class="fas fa-inbox" style="font-size:32px; margin-bottom:12px;"></i>
          <p>Chưa có hoạt động</p>
        </div>`;
      return;
    }

    let items = '';
    activities.forEach((act, idx) => {
      const initial = getInitial(act.user_name);
      const avatarColor = ['#667eea', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#3b82f6'][idx % 6];
      const timeText = act.created_at ? CRM.Utils.timeAgo(act.created_at) : '';

      items += `
        <div style="display:flex; gap:12px; padding:14px 20px; border-bottom:1px solid var(--border-color); transition: background 0.2s;" onmouseenter="this.style.background='rgba(255,255,255,0.02)'" onmouseleave="this.style.background='transparent'">
          <div class="avatar" style="background:${avatarColor}; width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; font-size:14px; flex-shrink:0;">${initial}</div>
          <div style="flex:1; min-width:0;">
            <div style="font-size:13px; color:var(--text-primary); line-height:1.5;">
              <strong style="color:var(--text-primary);">${act.user_name || 'Hệ thống'}</strong>
              <span style="color:var(--text-secondary);"> ${act.action || ''}</span>
            </div>
            ${act.details ? `<div style="font-size:12px; color:var(--text-muted); margin-top:2px;">${act.details}</div>` : ''}
            <div style="font-size:11px; color:var(--text-muted); margin-top:4px;"><i class="far fa-clock" style="margin-right:4px;"></i>${timeText}</div>
          </div>
        </div>`;
    });

    container.innerHTML = items;
  }

  // ── Fetch & Render toàn bộ ───────────────────────────────────

  async function fetchAndRender(isRefresh) {
    try {
      const result = await CRM.API.get('/api/dashboard/stats');
      const data = result.data || result;

      // Cập nhật stats
      updateStats(data);

      // Render biểu đồ
      renderBarChart(data.monthly_chart);
      renderDoughnutChart(data.records_by_type);
      renderLineChart(data.monthly_chart);

      // Render bảng & timeline
      renderDeadlines(data.upcoming_deadlines);
      renderActivities(data.recent_activities);

    } catch (err) {
      console.error('[Dashboard] Lỗi tải dữ liệu:', err);
      if (!isRefresh) {
        CRM.Toast.error('Không thể tải dữ liệu dashboard');
      }
    }
  }

  // ── Page Module ──────────────────────────────────────────────

  CRM.Pages = CRM.Pages || {};
  CRM.Pages.Dashboard = {

    /**
     * Render trang Dashboard
     */
    async render() {
      // Đặt tiêu đề trang
      CRM.App.setPageTitle('Dashboard', 'Tổng quan hệ thống');

      const container = document.getElementById('page-content');
      if (!container) return;

      // Hiển thị loading
      container.innerHTML = `
        <div class="loading-spinner" style="display:flex; align-items:center; justify-content:center; min-height:400px; flex-direction:column; gap:16px;">
          <div style="width:48px; height:48px; border: 3px solid var(--border-color); border-top-color: var(--accent-primary); border-radius:50%; animation: spin 0.8s linear infinite;"></div>
          <span style="color:var(--text-secondary); font-size:14px;">Đang tải dữ liệu...</span>
        </div>
        <style>
          @keyframes spin { to { transform: rotate(360deg); } }
        </style>`;

      // Render cấu trúc HTML
      container.innerHTML = buildPageHTML();

      // Tải dữ liệu lần đầu
      await fetchAndRender(false);

      // Tự động refresh mỗi 60 giây
      _refreshInterval = setInterval(() => {
        fetchAndRender(true);
      }, REFRESH_MS);
    },

    /**
     * Dọn dẹp khi rời trang
     */
    destroy() {
      // Xóa interval
      if (_refreshInterval) {
        clearInterval(_refreshInterval);
        _refreshInterval = null;
      }

      // Hủy tất cả Chart instances
      if (_chartBar) { _chartBar.destroy(); _chartBar = null; }
      if (_chartDoughnut) { _chartDoughnut.destroy(); _chartDoughnut = null; }
      if (_chartLine) { _chartLine.destroy(); _chartLine = null; }
    }
  };

})();
