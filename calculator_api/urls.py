from django.urls import path
from . import views

urlpatterns = [
    path('calculate/', views.calculate_api, name='calculate'),
    path('advanced/', views.advanced_api, name='advanced'),
    path('modes/', views.modes_api, name='modes'),
    path('history/', views.history_api, name='history'),
    path('clear-history/', views.clear_history_api, name='clear_history'),
    path('validate/', views.validate_api, name='validate'),
    path('ocr/', views.ocr_api, name='ocr'),
]
