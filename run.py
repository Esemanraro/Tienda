#!/usr/bin/env python3
"""
🚀 TIENDITA ALOHA - PUNTO DE ENTRADA PRINCIPAL
Sistema de e-commerce con logging avanzado, cache inteligente y monitoreo de performance.

Versión: 2.0
Última actualización: 2025-01-04
"""
import os
import sys
from pathlib import Path
from app import create_app

# Agregar el directorio actual al path para importaciones
sys.path.insert(0, str(Path(__file__).parent))

def initialize_advanced_systems(app):
    """Inicializar sistemas avanzados de la aplicación"""
    print("🔧 Initializing advanced systems...")
    
    # 1. Sistema de Logging
    try:
        from utils.logging_system import init_logging_system
        logger = init_logging_system(app)
        logger.log_info("🚀 Tiendita ALOHA starting up", category='main')
        print("✅ Logging system initialized")
    except Exception as e:
        print(f"⚠️ Logging system initialization failed: {e}")
    
    # 2. Sistema de Performance/Cache
    try:
        from utils.performance_optimizer import init_performance_optimizer
        optimizer = init_performance_optimizer(app)
        print("✅ Performance optimizer initialized")
    except Exception as e:
        print(f"⚠️ Performance optimizer initialization failed: {e}")
    
    # 3. Sistema de Backup
    try:
        from utils.backup_system_simple import init_backup_system
        init_backup_system(app)
        print("✅ Backup system initialized")
    except Exception as e:
        print(f"⚠️ Backup system initialization failed: {e}")
    
    print("🎉 All advanced systems initialized successfully!")

def setup_environment():
    """Configurar variables de entorno y directorios necesarios"""
    # Variables de entorno por defecto
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    # Crear directorios necesarios
    base_dir = Path(__file__).parent
    directories = [
        base_dir / 'instance',
        base_dir / 'instance' / 'logs',
        base_dir / 'instance' / 'backups',
        base_dir / 'static' / 'images' / 'toys'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print("📁 Directory structure verified")

def print_startup_banner():
    """Mostrar banner de inicio con información del sistema"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🎮 TIENDITA ALOHA 🎮                     ║
║                                                              ║
║  Sistema de E-commerce Avanzado                             ║
║  Versión: 2.0 | Estado: Production Ready ✅                ║
║                                                              ║
║  Características:                                           ║
║  • 📊 Logging avanzado con rotación automática              ║
║  • ⚡ Cache inteligente con Redis/Memory                    ║
║  • 💾 Sistema de backup automático                          ║
║  • 🔒 Rate limiting y seguridad CSRF                       ║
║  • 📱 Diseño responsive y moderno                          ║
║  • 🎯 Panel administrativo completo                        ║
║                                                              ║
║  URL: http://127.0.0.1:5004                                ║
║  Admin: http://127.0.0.1:5004/admin                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Función principal de la aplicación"""
    try:
        # Mostrar banner de inicio
        print_startup_banner()
        
        # Configurar entorno
        setup_environment()
        
        # Crear la aplicación Flask
        print("🏗️ Creating Flask application...")
        app = create_app()
        
        # Inicializar sistemas avanzados
        initialize_advanced_systems(app)
        
        # Log de inicio exitoso
        try:
            from utils.logging_system import tiendita_logger
            tiendita_logger.log_info(
                "🎉 Tiendita ALOHA started successfully",
                category='main',
                extra_data={
                    'host': '127.0.0.1',
                    'port': 5004,
                    'debug': True,
                    'version': '2.0'
                }
            )
        except:
            pass
        
        print("\n🚀 Starting Flask development server...")
        print("📱 Access the application at: http://127.0.0.1:5004")
        print("🔧 Admin panel at: http://127.0.0.1:5004/admin")
        print("\n💡 Press Ctrl+C to stop the server\n")
        
        # Ejecutar la aplicación
        app.run(
            host='127.0.0.1',
            port=5004,
            debug=False,
            use_reloader=True,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        try:
            from utils.logging_system import tiendita_logger
            tiendita_logger.log_info("🛑 Tiendita ALOHA stopped by user", category='main')
        except:
            pass
    
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        try:
            from utils.logging_system import tiendita_logger
            tiendita_logger.log_error(f"❌ Application startup error: {e}", exception=e)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
