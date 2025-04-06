import logging
import azure.functions as func
from .algo_run import main as automation_main

def main(mytimer: func.TimerRequest) -> None:
    logging.info("Timer trigger function started.")
    if mytimer.past_due:
        logging.warning("The timer is past due!")
    try:
        automation_main(mytimer)  # Now passes mytimer; it's accepted by main()
        logging.info("algo_run completed successfully.")
    except Exception as e:
        logging.exception("Error running automation script: %s", e)
