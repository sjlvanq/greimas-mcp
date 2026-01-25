from typing import Dict, Any
from core.analyzer import NarrativeAnalyzer, AnalysisResult
from core.prompt_template import PromptLibrary
from errors.exceptions import (
    EmptyTextError,
    MissingRequiredFieldError,
    InvalidResponseFormatError
)
from logger.logger import get_logger

logger = get_logger("FeasibilityAnalyzer")


class FeasibilityAnalyzer(NarrativeAnalyzer):
    """
    Analizador que verifica si un texto narrativo es viable para análisis actancial.
    
    Valida:
    - Requisito de Género (naturaleza narrativa)
    - Eje del Deseo (Sujeto <-> Objeto de Valor)
    - Dinamismo y Proceso (transformación de estado)
    """
    
    MIN_TEXT_LENGTH = 20
    REQUIRED_FIELDS = {
        "genre_requirement",
        "desire_axis_identified",
        "dynamism_and_process_identified",
        "overall_result"
    }
    
    def get_system_prompt(self) -> str:
        """Retorna el system prompt para análisis de factibilidad."""
        force_json = PromptLibrary.get_prompt("force_json").content
        appendix = PromptLibrary.get_prompt("appendix").content
        
        feasibility_template = PromptLibrary.get_prompt("feasibility_system")
        return feasibility_template.render(
            force_json=force_json,
            appendix=appendix
        )
    
    def get_user_prompt(self, narrative_text: str) -> str:
        """Retorna el user prompt para análisis de factibilidad."""
        return (
            f"Analiza la factibilidad de un análisis actancial del siguiente texto:\n\n"
            f"---\n{narrative_text}\n---"
        )
    
    def validate_input(self, narrative_text: str) -> tuple[bool, str]:
        """
        Valida que el texto sea válido para análisis de factibilidad.
        
        Args:
            narrative_text: Texto a validar
            
        Returns:
            (is_valid, error_message)
        """
        logger.debug("Validating input", text_length=len(narrative_text) if narrative_text else 0)
        
        if not narrative_text or not narrative_text.strip():
            logger.warning("Input validation failed: empty text")
            return False, "Text cannot be empty"
        
        if len(narrative_text.strip()) < self.MIN_TEXT_LENGTH:
            logger.warning("Input validation failed: text too short", min_length=self.MIN_TEXT_LENGTH, actual_length=len(narrative_text.strip()))
            return False, f"Text is too short for analysis (minimum {self.MIN_TEXT_LENGTH} characters)"
        
        logger.debug("Input validation passed")
        return True, ""
    
    def parse_response(self, json_response: Dict[str, Any]) -> AnalysisResult:
        """
        Procesa y valida la respuesta del análisis de factibilidad.
        
        Args:
            json_response: Respuesta JSON del LLM
            
        Returns:
            AnalysisResult con los datos validados
            
        Raises:
            MissingRequiredFieldError: Si faltan campos requeridos
        """
        logger.debug("Parsing feasibility response", fields=list(json_response.keys()))
        
        # Validar que todas las claves requeridas estén presentes
        missing_fields = self.REQUIRED_FIELDS - set(json_response.keys())
        if missing_fields:
            logger.error("Missing required fields in response", missing_fields=list(missing_fields))
            return AnalysisResult(
                success=False,
                data=json_response,
                error_message=f"Missing required fields: {', '.join(missing_fields)}",
                analysis_type=self.__class__.__name__
            )
        
        errors = []
        clean_results = {}
        fields_to_check = [
            "genre_requirement", 
            "desire_axis_identified", 
            "dynamism_and_process_identified", 
            "overall_result"
        ]

        # Validación de formato
        for field in fields_to_check:
            raw_val = str(json_response.get(field, ""))
            res = raw_val.split("-")[0].strip().capitalize()
            
            if res not in {"Pass", "Fail"}:
                errors.append(f"Invalid format in '{field}': '{raw_val}'")
            else:
                clean_results[field] = res
            
        # Validación de Consistencia Lógica (Anti-alucinación)
        if not errors:
            logical_pass = all(clean_results[f] == "Pass" for f in fields_to_check if f != "overall_result")
            model_pass = clean_results["overall_result"] == "Pass"
            
            if logical_pass != model_pass:
                errors.append(f"Inconsistency: Requirements are {logical_pass} but overall_result is {model_pass}")
        
        if errors:
            full_error_message = " | ".join(errors)
            logger.error("Validation failed", errors=full_error_message)
            return AnalysisResult(
                success=False,
                data=json_response,
                error_message=f"Validation errors: {full_error_message}",
                analysis_type=self.__class__.__name__
            )

        # Si overall_result es "Pass", la factibilidad se cumple
        is_feasible = clean_results["overall_result"] == "Pass"
        
        return AnalysisResult(
            success=True,
            data=json_response,
            analysis_type=self.__class__.__name__
        )