from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass
from logger.logger import get_logger

logger = get_logger("NarrativeAnalyzer")


@dataclass
class AnalysisResult:
    """Representa el resultado de un análisis."""
    success: bool
    data: Dict[str, Any]
    error_message: str = ""
    analysis_type: str = ""


class NarrativeAnalyzer(ABC):
    """Clase base abstracta para todos los analizadores narrativos."""
    
    def __init__(self, claude_client, temperature: float = 0.1):
        """
        Args:
            claude_client: Instancia de Claude para hacer llamadas LLM
            temperature: Temperatura para el modelo LLM
        """
        self.claude_client = claude_client
        self.temperature = temperature
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Retorna el system prompt específico del analizador."""
        pass
    
    @abstractmethod
    def get_user_prompt(self, narrative_text: str) -> str:
        """Retorna el user prompt específico del analizador."""
        pass
    
    @abstractmethod
    def validate_input(self, narrative_text: str) -> tuple[bool, str]:
        """
        Valida el input antes del análisis.
        
        Returns:
            (is_valid, error_message)
        """
        pass

    def _filter_response(self, raw_response: str) -> str:
        """
        Filtra la respuesta del LLM para asegurar JSON puro.
        
        Busca bloques de código delimitados por triple backticks (```json o ```).
        Si no se encuentra un bloque de código, se asume que la respuesta completa 
        debería ser el JSON.

        Args:
            response: Respuesta del LLM como texto.

        Returns:
            str: Una cadena de texto que contiene únicamente el JSON detectado, 
                 limpia de comentarios o texto adicional.
        """
        import re
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_response)
        content = match.group(1).strip() if match else raw_response.strip()
        return content
    
    @abstractmethod
    def parse_response(self, json_response: Dict[str, Any]) -> AnalysisResult:
        """
        Procesa y valida la respuesta del LLM.
        
        Args:
            json_response: Respuesta parseada del LLM
            
        Returns:
            AnalysisResult con los datos procesados
        """
        pass
    
    def analyze(self, narrative_text: str) -> AnalysisResult:
        """
        Ejecuta el análisis completo de un texto narrativo.
        
        Args:
            narrative_text: Texto a analizar
            
        Returns:
            AnalysisResult con los resultados o error
        """
        logger.debug(f"Starting {self.__class__.__name__}", text_length=len(narrative_text))
        
        # Validar input
        is_valid, error_msg = self.validate_input(narrative_text)
        if not is_valid:
            logger.warning(f"{self.__class__.__name__} validation failed", error=error_msg)
            return AnalysisResult(
                success=False,
                data={},
                error_message=error_msg,
                analysis_type=self.__class__.__name__
            )
        
        try:
            logger.debug(f"Calling LLM for {self.__class__.__name__}")
            
            # Llamar al LLM
            messages = []
            self.claude_client.add_user_message(messages, self.get_user_prompt(narrative_text))

            response = self.claude_client.chat(
                messages=messages,
                system=self.get_system_prompt(),
                temperature=self.temperature,
            )
            
            logger.debug(f"Received LLM response for {self.__class__.__name__}")

            # Parsear respuesta
            text_response = self.claude_client.text_from_message(response)
            logger.debug(f"Received response (raw)", text_response=text_response)

            json_string = self._filter_response(text_response)
            logger.debug(f"Filtered response (JSON string)", json_string=json_string)

            import json
            try:
                json_response = json.loads(json_string)
            except json.JSONDecodeError as e:
                raise ValueError(f"Extracted content is not valid JSON: {json_string[:100]}...") from e
            
            # Procesar y validar
            return self.parse_response(json_response)
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} analysis failed", error_type=type(e).__name__, error_msg=str(e), exc_info=True)
            return AnalysisResult(
                success=False,
                data={},
                error_message=f"{type(e).__name__}: {str(e)}",
                analysis_type=self.__class__.__name__
            )