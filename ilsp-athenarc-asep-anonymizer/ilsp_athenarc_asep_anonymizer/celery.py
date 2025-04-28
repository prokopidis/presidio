import json

from celery import Celery
from .pii_anonymizer import PiiAnonymizer

celery = Celery(
    'worker',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
)


@celery.task(name="anonymization")
def run_anonymization(*args, **kwargs):
    anonymizer_instance = PiiAnonymizer()
    return json.dumps(anonymizer_instance.anonymize(*args, **kwargs), default=lambda x: x.__dict__, ensure_ascii=False)
