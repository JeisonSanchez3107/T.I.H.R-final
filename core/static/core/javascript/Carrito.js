/**
 * Script global para gestión del carrito de compras
 * Mantiene sincronizado el badge del carrito en todas las páginas
 */

// Función para obtener el carrito de sessionStorage
function getCartGlobal() {
    // Usar getCarritoKey() si está disponible (páginas con contexto de usuario)
    // Si no, usar la clave genérica (fallback para páginas sin login)
    const key = typeof getCarritoKey === 'function' ? getCarritoKey() : 'carrito_guest';
    return JSON.parse(sessionStorage.getItem(key) || '[]');
}

// Función para actualizar el badge del carrito en todas las páginas
function updateCartBadgeGlobal() {
    // Actualizar botón flotante si existe la función global
    if (typeof updateFloatingCartButton === 'function') {
        updateFloatingCartButton();
    }
    
    // También actualizar badge en menús si existe (compatibilidad con páginas antiguas)
    if (typeof updateCartBadgeInMenus === 'function') {
        updateCartBadgeInMenus();
    }
}

// Actualizar badge cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    updateCartBadgeGlobal();
});

// Actualizar badge cuando cambia el almacenamiento (para múltiples pestañas)
window.addEventListener('storage', function(e) {
    if (e.key === 'carrito') {
        updateCartBadgeGlobal();
    }
});
