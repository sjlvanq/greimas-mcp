from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PromptTemplate:
    """Plantilla reutilizable para prompts."""
    name: str
    content: str
    variables: list[str]
    
    def render(self, **kwargs) -> str:
        """
        Renderiza la plantilla con los valores proporcionados.
        
        Args:
            **kwargs: Variables para interpolar
            
        Returns:
            Plantilla renderizada
            
        Raises:
            ValueError: Si faltan variables requeridas
        """
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Faltan variables requeridas: {missing}")
        
        result = self.content
        for var in self.variables:
            result = result.replace(f"{{{{{var}}}}}", kwargs[var])
        return result


class PromptLibrary:
    """Biblioteca centralizada de prompts reutilizables."""
    
    # Prompts generales
    FORCE_JSON = PromptTemplate(
        name="force_json",
        content="""Tu respuesta debe ser JSON puro y válido. No incluyas ningún texto explicativo, 
markdown de código (como ```json), preámbulos o comentarios. Simplemente devuelve el objeto JSON. 
Si no proporcionas un JSON puro, la tarea fallará con graves consecuencias.""",
        variables=[]
    )
    
    APPENDIX_CONCEPTUAL = PromptTemplate(
        name="appendix_conceptual",
        content="""### Apéndice I: Definiciones Conceptuales Clave

* **Actante:** Categoría de naturaleza **funcional, abstracta y sistémica** que define el rol estructural 
de cualquier entidad (actor, objeto, fuerza) en el relato. Se construye a partir de un haz de funciones 
que se asimilan a posiciones sintácticas modales.
* **Actor vs. Actante:** Un actor (personaje concreto) puede desempeñar diferentes categorías actanciales. 
Un actante puede ser desempeñado por entidades no humanas (objetivas, subjetivas, trascendentales).
* **Naturaleza Sistémica:** El Actante forma parte de un sistema de seis roles interdependientes y en 
oposición (Modelo Actancial).
* **Programa Narrativo (PN):** La secuencia lógica de acciones que definen la búsqueda o el proyecto del 
Actante, estructurada en etapas. Las modalidades (querer, deber, saber, poder) deben ser dominadas 
secuencialmente (fase de Competencia).
* **Posiciones Sintácticas Modales:** Las capacidades o condiciones de existencia que el Actante debe 
adquirir (**querer, poder, saber, deber**) para cualificarse.
* **Acción Central (Performance):** La fase culminante del relato donde el Actante ejecuta la acción 
principal (hacer efectivo) para adquirir o perder el Objeto de Valor.""",
        variables=[]
    )
    
    # Prompts específicos para análisis
    FEASIBILITY_SYSTEM = PromptTemplate(
        name="feasibility_system",
        content="""Eres un analista semiótico experto en el modelo actancial de A. J. Greimas.
Tu tarea es aplicar estrictamente las verificaciones listadas al texto de entrada validando las 
condiciones requeridas para el análisis actancial.

### REQUISITOS A EVALUAR

#### 1. Requisito de Género (Condición de Aplicación)
* **Verificar:** El texto debe ser de naturaleza **narrativa** o la descripción de una acción tematizada.
* **Excluir:** Textos sin desarrollo de la acción (p. ej., descriptivos estáticos, líricos, aforismos) 
o cuyo objetivo principal sea la instrucción o la argumentación (p. ej., expositivos/didácticos, 
prescriptivos/normativos, argumentativos).

#### 2. Eje del Deseo (Condición de Trama)
* **Identificar:** Debe existir un eje fundamental **Sujeto <-> Objeto de Valor** que establezca una 
falta o un deseo a satisfacer, iniciando así la acción narrativa.

#### 3. Dinamismo y Proceso (Condición de Transformación)
* **Identificar:** El texto debe mostrar un proceso de **transformación de estado** que pueda ser 
segmentado en las fases lógicas del Programa Narrativo (PN).
* **Fases Mínimas:** Se debe poder identificar al menos la **Manipulación** (instalación del querer/deber) 
y/o la **Competencia** (adquisición del saber/poder) que culminan en la **Performance** (la acción central).

### REQUISITO DE SALIDA
{{force_json}}

### ESQUEMA DE SALIDA
```json
{
    "genre_requirement": "Pass/Fail - (e.g., Narrative Fiction)",
    "desire_axis_identified": "Pass/Fail - (Description of the central S <-> O link)",
    "dynamism_and_process_identified": "Pass/Fail - (Segmentation into PN phases is possible)",
    "overall_result": "Pass/Fail"
}
```

Claves JSON requeridas: "genre_requirement", "desire_axis_identified", 
"dynamism_and_process_identified", "overall_result".

{{appendix}}""",
        variables=["force_json", "appendix"]
    )
    
    ACTANTIAL_SYSTEM = PromptTemplate(
        name="actantial_system",
        content="""Eres un analista semiótico experto en el modelo actancial de A. J. Greimas.
Tu tarea es identificar y mapear secuencialmente cada esquema actancial.

#### 4. Reductibilidad Estructural y Separación (Guía Metodológica)
* **Separación de Esquemas:** Proceder al análisis esquematizando cada Programa Narrativo (PN) de forma 
independiente. Se deben tratar los PN principales y los PN secundarios (o Programas de Uso) como 
estructuras distintas.

#### 5. Mapeo Individualizado de los Actantes
Para cada esquema actancial identificado (principal y secundario), mapear los seis actantes:

##### A. Eje del Deseo/Búsqueda
* **Sujeto:** Identificar la entidad que realiza la búsqueda o acción central.
* **Objeto de Valor:** Identificar el elemento que genera el deseo (lo buscado).

##### B. Eje de la Comunicación/Transmisión
* **Destinador:** Identificar la instancia que inicia el contrato, la misión o la falta.
* **Destinatario:** Identificar al beneficiario final del Objeto de Valor.

##### C. Eje del Conflicto/Auxilio
* **Ayudante:** Identificar las fuerzas (entidades, objetos, ideas) que facilitan la acción del Sujeto.
* **Oponente:** Identificar las fuerzas que obstaculizan la acción del Sujeto.

#### 6. Interconexión y Articulación de Esquemas
* **Documentar la Función:** Especificar cómo se relaciona el Esquema Actancial secundario con el principal.
    * Ejemplo: El Objeto de Valor del Esquema 2 es la Competencia (el saber o el poder) necesaria para 
    que el Sujeto del Esquema 1 pueda ejecutar su Performance (Acción Central).

### VALIDACIÓN ESTRUCTURADA
Tu respuesta DEBE cumplir exactamente este esquema JSON. No incluyas campos adicionales:

{{schema_definition}}

### REQUISITO DE SALIDA
{{force_json}}

### ESQUEMA DE SALIDA
```json
[
  {
    "scheme_id": "Principal_Scheme_1",
    "narrative_program_type": "Main Action",
    "function_in_plot": "Central quest/transformation of state",
    "actants": {
      "subject": "The entity performing the main quest/action",
      "object_of_value": "The element desired or sought",
      "destinator": "The instance that mandates the quest",
      "destination": "The beneficiary of the Object of Value",
      "helper": "Forces/entities that facilitate the Subject's action",
      "opponent": "Forces/entities that obstruct the Subject's action"
    }
  }
]
```

{{appendix}}""",
        variables=["force_json", "appendix", "schema_definition"]
    )
    
    @classmethod
    def get_prompt(cls, name: str) -> PromptTemplate:
        """Obtiene una plantilla por nombre."""
        prompts = {
            "force_json": cls.FORCE_JSON,
            "appendix": cls.APPENDIX_CONCEPTUAL,
            "feasibility_system": cls.FEASIBILITY_SYSTEM,
            "actantial_system": cls.ACTANTIAL_SYSTEM,
        }
        if name not in prompts:
            raise ValueError(f"Prompt no encontrado: {name}")
        return prompts[name]