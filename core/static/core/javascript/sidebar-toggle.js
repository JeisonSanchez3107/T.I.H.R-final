/**
 * Sidebar Toggle - DEFINICIÓN GLOBAL INMEDIATA
 * Función disponible antes de DOMContentLoaded
 */

// Definir la función toggleSidebar INMEDIATAMENTE de forma global
window.toggleSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (!sidebar) {
        console.error('Sidebar no encontrado');
        return;
    }
    
    const isActive = sidebar.classList.contains('active');
    
    if (isActive) {
        // Cerrar sidebar
        sidebar.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
        
        // Cambiar icono del botón
        const btn = document.querySelector('.sidebar-toggle');
        if (btn) btn.innerHTML = '☰';
    } else {
        // Abrir sidebar
        sidebar.classList.add('active');
        if (overlay) overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Cambiar icono del botón
        const btn = document.querySelector('.sidebar-toggle');
        if (btn) btn.innerHTML = '✕';
    }
};

// Configuración adicional cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (!sidebar) {
        console.warn('Sidebar no encontrado en el DOM');
        return;
    }
    
    // Asegurar que el sidebar esté oculto al inicio
    sidebar.classList.remove('active');
    if (overlay) overlay.classList.remove('active');
    
    // Click en overlay cierra el sidebar
    if (overlay) {
        overlay.addEventListener('click', function() {
            window.toggleSidebar();
        });
    }
    
    // Cerrar sidebar con tecla ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('active')) {
            window.toggleSidebar();
        }
    });
    
    // Cerrar sidebar al hacer clic en enlaces
    const sidebarLinks = sidebar.querySelectorAll('a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (sidebar.classList.contains('active')) {
                window.toggleSidebar();
            }
        });
    });
    
    // Soporte para gestos táctiles (swipe)
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        const swipeDistance = touchEndX - touchStartX;
        const minSwipeDistance = 50;
        
        // Swipe desde la izquierda para abrir
        if (touchStartX < 50 && swipeDistance > minSwipeDistance && !sidebar.classList.contains('active')) {
            window.toggleSidebar();
        }
        
        // Swipe hacia la izquierda para cerrar
        if (sidebar.classList.contains('active') && swipeDistance < -minSwipeDistance) {
            window.toggleSidebar();
        }
    }, { passive: true });
    
    console.log('✅ Sidebar toggle inicializado correctamente');
});
