from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nombre

class Subcategoria(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.categoria.nombre} - {self.nombre}"

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    cuit = models.CharField(max_length=20, blank=True, null=True, verbose_name="CUIT/CUIL")
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)\
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    # Opciones de Unidad de Medida (ideales para un corralón)
    UNIDAD_MEDIDA_CHOICES = [
        ('UN', 'Unidad'),
        ('KG', 'Kilogramo'),
        ('M', 'Metro Lineal'),
        ('M2', 'Metro Cuadrado'),
        ('M3', 'Metro Cúbico'),
        ('L', 'Litro'),
        ('PACK', 'Pack / Bulto'),
        ('BOL', 'Bolsa'),
        ('PAL', 'Pallet'),
    ]

    # Opciones de Alícuota de IVA (Adaptadas para Argentina)
    IVA_CHOICES = [
        (0.00, '0% (Exento)'),
        (10.50, '10.5%'),
        (21.00, '21.0%'),
        (27.00, '27.0%'),
    ]

    # 1. Identificación
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Código interno (SKU)")
    codigo_barras = models.CharField(max_length=100, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=255)

    # 2. Precios e Impuestos
    costo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Precio de venta base sin IVA")
    alicuota = models.DecimalField(max_digits=5, decimal_places=2, choices=IVA_CHOICES, default=21.00)

    # 3. Clasificación
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    unidad_medida = models.CharField(max_length=5, choices=UNIDAD_MEDIDA_CHOICES, default='UN')

    # 4. Proveedores (Relación Muchos a Muchos)
    proveedores = models.ManyToManyField(Proveedor, related_name='productos', blank=True)

    # 5. Inventario
    # Usamos DecimalField y no IntegerField para permitir fraccionar stock (ej: vender 1.5 kg o 2.5 m2)
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    stock_critico = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"[{self.sku}] {self.nombre}" if self.sku else self.nombre