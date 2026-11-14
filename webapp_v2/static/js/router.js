// Ứng dụng /app: tạo hồ sơ và quản trị. Trang giới thiệu là trang / (máy chủ dựng sẵn, services/trang_chu.py).
function goLanding(anchor) {
    window.location.replace('/' + (anchor ? '#' + anchor : ''));
    return '';
}

const routes = {
    '/': () => goLanding(),
    '/services': renderServices,
    '/wizard': renderWizard,
    '/admin': () => window.renderAdmin(),
    '/pricing': () => goLanding('bang-gia'),
    '/contact': () => goLanding('hoi-dap'),
    '/about': () => goLanding()
};

function initRouter() {
    window.addEventListener('hashchange', handleRoute);
    handleRoute();
}

function handleRoute() {
    const app = document.getElementById('app');
    // #/wizard?t=<id bộ mẫu>: phần sau dấu ? là tham số, không thuộc tên trang
    const path = window.location.hash.replace('#', '').split('?')[0] || '/';

    const renderer = routes[path] || routes['/'];
    app.innerHTML = renderer();

    if (path === '/wizard' && window.initWizard) {
        setTimeout(window.initWizard, 0);
    }

    if (path === '/admin' && window.initAdmin) {
        setTimeout(window.initAdmin, 0);
    }

    window.scrollTo(0, 0);

    if (window.initAnimations) {
        setTimeout(window.initAnimations, 100);
    }

    // Google Analytics: mỗi trang trong ứng dụng là một lượt xem (không tính trang quản trị)
    if (window.nacTrack && routes[path] && path !== '/admin') {
        window.nacTrack('page_view', { page_location: window.location.href, page_title: path.slice(1) || 'app' });
    }
}
