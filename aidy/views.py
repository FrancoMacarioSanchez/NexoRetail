import json
import logging
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import AidyConversation, AidyMessage
from .services.ai import interpretar
from .services.actions import execute_action
from .services.file_processing import process_document


logger = logging.getLogger(__name__)


# =========================================================
# CHAT
# =========================================================

@login_required
@require_POST
def chat(request):

    try:
        body = json.loads(request.body)

        message = body.get("message", "").strip()

        if not message:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "No recibí ningún mensaje.",
                },
                status=400,
            )

        conversation_id = body.get("conversation_id")

        # =================================================
        # CONVERSACIÓN
        # =================================================

        if conversation_id:

            conversation = AidyConversation.objects.get(
                id=conversation_id,
                usuario=request.user,
                activa=True,
            )

        else:

            conversation = AidyConversation.objects.create(
                usuario=request.user,
                titulo=message[:100],
            )

        # =================================================
        # MENSAJE DEL USUARIO
        # =================================================

        AidyMessage.objects.create(
            conversation=conversation,
            role="user",
            content=message,
        )

        # =================================================
        # CONTEXTO
        # =================================================

        previous_messages = (
            conversation.messages
            .order_by("-created_at")[:10]
        )

        contexto = "\n".join(
            f"{m.role}: {m.content}"
            for m in reversed(previous_messages)
        )

        logger.info(
            "AIDY mensaje: %s",
            message,
        )

        # =================================================
        # INTERPRETAR CON GEMINI
        # =================================================

        intent = interpretar(
            message,
            contexto,
        )

        logger.info(
            "AIDY intent: %s",
            intent.model_dump(),
        )

        # =================================================
        # PARAMETROS
        # =================================================

        if hasattr(
            intent.action,
            "parameters_dict",
        ):
            parameters = (
                intent.action.parameters_dict()
            )

        else:
            parameters = {}

        # =================================================
        # EJECUTAR ACCIÓN
        # =================================================

        result = execute_action(
            request,
            intent.action,
            products=intent.products,
        )

        logger.info(
            "AIDY resultado: %s",
            result,
        )

        response_message = result.get(
            "message",
            intent.message,
        )

        # =================================================
        # DATOS JSON-SAFE
        # =================================================

        action_data = {
            "type": intent.action.type,
            "parameters": parameters,
        }

        response_data = result.get(
            "data"
        )

        # =================================================
        # GUARDAR RESPUESTA
        # =================================================

        AidyMessage.objects.create(
            conversation=conversation,
            role="assistant",
            content=response_message,
            metadata={
                "action": intent.action.type,
                "parameters": parameters,
                "data": response_data,
            },
        )

        # =================================================
        # RESPUESTA
        # =================================================

        return JsonResponse(
            {
                "ok": True,
                "conversation_id": conversation.id,
                "message": response_message,
                "action": action_data,
                "data": response_data,
            }
        )

    except AidyConversation.DoesNotExist:

        action_response = result.get("action")

        if not action_response:
            action_response = {
                "type": intent.action.type,
                "parameters": (
                    intent.action.model_dump(mode="json")
                    .get("parameters", [])
                ),
            }

        return JsonResponse({
            "ok": True,
            "conversation_id": conversation.id,
            "message": response_message,
            "action": action_response,
            "data": result.get("data"),
        })

    except Exception as exc:

        logger.exception(
            "ERROR REAL DE AIDY"
        )

        return JsonResponse(
            {
                "ok": False,
                "message": (
                    f"Error de Aidy: "
                    f"{type(exc).__name__}: {str(exc)}"
                ),
            },
            status=500,
        )


# =========================================================
# PROCESAR ARCHIVO
# =========================================================

@login_required
@require_POST
def process_file(request):

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:

        return JsonResponse(
            {
                "ok": False,
                "message": (
                    "No se recibió ningún archivo."
                ),
            },
            status=400,
        )

    # =====================================================
    # FORMATOS PERMITIDOS
    # =====================================================

    allowed_extensions = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".csv",
        ".xlsx",
    }

    extension = os.path.splitext(
        uploaded_file.name
    )[1].lower()

    if extension not in allowed_extensions:

        return JsonResponse(
            {
                "ok": False,
                "message": (
                    "Tipo de archivo no permitido."
                ),
            },
            status=400,
        )

    try:

        logger.info(
            "AIDY procesando archivo: %s",
            uploaded_file.name,
        )

        # =================================================
        # PROCESAMIENTO
        # =================================================

        extraction = process_document(
            uploaded_file
        )

        logger.info(
            "AIDY extracción: %s",
            extraction.model_dump(),
        )

        document_data = extraction.model_dump()

        # =================================================
        # FACTURA EXTERNA
        # =================================================

        if extraction.tipo == "factura_externa":

            products = [
                producto.model_dump()
                for producto in extraction.productos
            ]

            message = (
                "Reconocí una factura externa"
            )

            if extraction.proveedor:

                message += (
                    f" de {extraction.proveedor}"
                )

            message += (
                f". Encontré {len(products)} producto(s). "
                "¿Querés cargarlos al stock?"
            )

            action = {
                "type": "preparar_ingreso_stock",
                "parameters": {
                    "productos": products,
                    "proveedor": extraction.proveedor,
                    "numero": extraction.numero,
                    "fecha": extraction.fecha,
                    "moneda": extraction.moneda,
                    "subtotal": extraction.subtotal,
                    "impuestos": extraction.impuestos,
                    "total": extraction.total,
                },
            }

        # =================================================
        # PRESUPUESTO INTERNO
        # =================================================

        elif extraction.tipo == "presupuesto_interno":

            products = [
                producto.model_dump()
                for producto in extraction.productos
            ]

            message = (
                "Reconocí un presupuesto"
            )

            if extraction.proveedor:

                message += (
                    f" para {extraction.proveedor}"
                )

            message += (
                f". Encontré {len(products)} producto(s)."
            )

            action = {
                "type": "crear_presupuesto",
                "parameters": {
                    "productos": products,
                    "numero": extraction.numero,
                    "fecha": extraction.fecha,
                    "moneda": extraction.moneda,
                    "subtotal": extraction.subtotal,
                    "impuestos": extraction.impuestos,
                    "total": extraction.total,
                },
            }

        # =================================================
        # OTRO
        # =================================================

        else:

            message = (
                "Pude leer el archivo, pero no pude "
                "identificarlo como una factura externa "
                "o un presupuesto interno."
            )

            action = {
                "type": "none",
                "parameters": {},
            }

        # =================================================
        # RESPUESTA
        # =================================================

        return JsonResponse(
            {
                "ok": True,
                "filename": uploaded_file.name,
                "message": message,
                "document": document_data,
                "action": action,
            }
        )

    except Exception as exc:

        logger.exception(
            "ERROR PROCESANDO ARCHIVO CON AIDY"
        )

        return JsonResponse(
            {
                "ok": False,
                "message": (
                    f"Error procesando archivo: "
                    f"{type(exc).__name__}: {str(exc)}"
                ),
            },
            status=500,
        )