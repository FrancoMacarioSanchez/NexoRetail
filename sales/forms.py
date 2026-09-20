from django import forms
from django.forms import inlineformset_factory
from .models import Cliente, Presupuesto, DetallePresupuesto, Envio

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['cuit', 'nombre', 'apellido', 'condicion_fiscal', 'mail', 'telefono', 'direcciones']
        widgets = {
            'direcciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Obra 1: Av. San Martín 123...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white focus:ring-2 focus:ring-accent outline-none transition-colors text-sm'

class PresupuestoForm(forms.ModelForm):
    # Forzamos los formatos aceptados y el tipo de input
    fecha_entrega = forms.DateField(
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'type': 'date', 
            'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:ring-2 focus:ring-accent'
        })
    )

    class Meta:
        model = Presupuesto
        fields = ['cliente', 'fecha_entrega']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white outline-none focus:ring-2 focus:ring-accent text-sm transition-colors'

class DetallePresupuestoForm(forms.ModelForm):
    class Meta:
        model = DetallePresupuesto
        fields = ['producto', 'cantidad', 'precio_unitario_historico']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-2 py-1.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-white outline-none focus:ring-2 focus:ring-accent text-sm'

# El FormSet permite crear múltiples "Detalles" vinculados a un solo "Presupuesto"
DetallePresupuestoFormSet = inlineformset_factory(
    parent_model=Presupuesto,
    model=DetallePresupuesto,
    form=DetallePresupuestoForm,
    extra=1, # Empieza con 1 fila en blanco
    can_delete=True
)            

from .models import Vehiculo, Chofer

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['patente', 'modelo', 'capacidad_carga_kg', 'activo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'w-4 h-4 text-accent border-gray-300 rounded focus:ring-accent'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white outline-none focus:ring-2 focus:ring-accent text-sm transition-colors'

class ChoferForm(forms.ModelForm):
    class Meta:
        model = Chofer
        fields = ['nombre', 'apellido', 'dni', 'telefono', 'licencia_conducir', 'activo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'w-4 h-4 text-accent border-gray-300 rounded focus:ring-accent'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white outline-none focus:ring-2 focus:ring-accent text-sm transition-colors'
class EnvioForm(forms.ModelForm):
    class Meta:
        model = Envio
        fields = ['direccion_entrega', 'estado', 'fecha_programada', 'chofer', 'vehiculo', 'observaciones']
        widgets = {
            'fecha_programada': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-white outline-none focus:ring-2 focus:ring-accent text-sm transition-colors'
            
from django import forms
from .models import Venta

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['tipo_factura', 'receptor', 'punto_venta', 'costo_envio', 'medio_pago', 'estado_pago']
        widgets = {
            'tipo_factura': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}),
            'receptor': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}),
            'punto_venta': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}),
            'costo_envio': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none', 'step': '0.01'}),
            'medio_pago': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}),
            'estado_pago': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}),
        }
        
from django import forms
from .models import Venta, Vehiculo, Chofer

class VentaConEnvioForm(forms.ModelForm):
    # Campos adicionales para configurar el envío en el mismo modal si se requiere
    requiere_envio = forms.BooleanField(required=False, initial=False, label="¿Requiere envío a domicilio / obra?")
    fecha_programada = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}))
    direccion_entrega = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none', 'placeholder': 'Calle, Número, Localidad'}))
    costo_envio = forms.DecimalField(required=False, initial=0.00, max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none', 'step': '0.01'}))
    vehiculo = forms.ModelChoiceField(queryset=Vehiculo.objects.filter(activo=True), required=False, widget=forms.Select(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}))
    chofer = forms.ModelChoiceField(queryset=Chofer.objects.filter(activo=True), required=False, widget=forms.Select(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}))
    observaciones_envio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none', 'rows': 2, 'placeholder': 'Observaciones para la entrega...'}))

    class Meta:
        model = Venta
        fields = ['tipo_factura', 'receptor', 'punto_venta', 'medio_pago', 'estado_pago']
        widgets = {
            'tipo_factura': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}),
            'receptor': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-500 dark:text-gray-400 text-sm outline-none cursor-not-allowed', 'readonly': 'readonly'}),
            'punto_venta': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-500 dark:text-gray-400 text-sm outline-none cursor-not-allowed', 'readonly': 'readonly'}),
            'medio_pago': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}),
            'estado_pago': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-white text-sm outline-none'}),
        }