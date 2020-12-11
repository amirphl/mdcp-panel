from django.http.response import HttpResponse
from panel.models import JarFile
from panel.forms import JarFileForm
from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect


def upload_jar(request):
    if request.method == 'POST':
        form = JarFileForm(request.POST, request.FILES)
        if form.is_valid():
            new_jar = JarFile(jarfile=request.FILES['jarfile'])
            new_jar.save()
            return HttpResponse("ok")
    else:
        form = JarFileForm()

    return render(request, 'upload_jar.html')
