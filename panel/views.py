import logging
import uuid
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from panel.models import Job, JobPartialResult
from state_manager import NUM_DEVICES_PER_JOB, submit_job, complete_inprogress_job

logger = logging.getLogger(__name__)
logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)


@login_required
def create_list_job(request):
    if request.method == 'POST':
        try:
            executable = request.FILES['executable']
            assert str(executable)[-4:] == '.jar'
            new_job = Job.objects.create(
                user=request.user,
                executable=request.FILES['executable'],
                input_file=request.FILES['input_file'],
                outputs_merger=request.FILES['outputs_merger'])
            submit_job(new_job)
        except (KeyError, AssertionError):
            return HttpResponse(content="bad request", status=400)
        except Exception as e:
            logger.info(str(e))
            return HttpResponse(content="internal server error", status=503)
        return redirect('/jobs/' + str(new_job.id))
    elif request.method == 'GET':
        jobs = Job.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'index.html', {'jobs': jobs})
    return HttpResponse(content='method not allowed', status=405)


@login_required
def retrieve_job(request, id):
    if request.method == 'GET':
        try:
            job = Job.objects.get(user=request.user, id=id)
            partial_results = JobPartialResult.objects.filter(
                job=job).order_by('index')
        except Job.DoesNotExist:
            return HttpResponse(content='job not found', status=404)
        return render(request, "job.html", context={'executable': job.executable,
                                                    'input_file': job.input_file,
                                                    'partial_results': partial_results,
                                                    'final_result': job.final_result_path,
                                                    })
    return HttpResponse(content='method not allowed', status=405)


def merge_partial_result(job):
    import subprocess
    partial_results = JobPartialResult.objects.filter(job=job)
    args = ['java', '-jar', '/code' + job.outputs_merger.url, ]
    for p in partial_results:
        args.append('/code' + p.partial_result_file.url)
    arr = job.outputs_merger.url.split('/')
    arr[-1] = str(uuid.uuid4()) + '.out'
    res_path = '/'.join(arr)
    job.final_result_path = res_path
    job.save()
    args.append('/code' + res_path)
    logger.info('executing:')
    logger.info(args)
    subprocess.call(args)


@csrf_exempt
def upload_partial_result(request, id):
    if request.method == 'POST':
        try:
            # job = Job.objects.get(user=request.user, id=id) TODO make it secure (authentication, rate limit)
            job = Job.objects.get(id=id)
            file = request.FILES['file']
            index = request.POST['index']
            consumed_time = request.POST['consumed_time']
            JobPartialResult.objects.create(
                job=job, index=index, consumed_time=consumed_time, partial_result_file=file)
            is_last_partial_result = JobPartialResult.objects.filter(
                job=job).count() == NUM_DEVICES_PER_JOB  # todo race condition
            if is_last_partial_result:
                merge_partial_result(job)
            device_id = request.POST['device_id']
            try:
                complete_inprogress_job(device_id)
            except (TypeError, KeyError, AssertionError) as e:
                logger.info(str(e))
                return HttpResponse(content='internal server error', status=503)
            return HttpResponse(content='uploaded successfully', status=201)
        except Job.DoesNotExist:
            return HttpResponse(content='job not found', status=404)
        except KeyError:
            return HttpResponse(content='bad request', status=400)
    return HttpResponse(content='method not allowed', status=405)
