from rest_framework import serializers
from .models import Categoria, Subcategoria, Proveedor, Producto

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class SubcategoriaSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')

    class Meta:
        model = Subcategoria
        fields = ['id', 'categoria', 'categoria_nombre', 'nombre']

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    # Estos campos de solo lectura ayudan al frontend a mostrar los nombres sin hacer peticiones extra
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    subcategoria_nombre = serializers.ReadOnlyField(source='subcategoria.nombre')
    
    class Meta:
        model = Producto
        fields = [
            'id', 'sku', 'codigo_barras', 'nombre', 'costo', 'precio', 'alicuota',
            'categoria', 'categoria_nombre', 'subcategoria', 'subcategoria_nombre',
            'unidad_medida', 'proveedores', 'stock_actual', 'stock_critico'
        ]