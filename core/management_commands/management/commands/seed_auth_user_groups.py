import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from django.db import transaction
from employees.models import Employee
from django.contrib.auth.models import User
from commons.utils import should_be, parse_date


class Command(BaseCommand):
    help = 'Assign users to groups based on company_id from an Excel file.'

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
        required_columns = ['COMPANY ID', 'GROUP NAME']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [
                col for col in required_columns if col not in df.columns]
            raise CommandError(f"Missing required columns: {
                               ', '.join(missing_columns)}")

        # Clean up data
        df['COMPANY ID'] = df['COMPANY ID'].fillna('').astype(
            str).str.strip().str.upper().replace(" ", "-", regex=True)
        df['GROUP NAME'] = df['GROUP NAME'].str.strip()

        # check columns that should be unique and existing
        columns_to_check = ['COMPANY ID']
        for column in columns_to_check:
            column_records = df[column].unique()
            field_name = 'name'
            if column == 'COMPANY ID':
                field_name = 'company_id'
            should_be('EXISTING', Employee, 'Employee',
                      field_name, column_records)

        # check columns that should be unique and existing. Multiple
        columns_to_check = ['GROUP NAME']
        for column in columns_to_check:
            #
            df[column] = df[column].replace({None: ''})
            df[column] = df[column].fillna('')
            df[column] = df[column].str.strip().str.upper()
            df[column] = df[column].replace({'': None})

            #
            column_records = df[column].unique()
            column_records = column_records[~pd.isnull(column_records)]

            if not pd.isna(column_records).any():
                field_name = 'name'
                if column == 'GROUP NAME':
                    model = Group
                    model_name = 'Group'

                    # employee can have multiple Group as to why we need to split it
                    split_records = []
                    for record in column_records:
                        # Split the record by comma and strip any whitespace
                        split_records.extend([r.strip()
                                             for r in record.split(',')])

                    # Remove duplicates and convert to a numpy array or list
                    column_records = pd.unique(split_records)

                should_be('EXISTING', model, model_name,
                          field_name, column_records)

        # Assign users to groups
        with transaction.atomic():
            for _, row in df.iterrows():
                company_id = row['COMPANY ID']
                group_names = row['GROUP NAME'].split(',')  # Split into a list

                # Trim whitespace from each group name
                group_names = [g.strip() for g in group_names]

                # Get users under the company_id
                users = User.objects.filter(employee__company_id=company_id)

                for group_name in group_names:
                    try:
                        group = Group.objects.get(name=group_name)
                        for user in users:
                            user.groups.add(group)  # Add user to group
                    except Group.DoesNotExist:
                        raise CommandError(
                            f"Group '{group_name}' does not exist.")

        self.stdout.write(self.style.SUCCESS(
            "User groups assigned successfully."))
