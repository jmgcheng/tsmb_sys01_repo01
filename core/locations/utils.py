import pandas as pd
from django.db import transaction
from django.core.management.base import CommandError
from commons.utils import should_be
from locations.models import Location


def verify_excel_locations(df, mode='INSERT'):
    required_columns = ['NAME', 'ADDRESS']

    if not all(col in df.columns for col in required_columns):
        missing_columns = [
            col for col in required_columns if col not in df.columns]
        raise CommandError(f"Missing required columns: {
                           ', '.join(missing_columns)}")

    df['NAME'] = df['NAME'].fillna(
        '').astype(str).str.strip().str.upper()
    df['ADDRESS'] = df['ADDRESS'].fillna('').astype(str).str.strip()

    # Validate required columns should have values
    for col in required_columns:
        for _, row in df.iterrows():
            if row[col] == '':
                raise CommandError(f"Missing values in some {col} rows.")

    # check columns that should be unique
    columns_to_check = ['NAME']
    for column in columns_to_check:
        column_records = df[column].unique()
        field_name = 'name'
        if column == 'NAME':
            field_name = 'name'
    if mode == 'INSERT':
        should_be('NOT EXISTING', Location, 'Location',
                  field_name, column_records)
    elif mode == 'UPDATE':
        should_be('EXISTING', Location, 'Location', field_name, column_records)

    return df


def insert_excel_locations(df):

    # First, verify and clean the input DataFrame
    df = verify_excel_locations(df, 'INSERT')

    # Insert new locations
    locations = []

    for _, row in df.iterrows():

        # Create Location instance
        location = Location(
            name=row['NAME'],
            address=row['ADDRESS']
        )

        locations.append(location)

    with transaction.atomic():
        #
        Location.objects.bulk_create(locations)

    return True
