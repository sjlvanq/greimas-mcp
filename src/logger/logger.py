import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Instancia global por defecto
_global_logger = None

class Logger:
    """Logger centralizado para la aplicación."""
    
    _instances = {}
    
    def __new__(cls, name: str = "greimas", *args, **kwargs):
        """Singleton por nombre de logger."""
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
    
    def __init__(self, name: str = "greimas", level: Optional[str] = None):
        # Evitar re-inicializar la misma instancia
        if hasattr(self, '_initialized'):
            if level:
                self.set_level(level)
            return
        self._initialized = True

        self.logger = logging.getLogger(name)

        # Determinar nivel efectivo
        if level is None:
            # Intentar heredar del logger global si existe
            global _global_logger
            if (_global_logger is not None and 
                getattr(_global_logger, 'logger', None) is not None and 
                _global_logger is not self):
                try:
                    current_level_int = _global_logger.logger.level
                    level = logging.getLevelName(current_level_int)
                except Exception:
                    level = "INFO"
            else:
                level = "INFO"

        # Aplicar nivel
        self.logger.setLevel(self._get_level(level))
        self.logger.propagate = False

        # Limpiar handlers previos
        self.logger.handlers.clear()

        # Configurar directorio de logs
        self.log_dir = Path(os.getenv('LOG_DIR', 'logs'))
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Fallback a current dir si no se puede crear
            self.log_dir = Path('.')

        # En entornos de pruebas (detecta pytest o variable TESTING) usar stdout
        in_test = bool(os.getenv('PYTEST_CURRENT_TEST') or os.getenv('TESTING'))
        if in_test:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(self.logger.level)
            fmt = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            stream_handler.setFormatter(fmt)
            self.logger.addHandler(stream_handler)
        else:
            # Siempre agregar handler a archivo (rotación por tamaño)
            self._setup_file_handler()
            # Y además un handler a stdout para ver logs durante ejecución
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(self.logger.level)
            fmt = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            stream_handler.setFormatter(fmt)
            self.logger.addHandler(stream_handler)

    @staticmethod
    def _get_level(level: str) -> int:
        """Convierte string a nivel de logging."""
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        try:
            return levels.get(level.upper(), logging.INFO)
        except Exception:
            return logging.INFO
       
    def _setup_file_handler(self) -> None:
        """Configura handler para archivo con rotación."""
        log_file = self.log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
        # Rotación por tamaño
        file_handler = logging.handlers.RotatingFileHandler(
            str(log_file),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5  # Mantener 5 archivos antiguos
        )
        file_handler.setLevel(logging.DEBUG)
        fmt = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(fmt)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **context) -> None:
        """Log de nivel DEBUG."""
        self._log(logging.DEBUG, message, context)
    
    def info(self, message: str, **context) -> None:
        """Log de nivel INFO."""
        self._log(logging.INFO, message, context)
    
    def warning(self, message: str, **context) -> None:
        """Log de nivel WARNING."""
        self._log(logging.WARNING, message, context)
    
    def error(self, message: str, exc_info: bool = False, **context) -> None:
        """Log de nivel ERROR."""
        self._log(logging.ERROR, message, context, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False, **context) -> None:
        """Log de nivel CRITICAL."""
        self._log(logging.CRITICAL, message, context, exc_info=exc_info)
    
    def _log(
        self,
        level: int,
        message: str,
        context: dict,
        exc_info: bool = False
    ) -> None:
        """
        Log con contexto opcional.
        
        Args:
            level: Nivel de logging
            message: Mensaje principal
            context: Contexto adicional (clave=valor)
            exc_info: Si incluir excepción
        """
        msg = message
        if context:
            # Formatear contexto: key1=value1, key2=value2
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            msg = f"{message} | {context_str}"
        
        self.logger.log(level, msg, exc_info=exc_info)
    
    def set_level(self, level: str) -> None:
        """Cambia el nivel de logging en runtime."""
        lvl = self._get_level(level)
        self.logger.setLevel(lvl)
        # Ajustar niveles de handlers también
        for h in self.logger.handlers:
            try:
                h.setLevel(lvl)
            except Exception:
                pass


def get_logger(name: str = "greimas", level: Optional[str] = None) -> Logger:
    """
    Obtiene una instancia del logger. 
    Si no se especifica nivel, intenta heredar el del logger global.
    """
    global _global_logger
    if _global_logger is None:
        # Crear instancia global con nivel INFO por defecto para evitar recursión
        _global_logger = Logger(name="greimas", level="INFO")
    if level is None:
        try:
            current_level_int = _global_logger.logger.level
            level = logging.getLevelName(current_level_int)
        except Exception:
            level = "INFO"
    return Logger(name, level=level)


def set_log_level(level: str) -> None:
    """Establece el nivel de logging global."""
    global _global_logger
    if _global_logger is None:
        _global_logger = get_logger()
    _global_logger.set_level(level)


# Exports para uso directo (wrappers seguros que no dependen de _global_logger ya inicializado)
def debug(message: str, **context):
    return get_logger().debug(message, **context)

def info(message: str, **context):
    return get_logger().info(message, **context)

def warning(message: str, **context):
    return get_logger().warning(message, **context)

def error(message: str, exc_info: bool = False, **context):
    return get_logger().error(message, exc_info=exc_info, **context)

def critical(message: str, exc_info: bool = False, **context):
    return get_logger().critical(message, exc_info=exc_info, **context)
