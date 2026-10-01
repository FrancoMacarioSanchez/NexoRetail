# aidy/services/ai.py

from google import genai
from django.conf import settings
from pydantic import BaseModel, Field
from typing import Literal


class AidyProduct(BaseModel):
    nombre: str
    cantidad: float = 1


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

    parameters: dict = Field(
        default_factory=dict
    )


class AidyIntent(BaseModel):

    message: str

    action: AidyAction

    products: list[AidyProduct] = Field(
        default_factory=list
    )


client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


SYSTEM_PROMPT = """
Sos Aidy, el asistente inteligente de NexoRetail.

NexoRetail es un sistema de gestión comercial.

Podés ayudar al usuario con:

- productos
- stock
- precios
- presupuestos
- ventas
- clientes
- archivos
- soporte

Nunca inventes información.

Cuando necesites consultar información de NexoRetail,
generá una acción.

Nunca ejecutes acciones directamente.

Las acciones permitidas son:

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

Si el usuario solamente conversa,
utilizá "none".

La respuesta debe ser amigable y breve.
"""


def interpretar(mensaje: str, contexto: str = "") -> AidyIntent:

    prompt = f"""
{SYSTEM_PROMPT}

Contexto de conversación:

{contexto}

Mensaje del usuario:

{mensaje}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": AidyIntent,
        },
    )

    if response.parsed:
        return response.parsed

    return AidyIntent.model_validate_json(
        response.text
    )