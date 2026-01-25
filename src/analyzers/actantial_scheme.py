from typing import Dict, Any, List
from core.analyzer import NarrativeAnalyzer, AnalysisResult
from core.prompt_template import PromptLibrary
from errors.exceptions import MissingRequiredFieldError
from logger.logger import get_logger

logger = get_logger("ActantialSchemeAnalyzer")


class ActantialSchemeAnalyzer(NarrativeAnalyzer):
    """
    Analizador que extrae esquemas actanciales de textos narrativos.
    
    Mapea los seis actantes según el modelo de A. J. Greimas:
    - Sujeto
    - Objeto de Valor
    - Destinador
    - Destinatario
    - Ayudante
    - Oponente
    """
    
    MIN_TEXT_LENGTH = 20
    REQUIRED_SCHEME_FIELDS = {
        "scheme_id",
        "narrative_program_type",
        "function_in_plot",
        "actants"
    }
    REQUIRED_ACTANT_FIELDS = {
        "subject",
        "object_of_value",
        "destinator",
        "destination",
        "helper",
        "opponent"
    }
    
    def get_system_prompt(self) -> str:
        """Retorna el system prompt para extracción de esquemas actanciales."""
        force_json = PromptLibrary.get_prompt("force_json").content
        appendix = PromptLibrary.get_prompt("appendix").content
        
        actantial_template = PromptLibrary.get_prompt("actantial_system")
        return actantial_template.render(
            force_json=force_json,
            appendix=appendix
        )
    
    def get_user_prompt(self, narrative_text: str) -> str:
        """Retorna el user prompt para extracción de esquemas actanciales."""
        return (
            f"Obtén el esquema actancial del siguiente texto:\n\n"
            f"---\n{narrative_text}\n---"
        )
    
    def validate_input(self, narrative_text: str) -> tuple[bool, str]:
        """
        Valida que el texto sea válido para análisis actancial.
        
        Args:
            narrative_text: Texto a validar
            
        Returns:
            (is_valid, error_message)
        """
        logger.debug("Validating input for actantial analysis", text_length=len(narrative_text) if narrative_text else 0)
        
        if not narrative_text or not narrative_text.strip():
            logger.warning("Input validation failed: empty text")
            return False, "Text cannot be empty"
        
        if len(narrative_text.strip()) < self.MIN_TEXT_LENGTH:
            logger.warning("Input validation failed: text too short", min_length=self.MIN_TEXT_LENGTH)
            return False, f"Text is too short for analysis (minimum {self.MIN_TEXT_LENGTH} characters)"
        
        logger.debug("Input validation passed")
        return True, ""
    
    def parse_response(self, json_response: Dict[str, Any] | List[Any]) -> AnalysisResult:
        """
        Procesa y valida la respuesta del análisis de esquemas actanciales.
        
        Args:
            json_response: Respuesta JSON del LLM (puede ser lista o dict)
            
        Returns:
            AnalysisResult con los esquemas validados
        """
        logger.debug("Parsing actantial scheme response", response_type=type(json_response).__name__)
        
        # Normalizar a lista si es un dict único
        schemes = json_response if isinstance(json_response, list) else [json_response]
        logger.debug(f"Processing {len(schemes)} scheme(s)")
        
        # Validar cada esquema
        validated_schemes = []
        errors = []
        
        for idx, scheme in enumerate(schemes):
            if not isinstance(scheme, dict):
                error_msg = f"Scheme {idx} is not a valid object"
                logger.error(error_msg, scheme_type=type(scheme).__name__)
                errors.append(error_msg)
                continue
            
            # Validar campos requeridos del esquema
            missing_scheme_fields = self.REQUIRED_SCHEME_FIELDS - set(scheme.keys())
            if missing_scheme_fields:
                error_msg = (
                    f"Scheme {idx} ({scheme.get('scheme_id', 'Unknown')}) "
                    f"missing fields: {', '.join(missing_scheme_fields)}"
                )
                logger.error(error_msg, scheme_id=scheme.get('scheme_id', 'Unknown'))
                errors.append(error_msg)
                continue
            
            # Validar estructura de actantes
            actants = scheme.get("actants", {})
            if not isinstance(actants, dict):
                error_msg = f"Scheme {idx} actants is not a valid object"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
            
            missing_actant_fields = self.REQUIRED_ACTANT_FIELDS - set(actants.keys())
            if missing_actant_fields:
                error_msg = (
                    f"Scheme {idx} ({scheme['scheme_id']}) "
                    f"missing actant fields: {', '.join(missing_actant_fields)}"
                )
                logger.error(error_msg, scheme_id=scheme['scheme_id'])
                errors.append(error_msg)
                continue
            
            logger.debug(f"Scheme {idx} ({scheme['scheme_id']}) validated successfully")
            validated_schemes.append(scheme)
        
        # Si hay errores pero al menos un esquema válido, retornar con advertencia
        if errors and not validated_schemes:
            logger.error("No valid schemes found", error_count=len(errors))
            return AnalysisResult(
                success=False,
                data={"schemes": []},
                error_message=f"No valid schemes found. Errors: {'; '.join(errors)}",
                analysis_type=self.__class__.__name__
            )
        
        if errors:
            # Retornar los esquemas válidos con warning
            logger.warning(f"Partial validation: {len(validated_schemes)} valid scheme(s), {len(errors)} error(s)", valid_count=len(validated_schemes), error_count=len(errors))
            return AnalysisResult(
                success=True,
                data={"schemes": validated_schemes, "warnings": errors},
                analysis_type=self.__class__.__name__
            )
        
        logger.info(f"Actantial analysis completed successfully", scheme_count=len(validated_schemes))
        return AnalysisResult(
            success=True,
            data={"schemes": validated_schemes},
            analysis_type=self.__class__.__name__
        )