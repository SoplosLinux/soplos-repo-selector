#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soplos Repo Selector 2.0 - Gestor de Repositorios Avanzado

Punto de entrada principal de la aplicación.
"""

import sys
import os
import warnings
from pathlib import Path

# Añadir la raíz del proyecto al PYTHONPATH
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Suprimir advertencias de accesibilidad para una salida más limpia
warnings.filterwarnings('ignore', '.*Couldn\'t connect to accessibility bus.*', Warning)
warnings.filterwarnings('ignore', '.*Failed to connect to socket.*', Warning)

# Deshabilitar puente de accesibilidad si no está explícitamente habilitado
if not os.environ.get('ENABLE_ACCESSIBILITY'):
    os.environ['NO_AT_BRIDGE'] = '1'
    os.environ['AT_SPI_BUS'] = '0'

def main():
    """Punto de entrada principal para Soplos Repo Selector."""
    try:
        # Importar y ejecutar la aplicación
        # Nota: core.application será implementado en el siguiente paso
        from core.application import run_application
        return run_application()
        
    except ImportError as e:
        print(f"Error de importación: {e}")
        print("Asegúrate de que todas las dependencias están instaladas:")
        print("  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        # Fallback temporal para depuración hasta que core esté listo
        import traceback
        traceback.print_exc()
        return 1
        
    except Exception as e:
        print(f"Error de la aplicación: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
