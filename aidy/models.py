# aidy/models.py

from django.conf import settings
from django.db import models


class AidyConversation(models.Model):

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="aidy_conversations",
    )

    titulo = models.CharField(
        max_length=200,
        blank=True,
    )

    creada_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizada_en = models.DateTimeField(
        auto_now=True,
    )

    activa = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["-actualizada_en"]

    def __str__(self):
        return self.titulo or f"Conversación #{self.id}"


class AidyMessage(models.Model):

    ROLE_CHOICES = [
        ("user", "Usuario"),
        ("assistant", "Aidy"),
        ("system", "Sistema"),
    ]

    conversation = models.ForeignKey(
        AidyConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    content = models.TextField()

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
      
# aidy/models.py

class AidySupportTicket(models.Model):

    ESTADOS = [
        ("abierto", "Abierto"),
        ("en_proceso", "En proceso"),
        ("resuelto", "Resuelto"),
        ("cerrado", "Cerrado"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    asunto = models.CharField(
        max_length=200
    )

    descripcion = models.TextField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="abierto",
    )

    creado_en = models.DateTimeField(
        auto_now_add=True
    )