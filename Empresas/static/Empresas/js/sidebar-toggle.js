// Función para alternar el sidebar en el dashboard de empresa (disponible globalmente)
window.toggleSidebar = function() {
    const sidebar = document.querySelector('aside');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
};

// Inicializar eventos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Cerrar sidebar al hacer clic en el overlay
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) {
        overlay.addEventListener('click', function() {
            window.toggleSidebar();
        });
    }

    // Cerrar sidebar al hacer clic en un enlace del menú (en móviles)
    const sidebarLinks = document.querySelectorAll('aside nav ul li a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 1024) {
                const sidebar = document.querySelector('aside');
                const overlay = document.querySelector('.sidebar-overlay');
                if (sidebar && overlay) {
                    sidebar.classList.remove('active');
                    overlay.classList.remove('active');
                }
            }
        });
    });

    // Cerrar sidebar con tecla ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const sidebar = document.querySelector('aside');
            const overlay = document.querySelector('.sidebar-overlay');
            if (sidebar && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
            }
        }
    });
});
