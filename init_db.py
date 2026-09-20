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
        
        # Pasamos los campos obligatorios según tu modelo: schema_name y nombre
        tenant = Client(
            schema_name='public',
            nombre='NexoRetail Global'
        )
        tenant.save()

        # Creamos el dominio asociado (Asegúrate de poner tu URL de Render exacta aquí)
        domain = Domain(
            domain='nexoretail.onrender.com', 
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