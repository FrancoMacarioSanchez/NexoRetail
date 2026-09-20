from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import Empleado
from .serializers import EmpleadoSerializer

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    
from django.shortcuts import render

from django.shortcuts import render
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
import json

# Importa tus modelos (ajusta las rutas según tus apps)
from sales.models import Venta, Presupuesto, Envio
from productos.models import Producto 

def dashboard_view(request):
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 1. KPI: Ventas del Mes y Crecimiento
    ventas_mes = Venta.objects.filter(fecha__gte=inicio_mes).aggregate(total=Sum('totales'))['total'] or 0
    
    hace_30_dias = hoy - timedelta(days=30)
    hace_60_dias = hoy - timedelta(days=60)
    ventas_30_actuales = Venta.objects.filter(fecha__gte=hace_30_dias).aggregate(t=Sum('totales'))['t'] or 0
    ventas_30_anteriores = Venta.objects.filter(fecha__gte=hace_60_dias, fecha__lt=hace_30_dias).aggregate(t=Sum('totales'))['t'] or 1 # Evitar div/0
    
    crecimiento_ventas = ((ventas_30_actuales - ventas_30_anteriores) / ventas_30_anteriores) * 100

    # 2. KPI: Presupuestos activos del mes
    presupuestos_mes = Presupuesto.objects.filter(fecha_creacion__gte=inicio_mes)
    presupuestos_total = presupuestos_mes.aggregate(total=Sum('total'))['total'] or 0
    
    # 3. KPI: Logística de Hoy
    envios_hoy = Envio.objects.filter(fecha_programada=hoy.date())
    envios_camino = envios_hoy.filter(estado='C').count()
    envios_pend = envios_hoy.filter(estado__in=['P', 'E']).count()

    # 4. KPI: Stock Crítico (Asumiendo que Producto tiene stock_actual y stock_minimo)
    stock_critico = Producto.objects.filter(stock_actual__lte=F('stock_critico')).count()

    # 5. Gráfico Chart.js: Evolución de los últimos 7 días
    dias_es = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    labels_grafico = []
    datos_grafico = []
    
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        if i == 0:
            labels_grafico.append("Hoy")
        else:
            labels_grafico.append(dias_es[dia.weekday()])
            
        total_dia = Venta.objects.filter(fecha__date=dia.date()).aggregate(t=Sum('totales'))['t'] or 0
        datos_grafico.append(float(total_dia))

    # 6. Actividad Reciente (Últimas 5 ventas)
    ultimas_ventas = Venta.objects.select_related('vendedor', 'cliente').order_by('-fecha')[:5]

    context = {
        'ventas_mes': ventas_mes,
        'crecimiento_ventas': round(crecimiento_ventas, 1),
        'crecimiento_ventas_abs': round(abs(crecimiento_ventas), 1),
        'es_crecimiento_positivo': crecimiento_ventas >= 0,
        
        'presupuestos_count': presupuestos_mes.count(),
        'presupuestos_total': presupuestos_total,
        
        'envios_hoy_total': envios_hoy.count(),
        'envios_camino': envios_camino,
        'envios_pend': envios_pend,
        
        'stock_critico': stock_critico,
        
        # json.dumps convierte las listas de Python a arreglos compatibles con JavaScript
        'labels_grafico': json.dumps(labels_grafico),
        'datos_grafico': json.dumps(datos_grafico),
        
        'ultimas_ventas': ultimas_ventas,
    }
    
    return render(request, 'dashboard.html', context)