from django.db import models
from django.conf import settings
from productos.models import Producto

class Cliente(models.Model):
    CONDICION_FISCAL_CHOICES = [
        ('RI', 'Responsable Inscripto'),
        ('MT', 'Monotributista'),
        ('EX', 'Exento'),
        ('CF', 'Consumidor Final'),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    condicion_fiscal = models.CharField(max_length=2, choices=CONDICION_FISCAL_CHOICES, default='CF')
    cuit = models.CharField(max_length=12, blank=False, null=False)
    direcciones = models.TextField(blank=True, null=True, help_text="Soporta múltiples direcciones de obra o entrega")
    mail = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        if self.apellido:
            return f"{self.nombre} {self.apellido}"
        return self.nombre


class Presupuesto(models.Model):
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    
    presupuestante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='presupuestos')

    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ganancia_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # NUEVO: Campo JSON para guardar el diccionario de IVAs
    iva_total_discriminado = models.JSONField(default=dict)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Presupuesto #{self.id} - {self.cliente.nombre}"


class DetallePresupuesto(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='detalles')
    # Usamos RESTRICT para evitar que alguien borre un producto si está en un presupuesto
    producto = models.ForeignKey(Producto, on_delete=models.RESTRICT)
    
    # Usamos Decimal porque podés presupuestar 1.5 metros de arena o 2.5 kg de clavos
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Campo extra sugerido: Guardar el precio histórico. 
    # Si el producto cambia de precio mañana, el presupuesto debe mantener el precio original.
    precio_unitario_historico = models.DecimalField(max_digits=12, decimal_places=2, help_text="Precio al momento de presupuestar")

    @property
    def subtotal(self):
        # Multiplica la cantidad por el precio que se congeló en su momento
        return self.cantidad * self.precio_unitario_historico
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    


class Venta(models.Model):
    TIPO_FACTURA_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
        ('C', 'Factura C'),
        ('X', 'Remito / Comprobante Interno'),
    ]

    MEDIO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('TARJETA_CREDITO', 'Tarjeta de Crédito'),
        ('TARJETA_DEBITO', 'Tarjeta de Débito'),
        ('CHEQUE', 'Cheque'),
        ('CTA_CTE', 'Cuenta Corriente'),
    ]

    ESTADO_PAGO_CHOICES = [
        ('SALDADA', 'Saldada'),
        ('IMPAGA', 'Impaga / Pendiente'),
    ]

    # Relación con Presupuesto (permite nulos por si es venta directa por mostrador)
    presupuesto = models.OneToOneField('Presupuesto', on_delete=models.RESTRICT, related_name='venta_asociada', null=True, blank=True)
    
    # Atributos de control comercial y financiero
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, help_text="Usuario que concretó la venta")
    cliente = models.ForeignKey('Cliente', on_delete=models.PROTECT, null=True, blank=True)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ganancia_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_total_discriminado = models.JSONField(default=dict, blank=True)

    # Facturación y Comprobante
    tipo_factura = models.CharField(max_length=1, choices=TIPO_FACTURA_CHOICES)
    receptor = models.CharField(max_length=200, help_text="Razón social o Nombre de quien factura")
    fecha = models.DateTimeField(auto_now_add=True)
    
    # Nuevos atributos operativos
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    medio_pago = models.CharField(max_length=20, choices=MEDIO_PAGO_CHOICES, default='EFECTIVO')
    estado_pago = models.CharField(max_length=15, choices=ESTADO_PAGO_CHOICES, default='SALDADA')

    # Datos de AFIP
    punto_venta = models.CharField(max_length=10, help_text="Ej: 0004", default="0001")
    cae = models.CharField(max_length=100, blank=True, null=True)
    fecha_vencimiento_cae = models.DateField(blank=True, null=True)
    
    # Total final de la venta (incluye productos + envío)
    totales = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Venta {self.tipo_factura}-{self.punto_venta}-{self.id} [{self.get_estado_pago_display()}] (CAE: {self.cae or 'Pendiente'})"
    
class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)    
    # Usamos DecimalField para la cantidad, indispensable para poder ingresar manualmente el peso exacto en la caja para los artículos pesables
    cantidad = models.DecimalField(max_digits=10, decimal_places=3) 
    precio_unitario_historico = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario_historico

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
from django.db import models
from .models import Venta # Asumiendo que Venta ya está en este archivo

class Vehiculo(models.Model):
    patente = models.CharField(max_length=20, unique=True)
    modelo = models.CharField(max_length=100)
    capacidad_carga_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="Capacidad máxima en kg")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.patente} - {self.modelo}"

class Chofer(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    licencia_conducir = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} (DNI: {self.dni})"

class Envio(models.Model):
    ESTADO_CHOICES = [
        ('P', 'Pendiente de Armado'),
        ('A', 'Armado / Listo'),
        ('C', 'En Camino'),
        ('E', 'Entregado'),
        ('X', 'Cancelado / Reprogramado'),
    ]

    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='envio')
    fecha_programada = models.DateField()
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='P')
    
    # Flota
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    chofer = models.ForeignKey(Chofer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Destino (Puede ser distinto al del cliente si es una obra específica)
    direccion_entrega = models.CharField(max_length=255)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Envío {self.id} - {self.get_estado_display()}"