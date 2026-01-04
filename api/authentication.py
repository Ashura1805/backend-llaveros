import os
import json
import firebase_admin
from firebase_admin import auth, credentials
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.conf import settings # Importamos settings para hallar la ruta exacta

# --- INICIALIZACIÓN SEGURA DE FIREBASE ---
try:
    # Intenta inicializar solo si aún no ha sido inicializado.
    if not firebase_admin._apps:
        
        # 1. BUSCAR EN VARIABLES DE ENTORNO (Para Railway/Nube)
        firebase_env = os.environ.get('FIREBASE_CREDENTIALS')
        
        if firebase_env:
            # Si estamos en la nube, leemos la variable
            cred_dict = json.loads(firebase_env)
            cred = credentials.Certificate(cred_dict)
            print("--- FIREBASE: Iniciado desde Variable de Entorno (Nube) ---")
            
        else:
            # 2. BUSCAR ARCHIVO LOCAL (Para tu PC)
            # Usamos BASE_DIR para encontrar el archivo en la raíz del proyecto siempre
            file_path = settings.BASE_DIR / 'serviceAccountKey.json'
            
            if os.path.exists(file_path):
                cred = credentials.Certificate(str(file_path))
                print(f"--- FIREBASE: Iniciado desde Archivo Local: {file_path} ---")
            else:
                print("--- ALERTA: No se encontró serviceAccountKey.json ni variable FIREBASE_CREDENTIALS ---")
                cred = None

        if cred:
            firebase_admin.initialize_app(cred)

except Exception as e:
    print(f"--- ERROR CRÍTICO FIREBASE: {e} ---")


# --- CLASE DE AUTENTICACIÓN ---
class FirebaseAuthentication(BaseAuthentication):
    """
    Clase de autenticación para Django REST Framework que verifica el token ID de Firebase.
    """
    def authenticate(self, request):
        # 1. Obtener el encabezado de autorización
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None 

        # Esperamos el formato: "Bearer <token>"
        try:
            token_type, firebase_token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                return None
        except ValueError:
            return None 

        # 2. Verificar el token con Firebase
        try:
            decoded_token = auth.verify_id_token(firebase_token)
            uid = decoded_token['uid']
        except Exception as e:
            raise AuthenticationFailed(f'Token de Firebase inválido: {e}')

        # 3. Sincronizar usuario en tu base de datos MySQL (Railway)
        User = get_user_model()
        try:
            user = User.objects.get(username=uid) 
        except User.DoesNotExist:
            # Crear usuario nuevo si no existe
            user = User.objects.create_user(
                username=uid, 
                email=decoded_token.get('email', f'{uid}@noemail.com'),
                password=None 
            )
            print(f"Usuario {uid} creado y sincronizado en MySQL.")
            
        return (user, decoded_token)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'