from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, PresupuestoViewSet, DetallePresupuestoViewSet, VentaViewSet, cliente_crear_editar_view, clientes_view, api_buscar_productos,api_detalle_cliente, presupuesto_detalle_view

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'presupuestos', PresupuestoViewSet)
router.register(r'detalles-presupuesto', DetallePresupuestoViewSet)
router.register(r'ventas', VentaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]