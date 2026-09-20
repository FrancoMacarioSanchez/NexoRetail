from django import forms
from .models import Producto

from django import forms
from .models import Proveedor, Categoria, Subcategoria

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'cuit', 'correo', 'telefono', 'direccion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white outline-none focus:ring-2 focus:ring-accent text-sm transition-colors'

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white outline-none focus:ring-2 focus:ring-accent text-sm transition-colors'

class SubcategoriaForm(forms.ModelForm):
    class Meta:
        model = Subcategoria
        fields = ['categoria', 'nombre']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white outline-none focus:ring-2 focus:ring-accent text-sm transition-colors'

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # Excluimos stock_actual si quieres que ingrese por compras, 
        # o lo dejamos para carga inicial. Aquí incluimos todo lo esencial.
        fields = ['sku', 'codigo_barras', 'nombre', 'costo', 'precio', 
                  'alicuota', 'categoria', 'subcategoria', 'unidad_medida', 
                  'stock_actual', 'stock_critico', 'proveedores']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicamos clases de Tailwind a todos los inputs automáticamente
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white outline-none focus:ring-2 focus:ring-accent text-sm transition-colors'