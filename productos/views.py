from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import Categoria, Subcategoria, Proveedor, Producto
from .serializers import CategoriaSerializer, SubcategoriaSerializer, ProveedorSerializer, ProductoSerializer

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class SubcategoriaViewSet(viewsets.ModelViewSet):
    queryset = Subcategoria.objects.all()
    serializer_class = SubcategoriaSerializer

class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from .models import Producto, Categoria, Subcategoria
from .forms import ProductoForm

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
def proveedores_view(request):
    proveedores = Proveedor.objects.all()
    form = ProveedorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('proveedores_list')
    return render(request, 'proveedores.html', {'proveedores': proveedores, 'form': form})

# --- CATEGORÍAS Y SUBCATEGORÍAS ---
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

def proveedor_eliminar_view(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        return redirect('proveedores_list')
    return redirect('proveedor_detalle', pk=pk)

# --- CATEGORÍAS Y SUBCATEGORÍAS: ELIMINAR Y EDITAR ---
def categoria_eliminar_view(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    categoria.delete()
    return redirect('categorias_list')

def subcategoria_eliminar_view(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)
    subcategoria.delete()
    return redirect('categorias_list')