document.addEventListener('DOMContentLoaded', () => {
    // 1. Page Loader Fadeout
    const pageLoader = document.getElementById('pageLoader');
    if (pageLoader) {
        const hideLoader = () => {
            pageLoader.style.opacity = '0';
            pageLoader.style.visibility = 'hidden';
        };

        if (document.readyState === 'complete') {
            setTimeout(hideLoader, 150);
        } else {
            window.addEventListener('load', hideLoader);
            setTimeout(hideLoader, 500);
        }
    }

    // 2. Active Nav Link Highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href) {
            const isExactMatch = currentPath === href;
            const isSubPathMatch = href !== '/adminpanel/' && href !== '/adminpanel/dashboard/' && currentPath.startsWith(href);
            
            if (isExactMatch || isSubPathMatch) {
                link.classList.add('active');
                const parentNav = link.closest('.nav-item');
                if (parentNav) parentNav.classList.add('active');
                
                const parentCollapse = link.closest('.collapse');
                if (parentCollapse) {
                    parentCollapse.classList.add('show');
                    const collapseTrigger = document.querySelector(`[data-bs-target="#${parentCollapse.id}"], [href="#${parentCollapse.id}"]`);
                    if (collapseTrigger) {
                        collapseTrigger.setAttribute('aria-expanded', 'true');
                        collapseTrigger.classList.add('active');
                    }
                }
            } else {
                link.classList.remove('active');
                const parentNav = link.closest('.nav-item');
                if (parentNav) parentNav.classList.remove('active');
            }
        }
    });

    // 3. Mobile Sidebar Toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('is-open');
        });

        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('is-open') && !sidebar.contains(e.target) && e.target !== sidebarToggle) {
                sidebar.classList.remove('is-open');
            }
        });
    }
});
