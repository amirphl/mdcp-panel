from django.contrib import admin
from panel.models import Job
from panel.models import JobPartialResult
# Register your models here.

admin.site.register(Job)
admin.site.register(JobPartialResult)
