import logging
import os
import sys


def configure_logging(app):
    """
    Sets up structured logging for the app.

    Locally this just logs to stdout. On EC2 this stdout stream is what
    the CloudWatch agent will tail and ship to CloudWatch Logs - no code
    change needed between environments, only agent config on the instance.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)

    # Quiet down noisy libraries unless we're debugging
    logging.getLogger("werkzeug").setLevel(
        logging.WARNING if log_level != "DEBUG" else logging.DEBUG
    )
