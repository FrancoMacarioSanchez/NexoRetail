import json
from django.db import transaction
import google.generativeai as genai
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

# Create your views here.
from rest_framework import viewsets
from .models import Categoria, Subcategoria, Proveedor, Producto
from .serializers import CategoriaSerializer, SubcategoriaSerializer, ProveedorSerializer, ProductoSerializer
@login_required
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
@login_required
class SubcategoriaViewSet(viewsets.ModelViewSet):
    queryset = Subcategoria.objects.all()
    serializer_class = SubcategoriaSerializer
@login_required
class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
@login_required
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from .models import Producto, Categoria, Subcategoria
from .forms import ProductoForm
@login_required
def inventario_view(request):
    query = request.GET.get('q', '')
    cat_id = request.GET.get('categoria', '')
    subcat_id = request.GET.get('subcategoria', '')
    stock_status = request.GET.get('stock', '')
    
    productos = Producto.objects.all().order_by('-id')
    
    if query:
        productos = productos.filter(nombre__icontains=query) | productos.filter(sku__icontains=query)
    if cat_id:
        productos = productos.filter(categoria_id=cat_id)
    if subcat_id:
        productos = productos.filter(subcategoria_id=subcat_id)
        
    if stock_status == 'critico':
        # Filtramos donde stock_actual es menor o igual al stock_critico
        productos = [p for p in productos if p.stock_actual <= p.stock_critico]
    elif stock_status == 'normal':
        productos = [p for p in productos if p.stock_actual > p.stock_critico]

    paginator = Paginator(productos, 10) # 10 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'categoria_seleccionada': cat_id,
        'subcategoria_seleccionada': subcat_id,
        'stock_seleccionado': stock_status,
        'categorias': Categoria.objects.all(),
        'subcategorias': Subcategoria.objects.all(),
    }
    
    # Si la petición viene de HTMX (al teclear o filtrar), devolvemos solo la tabla
    if request.headers.get('HX-Request'):
        return render(request, 'partials/tabla_productos.html', context)
        
    return render(request, 'inventario.html', context)


# Modificamos la vista existente para que acepte un ID opcional (Edición)
@login_required
def producto_crear_editar_view(request, pk=None):
    if pk:
        producto = get_object_or_404(Producto, pk=pk)
        titulo = "Editar Producto"
    else:
        producto = None
        titulo = "Crear Nuevo Producto"

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            
            continuar = request.POST.get('continuar') == 'true'
            
            if continuar and not pk: # Solo permitimos "guardar y añadir" si estamos creando
                response = render(request, 'partials/modal_producto.html', {'form': ProductoForm(), 'titulo': titulo})
                response['HX-Trigger'] = 'refreshTablaProductos'
                return response
            else:
                response = HttpResponse()
                response['HX-Trigger'] = 'refreshTablaProductos, closeModal'
                return response
    else:
        form = ProductoForm(instance=producto)
        
    return render(request, 'partials/modal_producto.html', {'form': form, 'titulo': titulo, 'producto': producto})

from django.shortcuts import render
from django.http import HttpResponse
from .forms import ProductoForm
@login_required
def producto_crear_view(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            
            continuar = request.POST.get('continuar') == 'true'
            
            if continuar:
                # Retornamos el modal renderizado de nuevo, pero con un form vacío (limpio)
                response = render(request, 'partials/modal_producto.html', {'form': ProductoForm()})
                response['HX-Trigger'] = 'refreshTablaProductos'
                return response
            else:
                # Solo enviamos la señal de cerrar el modal y actualizar la tabla
                response = HttpResponse()
                response['HX-Trigger'] = 'refreshTablaProductos, closeModal'
                return response
    else:
        form = ProductoForm()
        
    return render(request, 'partials/modal_producto.html', {'form': form})

from django.shortcuts import render, redirect
from .models import Proveedor, Categoria, Subcategoria
from .forms import ProveedorForm, CategoriaForm, SubcategoriaForm

# --- PROVEEDORES ---
@login_required
def proveedores_view(request):
    proveedores = Proveedor.objects.all()
    form = ProveedorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('proveedores_list')
    return render(request, 'proveedores.html', {'proveedores': proveedores, 'form': form})

# --- CATEGORÍAS Y SUBCATEGORÍAS ---
@login_required
def categorias_view(request):
    categorias = Categoria.objects.prefetch_related('subcategorias').all()
    cat_form = CategoriaForm(request.POST or None, prefix='cat')
    sub_form = SubcategoriaForm(request.POST or None, prefix='sub')
    
    if request.method == 'POST':
        if 'btn_categoria' in request.POST and cat_form.is_valid():
            cat_form.save()
            return redirect('categorias_list')
        elif 'btn_subcategoria' in request.POST and sub_form.is_valid():
            sub_form.save()
            return redirect('categorias_list')
            
    return render(request, 'categorias.html', {
        'categorias': categorias,
        'cat_form': cat_form,
        'sub_form': sub_form
    })
@login_required
def proveedor_detalle_view(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=proveedor)
    
    if request.method == 'POST' and 'btn_actualizar' in request.POST:
        if form.is_valid():
            form.save()
            return redirect('proveedor_detalle', pk=proveedor.pk)
            
    # Productos que vende este proveedor (gracias al related_name='productos')
    productos_proveedor = proveedor.productos.all()
    
    return render(request, 'proveedor_detalle.html', {
        'proveedor': proveedor,
        'form': form,
        'productos_proveedor': productos_proveedor
    })
@login_required
def proveedor_eliminar_view(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        return redirect('proveedores_list')
    return redirect('proveedor_detalle', pk=pk)

# --- CATEGORÍAS Y SUBCATEGORÍAS: ELIMINAR Y EDITAR ---
@login_required
def categoria_eliminar_view(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    categoria.delete()
    return redirect('categorias_list')
@login_required
def subcategoria_eliminar_view(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)
    subcategoria.delete()
    return redirect('categorias_list')

@login_required
def procesar_factura_ia(request):
    """Recibe la imagen/PDF, consulta a Gemini y devuelve el Modal y el Chat"""
    if request.method == 'POST' and request.FILES.get('archivo_ia'):
        archivo = request.FILES['archivo_ia']
        
        # 1. Gemini AI
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = """
        Analiza esta factura/remito. Devuelve ÚNICAMENTE un array JSON válido:
        [{"sku": "codigo o vacio", "nombre_raw": "nombre", "costo": 0.00, "cantidad": 1}]
        """
        
        try:
            response = model.generate_content(
                [prompt, {"mime_type": archivo.content_type, "data": archivo.read()}],
                generation_config={"response_mime_type": "application/json"}
            )
            datos_ia = json.loads(response.text)
        except Exception as e:
            return HttpResponse(f"<div class='p-3 bg-red-100 text-red-700 rounded-lg text-sm'>Error IA: {str(e)}</div>")

        # 2. Cruzar con Base de Datos
        items_detectados = []
        productos_db = Producto.objects.all().order_by('nombre')
        
        for item in datos_ia:
            sku = item.get('sku', '')
            nombre = item.get('nombre_raw', '')
            
            prod_db = Producto.objects.filter(sku=sku).first() if sku else None
            if not prod_db and nombre:
                prod_db = Producto.objects.filter(nombre__icontains=nombre).first()

            match_exacto = bool(prod_db)
            items_detectados.append({
                'match_exacto': match_exacto,
                'sku': prod_db.sku if match_exacto else sku,
                'nombre_raw': nombre,
                'costo': item.get('costo', 0.0),
                'precio': prod_db.precio if match_exacto else 0.0,
                'cantidad': item.get('cantidad', 1)
            })

        return render(request, 'partials/respuesta_chat_ia.html', {
            'items': items_detectados,
            'productos_db': productos_db,
            'nombre_archivo': archivo.name
        })

    return HttpResponse("Error", status=400)
import json
import uuid

import google.generativeai as genai
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from decimal import Decimal # <-- 1. AGREGA ESTE IMPORT ARRIBA DEL TODO
from .models import Producto
from .forms import ProductoForm # Asegúrate de importar tu formulario
@login_required
def ingreso_stock_view(request):
    """Vista principal"""
    productos = Producto.objects.all().order_by('nombre')
    form_nuevo_producto = ProductoForm() # Pasamos el formulario vacío al modal
    
    return render(request, 'ingreso_stock.html', {
        'productos': productos,
        'form_producto': form_nuevo_producto
    })
@login_required
def crear_producto_ajax(request):
    """Guarda el producto desde el modal sin recargar la página"""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            prod = form.save()
            # Devolvemos un script que actualiza la tabla mágicamente
            script = f"""
            <script>
                // Agregar el nuevo producto a todos los <select> de la tabla
                document.querySelectorAll('.select-producto').forEach(sel => {{
                    let opt = new Option('[{prod.sku}] {prod.nombre}', '{prod.sku}');
                    opt.dataset.costo = '{prod.costo}';
                    opt.dataset.precio = '{prod.precio}';
                    sel.add(opt);
                }});
                alert('✅ Producto "{prod.nombre}" creado exitosamente. Ya puedes seleccionarlo.');
                document.getElementById('modal-nuevo-producto').style.display = 'none';
            </script>
            """
            return HttpResponse(script)
        else:
            # Si hay error (ej: SKU duplicado), mostramos una alerta
            return HttpResponse("<script>alert('❌ Error: Revisa los campos obligatorios o SKUs duplicados.');</script>")
    return HttpResponse("Error", status=400)

@login_required
def guardar_ingreso_stock(request):
    """Guarda las filas finales en la Base de Datos"""
    if request.method == 'POST':
        productos_data = request.POST.getlist('productos_data[]')
        costos = request.POST.getlist('costos[]')
        ventas = request.POST.getlist('ventas[]')
        cantidades = request.POST.getlist('cantidades[]')

        try:
            with transaction.atomic():
                for p_data, c_str, v_str, cant_str in zip(productos_data, costos, ventas, cantidades):
                    
                    # 2. CORRECCIÓN: Usamos Decimal() en lugar de float()
                    costo = Decimal(c_str.replace(',', '.')) if c_str else Decimal('0.00')
                    precio = Decimal(v_str.replace(',', '.')) if v_str else Decimal('0.00')
                    cantidad = Decimal(cant_str.replace(',', '.')) if cant_str else Decimal('0.00')
                    
                    if cantidad <= 0: continue

                    datos = p_data.split('|')
                    modo = datos[0]

                    if modo == 'EXISTENTE':
                        sku = datos[1]
                        if not sku: continue
                        producto = Producto.objects.get(sku=sku)
                        
                        # Ahora ambos son Decimal, la suma funcionará perfectamente
                        producto.stock_actual += cantidad
                        if costo > 0: producto.costo = costo
                        if precio > 0: producto.precio = precio
                        producto.save()

                    elif modo == 'NUEVO':
                        sku = datos[1].strip() or f"PROD-{str(uuid.uuid4())[:8].upper()}"
                        nombre = datos[2].strip()
                        unidad = datos[3].strip() if len(datos) > 3 else 'UN'
                        
                        Producto.objects.create(
                            sku=sku, 
                            nombre=nombre, 
                            unidad_medida=unidad,
                            costo=costo, 
                            precio=precio, 
                            stock_actual=cantidad
                        )

            messages.success(request, f"¡Ingreso guardado con éxito! ({len(productos_data)} filas procesadas)")
        except Exception as e:
            messages.error(request, f"Error al guardar: {str(e)}")
            
    return redirect('ingreso_stock')