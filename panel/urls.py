from django.urls import path
from .views import upload_jar

urlpatterns = [
    path('upload_jar/', upload_jar, name='upload_jar'),
]
