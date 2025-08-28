/**
 * JavaScript optimizado para funcionalidad móvil
 * Tiendita ALOHA - Optimización Mobile v2.0
 * Mejoras: Performance, Memoria, Accesibilidad, Manejo de Errores
 */

// Configuración móvil
const MobileConfig = {
    breakpoint: 768,
    touchDelay: 300,
    scrollThreshold: 10,
    debounceDelay: 250,
    toastDuration: 3000
};

// Utilidades de rendimiento
const PerfUtils = {
    // Debounce mejorado
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    },

    // Throttle optimizado
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Intersection Observer para lazy loading
    createIntersectionObserver(callback, options = {}) {
        const defaultOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };
        return new IntersectionObserver(callback, { ...defaultOptions, ...options });
    }
};

// Detección de dispositivo móvil mejorada
const DeviceDetection = {
    isMobile() {
        return window.innerWidth <= MobileConfig.breakpoint || 
               /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },

    isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent);
    },

    isAndroid() {
        return /Android/.test(navigator.userAgent);
    },

    supportsTouch() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
};

// Gestión de navegación móvil optimizada
class MobileNavigation {
    constructor() {
        this.mobileNav = document.querySelector('.mobile-nav');
        this.lastScrollTop = 0;
        this.isVisible = true;
        this.scrollTimer = null;
        this.resizeTimer = null;
        this.eventListeners = new Map(); // Para limpieza de memoria
        
        this.init();
    }

    init() {
        if (!this.mobileNav) {
            console.warn('MobileNavigation: No se encontró elemento .mobile-nav');
            return;
        }
        
        try {
            this.setupScrollBehavior();
            this.setupTouchEvents();
            this.setupActiveStates();
            this.setupViewportHeight();
            this.setupKeyboardNavigation();
        } catch (error) {
            console.error('Error inicializando MobileNavigation:', error);
        }
    }

    // Comportamiento de scroll optimizado con throttle
    setupScrollBehavior() {
        const throttledScroll = PerfUtils.throttle(() => {
            this.handleScroll();
        }, 16); // ~60fps

        this.addEventListener(window, 'scroll', throttledScroll, { passive: true });
    }

    handleScroll() {
        if (!DeviceDetection.isMobile()) return;
        
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollDelta = Math.abs(scrollTop - this.lastScrollTop);
        
        if (scrollDelta < MobileConfig.scrollThreshold) return;
        
        if (scrollTop > this.lastScrollTop && scrollTop > 100) {
            this.hideNavigation();
        } else {
            this.showNavigation();
        }
        
        this.lastScrollTop = scrollTop;
    }

    hideNavigation() {
        if (!this.isVisible) return;
        this.mobileNav.style.transform = 'translateY(100%)';
        this.mobileNav.setAttribute('aria-hidden', 'true');
        this.isVisible = false;
    }

    showNavigation() {
        if (this.isVisible) return;
        this.mobileNav.style.transform = 'translateY(0)';
        this.mobileNav.setAttribute('aria-hidden', 'false');
        this.isVisible = true;
    }

    // Eventos táctiles optimizados
    setupTouchEvents() {
        const navLinks = this.mobileNav.querySelectorAll('a, button');
        
        navLinks.forEach(link => {
            this.addEventListener(link, 'touchstart', this.handleTouchStart.bind(this), { passive: true });
            this.addEventListener(link, 'touchend', this.handleTouchEnd.bind(this), { passive: true });
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

    // Estados activos con mejor lógica
    setupActiveStates() {
        const currentPath = window.location.pathname;
        const navLinks = this.mobileNav.querySelectorAll('a');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.includes(href) && href !== '/') {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            }
        });
    }

    // Navegación por teclado mejorada
    setupKeyboardNavigation() {
        this.addEventListener(this.mobileNav, 'keydown', (e) => {
            if (e.key === 'Escape') {
                const activeElement = document.activeElement;
                if (this.mobileNav.contains(activeElement)) {
                    activeElement.blur();
                }
            }
        });
    }

    // Ajuste de altura de viewport optimizado
    setupViewportHeight() {
        const debouncedResize = PerfUtils.debounce(() => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        }, MobileConfig.debounceDelay);
        
        // Ejecutar inmediatamente
        debouncedResize();
        
        this.addEventListener(window, 'resize', debouncedResize);
        this.addEventListener(window, 'orientationchange', () => {
            setTimeout(debouncedResize, 100);
        });
    }

    // Gestión de event listeners para limpieza de memoria
    addEventListener(element, event, handler, options) {
        element.addEventListener(event, handler, options);
        
        // Guardar referencia para limpieza posterior
        if (!this.eventListeners.has(element)) {
            this.eventListeners.set(element, []);
        }
        this.eventListeners.get(element).push({ event, handler, options });
    }

    // Método de limpieza
    destroy() {
        this.eventListeners.forEach((listeners, element) => {
            listeners.forEach(({ event, handler, options }) => {
                element.removeEventListener(event, handler, options);
            });
        });
        this.eventListeners.clear();
        
        if (this.scrollTimer) clearTimeout(this.scrollTimer);
        if (this.resizeTimer) clearTimeout(this.resizeTimer);
    }
}

// Gestión de formularios móviles mejorada
class MobileForms {
    constructor() {
        this.activeInputs = new WeakSet(); // Para evitar memory leaks
        this.submitTimers = new Map();
        this.init();
    }

    init() {
        try {
            this.setupInputFocus();
            this.setupFormValidation();
            this.setupQuantityControls();
            this.setupAccessibility();
        } catch (error) {
            console.error('Error inicializando MobileForms:', error);
        }
    }

    // Focus mejorado con manejo de errores
    setupInputFocus() {
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('focus', this.handleInputFocus.bind(this), { passive: true });
            input.addEventListener('blur', this.handleInputBlur.bind(this), { passive: true });
        });
    }

    handleInputFocus(e) {
        if (!DeviceDetection.isMobile()) return;
        
        const input = e.target;
        this.activeInputs.add(input);
        
        const formGroup = input.closest('.form-group');
        if (formGroup) {
            formGroup.classList.add('focused');
            formGroup.setAttribute('data-focused', 'true');
        }
        
        // Scroll suave mejorado con cancelación
        if (this.scrollTimer) clearTimeout(this.scrollTimer);
        
        this.scrollTimer = setTimeout(() => {
            if (this.activeInputs.has(input)) {
                input.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center',
                    inline: 'nearest'
                });
            }
        }, 300);
    }

    handleInputBlur(e) {
        const input = e.target;
        this.activeInputs.delete(input);
        
        const formGroup = input.closest('.form-group');
        if (formGroup) {
            formGroup.classList.remove('focused');
            formGroup.removeAttribute('data-focused');
        }
    }

    // Validación de formularios con mejor UX
    setupFormValidation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });
    }

    handleFormSubmit(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (submitBtn && !submitBtn.disabled) {
            // Prevenir doble envío
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
            submitBtn.setAttribute('aria-busy', 'true');
            
            // Limpiar timer anterior si existe
            if (this.submitTimers.has(form)) {
                clearTimeout(this.submitTimers.get(form));
            }
            
            // Fallback timer mejorado
            const timer = setTimeout(() => {
                if (submitBtn) {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                    submitBtn.setAttribute('aria-busy', 'false');
                }
                this.submitTimers.delete(form);
            }, 5000); // Aumentado a 5 segundos
            
            this.submitTimers.set(form, timer);
        }
    }

    // Controles de cantidad con validación
    setupQuantityControls() {
        const quantityControls = document.querySelectorAll('.quantity-control');
        
        quantityControls.forEach(control => {
            const minusBtn = control.querySelector('.qty-minus');
            const plusBtn = control.querySelector('.qty-plus');
            const input = control.querySelector('.qty-input');
            
            if (minusBtn && plusBtn && input) {
                minusBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.updateQuantity(input, -1);
                });
                
                plusBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.updateQuantity(input, 1);
                });
                
                // Validación en tiempo real
                input.addEventListener('input', () => {
                    this.validateQuantityInput(input);
                });
            }
        });
    }

    updateQuantity(input, delta) {
        const currentValue = parseInt(input.value) || 0;
        const min = parseInt(input.getAttribute('min')) || 0;
        const max = parseInt(input.getAttribute('max')) || 999;
        
        const newValue = Math.max(min, Math.min(max, currentValue + delta));
        
        if (newValue !== currentValue) {
            input.value = newValue;
            input.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Feedback visual
            input.classList.add('quantity-updated');
            setTimeout(() => input.classList.remove('quantity-updated'), 300);
        }
    }

    validateQuantityInput(input) {
        const value = parseInt(input.value);
        const min = parseInt(input.getAttribute('min')) || 0;
        const max = parseInt(input.getAttribute('max')) || 999;
        
        if (isNaN(value) || value < min) {
            input.value = min;
        } else if (value > max) {
            input.value = max;
        }
    }

    // Mejoras de accesibilidad
    setupAccessibility() {
        // Mejorar labels y aria-labels
        const inputs = document.querySelectorAll('input[type="number"]');
        inputs.forEach(input => {
            if (!input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
                const label = input.closest('.form-group')?.querySelector('label');
                if (label) {
                    const labelId = label.id || `label-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                    label.id = labelId;
                    input.setAttribute('aria-labelledby', labelId);
                }
            }
        });
    }

    // Limpieza de memoria
    destroy() {
        this.submitTimers.forEach(timer => clearTimeout(timer));
        this.submitTimers.clear();
        if (this.scrollTimer) clearTimeout(this.scrollTimer);
    }
}

// Gestión de notificaciones optimizada
class MobileNotifications {
    constructor() {
        this.activeToasts = new Set();
        this.maxToasts = 3;
        this.init();
    }

    init() {
        try {
            this.setupFlashMessages();
            this.setupToastNotifications();
        } catch (error) {
            console.error('Error inicializando MobileNotifications:', error);
        }
    }

    setupFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-message');
        
        flashMessages.forEach(message => {
            // Mejorar accesibilidad
            message.setAttribute('role', 'alert');
            message.setAttribute('aria-live', 'polite');
            
            // Auto-hide con mejor animación
            const hideTimer = setTimeout(() => {
                this.dismissMessage(message);
            }, 5000);
            
            // Swipe to dismiss
            this.setupSwipeToDismiss(message, hideTimer);
            
            // Botón de cerrar si no existe
            if (!message.querySelector('.close-btn')) {
                const closeBtn = document.createElement('button');
                closeBtn.className = 'close-btn';
                closeBtn.innerHTML = '×';
                closeBtn.setAttribute('aria-label', 'Cerrar mensaje');
                closeBtn.addEventListener('click', () => {
                    clearTimeout(hideTimer);
                    this.dismissMessage(message);
                });
                message.appendChild(closeBtn);
            }
        });
    }

    dismissMessage(message) {
        message.style.opacity = '0';
        message.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (message.parentNode) {
                message.remove();
            }
        }, 300);
    }

    setupSwipeToDismiss(element, timer) {
        let startX = 0;
        let currentX = 0;
        let isDragging = false;
        let startTime = 0;
        
        const handleTouchStart = (e) => {
            startX = e.touches[0].clientX;
            startTime = Date.now();
            isDragging = true;
            element.style.transition = 'none';
        };
        
        const handleTouchMove = (e) => {
            if (!isDragging) return;
            currentX = e.touches[0].clientX;
            const deltaX = currentX - startX;
            
            if (Math.abs(deltaX) > 10) {
                element.style.transform = `translateX(${deltaX}px)`;
                element.style.opacity = Math.max(0.3, 1 - Math.abs(deltaX) / 200);
            }
        };
        
        const handleTouchEnd = () => {
            if (!isDragging) return;
            isDragging = false;
            
            const deltaX = currentX - startX;
            const deltaTime = Date.now() - startTime;
            const velocity = Math.abs(deltaX) / deltaTime;
            
            element.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
            
            // Dismiss si swipe es suficientemente rápido o lejos
            if (Math.abs(deltaX) > 100 || velocity > 0.5) {
                clearTimeout(timer);
                element.style.transform = `translateX(${deltaX > 0 ? '100%' : '-100%'})`;
                element.style.opacity = '0';
                setTimeout(() => element.remove(), 300);
            } else {
                // Reset
                element.style.transform = 'translateX(0)';
                element.style.opacity = '1';
            }
        };
        
        element.addEventListener('touchstart', handleTouchStart, { passive: true });
        element.addEventListener('touchmove', handleTouchMove, { passive: true });
        element.addEventListener('touchend', handleTouchEnd, { passive: true });
    }

    setupToastNotifications() {
        // Crear contenedor si no existe
        if (!document.querySelector('.toast-container')) {
            const container = document.createElement('div');
            container.className = 'toast-container';
            container.setAttribute('aria-live', 'polite');
            container.setAttribute('aria-atomic', 'false');
            document.body.appendChild(container);
        }
    }

    showToast(message, type = 'info', duration = MobileConfig.toastDuration) {
        // Limitar número de toasts
        if (this.activeToasts.size >= this.maxToasts) {
            const oldestToast = this.activeToasts.values().next().value;
            this.removeToast(oldestToast);
        }
        
        const container = document.querySelector('.toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        
        // Estructura mejorada del toast
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                <button class="toast-close" aria-label="Cerrar notificación">×</button>
            </div>
        `;
        
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.removeToast(toast));
        
        container.appendChild(toast);
        this.activeToasts.add(toast);
        
        // Animate in
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto remove
        setTimeout(() => {
            this.removeToast(toast);
        }, duration);
        
        return toast;
    }

    removeToast(toast) {
        if (!this.activeToasts.has(toast)) return;
        
        this.activeToasts.delete(toast);
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }

    // Limpieza
    destroy() {
        this.activeToasts.forEach(toast => this.removeToast(toast));
        this.activeToasts.clear();
    }
}

// Utilidades móviles mejoradas
class MobileUtils {
    static preventZoom() {
        if (!DeviceDetection.supportsTouch()) return;
        
        let lastTouchEnd = 0;
        let touchCount = 0;
        
        // Prevenir zoom por pinch
        const handleTouchStart = (e) => {
            touchCount = e.touches.length;
            if (touchCount > 1) {
                e.preventDefault();
            }
        };
        
        // Prevenir doble tap zoom
        const handleTouchEnd = (e) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300 && touchCount === 1) {
                e.preventDefault();
            }
            lastTouchEnd = now;
            touchCount = 0;
        };
        
        document.addEventListener('touchstart', handleTouchStart, { passive: false });
        document.addEventListener('touchend', handleTouchEnd, { passive: false });
    }

    static setupPullToRefresh() {
        if (!DeviceDetection.supportsTouch()) return;
        
        let startY = 0;
        let currentY = 0;
        let isPulling = false;
        let pullIndicator = null;
        
        const createPullIndicator = () => {
            pullIndicator = document.createElement('div');
            pullIndicator.className = 'pull-to-refresh-indicator';
            pullIndicator.innerHTML = '↓ Desliza para actualizar';
            pullIndicator.style.cssText = `
                position: fixed;
                top: -50px;
                left: 50%;
                transform: translateX(-50%);
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                transition: top 0.3s ease;
                z-index: 9999;
            `;
            document.body.appendChild(pullIndicator);
        };
        
        const handleTouchStart = (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
                if (!pullIndicator) createPullIndicator();
            }
        };
        
        const handleTouchMove = (e) => {
            if (!isPulling) return;
            currentY = e.touches[0].clientY;
            const pullDistance = currentY - startY;
            
            if (pullDistance > 0 && pullDistance < 150) {
                if (pullIndicator) {
                    pullIndicator.style.top = `${pullDistance - 50}px`;
                }
            } else if (pullDistance >= 150) {
                if (pullIndicator) {
                    pullIndicator.innerHTML = '↑ Suelta para actualizar';
                    pullIndicator.style.background = '#28a745';
                }
            }
        };
        
        const handleTouchEnd = () => {
            if (!isPulling) return;
            isPulling = false;
            
            const pullDistance = currentY - startY;
            
            if (pullDistance >= 150) {
                // Trigger refresh
                if (pullIndicator) {
                    pullIndicator.innerHTML = '🔄 Actualizando...';
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                }
            } else {
                // Reset indicator
                if (pullIndicator) {
                    pullIndicator.style.top = '-50px';
                    setTimeout(() => {
                        if (pullIndicator && pullIndicator.parentNode) {
                            pullIndicator.remove();
                            pullIndicator = null;
                        }
                    }, 300);
                }
            }
        };
        
        document.addEventListener('touchstart', handleTouchStart, { passive: true });
        document.addEventListener('touchmove', handleTouchMove, { passive: true });
        document.addEventListener('touchend', handleTouchEnd, { passive: true });
    }

    static addToHomeScreen() {
        let deferredPrompt = null;
        
        const handleBeforeInstallPrompt = (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // Mostrar botón personalizado si existe
            const installBtn = document.querySelector('.install-app-btn');
            if (installBtn) {
                installBtn.style.display = 'block';
                installBtn.setAttribute('aria-hidden', 'false');
                
                const handleInstallClick = async () => {
                    if (!deferredPrompt) return;
                    
                    try {
                        deferredPrompt.prompt();
                        const choiceResult = await deferredPrompt.userChoice;
                        
                        if (choiceResult.outcome === 'accepted') {
                            console.log('Usuario aceptó instalar la app');
                            // Opcional: Analytics o feedback
                        }
                        
                        deferredPrompt = null;
                        installBtn.style.display = 'none';
                    } catch (error) {
                        console.error('Error en la instalación:', error);
                    }
                };
                
                installBtn.addEventListener('click', handleInstallClick);
            }
        };
        
        window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
        
        // Detectar cuando la app ya está instalada
        window.addEventListener('appinstalled', () => {
            console.log('App instalada exitosamente');
            deferredPrompt = null;
        });
    }

    // Optimización de imágenes para móvil
    static optimizeImages() {
        const images = document.querySelectorAll('img[data-src]');
        
        const imageObserver = PerfUtils.createIntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => {
            img.classList.add('lazy');
            imageObserver.observe(img);
        });
    }

    // Detección de conexión
    static setupConnectionMonitoring() {
        const updateConnectionStatus = () => {
            const isOnline = navigator.onLine;
            document.body.classList.toggle('offline', !isOnline);
            
            if (!isOnline) {
                const notification = new MobileNotifications();
                notification.showToast('Sin conexión a internet', 'warning', 5000);
            }
        };
        
        window.addEventListener('online', updateConnectionStatus);
        window.addEventListener('offline', updateConnectionStatus);
        updateConnectionStatus(); // Check inicial
    }
}

// Gestión global de instancias para limpieza
class MobileManager {
    constructor() {
        this.instances = new Map();
        this.isInitialized = false;
    }

    init() {
        if (this.isInitialized || !DeviceDetection.isMobile()) return;
        
        try {
            // Inicializar componentes principales
            this.instances.set('navigation', new MobileNavigation());
            this.instances.set('forms', new MobileForms());
            this.instances.set('notifications', new MobileNotifications());
            
            // Configurar utilidades
            MobileUtils.preventZoom();
            MobileUtils.setupPullToRefresh();
            MobileUtils.addToHomeScreen();
            MobileUtils.optimizeImages();
            MobileUtils.setupConnectionMonitoring();
            
            // Agregar clase al body
            document.body.classList.add('mobile-device');
            
            // Performance monitoring
            if ('performance' in window) {
                window.addEventListener('load', () => {
                    setTimeout(() => {
                        const perfData = window.performance.timing;
                        const loadTime = perfData.loadEventEnd - perfData.navigationStart;
                        console.log(`Tiendita ALOHA Mobile: Carga completada en ${loadTime}ms`);
                    }, 0);
                });
            }
            
            this.isInitialized = true;
            console.log('Tiendita ALOHA: Optimización móvil activada v2.0');
            
        } catch (error) {
            console.error('Error inicializando MobileManager:', error);
        }
    }

    destroy() {
        this.instances.forEach((instance, key) => {
            if (instance && typeof instance.destroy === 'function') {
                instance.destroy();
            }
        });
        this.instances.clear();
        this.isInitialized = false;
    }

    getInstance(name) {
        return this.instances.get(name);
    }
}

// Instancia global del manager
const mobileManager = new MobileManager();

// Inicialización optimizada
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => mobileManager.init());
} else {
    mobileManager.init();
}

// Limpieza al salir de la página
window.addEventListener('beforeunload', () => {
    mobileManager.destroy();
});

// Exportar para uso global
window.TienditaMobile = {
    // Clases principales
    MobileNavigation,
    MobileForms,
    MobileNotifications,
    MobileUtils,
    
    // Utilidades
    DeviceDetection,
    PerfUtils,
    
    // Manager principal
    MobileManager: mobileManager,
    
    // Funciones de conveniencia
    isMobile: DeviceDetection.isMobile,
    showToast: (message, type, duration) => {
        const notifications = mobileManager.getInstance('notifications');
        return notifications ? notifications.showToast(message, type, duration) : null;
    }
};
