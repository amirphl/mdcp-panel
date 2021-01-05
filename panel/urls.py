from django.urls import path
from .views import create_list_job, retrieve_job, upload_partial_result

urlpatterns = [
    path('jobs/', create_list_job, name='create_list_job'),
    path('jobs/<uuid:id>', retrieve_job, name='retrieve_job'),
    path('jobs/<uuid:id>/partial-results/', upload_partial_result, name='create_partial_result'),
]
