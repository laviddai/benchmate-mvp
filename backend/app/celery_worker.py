# backend/app/celery_worker.py
import os
from celery import Celery

# --- Celery app initialization ---
# This file now only defines and configures the Celery application instance.
# The actual task logic is moved to the `app/tasks/` directory.

REDIS_HOSTNAME = os.getenv("REDIS_HOSTNAME", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
CELERY_BROKER_URL = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/1"

celery_app = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    # This crucial line tells Celery where to find the task modules.
    # It will automatically discover the @celery_app.task decorators in these files.
    include=[
        "app.tasks.volcano_task",
        "app.tasks.pca_task",
        "app.tasks.heatmap_task",
        "app.tasks.imaging_task"
        # To add a new tool, you would just add
        # "app.tasks.***_task" to this list.
    ]
)

# Optional Celery configuration
celery_app.conf.task_track_started = True
celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']
celery_app.conf.timezone = 'UTC'
celery_app.conf.enable_utc = True

# The 'debug_task' is no longer here. If needed for testing, it could be
# moved to its own file in `app/tasks/debug_task.py`. For now, we will
# remove it for cleanliness.