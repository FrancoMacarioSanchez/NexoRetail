from rest_framework import serializers
from .models import Cliente, Presupuesto, DetallePresupuesto, Venta

class ClienteVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class DetallePresupuestoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetallePresupuesto
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario_historico']

class PresupuestoSerializer(serializers.ModelSerializer):
    # Anidamos los detalles para que al consultar un presupuesto traiga todos sus productos
    detalles = DetallePresupuestoSerializer(many=True, read_only=True)
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')

    class Meta:
        model = Presupuesto
        fields = [
            'id', 'fecha_creacion', 'fecha_entrega', 'presupuestante', 
            'cliente', 'cliente_nombre', 'costo_total', 'ganancia_total', 
            'iva_total_discriminado', 'total', 'detalles'
        ]

class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = '__all__'