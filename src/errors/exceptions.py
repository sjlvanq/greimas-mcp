class NarrativeAnalysisError(Exception):
    """Excepción base para errores de análisis narrativo."""
    
    def __init__(self, message: str, analysis_type: str = "", error_code: str = ""):
        self.message = message
        self.analysis_type = analysis_type
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(NarrativeAnalysisError):
    """Error en validación de input."""
    
    def __init__(self, message: str, analysis_type: str = ""):
        super().__init__(message, analysis_type, "VALIDATION_ERROR")


class EmptyTextError(ValidationError):
    """Texto vacío o demasiado corto."""
    
    def __init__(self, min_length: int = 20):
        msg = f"Text is too short for analysis (minimum {min_length} characters)"
        super().__init__(msg, analysis_type="TEXT_VALIDATION")


class LLMParsingError(NarrativeAnalysisError):
    """Error al parsear respuesta del LLM."""
    
    def __init__(self, message: str, original_exception: Exception = None):
        self.original_exception = original_exception
        super().__init__(message, analysis_type="LLM_PARSING", error_code="LLM_PARSE_ERROR")


class InvalidResponseFormatError(LLMParsingError):
    """Respuesta del LLM no es JSON válido."""
    
    def __init__(self, original_exception: Exception = None):
        msg = "LLM response is not valid JSON"
        super().__init__(msg, original_exception)


class MissingRequiredFieldError(NarrativeAnalysisError):
    """Campo requerido falta en la respuesta."""
    
    def __init__(self, field_name: str, analysis_type: str = ""):
        msg = f"Missing required field in response: {field_name}"
        super().__init__(msg, analysis_type, "MISSING_FIELD")


class UnexpectedAnalysisError(NarrativeAnalysisError):
    """Error inesperado durante el análisis."""
    
    def __init__(self, message: str, original_exception: Exception = None):
        self.original_exception = original_exception
        super().__init__(message, analysis_type="UNEXPECTED", error_code="UNEXPECTED_ERROR")