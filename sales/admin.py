from django.contrib import admin
from .models import Cliente, Presupuesto,Venta ,DetalleVenta, Envio

# Register your models her
admin.site.register(Cliente)
admin.site.register(Presupuesto)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(Envio)