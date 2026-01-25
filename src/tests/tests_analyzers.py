"""
Tests unitarios para validar la refactorización.

Ejecutar con: pytest tests/test_analyzers.py -v
python -m pytest server\tests\tests_analyzers.py -vv
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from core.analyzer import NarrativeAnalyzer, AnalysisResult
from analyzers.feasibility import FeasibilityAnalyzer
from analyzers.actantial_scheme import ActantialSchemeAnalyzer
from core.prompt_template import PromptLibrary, PromptTemplate
from errors.exceptions import (
    ValidationError,
    EmptyTextError,
    MissingRequiredFieldError,
    InvalidResponseFormatError
)


class TestPromptLibrary:
    """Tests para PromptLibrary."""
    
    def test_get_existing_prompt(self):
        """Debe retornar template existente."""
        prompt = PromptLibrary.get_prompt("force_json")
        assert isinstance(prompt, PromptTemplate)
        assert prompt.name == "force_json"
    
    def test_get_nonexistent_prompt(self):
        """Debe lanzar error para prompt inexistente."""
        with pytest.raises(ValueError):
            PromptLibrary.get_prompt("nonexistent")
    
    def test_template_render_with_variables(self):
        """Debe renderizar template con variables."""
        template = PromptTemplate(
            name="test",
            content="Hello {{name}}, welcome to {{place}}",
            variables=["name", "place"]
        )
        result = template.render(name="Alice", place="Wonderland")
        assert result == "Hello Alice, welcome to Wonderland"
    
    def test_template_render_missing_variables(self):
        """Debe fallar si faltan variables."""
        template = PromptTemplate(
            name="test",
            content="Hello {{name}}",
            variables=["name", "surname"]
        )
        with pytest.raises(ValueError):
            template.render(name="Alice")
    
    def test_feasibility_system_prompt_render(self):
        """Debe renderizar feasibility system prompt correctamente."""
        template = PromptLibrary.get_prompt("feasibility_system")
        rendered = template.render(
            force_json="JSON only",
            appendix="Definitions"
        )
        assert "JSON only" in rendered
        assert "Definitions" in rendered
        assert "{{" not in rendered  # Sin variables sin interpolar


class TestFeasibilityAnalyzer:
    """Tests para FeasibilityAnalyzer."""
    
    @pytest.fixture
    def mock_claude_client(self):
        """Mock del cliente Claude."""
        mock = Mock()
        mock.add_user_message = Mock()
        mock.chat = Mock()
        mock.text_from_message = Mock()
        return mock
    
    @pytest.fixture
    def analyzer(self, mock_claude_client):
        """Instancia de FeasibilityAnalyzer con mock."""
        return FeasibilityAnalyzer(mock_claude_client)
    
    def test_validate_input_empty_text(self, analyzer):
        """Debe rechazar texto vacío."""
        is_valid, msg = analyzer.validate_input("")
        assert not is_valid
        assert "empty" in msg.lower()
    
    def test_validate_input_too_short(self, analyzer):
        """Debe rechazar texto muy corto."""
        is_valid, msg = analyzer.validate_input("abc")
        assert not is_valid
        assert "short" in msg.lower()
    
    def test_validate_input_valid_text(self, analyzer):
        """Debe aceptar texto válido."""
        is_valid, msg = analyzer.validate_input("a" * 50)
        assert is_valid
        assert msg == ""
    
    def test_parse_response_valid(self, analyzer):
        """Debe parsear respuesta válida correctamente."""
        response = {
            "genre_requirement": "Pass - Narrative Fiction",
            "desire_axis_identified": "Pass - Prince seeks treasure",
            "dynamism_and_process_identified": "Pass - Quest structure",
            "overall_result": "Pass"
        }
        result = analyzer.parse_response(response)
        assert result.success
        assert result.data == response
    
    def test_parse_response_missing_fields(self, analyzer):
        """Debe detectar campos faltantes."""
        response = {
            "genre_requirement": "Pass",
            "desire_axis_identified": "Yes"
            # Faltan campos
        }
        result = analyzer.parse_response(response)
        assert not result.success
        assert "Missing" in result.error_message
    
    def test_parse_response_invalid_genre(self, analyzer):
        """Debe rechazar valor inválido de género."""
        response = {
            "genre_requirement": "Invalid",
            "desire_axis_identified": "Yes",
            "dynamism_and_process_identified": "Yes",
            "overall_result": "Pass"
        }
        result = analyzer.parse_response(response)
        assert not result.success
        assert "Invalid" in result.error_message
    
    def test_analyze_with_mock_llm(self, analyzer, mock_claude_client):
        """Debe ejecutar análisis completo con LLM mockeado."""
        # Setup mock
        mock_response = Mock()
        mock_claude_client.text_from_message.return_value = '{"genre_requirement": "Pass", "desire_axis_identified": "Pass", "dynamism_and_process_identified": "Pass", "overall_result": "Pass"}'
        mock_claude_client.chat.return_value = mock_response
        
        # Ejecutar
        result = analyzer.analyze("Once upon a time there was a prince seeking treasure across the kingdom")
        
        # Validar
        assert result.success
        assert result.analysis_type == "FeasibilityAnalyzer"
        assert mock_claude_client.chat.called
    
    def test_analyze_invalid_input(self, analyzer):
        """Debe retornar error para input inválido."""
        result = analyzer.analyze("")
        assert not result.success
        assert "empty" in result.error_message.lower()


class TestActantialSchemeAnalyzer:
    """Tests para ActantialSchemeAnalyzer."""
    
    @pytest.fixture
    def mock_claude_client(self):
        """Mock del cliente Claude."""
        mock = Mock()
        mock.add_user_message = Mock()
        mock.chat = Mock()
        mock.text_from_message = Mock()
        return mock
    
    @pytest.fixture
    def analyzer(self, mock_claude_client):
        """Instancia de ActantialSchemeAnalyzer con mock."""
        return ActantialSchemeAnalyzer(mock_claude_client)
    
    def test_parse_response_single_scheme(self, analyzer):
        """Debe procesar un esquema actancial único."""
        response = {
            "scheme_id": "Principal_Scheme_1",
            "narrative_program_type": "Main Quest",
            "function_in_plot": "Central transformation",
            "actants": {
                "subject": "Prince",
                "object_of_value": "Hidden Treasure",
                "destinator": "Fate",
                "destination": "Prince",
                "helper": "Magical Map",
                "opponent": "Evil Sorcerer"
            }
        }
        result = analyzer.parse_response(response)
        assert result.success
        assert len(result.data["schemes"]) == 1
    
    def test_parse_response_multiple_schemes(self, analyzer):
        """Debe procesar múltiples esquemas actanciales."""
        response = [
            {
                "scheme_id": "Principal_Scheme_1",
                "narrative_program_type": "Main Quest",
                "function_in_plot": "Central transformation",
                "actants": {
                    "subject": "Prince",
                    "object_of_value": "Treasure",
                    "destinator": "Fate",
                    "destination": "Prince",
                    "helper": "Map",
                    "opponent": "Sorcerer"
                }
            },
            {
                "scheme_id": "Secondary_Scheme_2",
                "narrative_program_type": "Competence Acquisition",
                "function_in_plot": "Gaining knowledge",
                "actants": {
                    "subject": "Prince",
                    "object_of_value": "Magic Spell",
                    "destinator": "Mentor",
                    "destination": "Prince",
                    "helper": "Ancient Book",
                    "opponent": "Time"
                }
            }
        ]
        result = analyzer.parse_response(response)
        assert result.success
        assert len(result.data["schemes"]) == 2
    
    def test_parse_response_missing_scheme_fields(self, analyzer):
        """Debe detectar campos faltantes en esquema."""
        response = {
            "scheme_id": "Test",
            # Faltan campos
            "actants": {}
        }
        result = analyzer.parse_response(response)
        assert not result.success
        assert "missing fields" in result.error_message.lower()
    
    def test_parse_response_missing_actant_fields(self, analyzer):
        """Debe detectar campos faltantes en actantes."""
        response = {
            "scheme_id": "Test",
            "narrative_program_type": "Quest",
            "function_in_plot": "Main action",
            "actants": {
                "subject": "Hero",
                # Faltan otros actantes
            }
        }
        result = analyzer.parse_response(response)
        assert not result.success
        assert "missing actant fields" in result.error_message.lower()
    
    def test_parse_response_invalid_actants_type(self, analyzer):
        """Debe rechazar actantes que no sean dict."""
        response = {
            "scheme_id": "Test",
            "narrative_program_type": "Quest",
            "function_in_plot": "Main action",
            "actants": "invalid"  # Debe ser dict
        }
        result = analyzer.parse_response(response)
        assert not result.success
    
    def test_validate_input_empty_text(self, analyzer):
        """Debe rechazar texto vacío."""
        is_valid, msg = analyzer.validate_input("")
        assert not is_valid
    
    def test_validate_input_valid_text(self, analyzer):
        """Debe aceptar texto válido."""
        is_valid, msg = analyzer.validate_input("a" * 50)
        assert is_valid


class TestAnalysisResult:
    """Tests para AnalysisResult."""
    
    def test_successful_result(self):
        """Debe crear resultado exitoso."""
        data = {"key": "value"}
        result = AnalysisResult(success=True, data=data, analysis_type="TestAnalyzer")
        assert result.success
        assert result.data == data
        assert result.error_message == ""
    
    def test_failed_result(self):
        """Debe crear resultado fallido."""
        result = AnalysisResult(
            success=False,
            data={},
            error_message="Test error",
            analysis_type="TestAnalyzer"
        )
        assert not result.success
        assert result.error_message == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])