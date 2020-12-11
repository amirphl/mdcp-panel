from django.db import models

# Create your models here.

from django.db import models


class JarFile(models.Model):
    jarfile = models.FileField(upload_to='jarfiles/%Y/%m/%d')
