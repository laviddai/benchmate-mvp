# backend/app/services/imagej_service.py

import imagej
import logging
import scyjava
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

class ImageJService:
    """
    A singleton service to manage the ImageJ gateway lifecycle.
    Ensures that the JVM is started only once.
    This is crucial for performance in a server environment.
    """
    _gateway = None
    _initialized = False

    def __init__(self):
        # This constructor should not be called directly by users.
        # The singleton pattern is managed by the instance() class method.
        raise RuntimeError("Call instance() to get the ImageJ gateway.")

    @classmethod
    def instance(cls):
        """
        Returns the singleton instance of the ImageJ gateway.
        Initializes the gateway on the first call.

        This method is thread-safe in Python's GIL context for our application's
        startup and typical Celery worker model.
        """
        if not cls._initialized:
            logger.info("Initializing ImageJ gateway for the first time...")
            try:
                # For a server environment, we might need to allocate more memory.
                # This must be done BEFORE imagej.init() is called.
                # Example: scyjava.config.add_option('-Xmx6g') # 6 gigabytes
                # For now, we use defaults.

                # Initialize in headless mode. PyImageJ will download the necessary
                # ImageJ2 components on the first run if not found.
                # We can later configure this to point to a specific local Fiji app
                # directory if we need to bundle specific plugins.
                cls._gateway = imagej.init(mode='headless')
                cls._initialized = True
                logger.info(f"ImageJ gateway initialized successfully. Version: {cls._gateway.getVersion()}")
            except Exception as e:
                logger.error(f"Failed to initialize ImageJ gateway: {e}", exc_info=True)
                # This is a critical failure. The application cannot proceed with
                # imaging tasks. Re-raising allows the calling process (e.g., app startup)
                # to know about the failure.
                raise e
        return cls._gateway

# This provides a clean, callable object for other modules to use.
# e.g., from app.services.imagej_service import imagej_service
# gateway = imagej_service.instance()
imagej_service = ImageJService

def init_imagej_gateway():
    """
    A startup function that can be called from main.py's startup event
    to eagerly initialize the ImageJ gateway. This allows us to catch
    initialization errors when the application starts, rather than on the
    first user request.
    """
    logger.info("Triggering eager initialization of ImageJ gateway...")
    ImageJService.instance()