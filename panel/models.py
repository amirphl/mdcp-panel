import uuid
from django.db import models
from django.conf import settings

class Job(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, unique=True,
                          default=uuid.uuid4, editable=False)
    executable = models.FileField(upload_to='jobs/%Y/%m/%d/executables/')
    input_file = models.FileField(upload_to='jobs/%Y/%m/%d/input_files/')

class JobPartialResult(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    index = models.IntegerField()
    partial_result_file = models.FileField(upload_to='jobs/%Y/%m/%d/result_files/')
