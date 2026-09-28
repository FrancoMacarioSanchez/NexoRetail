
import json
from decimal import Decimal
from datetime import datetime, date

import google.generativeai as genai

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth, TruncDay
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from productos.models import Producto

from .models import (
    Cliente,
    Presupuesto,
    DetallePresupuesto,
    Venta,
    DetalleVenta,
    Envio,
    Vehiculo,
    Chofer,
)

from .serializers import (
    ClienteVentaSerializer,
    PresupuestoSerializer,
    DetallePresupuestoSerializer,
    VentaSerializer,
)

from .forms import (
    ClienteForm,
    PresupuestoForm,
    DetallePresupuestoFormSet,
    VentaConEnvioForm,
    EnvioForm,
    VehiculoForm,
    ChoferForm,
)

from xhtml2pdf import pisa


# ============================================================
# VISTAS DE API - DJANGO REST FRAMEWORK
# ============================================================

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteVentaSerializer
    permission_classes = [IsAuthenticated]


class PresupuestoViewSet(viewsets.ModelViewSet):
    queryset = Presupuesto.objects.all()
    serializer_class = PresupuestoSerializer
    permission_classes = [IsAuthenticated]


class DetallePresupuestoViewSet(viewsets.ModelViewSet):
    queryset = DetallePresupuesto.objects.all()
    serializer_class = DetallePresupuestoSerializer
    permission_classes = [IsAuthenticated]


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]


# ============================================================
# CLIENTES
# ============================================================

@login_required
def clientes_view(request):
    query = request.GET.get('q', '')

    clientes = Cliente.objects.all().order_by('-id')

    if query:
        clientes = (
            clientes.filter(nombre__icontains=query)
            | clientes.filter(apellido__icontains=query)
        )

    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }

    if request.headers.get('HX-Request'):
        return render(
            request,
            'partials/tabla_clientes.html',
            context
        )

    return render(request, 'clientes.html', context)


@login_required
def cliente_crear_editar_view(request, pk=None):

    if pk:
        cliente = get_object_or_404(Cliente, pk=pk)
        titulo = "Editar Cliente"
    else:
        cliente = None
        titulo = "Crear Nuevo Cliente"

    if request.method == 'POST':

        form = ClienteForm(
            request.POST,
            instance=cliente
        )

        if form.is_valid():

            form.save()

            continuar = request.POST.get('continuar') == 'true'

            if continuar and not pk:

                response = render(
                    request,
                    'partials/modal_cliente.html',
                    {
                        'form': ClienteForm(),
                        'titulo': titulo
                    }
                )

                response['HX-Trigger'] = 'refreshTablaClientes'

                return response

            response = HttpResponse()

            response['HX-Trigger'] = (
                'refreshTablaClientes, closeModal'
            )

            return response

    else:

        form = ClienteForm(
            instance=cliente
        )

    return render(
        request,
        'partials/modal_cliente.html',
        {
            'form': form,
            'titulo': titulo,
            'cliente': cliente
        }
    )


@login_required
def api_detalle_cliente(request, pk):

    cliente = get_object_or_404(
        Cliente,
        pk=pk
    )

    return render(
        request,
        'partials/cliente_detalles.html',
        {
            'cliente': cliente
        }
    )


# ============================================================
# PRESUPUESTOS
# ============================================================

@login_required
def presupuestos_view(request):

    query = request.GET.get('q', '')

    presupuestos = (
        Presupuesto.objects
        .select_related('cliente')
        .order_by('-fecha_creacion')
    )

    if query:

        presupuestos = (
            presupuestos.filter(
                cliente__nombre__icontains=query
            )
            | presupuestos.filter(
                id__icontains=query
            )
        )

    paginator = Paginator(
        presupuestos,
        10
    )

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query
    }

    if request.headers.get('HX-Request'):

        return render(
            request,
            'partials/tabla_presupuestos.html',
            context
        )

    return render(
        request,
        'presupuestos.html',
        context
    )


@login_required
def presupuesto_detalle_view(request, pk):

    presupuesto = get_object_or_404(
        Presupuesto.objects
        .select_related(
            'cliente',
            'presupuestante'
        )
        .prefetch_related(
            'detalles__producto'
        ),
        pk=pk
    )

    return render(
        request,
        'presupuesto_detalle.html',
        {
            'presupuesto': presupuesto
        }
    )


@login_required
def presupuesto_crear_view(request):

    if request.method == 'POST':

        form = PresupuestoForm(
            request.POST
        )

        formset = DetallePresupuestoFormSet(
            request.POST
        )

        if form.is_valid() and formset.is_valid():

            presupuesto = form.save(
                commit=False
            )

            presupuesto.presupuestante = request.user
            presupuesto.save()

            detalles = formset.save(
                commit=False
            )

            for detalle in detalles:

                detalle.presupuesto = presupuesto
                detalle.save()

            subtotal_neto = Decimal('0.00')
            costo_total_presupuesto = Decimal('0.00')
            iva_total_presupuesto = Decimal('0.00')

            for detalle in presupuesto.detalles.all():

                linea_subtotal = (
                    detalle.cantidad
                    * detalle.precio_unitario_historico
                )

                subtotal_neto += linea_subtotal

                linea_costo = (
                    detalle.cantidad
                    * detalle.producto.costo
                )

                costo_total_presupuesto += linea_costo

                alicuota_decimal = (
                    detalle.producto.alicuota
                    / Decimal('100.00')
                )

                iva_total_presupuesto += (
                    linea_subtotal
                    * alicuota_decimal
                )

            presupuesto.costo_total = (
                costo_total_presupuesto
            )

            presupuesto.ganancia_total = (
                subtotal_neto
                - costo_total_presupuesto
            )

            presupuesto.iva_total_discriminado = (
                iva_total_presupuesto
            )

            presupuesto.total = (
                subtotal_neto
                + iva_total_presupuesto
            )

            presupuesto.save()

            return redirect('presupuestos')

    else:

        form = PresupuestoForm()
        formset = DetallePresupuestoFormSet()

    return render(
        request,
        'presupuesto_form.html',
        {
            'form': form,
            'formset': formset
        }
    )


# ============================================================
# PRODUCTOS
# ============================================================

@login_required
def api_buscar_productos(request):

    query = request.GET.get('q', '')

    if query:

        productos = (
            Producto.objects
            .filter(
                nombre__icontains=query
            )[:5]
        )

    else:

        productos = []

    return render(
        request,
        'partials/producto_search_results.html',
        {
            'productos': productos
        }
    )


# ============================================================
# POS
# ============================================================

@login_required
def pos_presupuesto_view(request):

    if request.method == 'POST':

        data = json.loads(
            request.body
        )

        cliente_id = data.get(
            'cliente_id'
        )

        detalles = data.get(
            'detalles',
            []
        )

        cliente = get_object_or_404(
            Cliente,
            id=cliente_id
        )

        presupuesto = Presupuesto.objects.create(
            presupuestante=request.user,
            cliente=cliente,
        )

        subtotal_neto = Decimal('0.00')
        costo_total = Decimal('0.00')

        iva_dict = {}

        for item in detalles:

            producto = get_object_or_404(
                Producto,
                id=item['producto_id']
            )

            cantidad = Decimal(
                str(item['cantidad'])
            )

            precio_unitario_congelado = (
                producto.precio
            )

            DetallePresupuesto.objects.create(
                presupuesto=presupuesto,
                producto=producto,
                cantidad=cantidad,
                precio_unitario_historico=(
                    precio_unitario_congelado
                )
            )

            linea_subtotal = (
                cantidad
                * precio_unitario_congelado
            )

            linea_costo = (
                cantidad
                * producto.costo
            )

            subtotal_neto += linea_subtotal
            costo_total += linea_costo

            alicuota_str = str(
                producto.alicuota
            )

            valor_iva = (
                linea_subtotal
                * (
                    producto.alicuota
                    / Decimal('100.00')
                )
            )

            if alicuota_str in iva_dict:

                iva_dict[alicuota_str] += (
                    valor_iva
                )

            else:

                iva_dict[alicuota_str] = (
                    valor_iva
                )

        iva_json = {
            key: float(value)
            for key, value in iva_dict.items()
        }

        suma_iva_total = sum(
            iva_dict.values()
        )

        presupuesto.costo_total = costo_total

        presupuesto.ganancia_total = (
            subtotal_neto
            - costo_total
        )

        presupuesto.iva_total_discriminado = (
            iva_json
        )

        presupuesto.total = (
            subtotal_neto
            + suma_iva_total
        )

        presupuesto.save()

        return JsonResponse({
            'status': 'success',
            'presupuesto_id': presupuesto.id
        })

    clientes = Cliente.objects.all()

    return render(
        request,
        'pos_presupuesto.html',
        {
            'clientes': clientes
        }
    )


@login_required
def actualizar_precios_presupuesto(
    request,
    presupuesto_id
):

    presupuesto = get_object_or_404(
        Presupuesto,
        id=presupuesto_id
    )

    subtotal_neto = Decimal('0.00')
    costo_total = Decimal('0.00')
    iva_total = Decimal('0.00')

    for detalle in presupuesto.detalles.all():

        producto = detalle.producto

        detalle.precio_unitario_historico = (
            producto.precio
        )

        detalle.save()

        linea_subtotal = (
            detalle.cantidad
            * detalle.precio_unitario_historico
        )

        subtotal_neto += linea_subtotal

        costo_total += (
            detalle.cantidad
            * producto.costo
        )

        iva_total += (
            linea_subtotal
            * (
                producto.alicuota
                / Decimal('100.00')
            )
        )

    presupuesto.costo_total = costo_total

    presupuesto.ganancia_total = (
        subtotal_neto
        - costo_total
    )

    presupuesto.iva_total_discriminado = (
        iva_total
    )

    presupuesto.total = (
        subtotal_neto
        + iva_total
    )

    presupuesto.save()

    return redirect(
        'presupuesto_detalle',
        pk=presupuesto.id
    )


@login_required
def presupuesto_editar_view(
    request,
    pk
):

    presupuesto = get_object_or_404(
        Presupuesto,
        pk=pk
    )

    if request.method == 'POST':

        try:

            data = json.loads(
                request.body
            )

            cliente_id = data.get(
                'cliente_id'
            )

            detalles_data = data.get(
                'detalles',
                []
            )

            cliente = get_object_or_404(
                Cliente,
                id=cliente_id
            )

            presupuesto.cliente = cliente

            presupuesto.detalles.all().delete()

            subtotal_neto = Decimal('0.00')
            costo_total = Decimal('0.00')

            iva_dict = {}

            for item in detalles_data:

                producto = get_object_or_404(
                    Producto,
                    id=item['producto_id']
                )

                cantidad = Decimal(
                    str(item['cantidad'])
                )

                precio_unitario = (
                    producto.precio
                )

                DetallePresupuesto.objects.create(
                    presupuesto=presupuesto,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario_historico=(
                        precio_unitario
                    )
                )

                linea_subtotal = (
                    cantidad
                    * precio_unitario
                )

                linea_costo = (
                    cantidad
                    * producto.costo
                )

                subtotal_neto += linea_subtotal
                costo_total += linea_costo

                alicuota_str = str(
                    producto.alicuota
                )

                valor_iva = (
                    linea_subtotal
                    * (
                        producto.alicuota
                        / Decimal('100.00')
                    )
                )

                if alicuota_str in iva_dict:

                    iva_dict[alicuota_str] += float(
                        valor_iva
                    )

                else:

                    iva_dict[alicuota_str] = float(
                        valor_iva
                    )

            suma_iva_total = Decimal(
                str(sum(iva_dict.values()))
            )

            presupuesto.costo_total = (
                costo_total
            )

            presupuesto.ganancia_total = (
                subtotal_neto
                - costo_total
            )

            presupuesto.iva_total_discriminado = (
                iva_dict
            )

            presupuesto.total = (
                subtotal_neto
                + suma_iva_total
            )

            presupuesto.save()

            return JsonResponse({
                'status': 'success',
                'presupuesto_id': presupuesto.id
            })

        except Exception as e:

            return JsonResponse(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=400
            )

    clientes = Cliente.objects.all()

    detalles_iniciales = []

    for detalle in presupuesto.detalles.all():

        detalles_iniciales.append({
            'producto_id': detalle.producto.id,
            'nombre': detalle.producto.nombre,
            'precio': float(
                detalle.precio_unitario_historico
            ),
            'alicuota': float(
                detalle.producto.alicuota
            ),
            'cantidad': float(
                detalle.cantidad
            )
        })

    context = {
        'presupuesto': presupuesto,
        'clientes': clientes,
        'detalles_iniciales': json.dumps(
            detalles_iniciales
        ),
        'es_edicion': True
    }

    return render(
        request,
        'pos_presupuesto.html',
        context
    )


# ============================================================
# CONVERTIR PRESUPUESTO EN VENTA
# ============================================================

@login_required
def presupuesto_convertir_view(
    request,
    pk
):

    presupuesto = get_object_or_404(
        Presupuesto,
        pk=pk
    )

    if (
        hasattr(presupuesto, 'venta_asociada')
        and presupuesto.venta_asociada
    ):

        messages.warning(
            request,
            "Este presupuesto ya cuenta con una venta generada."
        )

        return redirect(
            'presupuesto_detalle',
            pk=pk
        )

    punto_venta_tenant = getattr(
        request.tenant,
        'punto_venta',
        '0001'
    )

    ultima_venta = (
        Venta.objects
        .filter(
            cliente=presupuesto.cliente
        )
        .order_by('-fecha')
        .first()
    )

    if ultima_venta and ultima_venta.receptor:

        receptor_sugerido = (
            ultima_venta.receptor
        )

    else:

        receptor_sugerido = (
            str(presupuesto.cliente)
            if presupuesto.cliente
            else "Consumidor Final"
        )

    if request.method == 'POST':

        post_data = request.POST.copy()

        post_data['receptor'] = (
            receptor_sugerido
        )

        post_data['punto_venta'] = (
            punto_venta_tenant
        )

        form = VentaConEnvioForm(
            post_data
        )

        if form.is_valid():

            try:

                with transaction.atomic():

                    venta = form.save(
                        commit=False
                    )

                    venta.presupuesto = (
                        presupuesto
                    )

                    venta.vendedor = (
                        request.user
                    )

                    venta.cliente = (
                        presupuesto.cliente
                    )

                    venta.receptor = (
                        receptor_sugerido
                    )

                    venta.punto_venta = (
                        punto_venta_tenant
                    )

                    venta.costo_total = (
                        presupuesto.costo_total
                    )

                    venta.ganancia_total = (
                        presupuesto.ganancia_total
                    )

                    venta.iva_total_discriminado = (
                        presupuesto.iva_total_discriminado
                    )

                    costo_envio = (
                        form.cleaned_data.get(
                            'costo_envio',
                            0
                        )
                        or 0
                    )

                    requiere_envio = (
                        form.cleaned_data.get(
                            'requiere_envio'
                        )
                    )

                    venta.costo_envio = (
                        costo_envio
                        if requiere_envio
                        else 0
                    )

                    venta.totales = (
                        presupuesto.total
                        + (
                            costo_envio
                            if requiere_envio
                            else 0
                        )
                    )

                    venta.save()

                    for detalle_presupuesto in (
                        presupuesto.detalles
                        .select_related('producto')
                        .all()
                    ):

                        DetalleVenta.objects.create(
                            venta=venta,
                            producto=(
                                detalle_presupuesto.producto
                            ),
                            cantidad=(
                                detalle_presupuesto.cantidad
                            ),
                            precio_unitario_historico=(
                                detalle_presupuesto
                                .precio_unitario_historico
                            )
                        )

                        producto = (
                            detalle_presupuesto.producto
                        )

                        if (
                            hasattr(
                                producto,
                                'stock_actual'
                            )
                            and producto.stock_actual
                            is not None
                        ):

                            producto.stock_actual -= (
                                detalle_presupuesto.cantidad
                            )

                            producto.save()

                    if requiere_envio:

                        Envio.objects.create(
                            venta=venta,
                            fecha_programada=(
                                form.cleaned_data.get(
                                    'fecha_programada'
                                )
                                or presupuesto.fecha_entrega
                                or timezone.now().date()
                            ),
                            estado='P',
                            vehiculo=(
                                form.cleaned_data.get(
                                    'vehiculo'
                                )
                            ),
                            chofer=(
                                form.cleaned_data.get(
                                    'chofer'
                                )
                            ),
                            direccion_entrega=(
                                form.cleaned_data.get(
                                    'direccion_entrega'
                                )
                                or (
                                    presupuesto.cliente.direcciones
                                    if presupuesto.cliente
                                    else "Retira en local"
                                )
                            ),
                            observaciones=(
                                form.cleaned_data.get(
                                    'observaciones_envio'
                                )
                            )
                        )

                messages.success(
                    request,
                    f'¡Venta #{venta.id} registrada con éxito y stock descontado!'
                )

                return redirect(
                    'presupuesto_detalle',
                    pk=pk
                )

            except Exception as e:

                messages.error(
                    request,
                    f'Ocurrió un error interno al procesar la venta: {e}'
                )

        else:

            messages.error(
                request,
                "Por favor, revisa los datos del formulario."
            )

    else:

        form = VentaConEnvioForm(
            initial={
                'receptor': receptor_sugerido,
                'punto_venta': punto_venta_tenant,
                'requiere_envio': False,
                'direccion_entrega': (
                    presupuesto.cliente.direcciones
                    if presupuesto.cliente
                    else ""
                )
            }
        )

    return render(
        request,
        'partials/modal_convertir_venta.html',
        {
            'form': form,
            'presupuesto': presupuesto
        }
    )


# ============================================================
# VENTAS
# ============================================================

@login_required
def ventas_view(request):

    query = request.GET.get('q', '')
    fecha_desde = request.GET.get(
        'fecha_desde',
        ''
    )
    fecha_hasta = request.GET.get(
        'fecha_hasta',
        ''
    )
    cliente_id = request.GET.get(
        'cliente_id',
        ''
    )
    vendedor_id = request.GET.get(
        'vendedor_id',
        ''
    )
    estado_envio = request.GET.get(
        'estado_envio',
        ''
    )

    ventas = (
        Venta.objects
        .select_related(
            'cliente',
            'vendedor',
            'envio'
        )
        .order_by('-fecha')
    )

    if query:

        ventas = ventas.filter(
            Q(receptor__icontains=query)
            | Q(id__icontains=query)
            | Q(cae__icontains=query)
        )

    if fecha_desde:

        ventas = ventas.filter(
            fecha__date__gte=fecha_desde
        )

    if fecha_hasta:

        ventas = ventas.filter(
            fecha__date__lte=fecha_hasta
        )

    if cliente_id:

        ventas = ventas.filter(
            cliente_id=cliente_id
        )

    if vendedor_id:

        ventas = ventas.filter(
            vendedor_id=vendedor_id
        )

    if estado_envio:

        if estado_envio == 'SIN_ENVIO':

            ventas = ventas.filter(
                envio__isnull=True
            )

        else:

            ventas = ventas.filter(
                envio__estado=estado_envio
            )

    paginator = Paginator(
        ventas,
        15
    )

    page_number = request.GET.get(
        'page'
    )

    page_obj = paginator.get_page(
        page_number
    )

    User = get_user_model()

    context = {
        'page_obj': page_obj,
        'query': query,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'cliente_id': cliente_id,
        'vendedor_id': vendedor_id,
        'estado_envio': estado_envio,
        'clientes': Cliente.objects.all().order_by('nombre'),
        'vendedores': User.objects.filter(
            is_active=True
        ).order_by('username'),
        'estados_envio': Envio.ESTADO_CHOICES,
    }

    if request.headers.get('HX-Request'):

        return render(
            request,
            'partials/tabla_ventas.html',
            context
        )

    return render(
        request,
        'ventas.html',
        context
    )


@login_required
def venta_detalle_view(request, pk):

    venta = get_object_or_404(
        Venta.objects.select_related(
            'cliente',
            'vendedor',
            'presupuesto'
        ),
        pk=pk
    )

    detalles = []

    if venta.presupuesto:

        detalles = (
            venta.presupuesto
            .detalles
            .select_related('producto')
            .all()
        )

    return render(
        request,
        'venta_detalle.html',
        {
            'venta': venta,
            'detalles': detalles,
        }
    )


# ============================================================
# ENVÍOS
# ============================================================

@login_required
def envio_crear_editar_view(
    request,
    venta_id
):

    venta = get_object_or_404(
        Venta,
        id=venta_id
    )

    envio = getattr(
        venta,
        'envio',
        None
    )

    if request.method == 'POST':

        form = EnvioForm(
            request.POST,
            instance=envio
        )

        if form.is_valid():

            nuevo_envio = form.save(
                commit=False
            )

            nuevo_envio.venta = venta
            nuevo_envio.save()

            return HttpResponse(
                '<script>window.location.reload();</script>'
            )

    else:

        initial_data = {}

        if (
            not envio
            and venta.cliente
            and venta.cliente.direcciones
        ):

            initial_data[
                'direccion_entrega'
            ] = venta.cliente.direcciones

        form = EnvioForm(
            instance=envio,
            initial=initial_data
        )

    return render(
        request,
        'partials/modal_envio.html',
        {
            'form': form,
            'venta': venta,
            'envio': envio
        }
    )


@login_required
def envios_pendientes_view(request):

    envios = (
        Envio.objects
        .exclude(
            estado__in=['E', 'X']
        )
        .select_related(
            'venta__cliente',
            'chofer',
            'vehiculo'
        )
        .order_by(
            'fecha_programada'
        )
    )

    context = {
        'envios': envios,
        'estados': Envio.ESTADO_CHOICES,
    }

    return render(
        request,
        'envios.html',
        context
    )


@login_required
def cambiar_estado_envio(
    request,
    pk
):

    if request.method == 'POST':

        envio = get_object_or_404(
            Envio,
            pk=pk
        )

        nuevo_estado = request.POST.get(
            'estado'
        )

        if nuevo_estado in dict(
            Envio.ESTADO_CHOICES
        ):

            envio.estado = nuevo_estado
            envio.save()

        return render(
            request,
            'partials/badge_estado_envio.html',
            {
                'envio': envio,
                'estados': Envio.ESTADO_CHOICES
            }
        )

    return HttpResponse(
        status=405
    )


# ============================================================
# VEHÍCULOS
# ============================================================

@login_required
def vehiculos_view(request):

    vehiculos = Vehiculo.objects.all()

    form = VehiculoForm(
        request.POST or None
    )

    if (
        request.method == 'POST'
        and form.is_valid()
    ):

        form.save()

        return redirect(
            'vehiculos_list'
        )

    return render(
        request,
        'vehiculos.html',
        {
            'vehiculos': vehiculos,
            'form': form
        }
    )


# ============================================================
# CHOFERES
# ============================================================

@login_required
def choferes_view(request):

    choferes = Chofer.objects.all()

    form = ChoferForm(
        request.POST or None
    )

    if (
        request.method == 'POST'
        and form.is_valid()
    ):

        form.save()

        return redirect(
            'choferes_list'
        )

    return render(
        request,
        'choferes.html',
        {
            'choferes': choferes,
            'form': form
        }
    )


# ============================================================
# CLIENTE - DETALLE
# ============================================================

@login_required
def cliente_detalle_view(
    request,
    pk
):

    cliente = get_object_or_404(
        Cliente,
        pk=pk
    )

    pedidos = (
        Venta.objects
        .filter(cliente=cliente)
        .select_related(
            'vendedor',
            'envio'
        )
        .order_by('-fecha')
    )

    if request.method == 'POST':

        form = ClienteForm(
            request.POST,
            instance=cliente
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Datos del cliente actualizados correctamente.'
            )

            return redirect(
                'cliente_detalle',
                pk=cliente.pk
            )

    else:

        form = ClienteForm(
            instance=cliente
        )

    context = {
        'cliente': cliente,
        'pedidos': pedidos,
        'form': form,
    }

    return render(
        request,
        'cliente_detalle.html',
        context
    )


# ============================================================
# INFORMES DE GERENCIA
# ============================================================

@login_required
def informes_gerencia_view(request):

    fecha_inicio = request.GET.get(
        'fecha_inicio'
    )

    fecha_fin = request.GET.get(
        'fecha_fin'
    )

    ventas_qs = Venta.objects.all()

    if fecha_inicio:

        ventas_qs = ventas_qs.filter(
            fecha__date__gte=fecha_inicio
        )

    if fecha_fin:

        ventas_qs = ventas_qs.filter(
            fecha__date__lte=fecha_fin
        )

    resumen_periodo = ventas_qs.aggregate(
        total_facturado=Sum('totales'),
        cantidad_ventas=Count('id')
    )

    ventas_diarias = (
        ventas_qs
        .annotate(
            dia=TruncDay('fecha')
        )
        .values('dia')
        .annotate(
            total_dia=Sum('totales'),
            cantidad=Count('id')
        )
        .order_by('-dia')
    )

    totales_mensuales = (
        Venta.objects
        .all()
        .annotate(
            mes=TruncMonth('fecha')
        )
        .values('mes')
        .annotate(
            total_mes=Sum('totales'),
            cantidad=Count('id')
        )
        .order_by('-mes')
    )

    context = {
        'resumen_periodo': resumen_periodo,
        'ventas_diarias': ventas_diarias,
        'totales_mensuales': totales_mensuales,
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
    }

    return render(
        request,
        'informes.html',
        context
    )


# ============================================================
# FACTURA PDF
# ============================================================

@login_required
def descargar_factura_pdf(
    request,
    pk
):

    venta = get_object_or_404(
        Venta.objects.select_related(
            'cliente',
            'presupuesto'
        ),
        pk=pk
    )

    detalles = []

    if venta.presupuesto:

        detalles = (
            venta.presupuesto
            .detalles
            .select_related('producto')
            .all()
        )

    context = {
        'venta': venta,
        'detalles': detalles,
    }

    html_string = render_to_string(
        'pdf_factura.html',
        context
    )

    response = HttpResponse(
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = (
        f'inline; '
        f'filename="Factura_'
        f'{venta.punto_venta}_'
        f'{venta.id}.pdf"'
    )

    pisa_status = pisa.CreatePDF(
        html_string,
        dest=response
    )

    if pisa_status.err:

        return HttpResponse(
            'Tuvimos un error al generar el PDF '
            f'<pre>{html_string}</pre>'
        )

    return response


# ============================================================
# CHATBOT - GEMINI
# ============================================================

genai.configure(
    api_key=settings.GEMINI_API_KEY
)


@login_required
def chatbot_procesar_view(request):

    if request.method == 'POST':

        mensaje_usuario = request.POST.get(
            'mensaje',
            ''
        )

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
        {{
            "nombre": "nombre limpio del producto",
            "cantidad": 1.0
        }}
    ],
    "respuesta_bot": "Si la intención es 'general', escribe aquí tu respuesta conversacional amigable. Si no, déjalo en null."
}}

Mensaje del usuario: "{mensaje_usuario}"
"""

        try:

            model = genai.GenerativeModel(
                'gemini-flash-latest'
            )

            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json"
                }
            )

            data = json.loads(
                response.text
            )

            intencion = data.get(
                'intencion'
            )

            productos_json = data.get(
                'productos',
                []
            )

            html_respuesta = ""

            # ------------------------------------------------
            # CREAR PRESUPUESTO
            # ------------------------------------------------

            if intencion == 'crear_presupuesto':

                nombre_cliente = data.get(
                    'cliente'
                )

                cliente_obj = (
                    Cliente.objects
                    .filter(
                        nombre__icontains=nombre_cliente
                    )
                    .first()
                    if nombre_cliente
                    else None
                )

                if not cliente_obj:

                    cliente_obj = (
                        Cliente.objects
                        .filter(
                            condicion_fiscal='CF'
                        )
                        .first()
                    )

                presupuesto = (
                    Presupuesto.objects.create(
                        cliente=cliente_obj,
                        presupuestante=request.user,
                        costo_total=0,
                        ganancia_total=0,
                        total=0
                    )
                )

                total_presupuesto = Decimal(
                    '0.00'
                )

                items_agregados = []
                errores = []

                for prod_data in productos_json:

                    prod_nombre = prod_data.get(
                        'nombre',
                        ''
                    )

                    cant = Decimal(
                        str(
                            prod_data.get(
                                'cantidad',
                                1
                            )
                        )
                    )

                    producto_obj = (
                        Producto.objects
                        .filter(
                            nombre__icontains=prod_nombre
                        )
                        .first()
                    )

                    if producto_obj:

                        precio_u = getattr(
                            producto_obj,
                            'precio',
                            Decimal('0.00')
                        )

                        DetallePresupuesto.objects.create(
                            presupuesto=presupuesto,
                            producto=producto_obj,
                            cantidad=cant,
                            precio_unitario_historico=precio_u
                        )

                        total_presupuesto += (
                            cant * precio_u
                        )

                        items_agregados.append(
                            f"{cant} x {producto_obj.nombre}"
                        )

                    else:

                        errores.append(
                            prod_nombre
                        )

                presupuesto.total = (
                    total_presupuesto
                )

                presupuesto.save()

                html_respuesta = (
                    f"¡Presupuesto creado para "
                    f"<strong>{cliente_obj or 'Consumidor Final'}</strong>!"
                    f"<br><br>"
                )

                html_respuesta += (
                    "<ul class='list-disc pl-4 mb-2'>"
                    "<li>"
                    + "</li><li>".join(
                        items_agregados
                    )
                    + "</li></ul>"
                )

                if errores:

                    html_respuesta += (
                        f"<p class='text-amber-500 text-xs'>"
                        f"No encontré: "
                        f"{', '.join(errores)}"
                        f"</p>"
                    )

                html_respuesta += (
                    f"<div class='mt-2 font-black'>"
                    f"Total: ${total_presupuesto:,.2f}"
                    f"</div>"
                )

                html_respuesta += (
                    f"<a href='{reverse('presupuesto_detalle', args=[presupuesto.id])}' "
                    f"class='mt-3 inline-block px-4 py-2 bg-accent text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition'>"
                    f"Abrir Presupuesto #{presupuesto.id}"
                    f"</a>"
                )

            # ------------------------------------------------
            # CONSULTAR STOCK
            # ------------------------------------------------

            elif intencion == 'consultar_stock':

                html_respuesta = (
                    "<strong>Consulta de Stock:</strong>"
                    "<br>"
                    "<ul class='mt-2 space-y-1'>"
                )

                for prod_data in productos_json:

                    producto_obj = (
                        Producto.objects
                        .filter(
                            nombre__icontains=prod_data.get(
                                'nombre'
                            )
                        )
                        .first()
                    )

                    if producto_obj:

                        stock = getattr(
                            producto_obj,
                            'stock_actual',
                            0
                        )

                        color = (
                            "text-emerald-500"
                            if stock > 0
                            else "text-red-500 font-bold"
                        )

                        html_respuesta += (
                            f"<li>"
                            f"{producto_obj.nombre}: "
                            f"<span class='{color}'>"
                            f"{stock} unidades"
                            f"</span>"
                            f"</li>"
                        )

                    else:

                        html_respuesta += (
                            f"<li>"
                            f"<span class='text-gray-400'>"
                            f"No encontré el producto "
                            f"'{prod_data.get('nombre')}'"
                            f"</span>"
                            f"</li>"
                        )

                html_respuesta += "</ul>"

            # ------------------------------------------------
            # CONSULTAR PRECIO
            # ------------------------------------------------

            elif intencion == 'consultar_precio':

                html_respuesta = (
                    "<strong>Consulta de Precios (Sin IVA):</strong>"
                    "<br>"
                    "<ul class='mt-2 space-y-1'>"
                )

                for prod_data in productos_json:

                    producto_obj = (
                        Producto.objects
                        .filter(
                            nombre__icontains=prod_data.get(
                                'nombre'
                            )
                        )
                        .first()
                    )

                    if producto_obj:

                        precio = getattr(
                            producto_obj,
                            'precio',
                            0
                        )

                        html_respuesta += (
                            f"<li>"
                            f"{producto_obj.nombre}: "
                            f"<strong>"
                            f"${precio:,.2f}"
                            f"</strong>"
                            f"</li>"
                        )

                    else:

                        html_respuesta += (
                            f"<li>"
                            f"<span class='text-gray-400'>"
                            f"No encontré el producto "
                            f"'{prod_data.get('nombre')}'"
                            f"</span>"
                            f"</li>"
                        )

                html_respuesta += "</ul>"

            # ------------------------------------------------
            # GENERAL
            # ------------------------------------------------

            else:

                html_respuesta = data.get(
                    'respuesta_bot',
                    "¡Hola! ¿En qué te puedo ayudar hoy con el sistema?"
                )

        except Exception as e:

            html_respuesta = (
                f"<span class='text-rose-500'>"
                f"Ocurrió un error procesando tu pedido: "
                f"{str(e)}"
                f"</span>"
            )

        return render(
            request,
            'partials/chat_message.html',
            {
                'mensaje_usuario': mensaje_usuario,
                'respuesta_bot': html_respuesta
            }
        )

    return HttpResponse(
        "Método no permitido",
        status=405
    )
