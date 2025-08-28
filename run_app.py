#!/usr/bin/env python3
import os
from app.app import app

if __name__ == '__main__':
    # Configurar variables de entorno
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Ejecutar la aplicación en puerto 5003
    app.run(host='127.0.0.1', port=5003, debug=True)
