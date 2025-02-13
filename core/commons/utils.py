import pandas as pd
import datetime
from django.utils.regex_helper import _lazy_re_compile
from django.db.models import Q
from django.core.management.base import CommandError


date_re = _lazy_re_compile(
    r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$")


def get_existing_names_case_insensitive(model, field_name, values):
    """
    Perform a case-insensitive filter on the given model's field for the provided list of values.
    Returns a list of matching values that exist in the database.
    """
    query = Q()
    for value in values:
        query |= Q(**{f"{field_name}__iexact": value})

    return model.objects.filter(query).values_list(field_name, flat=True)


def should_be(mode, model, model_name, field_name, column_records):
    records_results = get_existing_names_case_insensitive(
        model, field_name, column_records)

    if mode.upper() == 'NOT EXISTING':
        # eg. use for checking if values are already existing so we can safely insert new records
        if records_results:
            raise CommandError(f"The following {model_name}.{field_name} values already exist: {
                               ', '.join(records_results)}")
    elif mode.upper() == 'EXISTING':
        # eg. use for checking if values are existing for updating records. Can also be used for checking if foreign key values do exist
        missing_records = set(column_records) - \
            {name.upper() for name in records_results}

        if missing_records:
            raise CommandError(f"The following {model_name}.{field_name} values do not exist: {
                ', '.join(missing_records)}")


def parse_date(date_str):
    if pd.isna(date_str):
        return None
    try:
        return datetime.date.fromisoformat(date_str)
    except ValueError:
        if match := date_re.match(date_str):
            kw = {k: int(v) for k, v in match.groupdict().items()}
            return datetime.date(**kw)
