import json
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator

from rest_framework import viewsets

# Asegúrate de que la ruta de importación de Producto sea la correcta
from productos.models import Producto
from .models import Cliente, Presupuesto, DetallePresupuesto, Venta, DetalleVenta
from .serializers import ClienteVentaSerializer, PresupuestoSerializer, DetallePresupuestoSerializer, VentaSerializer
from .forms import ClienteForm, PresupuestoForm, DetallePresupuestoFormSet


# ==========================================
# VISTAS DE API (Django Rest Framework)
# ==========================================

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteVentaSerializer

class PresupuestoViewSet(viewsets.ModelViewSet):
    queryset = Presupuesto.objects.all()
    serializer_class = PresupuestoSerializer

class DetallePresupuestoViewSet(viewsets.ModelViewSet):
    queryset = DetallePresupuesto.objects.all()
    serializer_class = DetallePresupuestoSerializer

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer


# ==========================================
# VISTAS DE CLIENTES (HTMX / Templates)
# ==========================================

def clientes_view(request):
    query = request.GET.get('q', '')
    clientes = Cliente.objects.all().order_by('-id')
    
    if query:
        clientes = clientes.filter(nombre__icontains=query) | clientes.filter(apellido__icontains=query)

    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }
    
    # Si la petición viene de HTMX (ej. buscador o paginación), devolvemos solo la tabla
    if request.headers.get('HX-Request'):
        return render(request, 'partials/tabla_clientes.html', context)
        
    return render(request, 'clientes.html', context)

def cliente_crear_editar_view(request, pk=None):
    if pk:
        cliente = get_object_or_404(Cliente, pk=pk)
        titulo = "Editar Cliente"
    else:
        cliente = None
        titulo = "Crear Nuevo Cliente"

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            
            continuar = request.POST.get('continuar') == 'true'
            
            # Si guardó con Shift+Enter (crear y añadir otro)
            if continuar and not pk:
                response = render(request, 'partials/modal_cliente.html', {'form': ClienteForm(), 'titulo': titulo})
                response['HX-Trigger'] = 'refreshTablaClientes'
                return response
            # Si guardó normal (cierra modal y actualiza tabla)
            else:
                response = HttpResponse()
                response['HX-Trigger'] = 'refreshTablaClientes, closeModal'
                return response
    else:
        form = ClienteForm(instance=cliente)
        
    return render(request, 'partials/modal_cliente.html', {'form': form, 'titulo': titulo, 'cliente': cliente})

def api_detalle_cliente(request, pk):
    """Devuelve los datos del cliente en formato HTML para inyectar en la vista."""
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'partials/cliente_detalles.html', {'cliente': cliente})


# ==========================================
# VISTAS DE PRESUPUESTOS (Gestión Clásica)
# ==========================================

def presupuestos_view(request):
    query = request.GET.get('q', '')
    # select_related optimiza la consulta SQL al traer al cliente junto con el presupuesto
    presupuestos = Presupuesto.objects.select_related('cliente').order_by('-fecha_creacion')
    
    if query:
        presupuestos = presupuestos.filter(cliente__nombre__icontains=query) | presupuestos.filter(id__icontains=query)

    paginator = Paginator(presupuestos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj, 
        'query': query
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'partials/tabla_presupuestos.html', context)
        
    return render(request, 'presupuestos.html', context)

def presupuesto_detalle_view(request, pk):
    # Prefetch optimiza la carga de la base de datos trayendo todos los detalles de una vez
    presupuesto = get_object_or_404(Presupuesto.objects.select_related('cliente', 'presupuestante').prefetch_related('detalles__producto'), pk=pk)
    
    return render(request, 'presupuesto_detalle.html', {
        'presupuesto': presupuesto
    })

def presupuesto_crear_view(request):
    if request.method == 'POST':
        form = PresupuestoForm(request.POST)
        formset = DetallePresupuestoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # 1. Guardamos el presupuesto base
            presupuesto = form.save()

            # 2. Guardamos los productos (detalles) vinculados a este presupuesto
            detalles = formset.save(commit=False)
            for detalle in detalles:
                detalle.presupuesto = presupuesto
                detalle.save()
            
            # 3. Cálculos matemáticos
            subtotal_neto = Decimal('0.00')
            costo_total_presupuesto = Decimal('0.00')
            iva_total_presupuesto = Decimal('0.00')

            for detalle in presupuesto.detalles.all():
                linea_subtotal = detalle.cantidad * detalle.precio_unitario_historico
                subtotal_neto += linea_subtotal
                
                linea_costo = detalle.cantidad * detalle.producto.costo
                costo_total_presupuesto += linea_costo
                
                alicuota_decimal = detalle.producto.alicuota / Decimal('100.00')
                iva_total_presupuesto += linea_subtotal * alicuota_decimal

            # Asignación de campos existentes en el modelo Presupuesto
            presupuesto.costo_total = costo_total_presupuesto
            presupuesto.ganancia_total = subtotal_neto - costo_total_presupuesto
            presupuesto.iva_total_discriminado = iva_total_presupuesto
            presupuesto.total = subtotal_neto + iva_total_presupuesto

            # Guardamos los totales definitivos
            presupuesto.save()

            return redirect('presupuestos') # Redirige a la lista
            
    else:
        form = PresupuestoForm()
        formset = DetallePresupuestoFormSet()

    return render(request, 'presupuesto_form.html', {'form': form, 'formset': formset})


# ==========================================
# VISTAS DE PRODUCTOS (Buscador Auxiliar)
# ==========================================

def api_buscar_productos(request):
    query = request.GET.get('q', '')
    if query:
        productos = Producto.objects.filter(nombre__icontains=query)[:5]
    else:
        productos = []
    
    return render(request, 'partials/producto_search_results.html', {'productos': productos})


# ==========================================
# VISTAS POS (Point Of Sale)
# ==========================================

def pos_presupuesto_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cliente_id = data.get('cliente_id')
        detalles = data.get('detalles', [])
        
        cliente = get_object_or_404(Cliente, id=cliente_id)
        presupuesto = Presupuesto.objects.create(
            presupuestante=request.user,
            cliente=cliente,
        )
        
        subtotal_neto = Decimal('0.00')
        costo_total = Decimal('0.00')
        iva_dict = {} # Inicializamos el diccionario de IVA
        
        for item in detalles:
            producto = get_object_or_404(Producto, id=item['producto_id'])
            cantidad = Decimal(item['cantidad'])
            
            precio_unitario_congelado = producto.precio
            
            DetallePresupuesto.objects.create(
                presupuesto=presupuesto,
                producto=producto,
                cantidad=cantidad,
                precio_unitario_historico=precio_unitario_congelado
            )
            
            linea_subtotal = cantidad * precio_unitario_congelado
            linea_costo = cantidad * producto.costo
            
            subtotal_neto += linea_subtotal
            costo_total += linea_costo
            
            # Agrupamos el IVA por alícuota
            alicuota_str = str(producto.alicuota) # Usamos string para las claves del JSON (ej: '21.0')
            valor_iva = linea_subtotal * (producto.alicuota / Decimal('100.00'))
            
            if alicuota_str in iva_dict:
                iva_dict[alicuota_str] += valor_iva
            else:
                iva_dict[alicuota_str] = valor_iva
            
        # Convertimos los valores Decimal a float para que se puedan guardar en el JSONField
        iva_json = {k: float(v) for k, v in iva_dict.items()}
        
        # Calculamos el total sumando el subtotal más la suma de todos los valores del diccionario IVA
        suma_iva_total = sum(iva_dict.values())
            
        presupuesto.costo_total = costo_total
        presupuesto.ganancia_total = subtotal_neto - costo_total
        presupuesto.iva_total_discriminado = iva_json # Guardamos el diccionario
        presupuesto.total = subtotal_neto + suma_iva_total
        presupuesto.save()
        
        return JsonResponse({'status': 'success', 'presupuesto_id': presupuesto.id})

    # Si es GET, mostramos la interfaz POS
    clientes = Cliente.objects.all()
    return render(request, 'pos_presupuesto.html', {'clientes': clientes})

def actualizar_precios_presupuesto(request, presupuesto_id):
    """
    Función para el botón 'Actualizar Precios'.
    Recalcula el presupuesto tomando los precios actuales del modelo Producto.
    """
    presupuesto = get_object_or_404(Presupuesto, id=presupuesto_id)
    
    subtotal_neto = Decimal('0.00')
    costo_total = Decimal('0.00')
    iva_total = Decimal('0.00')
    
    for detalle in presupuesto.detalles.all():
        producto = detalle.producto
        # Actualizamos el precio congelado al valor del día de hoy
        detalle.precio_unitario_historico = producto.precio
        detalle.save()
        
        linea_subtotal = detalle.cantidad * detalle.precio_unitario_historico
        subtotal_neto += linea_subtotal
        costo_total += detalle.cantidad * producto.costo
        iva_total += linea_subtotal * (producto.alicuota / Decimal('100.00'))
        
    presupuesto.costo_total = costo_total
    presupuesto.ganancia_total = subtotal_neto - costo_total
    presupuesto.iva_total_discriminado = iva_total
    presupuesto.total = subtotal_neto + iva_total
    presupuesto.save()
    
    return redirect('presupuesto_detalle', pk=presupuesto.id)

def presupuesto_editar_view(request, pk):
    # Obtenemos el presupuesto a editar
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cliente_id = data.get('cliente_id')
            detalles_data = data.get('detalles', [])
            
            cliente = get_object_or_404(Cliente, id=cliente_id)
            
            # Actualizamos el cliente
            presupuesto.cliente = cliente
            
            # Borramos los detalles viejos para reemplazarlos por los nuevos
            presupuesto.detalles.all().delete()
            
            subtotal_neto = Decimal('0.00')
            costo_total = Decimal('0.00')
            iva_dict = {}
            
            for item in detalles_data:
                producto = get_object_or_404(Producto, id=item['producto_id'])
                cantidad = Decimal(str(item['cantidad']))
                
                # Usamos el precio actual del producto (o podrías pasarlo desde el frontend)
                precio_unitario = producto.precio
                
                DetallePresupuesto.objects.create(
                    presupuesto=presupuesto,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario_historico=precio_unitario
                )
                
                linea_subtotal = cantidad * precio_unitario
                linea_costo = cantidad * producto.costo
                
                subtotal_neto += linea_subtotal
                costo_total += linea_costo
                
                alicuota_str = str(producto.alicuota)
                valor_iva = linea_subtotal * (producto.alicuota / Decimal('100.00'))
                
                if alicuota_str in iva_dict:
                    iva_dict[alicuota_str] += float(valor_iva)
                else:
                    iva_dict[alicuota_str] = float(valor_iva)
                    
            suma_iva_total = Decimal(str(sum(iva_dict.values())))
            
            presupuesto.costo_total = costo_total
            presupuesto.ganancia_total = subtotal_neto - costo_total
            presupuesto.iva_total_discriminado = iva_dict
            presupuesto.total = subtotal_neto + suma_iva_total
            presupuesto.save()
            
            return JsonResponse({'status': 'success', 'presupuesto_id': presupuesto.id})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # -----------------------------------------
    # Si es un GET, preparamos los datos para el Frontend
    # -----------------------------------------
    clientes = Cliente.objects.all()
    
    # Pre-armamos el carrito en formato JSON para que el Javascript lo lea
    detalles_iniciales = []
    for d in presupuesto.detalles.all():
        detalles_iniciales.append({
            'producto_id': d.producto.id,
            'nombre': d.producto.nombre,
            'precio': float(d.precio_unitario_historico), 
            'alicuota': float(d.producto.alicuota),
            'cantidad': float(d.cantidad)
        })
        
    context = {
        'presupuesto': presupuesto,
        'clientes': clientes,
        'detalles_iniciales': json.dumps(detalles_iniciales),
        'es_edicion': True
    }
    return render(request, 'pos_presupuesto.html', context)

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Presupuesto, Venta, DetalleVenta, Envio
from .forms import VentaConEnvioForm

def presupuesto_convertir_view(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
    
    # Validar que no se convierta dos veces
    if hasattr(presupuesto, 'venta_asociada') and presupuesto.venta_asociada:
        messages.warning(request, "Este presupuesto ya cuenta con una venta generada.")
        return redirect('presupuesto_detalle', pk=pk)

    # 1. Obtener el punto de venta desde el Tenant actual (con un fallback por seguridad)
    punto_venta_tenant = getattr(request.tenant, 'punto_venta', '0001')

    # 2. Obtener el receptor: intentar buscar la última venta registrada para reutilizar el receptor, o usar el cliente del presupuesto
    ultima_venta = Venta.objects.filter(cliente=presupuesto.cliente).order_by('-fecha').first()
    if ultima_venta and ultima_venta.receptor:
        receptor_sugerido = ultima_venta.receptor
    else:
        receptor_sugerido = str(presupuesto.cliente) if presupuesto.cliente else "Consumidor Final"

    if request.method == 'POST':
        # Copiamos el POST para inyectar los datos automáticos protegidos
        post_data = request.POST.copy()
        post_data['receptor'] = receptor_sugerido
        post_data['punto_venta'] = punto_venta_tenant

        form = VentaConEnvioForm(post_data)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Guardar la Venta principal
                    venta = form.save(commit=False)
                    venta.presupuesto = presupuesto
                    venta.vendedor = request.user if request.user.is_authenticated else None
                    venta.cliente = presupuesto.cliente
                    venta.receptor = receptor_sugerido
                    venta.punto_venta = punto_venta_tenant
                    
                    venta.costo_total = presupuesto.costo_total
                    venta.ganancia_total = presupuesto.ganancia_total
                    venta.iva_total_discriminado = presupuesto.iva_total_discriminado
                    
                    # Calcular total considerando el costo del envío si se seleccionó
                    costo_envio = form.cleaned_data.get('costo_envio', 0) or 0
                    requiere_envio = form.cleaned_data.get('requiere_envio')
                    
                    venta.costo_envio = costo_envio if requiere_envio else 0
                    venta.totales = presupuesto.total + (costo_envio if requiere_envio else 0)
                    venta.save()

                    # 2. Migrar los detalles del Presupuesto a DetalleVenta y descontar Stock
                    for det_p in presupuesto.detalles.select_related('producto').all():
                        DetalleVenta.objects.create(
                            venta=venta,
                            producto=det_p.producto,
                            cantidad=det_p.cantidad,
                            precio_unitario_historico=det_p.precio_unitario_historico
                        )
                        
                        # Descuento de stock en el modelo Producto
                        producto = det_p.producto
                        if hasattr(producto, 'stock_actual') and producto.stock_actual is not None:
                            producto.stock_actual -= det_p.cantidad
                            producto.save()

                    # 3. Crear el Envio si fue requerido
                    if requiere_envio:
                        Envio.objects.create(
                            venta=venta,
                            fecha_programada=form.cleaned_data.get('fecha_programada') or presupuesto.fecha_entrega or timezone.now().date(),
                            estado='P', # Pendiente de armado
                            vehiculo=form.cleaned_data.get('vehiculo'),
                            chofer=form.cleaned_data.get('chofer'),
                            direccion_entrega=form.cleaned_data.get('direccion_entrega') or (presupuesto.cliente.direcciones if presupuesto.cliente else "Retira en local"),
                            observaciones=form.cleaned_data.get('observaciones_envio')
                        )

                messages.success(request, f'¡Venta #{venta.id} registrada con éxito y stock descontado!')
                return redirect('presupuesto_detalle', pk=pk)
                
            except Exception as e:
                messages.error(request, f'Ocurrió un error interno al procesar la venta: {e}')
        else:
            messages.error(request, "Por favor, revisa los datos del formulario.")
    else:
        form = VentaConEnvioForm(initial={
            'receptor': receptor_sugerido,
            'punto_venta': punto_venta_tenant,
            'requiere_envio': False,
            'direccion_entrega': presupuesto.cliente.direcciones if presupuesto.cliente else ""
        })

    return render(request, 'partials/modal_convertir_venta.html', {'form': form, 'presupuesto': presupuesto})

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Venta, Envio

# Asumiendo que tu modelo Cliente está en la misma app, si está en otra, ajústalo:
# from customers.models import Cliente 
from .models import Cliente 

User = get_user_model()

def ventas_view(request):
    # 1. Capturar todos los parámetros del request
    query = request.GET.get('q', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    cliente_id = request.GET.get('cliente_id', '')
    vendedor_id = request.GET.get('vendedor_id', '')
    estado_envio = request.GET.get('estado_envio', '')

    # 2. Consulta base optimizada
    ventas = Venta.objects.select_related('cliente', 'vendedor', 'envio').order_by('-fecha')
    
    # 3. Aplicar filtros secuencialmente
    if query:
        ventas = ventas.filter(
            Q(receptor__icontains=query) |
            Q(id__icontains=query) |
            Q(cae__icontains=query)
        )

    if fecha_desde:
        ventas = ventas.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        ventas = ventas.filter(fecha__date__lte=fecha_hasta)

    if cliente_id:
        ventas = ventas.filter(cliente_id=cliente_id)
        
    if vendedor_id:
        ventas = ventas.filter(vendedor_id=vendedor_id)

    if estado_envio:
        if estado_envio == 'SIN_ENVIO':
            ventas = ventas.filter(envio__isnull=True)
        else:
            ventas = ventas.filter(envio__estado=estado_envio)

    # 4. Paginación
    paginator = Paginator(ventas, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 5. Obtener datos para poblar los selects en el HTML
    context = {
        'page_obj': page_obj,
        # Mantener los valores ingresados en los inputs
        'query': query,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'cliente_id': cliente_id,
        'vendedor_id': vendedor_id,
        'estado_envio': estado_envio,
        # Listas para los desplegables
        'clientes': Cliente.objects.all().order_by('nombre'), # Cambia 'nombre' por 'razon_social' si es tu caso
        'vendedores': User.objects.filter(is_active=True).order_by('username'),
        'estados_envio': Envio.ESTADO_CHOICES,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'partials/tabla_ventas.html', context)
        
    return render(request, 'ventas.html', context)

def venta_detalle_view(request, pk):
    # Traemos la venta con sus relaciones directas para evitar consultas extra
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'vendedor', 'presupuesto'), pk=pk)
    
    # Si la venta viene de un presupuesto, obtenemos sus detalles
    detalles = []
    if venta.presupuesto:
        detalles = venta.presupuesto.detalles.select_related('producto').all()

    context = {
        'venta': venta,
        'detalles': detalles,
    }
    return render(request, 'venta_detalle.html', context)

from .models import Envio
from .forms import EnvioForm

def envio_crear_editar_view(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    # Buscamos si la venta ya tiene un envío (gracias al related_name='envio')
    envio = getattr(venta, 'envio', None)
    
    if request.method == 'POST':
        form = EnvioForm(request.POST, instance=envio)
        if form.is_valid():
            nuevo_envio = form.save(commit=False)
            nuevo_envio.venta = venta # Vinculamos forzosamente la venta
            nuevo_envio.save()
            
            # Recarga la página completa para mostrar los cambios en el detalle
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        # Si es un envío nuevo y el cliente tiene dirección, la pre-cargamos por comodidad
        initial_data = {}
        if not envio and venta.cliente and venta.cliente.direcciones:
            initial_data['direccion_entrega'] = venta.cliente.direcciones

        form = EnvioForm(instance=envio, initial=initial_data)

    return render(request, 'partials/modal_envio.html', {'form': form, 'venta': venta, 'envio': envio})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Cliente, Venta
from .forms import ClienteForm

def cliente_detalle_view(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # El 'related' de pedidos/ventas asociadas al cliente
    pedidos = Venta.objects.filter(cliente=cliente).select_related('vendedor', 'envio').order_by('-fecha')

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos del cliente actualizados correctamente.')
            return redirect('cliente_detalle', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)

    context = {
        'cliente': cliente,
        'pedidos': pedidos,
        'form': form,
    }
    return render(request, 'cliente_detalle.html', context)

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Envio

def envios_pendientes_view(request):
    # Traemos todos los envíos que no estén entregados ni cancelados
    envios = Envio.objects.exclude(estado__in=['E', 'X']).select_related('venta__cliente', 'chofer', 'vehiculo').order_by('fecha_programada')
    
    context = {
        'envios': envios,
        'estados': Envio.ESTADO_CHOICES,
    }
    return render(request, 'envios.html', context)

# Vista exclusiva para HTMX: Cambia el estado y devuelve solo el badge actualizado
def cambiar_estado_envio(request, pk):
    if request.method == 'POST':
        envio = get_object_or_404(Envio, pk=pk)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado in dict(Envio.ESTADO_CHOICES):
            envio.estado = nuevo_estado
            envio.save()
            
        # Retornamos el snippet HTML con el diseño actualizado
        return render(request, 'partials/badge_estado_envio.html', {'envio': envio, 'estados': Envio.ESTADO_CHOICES})
    
from django.shortcuts import render, get_object_or_404, redirect
from .models import Vehiculo, Chofer
from .forms import VehiculoForm, ChoferForm

# --- VEHÍCULOS ---
def vehiculos_view(request):
    vehiculos = Vehiculo.objects.all()
    form = VehiculoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('vehiculos_list')
    return render(request, 'vehiculos.html', {'vehiculos': vehiculos, 'form': form})

# --- CHOFERES ---
def choferes_view(request):
    choferes = Chofer.objects.all()
    form = ChoferForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('choferes_list')
    return render(request, 'choferes.html', {'choferes': choferes, 'form': form})

from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDay
from datetime import datetime, date
from .models import Venta

def informes_gerencia_view(request):
    # Obtener filtros de fecha de la URL (si el usuario los envió)
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Queryset base de ventas
    ventas_qs = Venta.objects.all()

    # Aplicar filtros si existen
    if fecha_inicio:
        ventas_qs = ventas_qs.filter(fecha__date__gte=fecha_inicio)
    if fecha_fin:
        ventas_qs = ventas_qs.filter(fecha__date__lte=fecha_fin)

    # 1. Totales generales del período filtrado
    resumen_periodo = ventas_qs.aggregate(
        total_facturado=Sum('totales'),
        cantidad_ventas=Count('id')
    )

    # 2. Resumen de ventas diarias (agrupado por día)
    ventas_diarias = (
        ventas_qs.annotate(dia=TruncDay('fecha'))
        .values('dia')
        .annotate(total_dia=Sum('totales'), cantidad=Count('id'))
        .order_by('-dia')
    )

    # 3. Totales mensuales (Histórico general o filtrado)
    totales_mensuales = (
        Venta.objects.all()
        .annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total_mes=Sum('totales'), cantidad=Count('id'))
        .order_by('-mes')
    )

    context = {
        'resumen_periodo': resumen_periodo,
        'ventas_diarias': ventas_diarias,
        'totales_mensuales': totales_mensuales,
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
    }

    return render(request, 'informes.html', context)

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from .models import Venta

def descargar_factura_pdf(request, pk):
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'presupuesto'), pk=pk)
    
    detalles = []
    if venta.presupuesto:
        detalles = venta.presupuesto.detalles.select_related('producto').all()

    context = {
        'venta': venta,
        'detalles': detalles,
    }

    # Renderizamos la plantilla HTML
    html_string = render_to_string('pdf_factura.html', context)
    
    # Creamos la respuesta HTTP tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Factura_{venta.punto_venta}_{venta.id}.pdf"'
    
    # Generamos el PDF con xhtml2pdf
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Tuvimos un error al generar el PDF <pre>' + html_string + '</pre>')
        
    return response

import json
import google.generativeai as genai
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Q
from sales.models import Presupuesto, DetallePresupuesto, Cliente
from productos.models import Producto

# Configurar Gemini con tu API Key
genai.configure(api_key=settings.GEMINI_API_KEY)

def chatbot_procesar_view(request):
    if request.method == 'POST':
        mensaje_usuario = request.POST.get('mensaje', '')
        
        # 1. EL PROMPT PARA GEMINI (Instrucciones estrictas)
        prompt = f"""
        Eres el cerebro de un chatbot para un corralón de materiales/mayorista llamado NexoRetail.
        Tu trabajo es analizar el mensaje del usuario y extraer la intención y los parámetros en formato JSON estricto.
        
        Las intenciones posibles son:
        - "crear_presupuesto": Si pide armar un presupuesto, cotización o pedido.
        - "consultar_stock": Si pregunta si hay disponibilidad o cuánto queda de un producto.
        - "consultar_precio": Si pregunta cuánto vale o el precio de un producto.
        - "general": Para saludos, agradecimientos o consultas que no apliquen a las anteriores.

        Debes responder UNICAMENTE con un objeto JSON con esta estructura exacta:
        {{
            "intencion": "una de las opciones",
            "cliente": "nombre del cliente si lo menciona, o null",
            "productos": [
                {{"nombre": "nombre limpio del producto", "cantidad": 1.0}}
            ],
            "respuesta_bot": "Si la intención es 'general', escribe aquí tu respuesta conversacional amigable. Si no, déjalo en null."
        }}

        Mensaje del usuario: "{mensaje_usuario}"
        """

        try:
            # 2. LLAMAR A GEMINI
            # Usamos flash porque es el más rápido para tareas de ruteo/extracción
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parseamos el JSON devuelto por Gemini
            data = json.loads(response.text)
            intencion = data.get('intencion')
            productos_json = data.get('productos', [])
            #print(data)
            html_respuesta = ""

            # -------------------------------------------------------------
            # LÓGICA 1: CREAR PRESUPUESTO
            # -------------------------------------------------------------
            if intencion == 'crear_presupuesto':
                # (Misma lógica que armamos antes, pero ahora con los datos limpios de Gemini)
                nombre_cliente = data.get('cliente')
                cliente_obj = Cliente.objects.filter(nombre__icontains=nombre_cliente).first() if nombre_cliente else None
                if not cliente_obj:
                    cliente_obj = Cliente.objects.filter(condicion_fiscal='CF').first() # Consumidor Final

                presupuesto = Presupuesto.objects.create(
                    cliente=cliente_obj,
                    presupuestante=request.user if request.user.is_authenticated else None,
                    costo_total=0, ganancia_total=0, total=0
                )

                total_presupuesto = Decimal('0.00')
                items_agregados = []
                errores = []

                for prod_data in productos_json:
                    prod_nombre = prod_data.get('nombre', '')
                    cant = Decimal(str(prod_data.get('cantidad', 1)))
                    
                    producto_obj = Producto.objects.filter(nombre__icontains=prod_nombre).first()
                    if producto_obj:
                        precio_u = getattr(producto_obj, 'precio', Decimal('0.00'))
                        DetallePresupuesto.objects.create(
                            presupuesto=presupuesto, producto=producto_obj,
                            cantidad=cant, precio_unitario_historico=precio_u
                        )
                        total_presupuesto += (cant * precio_u)
                        items_agregados.append(f"{cant} x {producto_obj.nombre}")
                    else:
                        errores.append(prod_nombre)

                presupuesto.total = total_presupuesto
                presupuesto.save()

                html_respuesta = f"¡Presupuesto creado para <strong>{cliente_obj or 'Consumidor Final'}</strong>!<br><br>"
                html_respuesta += "<ul class='list-disc pl-4 mb-2'><li>" + "</li><li>".join(items_agregados) + "</li></ul>"
                if errores:
                    html_respuesta += f"<p class='text-amber-500 text-xs'>No encontré: {', '.join(errores)}</p>"
                html_respuesta += f"<div class='mt-2 font-black'>Total: ${total_presupuesto:,.2f}</div>"
                html_respuesta += f"<a href='{reverse('presupuesto_detalle', args=[presupuesto.id])}' class='mt-3 inline-block px-4 py-2 bg-accent text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition'>Abrir Presupuesto #{presupuesto.id}</a>"

            # -------------------------------------------------------------
            # LÓGICA 2: CONSULTAR STOCK
            # -------------------------------------------------------------
            elif intencion == 'consultar_stock':
                html_respuesta = "<strong>Consulta de Stock:</strong><br><ul class='mt-2 space-y-1'>"
                for prod_data in productos_json:
                    producto_obj = Producto.objects.filter(nombre__icontains=prod_data.get('nombre')).first()
                    if producto_obj:
                        stock = getattr(producto_obj, 'stock_actual', 0)
                        color = "text-emerald-500" if stock > 0 else "text-red-500 font-bold"
                        html_respuesta += f"<li>{producto_obj.nombre}: <span class='{color}'>{stock} unidades</span></li>"
                    else:
                        html_respuesta += f"<li><span class='text-gray-400'>No encontré el producto '{prod_data.get('nombre')}'</span></li>"
                html_respuesta += "</ul>"

            # -------------------------------------------------------------
            # LÓGICA 3: CONSULTAR PRECIO
            # -------------------------------------------------------------
            elif intencion == 'consultar_precio':
                html_respuesta = "<strong>Consulta de Precios (Sin IVA):</strong><br><ul class='mt-2 space-y-1'>"
                for prod_data in productos_json:
                    producto_obj = Producto.objects.filter(nombre__icontains=prod_data.get('nombre')).first()
                    if producto_obj:
                        precio = getattr(producto_obj, 'precio', 0)
                        html_respuesta += f"<li>{producto_obj.nombre}: <strong>${precio:,.2f}</strong></li>"
                    else:
                        html_respuesta += f"<li><span class='text-gray-400'>No encontré el producto '{prod_data.get('nombre')}'</span></li>"
                html_respuesta += "</ul>"

            # -------------------------------------------------------------
            # LÓGICA 4: GENERAL / CHAT
            # -------------------------------------------------------------
            else:
                html_respuesta = data.get('respuesta_bot', "¡Hola! ¿En qué te puedo ayudar hoy con el sistema?")

        except Exception as e:
            html_respuesta = f"<span class='text-rose-500'>Ocurrió un error procesando tu pedido: {str(e)}</span>"

        return render(request, 'partials/chat_message.html', {
            'mensaje_usuario': mensaje_usuario,
            'respuesta_bot': html_respuesta
        })