const routes = {
    '/': renderLanding,
    '/services': renderServices,
    '/wizard': renderWizard,
    '/admin': () => window.renderAdmin(),
    '/pricing': renderLanding,
    '/contact': renderLanding,
    '/about': renderLanding
};

function initRouter() {
    window.addEventListener('hashchange', handleRoute);
    handleRoute();
}

function handleRoute() {
    const app = document.getElementById('app');
    let path = window.location.hash.replace('#', '') || '/';
    
    const renderer = routes[path] || routes['/'];
    app.innerHTML = renderer();
    
    if (path === '/wizard' && window.initWizard) {
        setTimeout(window.initWizard, 0);
    }

    if (path === '/admin' && window.initAdmin) {
        setTimeout(window.initAdmin, 0);
    }

    if ((path === '/' || path === '') && window.initLandingHarvey) {
        setTimeout(window.initLandingHarvey, 0);
    }
    
    if (['/pricing', '/contact', '/about'].includes(path)) {
        setTimeout(() => {
            const el = document.getElementById(path.substring(1));
            if(el) {
                el.scrollIntoView({ behavior: 'smooth' });
            } else {
                window.scrollTo(0, 0);
            }
        }, 100);
    } else {
        window.scrollTo(0, 0);
    }

    if (window.initAnimations) {
        setTimeout(window.initAnimations, 100);
    }
}
