import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from customers.models import Customer


class Command(BaseCommand):
    help = 'Insert new customers from an Excel file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', type=str, help='The Excel file (XLSX) containing customer data.'
        )

    def handle(self, *args, **options):
        filename = options['filename']

        # Load Excel file
        try:
            df = pd.read_excel(filename)
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")

        # Check required columns
        required_columns = ['CUSTOMER ID', 'NAME']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [
                col for col in required_columns if col not in df.columns]
            raise CommandError(f"Missing required columns: {
                               ', '.join(missing_columns)}")

        # Clean up data
        df['CUSTOMER ID'] = df['CUSTOMER ID'].fillna(
            '').str.strip().str.upper().replace(" ", "-", regex=True)
        df['NAME'] = df['NAME'].fillna('').str.strip().str.upper()

        # Validate unique customer id
        existing_customer_id = set(
            Customer.objects.values_list('customer_id', flat=True))
        duplicate_customer_id = set(df['CUSTOMER ID']) & existing_customer_id
        if duplicate_customer_id:
            raise CommandError(
                f"Duplicate CUSTOMER ID(s) already exist in database: {', '.join(duplicate_customer_id)}")

        # Validate unique name
        existing_name = set(Customer.objects.values_list('name', flat=True))
        duplicate_name = set(df['NAME']) & existing_name
        if duplicate_name:
            raise CommandError(
                f"Duplicate NAME(s) already exist in database: {', '.join(duplicate_name)}")

        # Insert customers
        with transaction.atomic():
            for _, row in df.iterrows():
                customer_id = row['CUSTOMER ID']
                name = row['NAME']

                # Avoid duplicate entries
                customer, created = Customer.objects.get_or_create(
                    customer_id=customer_id,
                    name=name
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"Inserted: {name}"))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Skipped (already exists): {name}"))

        self.stdout.write(self.style.SUCCESS(
            "Customer data import completed!"))
