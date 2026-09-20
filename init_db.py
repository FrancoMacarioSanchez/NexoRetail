import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "NexoRetail.settings")
django.setup()

from customers.models import Client, Domain
from django.contrib.auth import get_user_model

def setup_initial_data():
    # 1. Crear el tenant público si no existe
    if not Client.objects.filter(schema_name='public').exists():
        print("Creando tenant público...")
        tenant = Client(
            schema_name='public',
            name='NexoRetail Global',
            paid_until='2099-12-31',
            on_trial=False
        )
        tenant.save()

        # Usamos un dominio comodín para el esquema público en Render
        domain = Domain(
            domain='nexoretail.onrender.com', # Poné acá la URL que te dio Render (sin https://)
            tenant=tenant,
            is_primary=True
        )
        domain.save()
        print("Tenant público creado exitosamente.")

    # 2. Crear superusuario si no existe
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        print("Creando superusuario...")
        User.objects.create_superuser('admin', 'admin@nexoretail.com', 'admin1234')
        print("Superusuario creado: admin / admin1234")

if __name__ == '__main__':
    setup_initial_data()