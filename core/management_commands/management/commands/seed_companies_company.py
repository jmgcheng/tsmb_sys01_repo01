import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from companies.models import Company


class Command(BaseCommand):
    help = 'Insert new companies from an Excel file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', type=str, help='The Excel file (XLSX) containing company data.'
        )

    def handle(self, *args, **options):
        filename = options['filename']

        # Load Excel file
        try:
            df = pd.read_excel(filename)
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")

        # Check required columns
        required_columns = ['NAME']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [
                col for col in required_columns if col not in df.columns]
            raise CommandError(f"Missing required columns: {
                               ', '.join(missing_columns)}")

        # Clean up data
        df['NAME'] = df['NAME'].fillna('').str.strip().str.upper()

        # Validate unique NAME
        existing_name = set(Company.objects.values_list('name', flat=True))
        duplicate_name = set(df['NAME']) & existing_name
        if duplicate_name:
            raise CommandError(f"Duplicate NAME(s) already exist in database: {
                               ', '.join(duplicate_name)}")

        # Insert companies
        with transaction.atomic():
            for _, row in df.iterrows():
                name = row['NAME']

                # Avoid duplicate entries
                company, created = Company.objects.get_or_create(
                    name=name
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"Inserted: {name}"))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Skipped (already exists): {name}"))

        self.stdout.write(self.style.SUCCESS(
            "Company data import completed!"))
