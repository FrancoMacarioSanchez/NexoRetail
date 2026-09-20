from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    # TenantMixin ya incluye el campo 'schema_name' de forma nativa
    CONDICION_FISCAL_CHOICES = [
            ('RI', 'Responsable Inscripto'),
            ('MT', 'Monotributista'),
            ('EX', 'Exento'),
            ('CF', 'Consumidor Final'),
        ]
    
    # 1. Datos del Corralón / Mayorista (Tu cliente del SaaS)
    nombre = models.CharField(max_length=100, help_text="Nombre de fantasía o Razón Social")
    cuit = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.CharField(blank=True, null=True, default="generic")
    condicion_fiscal = models.CharField(max_length=2, choices=CONDICION_FISCAL_CHOICES, default='CF')
    punto_venta = models.CharField(max_length=3, blank=True, null=True)

    
    # 2. Control de Suscripción del SaaS
    activo = models.BooleanField(default=True, help_text="Si es False, se le bloquea el acceso al sistema")
    creado_el = models.DateField(auto_now_add=True)
    pagado_hasta = models.DateField(null=True, blank=True, help_text="Fecha de vencimiento de la suscripción")

    # 3. Configuraciones automáticas de django-tenants
    auto_create_schema = True # Crea el esquema en PostgreSQL automáticamente al guardar
    auto_drop_schema = False  # Recomendado en False para no borrar datos accidentalmente si eliminás el cliente

    def __str__(self):
        return self.nombre


class Domain(DomainMixin):
    # DomainMixin ya incluye los campos:
    # - domain (ej: corralonjuan.tusaas.com)
    # - tenant (ForeignKey a Client)
    # - is_primary (BooleanField)
    
    pass