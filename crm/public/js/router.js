/**
 * router.js - Hash-based routing cho NAC CRM
 */
window.CRM = window.CRM || {};

CRM.Router = (() => {
  let currentPage = null;

  const pages = {
    dashboard: () => CRM.Pages.Dashboard,
    records: () => CRM.Pages.Records,
    customers: () => CRM.Pages.Customers,
    finance: () => CRM.Pages.Finance,
    reports: () => CRM.Pages.Reports,
    settings: () => CRM.Pages.Settings
  };

  function init() {
    window.addEventListener('hashchange', handleRoute);
    handleRoute();
  }

  function handleRoute() {
    const hash = window.location.hash.slice(1) || 'dashboard';
    const pageName = hash.split('/')[0];

    if (pageName === currentPage) return;

    // Destroy current page
    if (currentPage && pages[currentPage]) {
      const mod = pages[currentPage]();
      if (mod && mod.destroy) mod.destroy();
    }

    currentPage = pageName;
    CRM.Sidebar.setActive(pageName);

    // Render new page
    if (pages[pageName]) {
      const mod = pages[pageName]();
      if (mod && mod.render) {
        mod.render();
      } else {
        renderNotFound();
      }
    } else {
      renderNotFound();
    }
  }

  function navigate(page) {
    window.location.hash = page;
  }

  function getCurrentPage() {
    return currentPage || 'dashboard';
  }

  function renderNotFound() {
    const content = document.getElementById('page-content');
    if (content) {
      content.innerHTML = `
        <div class="empty-state" style="min-height:60vh">
          <i class="fa-solid fa-compass empty-state-icon"></i>
          <div class="empty-state-title">Trang không tìm thấy</div>
          <div class="empty-state-message">Trang bạn yêu cầu không tồn tại</div>
          <button class="btn btn-primary mt-3" onclick="CRM.Router.navigate('dashboard')">Về Dashboard</button>
        </div>
      `;
    }
  }

  return { init, navigate, getCurrentPage };
})();
