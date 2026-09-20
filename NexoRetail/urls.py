from django.contrib import admin
from django.urls import path, include
from core.views import dashboard_view
from productos.views import inventario_view, producto_crear_view, producto_crear_editar_view, proveedores_view,categorias_view,proveedor_detalle_view, proveedor_eliminar_view, categoria_eliminar_view,subcategoria_eliminar_view
from sales.views import clientes_view, cliente_crear_editar_view,  pos_presupuesto_view, presupuestos_view, api_detalle_cliente, api_buscar_productos, presupuesto_detalle_view, actualizar_precios_presupuesto, presupuesto_editar_view,presupuesto_convertir_view, ventas_view,venta_detalle_view, envio_crear_editar_view,cliente_detalle_view
from sales.views import envios_pendientes_view,cambiar_estado_envio, vehiculos_view,choferes_view, informes_gerencia_view,descargar_factura_pdf,chatbot_procesar_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('inventario/', inventario_view, name='inventario'),
    path('inventario/crear', producto_crear_view, name='producto_crear' ),
    path('producto/editar/<int:pk>/', producto_crear_editar_view, name='producto_editar'),
    # Proveedores
    path('proveedores/', proveedores_view, name='proveedores_list'),
    path('proveedores/<int:pk>/', proveedor_detalle_view, name='proveedor_detalle'),
    path('proveedores/<int:pk>/eliminar/', proveedor_eliminar_view, name='proveedor_eliminar'),
    
    # Categorías y Subcategorías
    path('categorias/', categorias_view, name='categorias_list'),
    path('categorias/<int:pk>/eliminar/', categoria_eliminar_view, name='categoria_eliminar'),
    path('subcategorias/<int:pk>/eliminar/', subcategoria_eliminar_view, name='subcategoria_eliminar'),
    
    path('clientes/', clientes_view, name='clientes'),
    path('clientes/nuevo/', cliente_crear_editar_view, name='cliente_crear'),
    path('clientes/editar/<int:pk>/', cliente_crear_editar_view, name='cliente_editar'),
    path('clientes/<int:pk>/', cliente_detalle_view, name='cliente_detalle'),
    
    path('presupuestos/', presupuestos_view, name='presupuestos'),
    path('presupuestos/nuevo/',  pos_presupuesto_view, name='pos_presupuesto'),
    path('presupuestos/<int:pk>/', presupuesto_detalle_view, name='presupuesto_detalle'),
    path('presupuesto/<int:presupuesto_id>/actualizar-precios/', actualizar_precios_presupuesto, name='actualizar_precios_presupuesto'),
    path('presupuestos/editar/<int:pk>/', presupuesto_editar_view, name='presupuesto_editar'),
    path('presupuestos/<int:pk>/convertir/', presupuesto_convertir_view, name='presupuesto_convertir'),
    
    path('ventas/<int:venta_id>/envio/', envio_crear_editar_view, name='envio_crear_editar'),
    path('ventas/', ventas_view, name='ventas'),
    path('ventas/<int:pk>/pdf/', descargar_factura_pdf, name='descargar_factura_pdf'),
    path('ventas/<int:pk>/', venta_detalle_view, name='venta_detalle'),
    
    path('envios/', envios_pendientes_view, name='envios_pendientes'),
    path('envios/<int:pk>/cambiar-estado/', cambiar_estado_envio, name='cambiar_estado_envio'),
    path('vehiculos/', vehiculos_view, name='vehiculos_list'),
    path('choferes/', choferes_view, name='choferes_list'),
    
    
    path('informes/', informes_gerencia_view, name='informes_gerencia'),
    
    # Endpoints de la API del SaaS
    path('api/inventario/', include('productos.urls')),
    path('api/comercial/', include('sales.urls')),
    path('api/recursos-humanos/', include('core.urls')),
    path('api/clientes/<int:pk>/detalles/', api_detalle_cliente, name='api_detalle_cliente'),
    path('api/buscar-productos/', api_buscar_productos, name='api_buscar_productos'),
    
    
    path('chatbot/procesar/', chatbot_procesar_view, name='chatbot_procesar'),
]