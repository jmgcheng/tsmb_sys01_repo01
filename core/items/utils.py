import random
import string
import os
import pandas as pd
import datetime
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import CommandError
from commons.utils import should_be, parse_date
from items.models import Item, ItemPriceAdjustment, ItemUnit
from companies.models import Company


def load_foreign_keys():
    # just creating dictionaries here for easy access of values later
    units = {u.name.upper(): u for u in ItemUnit.objects.all()}
    companies = {c.name.upper(): c for c in Company.objects.all()}
    items = {i.name.upper(): i for i in Item.objects.all()}

    return {
        'units': units,
        'companies': companies,
        'items': items,
    }


def verify_excel_items(df, mode='INSERT'):
    required_columns = ['NAME', 'COMPANY', 'UNIT',
                        'NUM PER UNIT', 'WEIGHT', 'ORIGINAL PRICE']

    if not all(col in df.columns for col in required_columns):
        missing_columns = [
            col for col in required_columns if col not in df.columns]
        raise CommandError(f"Missing required columns: {
                           ', '.join(missing_columns)}")

    df['NAME'] = df['NAME'].fillna('').astype(str).str.strip().str.upper()
    df['COMPANY'] = df['COMPANY'].fillna(
        '').astype(str).str.strip().str.upper()
    df['UNIT'] = df['UNIT'].fillna('').astype(str).str.strip().str.upper()
    df['NUM PER UNIT'] = df['NUM PER UNIT'].fillna(0)
    df['WEIGHT'] = df['WEIGHT'].fillna(0)
    df['ORIGINAL PRICE'] = df['ORIGINAL PRICE'].fillna(0)

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
        should_be('NOT EXISTING', Item, 'Item', field_name, column_records)
    elif mode == 'UPDATE':
        should_be('EXISTING', Item, 'Item', field_name, column_records)

    # Verify if values exists
    columns_to_check = ['COMPANY', 'UNIT']
    for column in columns_to_check:
        column_records = df[column].unique()
        field_name = 'name'
        if column == 'COMPANY':
            model = Company
            model_name = 'Company'
        elif column == 'UNIT':
            model = ItemUnit
            model_name = 'ItemUnit'

        should_be('EXISTING', model, model_name, field_name, column_records)

    return df


def verify_excel_items_price_adjustments(df, mode='INSERT'):
    required_columns = ['ITEM', 'DATE', 'NEW PRICE']

    if not all(col in df.columns for col in required_columns):
        missing_columns = [
            col for col in required_columns if col not in df.columns]
        raise CommandError(f"Missing required columns: {
                           ', '.join(missing_columns)}")

    df['ITEM'] = df['ITEM'].fillna('').astype(str).str.strip().str.upper()
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df['DATE'] = df['DATE'].map(lambda x: x.strftime('%Y-%m-%d'))
    df['NEW PRICE'] = df['NEW PRICE'].fillna(0)

    # Validate required columns should have values
    for col in required_columns:
        for _, row in df.iterrows():
            if row[col] == '':
                raise CommandError(f"Missing values in some {col} rows.")

    # Verify if values exists
    columns_to_check = ['ITEM']
    for column in columns_to_check:
        column_records = df[column].unique()
        field_name = 'name'
        if column == 'ITEM':
            model = Item
            model_name = 'Item'

        should_be('EXISTING', model, model_name, field_name, column_records)

    return df


def insert_excel_items(df):
    # First, verify and clean the input DataFrame
    df = verify_excel_items(df, 'INSERT')

    # Load foreign key references
    foreign_keys = load_foreign_keys()

    # Insert new items
    items = []

    for _, row in df.iterrows():

        # Create item instance
        item = Item(
            name=row['NAME'],
            weight=row['WEIGHT'],
            unit=None if pd.isna(foreign_keys['units'].get(
                row['UNIT'], None)) else foreign_keys['units'].get(row['UNIT'].upper(), None),
            num_per_unit=row['NUM PER UNIT'],
            company=None if pd.isna(foreign_keys['companies'].get(
                row['COMPANY'], None)) else foreign_keys['companies'].get(row['COMPANY'].upper(), None),
            price=row['ORIGINAL PRICE']
        )

        items.append(item)

    with transaction.atomic():
        #
        Item.objects.bulk_create(items)

    return True


def update_excel_items(df):
    # First, verify and clean the input DataFrame
    df = verify_excel_items(df, 'UPDATE')

    # Load foreign key references
    foreign_keys = load_foreign_keys()

    # Prepare lists for bulk updates
    items_to_update = []

    try:
        with transaction.atomic():
            for _, row in df.iterrows():
                try:
                    # Fetch the existing Item record by unique identifier
                    item = Item.objects.select_related(
                        'unit', 'company').get(name=row['NAME'])

                    # Update Item fields
                    item.weight = row['WEIGHT']
                    item.unit = None if pd.isna(foreign_keys['units'].get(
                        row['UNIT'], None)) else foreign_keys['units'].get(row['UNIT'].upper(), None)
                    item.num_per_unit = row['NUM PER UNIT']
                    item.company = None if pd.isna(foreign_keys['companies'].get(
                        row['COMPANY'], None)) else foreign_keys['companies'].get(row['COMPANY'].upper(), None)
                    item.price = row['ORIGINAL PRICE']

                    items_to_update.append(item)

                except ObjectDoesNotExist:
                    # Handle the case where an employee does not exist, if needed
                    continue

            # Perform bulk update on Items
            Item.objects.bulk_update(items_to_update, [
                'weight',
                'unit',
                'num_per_unit',
                'company',
                'price'
            ])

        return True

    except Exception as e:
        print(f"Error during update: {e}")
        return False


def insert_excel_items_price_adjustments(df):
    # First, verify and clean the input DataFrame
    df = verify_excel_items_price_adjustments(df, 'INSERT')

    # Load foreign key references
    foreign_keys = load_foreign_keys()

    # Insert new items
    price_adjustments = []

    for _, row in df.iterrows():

        # Create item instance
        item_price_adjustment = ItemPriceAdjustment(
            item=None if pd.isna(foreign_keys['items'].get(
                row['ITEM'], None)) else foreign_keys['items'].get(row['ITEM'].upper(), None),
            date=parse_date(row.get('DATE')),
            new_price=row['NEW PRICE']
        )

        price_adjustments.append(item_price_adjustment)

    with transaction.atomic():
        #
        ItemPriceAdjustment.objects.bulk_create(price_adjustments)

    return True


def handle_uploaded_file(f):
    file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', f.name)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path
