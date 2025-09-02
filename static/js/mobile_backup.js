/**
 * JavaScript especifico para funcionalidad movil
 * Tiendita ALOHA - Optimizacion Mobile
 */

// Configuracion movil
const MobileConfig = {
    breakpoint: 768,
    touchDelay: 300,
    scrollThreshold: 10
};

// Deteccion de dispositivo movil
const isMobile = () => {
    return window.innerWidth <= MobileConfig.breakpoint || 
           /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

// Gestion de navegacion movil
class MobileNavigation {
    constructor() {
        this.mobileNav = document.querySelector('.mobile-nav');
        this.lastScrollTop = 0;
        this.isVisible = true;
        this.init();
    }

    init() {
        if (!this.mobileNav) return;
        
        this.setupScrollBehavior();
        this.setupTouchEvents();
        this.setupActiveStates();
        this.setupViewportHeight();
    }

    // Comportamiento de scroll para ocultar/mostrar navegacion
    setupScrollBehavior() {
        let ticking = false;
        
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    this.handleScroll();
                    ticking = false;
                });
                ticking = true;
            }
        });
    }

    handleScroll() {
        if (!isMobile()) return;
        
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollDelta = Math.abs(scrollTop - this.lastScrollTop);
        
        if (scrollDelta < MobileConfig.scrollThreshold) return;
        
        if (scrollTop > this.lastScrollTop && scrollTop > 100) {
            // Scrolling down - hide nav
            this.hideNavigation();
        } else {
            // Scrolling up - show nav
            this.showNavigation();
        }
        
        this.lastScrollTop = scrollTop;
    }

    hideNavigation() {
        if (!this.isVisible) return;
        this.mobileNav.style.transform = 'translateY(100%)';
        this.isVisible = false;
    }

    showNavigation() {
        if (this.isVisible) return;
        this.mobileNav.style.transform = 'translateY(0)';
        this.isVisible = true;
    }

    // Eventos tactiles para mejor UX
    setupTouchEvents() {
        const navLinks = this.mobileNav.querySelectorAll('a');
        
        navLinks.forEach(link => {
            link.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
            link.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
        });
    }

    handleTouchStart(e) {
        e.currentTarget.classList.add('touch-active');
    }

    handleTouchEnd(e) {
        setTimeout(() => {
            e.currentTarget.classList.remove('touch-active');
        }, 150);
    }

    // Estados activos mejorados
    setupActiveStates() {
        const currentPath = window.location.pathname;
        const navLinks = this.mobileNav.querySelectorAll('a');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.includes(href) && href !== '/') {
                link.classList.add('active');
            }
        });
    }

    // Ajuste de altura de viewport para moviles
    setupViewportHeight() {
        const setViewportHeight = () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        };
        
        setViewportHeight();
        window.addEventListener('resize', setViewportHeight);
        window.addEventListener('orientationchange', () => {
            setTimeout(setViewportHeight, 100);
        });
    }
}

// Gestion de formularios moviles
class MobileForms {
    constructor() {
        this.init();
    }

    init() {
        this.setupInputFocus();
        this.setupFormValidation();
        this.setupQuantityControls();
    }

    // Mejora del focus en inputs moviles
    setupInputFocus() {
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('focus', this.handleInputFocus.bind(this));
            input.addEventListener('blur', this.handleInputBlur.bind(this));
        });
    }

    handleInputFocus(e) {
        if (!isMobile()) return;
        
        const input = e.target;
        input.closest('.form-group')?.classList.add('focused');
        
        // Scroll suave al input
        setTimeout(() => {
            input.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center',
                inline: 'nearest'
            });
        }, 300);
    }

    handleInputBlur(e) {
        const input = e.target;
        input.closest('.form-group')?.classList.remove('focused');
    }

    // Validacion de formularios mejorada
    setupFormValidation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });
    }

    handleFormSubmit(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (submitBtn) {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
            
            // Restaurar despues de 3 segundos como fallback
            setTimeout(() => {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }, 3000);
        }
    }

    // Controles de cantidad mejorados
    setupQuantityControls() {
        const quantityControls = document.querySelectorAll('.quantity-control');
        
        quantityControls.forEach(control => {
            const minusBtn = control.querySelector('.qty-minus');
            const plusBtn = control.querySelector('.qty-plus');
            const input = control.querySelector('.qty-input');
            
            if (minusBtn && plusBtn && input) {
                minusBtn.addEventListener('click', () => this.updateQuantity(input, -1));
                plusBtn.addEventListener('click', () => this.updateQuantity(input, 1));
            }
        });
    }

    updateQuantity(input, delta) {
        const currentValue = parseInt(input.value) || 0;
        const newValue = Math.max(0, currentValue + delta);
        input.value = newValue;
        
        // Trigger change event
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }
}

// Gestion de notificaciones moviles
class MobileNotifications {
    constructor() {
        this.init();
    }

    init() {
        this.setupFlashMessages();
        this.setupToastNotifications();
    }

    setupFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-message');
        
        flashMessages.forEach(message => {
            // Auto-hide despues de 5 segundos
            setTimeout(() => {
                message.style.opacity = '0';
                setTimeout(() => {
                    message.remove();
                }, 300);
            }, 5000);
            
            // Swipe to dismiss
            this.setupSwipeToDismiss(message);
        });
    }

    setupSwipeToDismiss(element) {
        let startX = 0;
        let currentX = 0;
        let isDragging = false;
        
        element.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
        }, { passive: true });
        
        element.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            currentX = e.touches[0].clientX;
            const deltaX = currentX - startX;
            
            if (Math.abs(deltaX) > 10) {
                element.style.transform = `translateX(${deltaX}px)`;
                element.style.opacity = 1 - Math.abs(deltaX) / 200;
            }
        }, { passive: true });
        
        element.addEventListener('touchend', () => {
            if (!isDragging) return;
            isDragging = false;
            
            const deltaX = currentX - startX;
            
            if (Math.abs(deltaX) > 100) {
                // Dismiss
                element.style.transform = `translateX(${deltaX > 0 ? '100%' : '-100%'})`;
                element.style.opacity = '0';
                setTimeout(() => element.remove(), 300);
            } else {
                // Reset
                element.style.transform = 'translateX(0)';
                element.style.opacity = '1';
            }
        }, { passive: true });
    }

    setupToastNotifications() {
        // Crear contenedor para toasts si no existe
        if (!document.querySelector('.toast-container')) {
            const container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
    }

    showToast(message, type = 'info', duration = 3000) {
        const container = document.querySelector('.toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// Utilidades moviles
class MobileUtils {
    static preventZoom() {
        // Prevenir zoom en inputs
        document.addEventListener('touchstart', (e) => {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        }, { passive: false });
        
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }

    static setupPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let isPulling = false;
        
        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        }, { passive: true });
        
        document.addEventListener('touchmove', (e) => {
            if (!isPulling) return;
            currentY = e.touches[0].clientY;
            const pullDistance = currentY - startY;
            
            if (pullDistance > 100) {
                // Trigger refresh
                window.location.reload();
            }
        }, { passive: true });
        
        document.addEventListener('touchend', () => {
            isPulling = false;
        }, { passive: true });
    }

    static addToHomeScreen() {
        let deferredPrompt;
        
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // Mostrar boton de instalacion personalizado
            const installBtn = document.querySelector('.install-app-btn');
            if (installBtn) {
                installBtn.style.display = 'block';
                installBtn.addEventListener('click', () => {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((choiceResult) => {
                        if (choiceResult.outcome === 'accepted') {
                            console.log('Usuario acepto instalar la app');
                        }
                        deferredPrompt = null;
                    });
                });
            }
        });
    }
}

// Inicializacion cuando el DOM este listo
document.addEventListener('DOMContentLoaded', () => {
    if (isMobile()) {
        // Inicializar componentes moviles
        new MobileNavigation();
        new MobileForms();
        new MobileNotifications();
        
        // Configurar utilidades
        MobileUtils.preventZoom();
        MobileUtils.setupPullToRefresh();
        MobileUtils.addToHomeScreen();
        
        // Agregar clase movil al body
        document.body.classList.add('mobile-device');
        
        console.log('Tiendita ALOHA: Optimizacion movil activada');
    }
});

// Exportar para uso global
window.TienditaMobile = {
    MobileNavigation,
    MobileForms,
    MobileNotifications,
    MobileUtils,
    isMobile
};
