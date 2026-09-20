from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Empleado

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        # Evitamos que la contraseña se envíe en las respuestas
        extra_kwargs = {'password': {'write_only': True}}

class EmpleadoSerializer(serializers.ModelSerializer):
    # Anidamos los datos del usuario de Django para tener el email y nombre completo
    usuario_datos = UserSerializer(source='usuario', read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = Empleado
        fields = ['id', 'usuario', 'usuario_datos', 'rol', 'rol_display', 'legajo', 'telefono', 'fecha_ingreso', 'activo']