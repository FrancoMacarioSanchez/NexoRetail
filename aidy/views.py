# aidy/views.py

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import AidyConversation, AidyMessage
from .services.ai import interpretar
from .services.actions import execute_action


@login_required
@require_POST
def chat(request):

    try:
        body = json.loads(
            request.body
        )

        message = body.get(
            "message",
            ""
        ).strip()

        if not message:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "No recibí ningún mensaje."
                },
                status=400
            )

        conversation_id = body.get(
            "conversation_id"
        )

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

        AidyMessage.objects.create(
            conversation=conversation,
            role="user",
            content=message,
        )

        previous_messages = (
            conversation.messages
            .order_by("-created_at")[:10]
        )

        contexto = "\n".join(
            f"{m.role}: {m.content}"
            for m in reversed(previous_messages)
        )

        intent = interpretar(
            message,
            contexto
        )

        result = execute_action(
            request,
            intent.action
        )

        response_message = result.get(
            "message",
            intent.message
        )

        AidyMessage.objects.create(
            conversation=conversation,
            role="assistant",
            content=response_message,
            metadata={
                "action": intent.action.type,
                "data": result.get("data"),
            },
        )

        return JsonResponse({
            "ok": True,
            "conversation_id": conversation.id,
            "message": response_message,
            "action": {
                "type": intent.action.type,
                "parameters": intent.action.parameters,
            },
            "data": result.get("data"),
        })

    except Exception as e:

        return JsonResponse(
            {
                "ok": False,
                "message": (
                    "Tuve un problema procesando "
                    "la solicitud."
                ),
                "error": str(e),
            },
            status=500
        )