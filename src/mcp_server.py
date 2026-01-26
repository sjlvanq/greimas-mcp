import json
import os
from typing import Dict, Any
from core.claude import Claude
from anthropic.types import Message
from dotenv import load_dotenv
from logger.logger import get_logger, set_log_level

load_dotenv()

# Configuración de sistema de logs antes de importar los analizadores
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
set_log_level(LOG_LEVEL)

from analyzers.feasibility import FeasibilityAnalyzer
from analyzers.actantial_scheme import ActantialSchemeAnalyzer
from core.analyzer import AnalysisResult

logger = get_logger("MCPServer")

# Anthropic Config
claude_analist_model = os.getenv("CLAUDE_ANALIST_MODEL", "")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

# Inicializar servidor MCP
try:
    # Intentamos importar la implementación real si está disponible en el entorno
    from mcp.server.fastmcp import FastMCP  # type: ignore
except ModuleNotFoundError:
    FastMCP = None


class _LazyMCP:
    """Proxy perezoso para crear FastMCP solo cuando se use.

    Si el paquete externo no está instalado o el entorno virtual no está activo,
    se lanza un ModuleNotFoundError con mensaje explicativo al intentar usarlo.
    """
    def __init__(self, name: str, log_level: str | None = None):
        self._name = name
        self._log_level = log_level
        self._instance = None

    def _ensure_instance(self):
        if self._instance is not None:
            return
        try:
            if FastMCP is None:
                # Reintentar importar para obtener un mensaje más reciente del entorno
                from mcp.server.fastmcp import FastMCP as _RealFastMCP  # type: ignore
            else:
                _RealFastMCP = FastMCP
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "Unable to import 'mcp.server.fastmcp'. Ensure the runtime environment has the required package 'mcp' installed "
                "and that your virtualenv is active (use `uv run --active main.py` or activate the venv before running)."
            ) from e

        self._instance = _RealFastMCP(self._name, log_level=self._log_level)

    def __getattr__(self, item):
        self._ensure_instance()
        return getattr(self._instance, item)


# Create a lazy mcp proxy instance so decorators referencing `mcp` at import time don't fail
# immediately if the external package is missing. The real ModuleNotFoundError will be
# raised with a helpful message when the proxy is first used.
mcp = _LazyMCP("DocumentMCP", log_level=os.getenv("LOG_LEVEL", "ERROR"))

# Tipos de retorno
FeasibilityOutput = Dict[str, str]
ActantialSchemesOutput = Dict[str, Any]

# Inicializar cliente Claude
claude_client = Claude(model=claude_analist_model)

# Inicializar analizadores
feasibility_analyzer = FeasibilityAnalyzer(claude_client)
actantial_analyzer = ActantialSchemeAnalyzer(claude_client)


def _analysis_result_to_dict(result: AnalysisResult) -> Dict[str, Any]:
    """
    Convierte un AnalysisResult a diccionario para retornar a MCP.
    
    Args:
        result: AnalysisResult a convertir
        
    Returns:
        Diccionario con los datos del resultado
    """
    if result.success:
        logger.debug("Analysis successful", analysis_type=result.analysis_type)
        return result.data
    else:
        logger.error("Analysis failed", analysis_type=result.analysis_type, error=result.error_message)
        return {
            "overall_result": "Fail",
            "analysis_notes": result.error_message
        }

def load_actantial_schema() -> Dict[str, Any]:
    """Carga el esquema JSON de validación para estructuras actanciales."""
    schema_path = os.path.join(
        os.path.dirname(__file__),
        "resources/actantial_schema.json"
    )
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        logger.debug("Actantial schema loaded successfully", path=schema_path)
        return schema
    except FileNotFoundError:
        logger.error("Actantial schema file not found", path=schema_path)
        raise
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in actantial schema", error=str(e))
        raise

@mcp.resource("schema://actantial-model")
def get_actantial_schema() -> str:
    """
    Expone el esquema JSON de validación para estructuras actanciales
    como recurso MCP.
    """
    schema = load_actantial_schema()
    return json.dumps(schema, indent=2)

@mcp.tool(
    name="CheckNarrativeFeasibility",
    description="Verifies if the provided text meets the necessary conditions for a successful "
                "Greimasian Actantial Analysis. Checks narrative genre, desire axis, and narrative "
                "dynamism."
)
def check_narrative_feasibility(narrative_text: str) -> FeasibilityOutput:
    """
    Verifica la factibilidad de realizar un análisis actancial en un texto.
    
    Args:
        narrative_text: Texto narrativo a analizar
        
    Returns:
        FeasibilityOutput con los resultados de la validación
    """
    logger.info("Starting feasibility check", text_length=len(narrative_text))
    result = feasibility_analyzer.analyze(narrative_text)
    return _analysis_result_to_dict(result)


@mcp.tool(
    name="ExtractActantScheme",
    description="Extracts the Greimasian Actantial Scheme from the provided narrative text. "
                "Maps the six actants (Subject, Object of Value, Sender, Receiver, Helper, Opponent) "
                "and identifies narrative programs and their interconnections."
)
def extract_actant_scheme(narrative_text: str) -> ActantialSchemesOutput:
    """
    Extrae el esquema actancial de un texto narrativo.
    
    Args:
        narrative_text: Texto narrativo a analizar
        
    Returns:
        ActantialSchemesOutput con los esquemas actanciales identificados
    """
    logger.info("Starting actantial scheme extraction", text_length=len(narrative_text))
    result = actantial_analyzer.analyze(narrative_text)
    return _analysis_result_to_dict(result)


if __name__ == "__main__":
    mcp.run(transport="stdio")
