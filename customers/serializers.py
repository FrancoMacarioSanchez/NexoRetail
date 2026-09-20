from rest_framework import serializers
from .models import Client, Domain

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['id', 'domain', 'is_primary']

class ClientSerializer(serializers.ModelSerializer):
    # Mostramos los dominios asociados al cliente de forma anidada (solo lectura)
    domains = DomainSerializer(many=True, read_only=True, source='domain_set')

    class Meta:
        model = Client
        fields = ['id', 'schema_name', 'nombre', 'cuit', 'telefono', 'email', 'activo', 'creado_el', 'pagado_hasta', 'domains']