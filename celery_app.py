from celery import Celery

Celery_app = Celery(
    "tarefa_livros",
    broker = "redis://redis:6379/0",
    backend= "redis://redis:6379/0"
)
Celery_app.config.update(
    task_track_started = True,
    result_expires = 3600,
    result_persistent = True,
    task_serializer = "json",
    result_serializer = "json",
    aceppt_content = [ "json"]
)