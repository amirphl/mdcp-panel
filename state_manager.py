import sched
import time
import json
import logging
import os
import re
import uuid
import paho.mqtt.client as mqtt
from cache_repository import CacheRepository


logger = logging.getLogger(__name__)
logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)


MQTT_BROKER = os.getenv('MQTT_BROKER')
QOS = int(os.getenv('QOS'))
DEVICE_REGISTRATION_TOPIC = os.getenv('DEVICE_REGISTRATION_TOPIC')
DEVICE_UNREGISTRATION_TOPIC = os.getenv('DEVICE_UNREGISTRATION_TOPIC')
DEVICE_ = os.getenv('DEVICE')
JOB_ = os.getenv('JOB')
COMPLETED = os.getenv('COMPLETED')
IN_PROGRESS = os.getenv('IN_PROGRESS')
FAILED = os.getenv('FAILED')
NUM_DEVICES_PER_JOB = int(os.getenv('NUM_DEVICES_PER_JOB'))
FAILED_JOBS_SCHEDULING_INTERVAL = int(
    os.getenv('FAILED_JOBS_SCHEDULING_INTERVAL'))

assert MQTT_BROKER is not None
assert DEVICE_REGISTRATION_TOPIC is not None
assert DEVICE_UNREGISTRATION_TOPIC is not None
assert QOS is not None
assert DEVICE_ is not None
assert JOB_ is not None
assert COMPLETED is not None
assert IN_PROGRESS is not None
assert FAILED is not None
assert NUM_DEVICES_PER_JOB is not None
assert NUM_DEVICES_PER_JOB >= 2
assert FAILED_JOBS_SCHEDULING_INTERVAL >= 300

logger.info('using env vars:')
logger.info('MQTT_BROKER = ' + MQTT_BROKER)
logger.info('DEVICE_REGISTRATION_TOPIC = ' + DEVICE_REGISTRATION_TOPIC)
logger.info('DEVICE_UNREGISTRATION_TOPIC = ' + DEVICE_UNREGISTRATION_TOPIC)
logger.info('QOS = ' + str(QOS))
logger.info('DEVICE = ' + DEVICE_)
logger.info('JOB = ' + JOB_)
logger.info('COMPLETED = ' + COMPLETED)
logger.info('IN_PROGRESS = ' + IN_PROGRESS)
logger.info('FAILED = ' + FAILED)
logger.info('FAILED_JOBS_SCHEDULING_INTERVAL = ' +
            str(FAILED_JOBS_SCHEDULING_INTERVAL))
logger.info('===============')
logger.info('===============')
logger.info('===============')


class MockJob:
    class Executable:
        def __init__(self, url):
            self.url = url

    class InputFile:
        def __init__(self, url):
            self.url = url

    def __init__(self, id, executable_url, input_file_url, index):
        self.id = id
        self.executable = self.Executable(executable_url)
        self.input_file = self.InputFile(input_file_url)
        self.index = index


def publish(topic, payload):
    c.publish(topic, payload, QOS)


def connect_to_broker(on_connect, on_disconnect):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(host=MQTT_BROKER)
    return client


def on_connect_factory(topic):
    def on_connect(client, userdata, flags, rc, properties=None):
        logger.info('connected to broker. purpose: %s' % topic)
    return on_connect


def on_disconnect_factory(topic):
    def on_disconnect(client, userdata, rc):
        logger.info('disconnected from broker. purpose: %s' % topic)
    return on_disconnect


c = connect_to_broker(on_connect_factory('no_topic'),
                      on_disconnect_factory('no_topic'))
c.loop_start()

s = sched.scheduler(time.time, time.sleep)


def get_device_key_pattern():
    return DEVICE_ + '*'


def get_device_key_regex():
    return DEVICE_ + '(.*)'


def get_device_key(device_id):
    return DEVICE_ + device_id


def get_job_key_pattern():
    return JOB_ + '*'


def get_job_key_regex():
    return JOB_ + '(.*)'


def get_job_key(device_id):
    return JOB_ + device_id


def remove_device(device_id):
    key = get_device_key(device_id)
    CacheRepository.delete(key)


def add_device(device_id):
    key = get_device_key(device_id)
    CacheRepository.store(key, '1', expire_in_seconds=None)


def get_device(device_id):
    key = get_device_key(device_id)
    return CacheRepository.get(key)


def get_job_payload(job, index):
    return job.executable.url + " " + job.input_file.url + " " + str(index) + " " + str(NUM_DEVICES_PER_JOB) + " " + str(job.id)


def add_job(device_id, job, index, status):
    key = get_job_key(device_id)
    value = json.dumps({
        'job': str(job.id),
        'executable_url': job.executable.url,
        'input_file_url': job.input_file.url,
        'index': index,
        'status': status
    })
    # TODO later add current NUM_DEVICES_PER_JOB to value since it may change during program life cycles and deployments
    CacheRepository.store(key, value, expire_in_seconds=None)


def get_job(device_id):
    key = get_job_key(device_id)
    value = CacheRepository.get(key)
    if value is None:
        logger.error(
            'no job found for device with id %s . something went wrong' % device_id)
        return None
    else:
        return json.loads(value)


def remove_job(device_id):
    key = get_job_key(device_id)
    CacheRepository.delete(key)


def has_device_completed_job(device_id):
    job_info = get_job(device_id)
    return job_info['status'] == COMPLETED


def fail_inprogress_job(device_id):
    key = get_job_key(device_id)
    job_info = get_job(device_id)
    assert job_info['status'] == IN_PROGRESS
    job_info['status'] = FAILED
    CacheRepository.store(key, json.dumps(job_info), expire_in_seconds=None)
    logger.info('made job %s %s' % (device_id, FAILED))


def complete_inprogress_job(device_id):
    key = get_job_key(device_id)
    job_info = get_job(device_id)
    assert job_info['status'] == IN_PROGRESS
    job_info['status'] = COMPLETED
    CacheRepository.store(key, json.dumps(job_info), expire_in_seconds=None)
    logger.info('made job %s %s' % (device_id, COMPLETED))


def register_device(device_id):
    add_device(device_id)
    logger.info('registered device with id %s' % device_id)


def unregister_device(device_id):
    logger.info('received unregistration for device with id %s' % device_id)
    device = get_device(device_id)
    if device is None:
        try:
            if has_device_completed_job(device_id):
                logger.info(
                    'device %s has already completed it\'s job. bypassed unregisteration' % device_id)
            else:
                fail_inprogress_job(device_id)
                logger.warning(
                    'unregistered device %s which has not completed it\'s job yet' % device_id)
        except (TypeError, KeyError, AssertionError) as e:
            logger.error(str(e))
    else:
        remove_device(device_id)
        logger.info('unregistered device with id %s' % device_id)


def handle_subscriptions():
    def on_message(client, userdata, message):
        device_id = message.payload.decode()
        register_device(device_id)
    client = connect_to_broker(on_connect_factory(
        DEVICE_REGISTRATION_TOPIC), on_disconnect_factory(DEVICE_REGISTRATION_TOPIC))
    client.on_message = on_message
    client.subscribe(topic=DEVICE_REGISTRATION_TOPIC, qos=QOS)
    return client


def handle_unsubscriptions():
    def on_message(client, userdata, message):
        device_id = message.payload.decode()
        unregister_device(device_id)
    client = connect_to_broker(on_connect_factory(
        DEVICE_UNREGISTRATION_TOPIC), on_disconnect_factory(DEVICE_UNREGISTRATION_TOPIC))
    client.on_message = on_message
    client.subscribe(topic=DEVICE_UNREGISTRATION_TOPIC, qos=QOS)
    return client


def submit_job(job):
    device_key_pattern = get_device_key_pattern()
    scan_iter = CacheRepository.get_scan_iter(device_key_pattern)
    i = 0
    for key in scan_iter:
        if i == NUM_DEVICES_PER_JOB:
            break
        device_id = re.search(get_device_key_regex(),
                              key.decode()).group(1)
        submit_job_to_device(device_id, job, i)
        logger.info('send job %s to device %s with index %s' %
                    (job.id, device_id, i))
        i = i + 1

    for j in range(i, NUM_DEVICES_PER_JOB):
        device_id = 'not_found_' + str(uuid.uuid4())
        add_job(device_id, job, j, FAILED)
        logger.info('send job %s to device %s with index %s' %
                    (job.id, device_id, j))


def submit_job_to_device(device_id, job, index):
    payload = get_job_payload(job, index)
    publish(device_id, payload)
    remove_device(device_id)
    add_job(device_id, job, index, IN_PROGRESS)


def check_long_running_jobs():
    # TODO
    pass


def schedule_failed_jobs(sc):
    device_key_pattern = get_device_key_pattern()
    job_key_pattern = get_job_key_pattern()
    device_iter = CacheRepository.get_scan_iter(device_key_pattern)
    job_iter = CacheRepository.get_scan_iter(job_key_pattern)

    for job_key in job_iter:
        old_device_id = re.search(get_job_key_regex(),
                                  job_key.decode()).group(1)
        job_info = get_job(old_device_id)
        if job_info['status'] != FAILED:
            continue

        device_key = next(device_iter, None)
        if device_key is None:
            logger.info(
                'scheduler: found no active device to send %s job %s' % (FAILED, job_key))
            break

        device_id = re.search(get_device_key_regex(),
                              device_key.decode()).group(1)
        id = job_info['job']
        executable_url = job_info['executable_url']
        input_file_url = job_info['input_file_url']
        index = job_info['index']
        new_job = MockJob(id, executable_url, input_file_url, index)
        submit_job_to_device(device_id, new_job, index)
        # TODO we can change the key structure instead of removing the record
        remove_job(old_device_id)
        logger.info('scheduler: send job %s to device %s with index %s' %
                    (new_job.id, device_id, index))
    s.enter(FAILED_JOBS_SCHEDULING_INTERVAL, 1, schedule_failed_jobs, (sc,))


if __name__ == '__main__':
    subscriptions_handler = handle_subscriptions()
    subscriptions_handler.loop_start()
    unsubscriptions_handler = handle_unsubscriptions()
    unsubscriptions_handler.loop_start()
    s.enter(FAILED_JOBS_SCHEDULING_INTERVAL, 1, schedule_failed_jobs, (s,))
    s.run()
    logger.info("The End.")
