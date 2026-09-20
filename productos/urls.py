from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, SubcategoriaViewSet, ProveedorViewSet, ProductoViewSet

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet)
router.register(r'subcategorias', SubcategoriaViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'productos', ProductoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]