from typing import Literal

from django.conf import settings
from google import genai
from pydantic import BaseModel, Field


# =========================================================
# PRODUCTO
# =========================================================

class AidyProduct(BaseModel):
    nombre: str
    cantidad: float = 1


# =========================================================
# PARAMETRO
# =========================================================

class AidyParameter(BaseModel):
    clave: str
    valor: str = ""


# =========================================================
# ACCION
# =========================================================

class AidyAction(BaseModel):

    type: Literal[
        "buscar_producto",
        "ver_producto",
        "consultar_stock",
        "consultar_precio",
        "crear_presupuesto",
        "abrir_presupuesto",
        "buscar_venta",
        "abrir_venta",
        "procesar_archivo",
        "preparar_ingreso_stock",
        "crear_ticket_soporte",
        "navegar",
        "none",
    ]

    parameters: list[AidyParameter] = Field(
        default_factory=list
    )

    def parameters_dict(self):
        return {
            parameter.clave: parameter.valor
            for parameter in self.parameters
        }


# =========================================================
# INTENT
# =========================================================

class AidyIntent(BaseModel):

    message: str

    action: AidyAction

    products: list[AidyProduct] = Field(
        default_factory=list
    )


# =========================================================
# CLIENTE
# =========================================================

def get_client():

    api_key = getattr(
        settings,
        "GEMINI_API_KEY",
        None,
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY no está configurada."
        )

    return genai.Client(
        api_key=api_key
    )


# =========================================================
# PROMPT
# =========================================================

SYSTEM_PROMPT = """
Sos Aidy, el asistente inteligente de NexoRetail.

NexoRetail es un sistema de gestión comercial.

Podés ayudar con:

- productos
- stock
- precios
- presupuestos
- ventas
- clientes
- archivos
- soporte

Nunca inventes información.

Cuando necesites consultar información
del sistema, generá una acción.

Nunca ejecutes acciones directamente.

ACCIONES DISPONIBLES:

buscar_producto
ver_producto
consultar_stock
consultar_precio
crear_presupuesto
abrir_presupuesto
buscar_venta
abrir_venta
procesar_archivo
preparar_ingreso_stock
crear_ticket_soporte
navegar
none


PARAMETROS:

Los parámetros son una lista.

Cada elemento tiene:

clave
valor

Ejemplo:

Usuario:
"Buscá Coca Cola"

Acción:

type:
buscar_producto

parameters:

clave:
producto

valor:
Coca Cola


Otro ejemplo:

Usuario:
"¿Cuánto stock tengo de Coca Cola?"

Acción:

type:
consultar_stock

parameters:

clave:
producto

valor:
Coca Cola


Si una acción no necesita parámetros:

parameters:
[]


Si el usuario solamente conversa:

type:
none


Nunca inventes datos de productos,
stock, precios, ventas o clientes.

La respuesta debe ser breve y amigable.
"""


# =========================================================
# INTERPRETAR
# =========================================================

def interpretar(
    mensaje: str,
    contexto: str = "",
) -> AidyIntent:

    prompt = f"""
{SYSTEM_PROMPT}

========================================
CONTEXTO
========================================

{contexto}

========================================
MENSAJE
========================================

{mensaje}

========================================
TAREA
========================================

Interpretá el mensaje del usuario.
Devolvé exclusivamente el JSON solicitado.
"""

    client = get_client()

    # Gemini 3.8 Flash
    model = getattr(
        settings,
        "AIDY_GEMINI_MODEL",
        "gemini-3.8-flash",
    )

    # =====================================================
    # INTERACTIONS API
    # =====================================================

    interaction = client.interactions.create(
        model=model,
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": AidyIntent.model_json_schema(),
        },
    )

    # =====================================================
    # RESPUESTA
    # =====================================================

    output = interaction.output_text

    if not output:
        raise ValueError(
            "Gemini no devolvió contenido."
        )

    try:

        return AidyIntent.model_validate_json(
            output
        )

    except Exception as exc:

        raise ValueError(
            f"Gemini devolvió un JSON inválido: {output}"
        ) from exc