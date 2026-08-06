/**
 * Mobile Menu Controller
 * Controla abertura/fechamento do menu lateral em dispositivos móveis.
 * Injeta overlay e botão hambúrguer quando a página usa .sidebar + .header.
 * Não altera autenticação nem conteúdo do menu (auth.js / menu.js).
 */

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
    let overlay = document.querySelector('.sidebar-overlay');
    if (overlay) return overlay;

    overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.setAttribute('aria-hidden', 'true');
    overlay.addEventListener('click', closeSidebar);

    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(overlay, container.firstChild);
    } else {
        document.body.insertBefore(overlay, document.body.firstChild);
    }
    return overlay;
}

function ensureMenuToggle() {
    if (document.querySelector('.menu-toggle')) return;

    const header = document.querySelector('.header');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'menu-toggle';
    btn.setAttribute('aria-label', 'Abrir menu');
    btn.setAttribute('aria-controls', 'sidebar');
    btn.innerHTML = '<i class="fas fa-bars" aria-hidden="true"></i>';
    btn.addEventListener('click', function (event) {
        event.preventDefault();
        toggleSidebar();
    });

    if (header) {
        let leading = header.querySelector('.header-leading');
        if (!leading) {
            leading = document.createElement('div');
            leading.className = 'header-leading';
            const title = header.querySelector('.header-title');
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

    // Shells custom (ex.: upload inteligente) sem .header padrão
    if (!getSidebar()) return;
    btn.classList.add('menu-toggle-floating');
    document.body.appendChild(btn);
}

function toggleSidebar() {
    const sidebar = ensureSidebarId(getSidebar());
    const overlay = ensureSidebarOverlay();

    if (!sidebar || !overlay) return;

    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
    overlay.setAttribute('aria-hidden', sidebar.classList.contains('open') ? 'false' : 'true');

    if (sidebar.classList.contains('open')) {
        document.body.classList.add('sidebar-open');
    } else {
        document.body.classList.remove('sidebar-open');
    }
}

function closeSidebar() {
    const sidebar = ensureSidebarId(getSidebar());
    const overlay = document.querySelector('.sidebar-overlay');

    if (sidebar) sidebar.classList.remove('open');
    if (overlay) {
        overlay.classList.remove('active');
        overlay.setAttribute('aria-hidden', 'true');
    }
    document.body.classList.remove('sidebar-open');
    document.body.style.overflow = '';
}

function initMobileMenu() {
    const sidebar = ensureSidebarId(getSidebar());
    if (!sidebar) return;

    ensureSidebarOverlay();
    ensureMenuToggle();

    document.querySelectorAll('.sidebar-nav .nav-item, .sidebar a.nav-item').forEach(function (item) {
        item.addEventListener('click', function () {
            if (window.innerWidth < 1024) {
                closeSidebar();
            }
        });
    });

    let resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            if (window.innerWidth >= 1024) {
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

    let touchStartX = 0;
    let touchEndX = 0;

    sidebar.addEventListener('touchstart', function (e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    sidebar.addEventListener('touchend', function (e) {
        touchEndX = e.changedTouches[0].screenX;
        const swipeThreshold = 50;
        if (touchStartX - touchEndX < -swipeThreshold && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    }, { passive: true });
}

document.addEventListener('DOMContentLoaded', function () {
    initMobileMenu();
    // auth.js reescreve a sidebar após o boot — reinsere shell sem alterar o menu
    setTimeout(initMobileMenu, 100);
    setTimeout(initMobileMenu, 600);
});

window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;
