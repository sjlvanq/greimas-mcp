"""
Configuración centralizada de logging para el proyecto.

Archivo de ejemplo con diferentes niveles de configuración.
"""

import os
from core.logger import set_log_level, get_logger

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

# Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# Recomendaciones:
# - DEBUG: Desarrollo local, máximo detalle
# - INFO: Producción normal, eventos importantes
# - WARNING: Solo advertencias y errores
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

# Aplicar configuración
set_log_level(LOG_LEVEL)

# ============================================================================
# LOGGERS ESPECÍFICOS POR MÓDULO
# ============================================================================

# Logger para análisis de factibilidad
feasibility_logger = get_logger("FeasibilityAnalyzer")

# Logger para esquemas actanciales
actantial_logger = get_logger("ActantialSchemeAnalyzer")

# Logger para servidor MCP
server_logger = get_logger("MCPServer")

# Logger para análisis base
base_logger = get_logger("NarrativeAnalyzer")


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Ejemplos de logging en diferentes niveles
    logger = get_logger("ExampleApp")

    logger.debug("Mensaje de debug - información detallada para desarrollo")
    logger.info("Mensaje informativo - eventos importantes", user_id=123, action="login")
    logger.warning("Advertencia - algo sospechoso pero no crítico", attempt=3)
    logger.error("Error - algo falló", error_type="ValueError", recovery="retry")
    logger.critical("Error crítico - sistema comprometido", component="auth")
