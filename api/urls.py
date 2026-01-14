from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Crear el router y registrar los ViewSets
router = DefaultRouter()
router.register(r'register', views.RegisterViewSet, basename='register')
router.register(r'categorias', views.CategoriaViewSet)
router.register(r'llaveros', views.LlaveroViewSet)
router.register(r'clientes', views.ClienteViewSet)
router.register(r'materiales', views.MaterialViewSet)
router.register(r'llaveros-materiales', views.LlaveroMaterialViewSet)
router.register(r'pedidos', views.PedidoViewSet)
router.register(r'detalle-pedidos', views.DetallePedidoViewSet)

urlpatterns = [
    # 1. Rutas del Router (CRUD automático)
    path('', include(router.urls)),

    # 2. Rutas del Login (IGUAL QUE EN ANDROID)
    path('android/login/', views.android_login_view, name='android_login'),
    
    # Por eso aquí ponemos: 'auth/google/'
    path('auth/google/', views.login_with_google, name='google_login'),

    # 3. Listas Simples
    path('lista-categorias/', views.CategoriaList.as_view(), name='categoria-list'),
    path('products/<int:category_id>/', views.ProductoList.as_view(), name='producto-list'),
]