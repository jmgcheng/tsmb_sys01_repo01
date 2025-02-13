import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from employees.models import EmployeeJobLevel
from django.db import transaction


class Command(BaseCommand):
    help = 'Insert new employee level from a CSV or XLSX file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', type=str, help='The CSV or XLSX file containing employee level to insert.')

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
        employee_level = df['NAME'].dropna().unique()

        # Check for existing employee_level
        existing_employee_level = EmployeeJobLevel.objects.filter(
            name__in=employee_level).values_list('name', flat=True)

        if existing_employee_level:
            self.stdout.write(self.style.WARNING(
                'The following employee level already exist in the database:'))
            for level in existing_employee_level:
                self.stdout.write(f'- {level}')
            self.stdout.write(self.style.ERROR(
                'Aborting operation due to existing records.'))
        else:
            # Insert new employee level in a transaction
            try:
                with transaction.atomic():
                    for _, row in df.iterrows():
                        name = row['NAME']

                        level = EmployeeJobLevel.objects.create(
                            name=name
                        )

                    self.stdout.write(self.style.SUCCESS(
                        'New Employee level records have been successfully added to the database.'))
            except Exception as e:
                raise CommandError(
                    f'Error inserting new employee level: {str(e)}')
