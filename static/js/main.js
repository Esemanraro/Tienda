// Cache para el contenedor de toasts
let toastContainer = null;

// Función global para mostrar notificaciones toast optimizada
function showToast(message, type = 'info', duration = 1500) {
    // Usar requestAnimationFrame para mejor rendimiento
    requestAnimationFrame(() => {
        // Crear contenedor si no existe (solo una vez)
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            Object.assign(toastContainer.style, {
                position: 'fixed',
                top: '20px', // Volvemos arriba pero del lado izquierdo
                left: '20px', // Cambio a lado izquierdo para evitar superposición
                zIndex: '1050', // Z-index más bajo para no interferir con modales
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start', // Alineación a la izquierda
                pointerEvents: 'none',
                maxWidth: '320px'
            });
            document.body.appendChild(toastContainer);
        }
        
        // Crear toast
        const toast = document.createElement('div');
        const toastId = 'toast-' + Date.now();
        toast.id = toastId;
        toast.className = `toast toast-${type}`;
        
        // Estilos con mejor rendimiento usando Object.assign
        Object.assign(toast.style, {
            background: type === 'success' ? 'linear-gradient(135deg, #28a745 0%, #20c997 100%)' : 
                       type === 'error' ? 'linear-gradient(135deg, #dc3545 0%, #fd7e14 100%)' : 
                       'linear-gradient(135deg, #007bff 0%, #6f42c1 100%)',
            color: 'white',
            padding: '10px 16px',
            margin: '3px 0',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            border: '1px solid rgba(255,255,255,0.1)',
            opacity: '0',
            transform: 'translateX(-120%)', // Animación desde la izquierda
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            maxWidth: '280px',
            wordWrap: 'break-word',
            pointerEvents: 'auto',
            willChange: 'transform, opacity',
            backfaceVisibility: 'hidden',
            fontSize: '14px',
            fontWeight: '500',
            backdropFilter: 'blur(10px)',
            cursor: 'pointer'
        });
        
        toast.textContent = message;
        
        // Agregar funcionalidad de cerrar al hacer clic
        toast.addEventListener('click', () => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(-120%)'; // Salida hacia la izquierda
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        });
        
        // Agregar al DOM
        toastContainer.appendChild(toast);
        
        // Forzar reflow para activar la transición
        void toast.offsetWidth;
        
        // Animar entrada
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        });
        
        // Configurar eliminación
        let removeTimeout = setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(120%)';
            
            // Eliminar después de la animación
            toast.addEventListener('transitionend', function handler() {
                toast.removeEventListener('transitionend', handler);
                if (toast.parentNode === toastContainer) {
                    toastContainer.removeChild(toast);
                }
            }, { once: true });
        }, duration);
        
        // Cerrar al hacer clic
        toast.addEventListener('click', () => {
            clearTimeout(removeTimeout);
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(120%)';
            
            toast.addEventListener('transitionend', function handler() {
                toast.removeEventListener('transitionend', handler);
                if (toast.parentNode === toastContainer) {
                    toastContainer.removeChild(toast);
                }
            }, { once: true });
        });
    });
}

// Función para actualizar el badge del carrito
function updateCartBadge(count) {
    // Actualizar badge desktop
    const desktopBadge = document.querySelector('.cart-badge');
    const desktopLink = document.querySelector('.cart-link');
    
    if (desktopLink) {
        if (count > 0) {
            if (desktopBadge) {
                desktopBadge.textContent = count;
            } else {
                const badge = document.createElement('span');
                badge.className = 'cart-badge';
                badge.textContent = count;
                desktopLink.appendChild(badge);
            }
        } else if (desktopBadge) {
            desktopBadge.remove();
        }
    }
    
    // Actualizar badge móvil
    const mobileBadge = document.querySelector('.cart-badge-mobile');
    const mobileLink = document.querySelector('.cart-link-mobile');
    
    if (mobileLink) {
        if (count > 0) {
            if (mobileBadge) {
                mobileBadge.textContent = count;
            } else {
                const badge = document.createElement('span');
                badge.className = 'cart-badge-mobile';
                badge.textContent = count;
                mobileLink.appendChild(badge);
            }
        } else if (mobileBadge) {
            mobileBadge.remove();
        }
    }
}

function addToCart(toyId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    console.log('Intentando agregar al carrito:', toyId);
    console.log('CSRF Token:', csrfToken);
    
    // Crear los datos del formulario
    const formData = new FormData();
    formData.append('toy_id', toyId);
    formData.append('quantity', 1);
    formData.append('csrf_token', csrfToken);
    
    fetch('/add_to_cart', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('Respuesta recibida:', response.status);
        if (response.redirected) {
            // Si hay redirección, probablemente fue exitoso
            showToast('✨ ¡Producto agregado al carrito!', 'success');
            return { success: true };
        }
        return response.json();
    })
    .then(data => {
        console.log('Datos recibidos:', data);
        if (data.success) {
            showToast('✨ ¡Producto agregado al carrito!', 'success');
            // Actualizar el badge del carrito si existe cart_count en la respuesta
            if (data.cart_count !== undefined) {
                updateCartBadge(data.cart_count);
            }
        } else {
            showToast(data.message || '❌ Error al agregar al carrito', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('❌ Error al agregar al carrito', 'error');
    });
}
