from django.contrib import admin
from .models import Categoria, Subcategoria, Producto

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Subcategoria)
admin.site.register(Producto)