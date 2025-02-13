import pandas as pd
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.core.management.base import CommandError
from employees.utils import insert_excel_employees, update_excel_employees


@shared_task()
def import_employees_task(file_path, mode='INSERT'):
    # notes
    # returning pass, True, False, or nothing at all will still mark the task SUCCESS.
    # raise an Exception or CommandError here or inside called functions to force FAILURE on celery task
    # raise CommandError(f"Testing commanderror")

    df = pd.read_excel(file_path)
    if mode == 'INSERT':
        insert_excel_employees(df)
    elif mode == 'UPDATE':
        update_excel_employees(df)
    else:
        raise Exception("TE01: Mode expecting INSERT or UPDATE only.")
