from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group

class Empleado(models.Model):
    ROL_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('VENDEDOR', 'Vendedor'),
        ('LOGISTICA', 'Logística y Depósito'),
        ('CAJA', 'Cajero / Facturación'),
    ]

    # Vinculamos este perfil al modelo de Usuario de Django (que maneja email y contraseña)
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='empleado_perfil')
    
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='VENDEDOR')
    legajo = models.CharField(max_length=20, blank=True, null=True, help_text="Número de legajo interno")
    telefono = models.CharField(max_length=50, blank=True, null=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True, help_text="Desmarcar si el empleado es desvinculado")

    def __str__(self):
        nombre_completo = self.usuario.get_full_name()
        return f"{nombre_completo or self.usuario.username} - {self.get_rol_display()}"

    def save(self, *args, **kwargs):
        # 1. Guardamos el empleado en la base de datos
        super().save(*args, **kwargs)
        
        # 2. Automatización de Permisos: 
        # Buscamos o creamos un Grupo de Django con el nombre del Rol (ej: "Vendedor")
        grupo, created = Group.objects.get_or_create(name=self.get_rol_display())
        
        # 3. Asignamos al usuario a ese grupo
        self.usuario.groups.clear() # Limpiamos grupos anteriores por si cambió de puesto
        self.usuario.groups.add(grupo)