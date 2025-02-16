import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from transacts.models import TransactHeader, TransactDetail, TransactStatus
from companies.models import Company
from locations.models import Location
from items.models import Item
from datetime import datetime


class Command(BaseCommand):
    help = 'Insert new transacts from an Excel file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', type=str, help='The Excel file (XLSX) containing transact data.')

    def handle(self, *args, **options):
        filename = options['filename']

        # Load Excel file
        try:
            # Read all as strings to avoid conversion issues
            df = pd.read_excel(filename, dtype=str)
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")

        # Check required columns
        required_columns = ['DATE', 'COMPANY',
                            'SI NO', 'LOCATION', 'ITEM', 'QUANTITY']
        missing_columns = [
            col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise CommandError(
                f"Missing required columns: {', '.join(missing_columns)}")

        #
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df['DATE'] = df['DATE'].map(lambda x: x.strftime('%Y-%m-%d'))
        df['COMPANY'] = df['COMPANY'].fillna(
            '').astype(str).str.strip().str.upper()
        df['SI NO'] = df['SI NO'].fillna('').astype(
            str).str.strip().str.upper().replace(" ", "-", regex=True)
        df['LOCATION'] = df['LOCATION'].fillna(
            '').astype(str).str.strip().str.upper()
        df['ITEM'] = df['ITEM'].fillna('').astype(str).str.strip().str.upper()
        df['QUANTITY'] = df['QUANTITY'].fillna(0)

        # Convert 'DATE' column to actual date format
        # try:
        #     df['DATE'] = pd.to_datetime(df['DATE']).dt.date  # Convert to date format
        # except Exception as e:
        #     raise CommandError(f"Error processing 'DATE' column: {e}")

        # Group by (DATE, COMPANY, SI NO, LOCATION) to determine unique headers
        grouped = df.groupby(['DATE', 'COMPANY', 'SI NO', 'LOCATION'])

        with transaction.atomic():  # Ensure atomicity
            for (date, company_name, si_no, location_name), group in grouped:
                # Validate related fields
                company = Company.objects.filter(name=company_name).first()
                if not company:
                    self.stdout.write(self.style.ERROR(
                        f"Skipping: Company '{company_name}' does not exist."))
                    continue

                location = Location.objects.filter(name=location_name).first()
                if not location:
                    self.stdout.write(self.style.ERROR(
                        f"Skipping: Location '{location_name}' does not exist."))
                    continue

                # Ensure status "FILED" exists
                status = TransactStatus.objects.filter(name="FILED").first()
                if not status:
                    raise CommandError(
                        "TransactStatus 'FILED' not found. Please create it first.")

                # Check if the header already exists
                transact_header, created = TransactHeader.objects.get_or_create(
                    si_no=si_no,
                    company=company,
                    location=location,
                    date=date,
                    defaults={'status': status}
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"Created TransactHeader: {si_no} for {company_name}"))

                # Insert details
                for _, row in group.iterrows():
                    item_name = row['ITEM'].strip()
                    quantity = int(row['QUANTITY'])

                    item = Item.objects.filter(name=item_name).first()
                    if not item:
                        self.stdout.write(self.style.ERROR(
                            f"Skipping detail: Item '{item_name}' does not exist."))
                        continue

                    TransactDetail.objects.create(
                        transact_header=transact_header,
                        item=item,
                        quantity=quantity
                    )

                self.stdout.write(self.style.SUCCESS(
                    f"Processed {len(group)} items for TransactHeader: {si_no}"))

        self.stdout.write(self.style.SUCCESS(
            "Transaction import completed successfully!"))
