# aidy/services/products.py

from productos.models import Producto


def buscar_productos(query):

    return list(
        Producto.objects
        .filter(
            nombre__icontains=query
        )
        .order_by("nombre")[:10]
    )


def producto_data(producto):

    return {
        "id": producto.id,
        "sku": producto.sku,
        "codigo_barras": producto.codigo_barras,
        "nombre": producto.nombre,
        "costo": str(producto.costo),
        "precio": str(producto.precio),
        "stock": str(producto.stock_actual),
        "stock_critico": str(producto.stock_critico),
        "unidad_medida": producto.unidad_medida,
        "alicuota": str(producto.alicuota),
    }