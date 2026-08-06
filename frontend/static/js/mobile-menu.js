/**
 * Mobile Menu Controller — R01-A shell (estabilizado)
 * Injeta overlay + hambúrguer. Não altera auth.js / menu / APIs.
 */

var MOBILE_MQ = '(max-width: 1024px)';
var __mobileGlobalListenersBound = false;

function isMobileViewport() {
    return window.matchMedia(MOBILE_MQ).matches;
}

function getSidebar() {
    return document.getElementById('sidebar')
        || document.querySelector('aside.sidebar')
        || document.querySelector('.container > .sidebar')
        || document.querySelector('.powerbi-container > .sidebar')
        || document.querySelector('div.sidebar');
}

function ensureSidebarId(sidebar) {
    if (sidebar && !sidebar.id) {
        sidebar.id = 'sidebar';
    }
    return sidebar;
}

function ensureSidebarOverlay() {
    var overlay = document.querySelector('.sidebar-overlay');
    if (overlay) return overlay;

    overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.setAttribute('aria-hidden', 'true');
    overlay.addEventListener('click', closeSidebar);

    var container = document.querySelector('.container') || document.querySelector('.powerbi-container');
    if (container) {
        container.insertBefore(overlay, container.firstChild);
    } else {
        document.body.insertBefore(overlay, document.body.firstChild);
    }
    return overlay;
}

function ensureMenuToggle() {
    if (document.querySelector('.menu-toggle')) return;

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'menu-toggle';
    btn.setAttribute('aria-label', 'Abrir menu');
    btn.setAttribute('aria-controls', 'sidebar');
    btn.innerHTML = '<i class="fas fa-bars" aria-hidden="true"></i>';
    btn.addEventListener('click', function (event) {
        event.preventDefault();
        toggleSidebar();
    });

    var header = document.querySelector('.header');
    if (header) {
        var leading = header.querySelector('.header-leading');
        if (!leading) {
            leading = document.createElement('div');
            leading.className = 'header-leading';
            var title = header.querySelector('.header-title');
            if (title && title.parentElement === header) {
                header.insertBefore(leading, title);
                leading.appendChild(btn);
                leading.appendChild(title);
            } else {
                header.insertBefore(leading, header.firstChild);
                leading.appendChild(btn);
            }
        } else if (!leading.querySelector('.menu-toggle')) {
            leading.insertBefore(btn, leading.firstChild);
        }
        return;
    }

    if (!getSidebar()) return;
    btn.classList.add('menu-toggle-floating');
    document.body.appendChild(btn);
}

function bindSidebarInstance(sidebar) {
    if (!sidebar) return;
    if (sidebar.getAttribute('data-mobile-sidebar-bound') === '1') {
        bindNavCloseHandlers(sidebar);
        return;
    }

    sidebar.setAttribute('data-mobile-sidebar-bound', '1');

    var touchStartX = 0;
    sidebar.addEventListener('touchstart', function (e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    sidebar.addEventListener('touchend', function (e) {
        var touchEndX = e.changedTouches[0].screenX;
        if (touchStartX - touchEndX < -50 && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    }, { passive: true });

    bindNavCloseHandlers(sidebar);
}

function bindNavCloseHandlers(sidebar) {
    var root = sidebar || document;
    root.querySelectorAll('.sidebar-nav .nav-item, a.nav-item').forEach(function (item) {
        if (item.getAttribute('data-mobile-nav-bound') === '1') return;
        item.setAttribute('data-mobile-nav-bound', '1');
        item.addEventListener('click', function () {
            if (isMobileViewport()) {
                closeSidebar();
            }
        });
    });
}

function bindGlobalListenersOnce() {
    if (__mobileGlobalListenersBound) return;
    __mobileGlobalListenersBound = true;

    var resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            if (!isMobileViewport()) {
                closeSidebar();
            } else {
                ensureMenuToggle();
            }
        }, 250);
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeSidebar();
        }
    });
}

function toggleSidebar() {
    var sidebar = ensureSidebarId(getSidebar());
    var overlay = ensureSidebarOverlay();
    if (!sidebar || !overlay) return;

    bindSidebarInstance(sidebar);

    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
    var open = sidebar.classList.contains('open');
    overlay.setAttribute('aria-hidden', open ? 'false' : 'true');
    document.body.classList.toggle('sidebar-open', open);
}

function closeSidebar() {
    var sidebar = ensureSidebarId(getSidebar());
    var overlay = document.querySelector('.sidebar-overlay');
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) {
        overlay.classList.remove('active');
        overlay.setAttribute('aria-hidden', 'true');
    }
    document.body.classList.remove('sidebar-open');
}

function initMobileMenu() {
    var sidebar = ensureSidebarId(getSidebar());
    if (!sidebar) return;

    ensureSidebarOverlay();
    ensureMenuToggle();
    bindSidebarInstance(sidebar);
    bindGlobalListenersOnce();
}

document.addEventListener('DOMContentLoaded', function () {
    initMobileMenu();
    // auth.js pode substituir a sidebar após o boot — reinicializa a instância
    setTimeout(initMobileMenu, 100);
    setTimeout(initMobileMenu, 600);
});

window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;
window.isMobileViewport = isMobileViewport;
