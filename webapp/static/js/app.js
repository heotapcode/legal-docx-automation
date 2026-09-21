document.addEventListener('DOMContentLoaded', () => {
    // Initialize SPA Router
    initRouter();
    
    // Expose initAnimations to window so router can re-call it on page changes
    window.initAnimations = () => {
        setupScrollAnimations();
        setupNavbarScroll();
    };
    
    window.initAnimations();
});

// Intersection Observer for scroll animations
function setupScrollAnimations() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    });
    
    elements.forEach(el => {
        observer.observe(el);
    });
}

// Navbar background change on scroll
function setupNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    }
    
    const onScroll = () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            if (window.location.hash === '' || window.location.hash === '#/') {
                navbar.classList.remove('scrolled');
            }
        }
    };
    
    window.removeEventListener('scroll', window._navScrollHandler);
    window._navScrollHandler = onScroll;
    window.addEventListener('scroll', onScroll);
}
