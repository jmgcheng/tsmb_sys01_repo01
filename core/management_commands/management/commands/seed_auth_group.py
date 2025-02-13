import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from django.db import transaction


class Command(BaseCommand):
    help = 'Insert new group in auth_group from a CSV or XLSX file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', type=str, help='The CSV or XLSX file containing data to insert.')

    def handle(self, *args, **options):
        filename = options['filename']

        # Determine file type
        if filename.endswith('.csv'):
            df = pd.read_csv(filename)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filename)
        else:
            raise CommandError(
                'Unsupported file type. Please provide a CSV or XLSX file.')

        # Check if the required columns exist
        required_columns = ['NAME']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [
                col for col in required_columns if col not in df.columns]
            raise CommandError(f"Missing required columns: {
                               ', '.join(missing_columns)}")

        # Clean up data
        df['NAME'] = df['NAME'].fillna('').str.strip().str.upper()
        group_names = df['NAME'].dropna().unique()

        # Insert groups
        with transaction.atomic():
            created_count = 0
            for name in group_names:
                if not Group.objects.filter(name=name).exists():
                    Group.objects.create(name=name)
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully inserted {
                               created_count} new groups.")
        )
