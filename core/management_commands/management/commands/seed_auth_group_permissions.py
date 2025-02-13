import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Assign permissions to groups from an Excel file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', type=str, help='The Excel file (XLSX) containing group-permission mappings.'
        )

    def handle(self, *args, **options):
        filename = options['filename']

        # Load Excel file
        try:
            df = pd.read_excel(filename)
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")

        # Check required columns
        required_columns = ['GROUP', 'PERMISSIONS']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [
                col for col in required_columns if col not in df.columns]
            raise CommandError(f"Missing required columns: {
                               ', '.join(missing_columns)}")

        # Clean up data
        df['GROUP'] = df['GROUP'].fillna('').str.strip().str.upper()
        df['PERMISSIONS'] = df['PERMISSIONS'].fillna('').str.strip()

        # Validate groups exist
        group_names = df['GROUP'].unique()
        existing_groups = set(Group.objects.filter(
            name__in=group_names).values_list('name', flat=True))
        missing_groups = set(group_names) - existing_groups

        if missing_groups:
            raise CommandError(f"Groups not found: {
                               ', '.join(missing_groups)}")

        # Validate permissions exist
        all_permission_codenames = set(
            Permission.objects.values_list('codename', flat=True))

        # Assign permissions to groups
        with transaction.atomic():
            for _, row in df.iterrows():
                group_name = row['GROUP']
                permission_codenames = [perm.strip()
                                        for perm in row['PERMISSIONS'].split(',')]

                # Validate permissions
                invalid_permissions = [
                    perm for perm in permission_codenames if perm not in all_permission_codenames]
                if invalid_permissions:
                    raise CommandError(f"Invalid permissions: {
                                       ', '.join(invalid_permissions)}")

                # Assign permissions
                group = Group.objects.get(name=group_name)
                permissions = Permission.objects.filter(
                    codename__in=permission_codenames)
                # Replaces existing permissions
                group.permissions.set(permissions)

        self.stdout.write(self.style.SUCCESS(
            "Permissions assigned successfully!"))
