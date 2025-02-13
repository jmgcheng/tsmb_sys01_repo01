import random
import string
import os
import pandas as pd
import datetime
from django.conf import settings
from django.utils.regex_helper import _lazy_re_compile
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import CommandError
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from commons.utils import should_be, parse_date
from employees.models import Employee, EmployeeJob, EmployeeJobLevel, EmployeeJobSpecialty, EmployeeStatus


# date_re = _lazy_re_compile(
#     r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$")


def generate_username(name):
    first_word = name.split()[0].lower().replace(",", "")
    random_digits = ''.join(random.choices(string.digits, k=5))
    return f"{first_word}_{random_digits}"


# def get_existing_names_case_insensitive(model, field_name, values):
#     """
#     Perform a case-insensitive filter on the given model's field for the provided list of values.
#     Returns a list of matching values that exist in the database.
#     """
#     query = Q()
#     for value in values:
#         query |= Q(**{f"{field_name}__iexact": value})

#     return model.objects.filter(query).values_list(field_name, flat=True)


# def should_be(mode, model, model_name, field_name, column_records):
#     records_results = get_existing_names_case_insensitive(
#         model, field_name, column_records)

#     if mode.upper() == 'NOT EXISTING':
#         # eg. use for checking if values are already existing so we can safely insert new records
#         if records_results:
#             raise CommandError(f"The following {model_name}.{field_name} values already exist: {
#                                ', '.join(records_results)}")
#     elif mode.upper() == 'EXISTING':
#         # eg. use for checking if values are existing for updating records. Can also be used for checking if foreign key values do exist
#         missing_records = set(column_records) - \
#             {name.upper() for name in records_results}

#         if missing_records:
#             raise CommandError(f"The following {model_name}.{field_name} values do not exist: {
#                 ', '.join(missing_records)}")


# def parse_date(date_str):
#     if pd.isna(date_str):
#         return None
#     try:
#         return datetime.date.fromisoformat(date_str)
#     except ValueError:
#         if match := date_re.match(date_str):
#             kw = {k: int(v) for k, v in match.groupdict().items()}
#             return datetime.date(**kw)


def load_foreign_keys():
    # just creating dictionaries here for easy access of values later

    statuses = {s.name.upper(): s for s in EmployeeStatus.objects.all()}
    positions = {p.name.upper(): p for p in EmployeeJob.objects.all()}
    levels = {l.name.upper(): l for l in EmployeeJobLevel.objects.all()}
    specialties = {
        s.name.upper(): s for s in EmployeeJobSpecialty.objects.all()}

    return {
        'statuses': statuses,
        'positions': positions,
        'levels': levels,
        'specialties': specialties,
    }


def verify_excel_employees(df, mode='INSERT'):
    required_columns = ['COMPANY ID', 'FIRST NAME', 'LAST NAME', 'GENDER',
                        'CONTACT', 'ADDRESS', 'BIRTH DATE', 'START DATE', 'STATUS', 'POSITION']

    # for column in required_columns:
    #     if column not in df.columns:
    #         raise CommandError(f"Missing required column: {column}")

    if not all(col in df.columns for col in required_columns):
        missing_columns = [
            col for col in required_columns if col not in df.columns]
        raise CommandError(f"Missing required columns: {
                           ', '.join(missing_columns)}")

    # print(df)

    df['COMPANY ID'] = df['COMPANY ID'].fillna(
        '').astype(str).str.strip().str.upper().replace(" ", "-", regex=True)
    df['FIRST NAME'] = df['FIRST NAME'].fillna('').str.strip()
    df['LAST NAME'] = df['LAST NAME'].fillna('').str.strip()
    df['GENDER'] = df['GENDER'].fillna('').str.strip().str.upper()
    df['CONTACT'] = df['CONTACT'].fillna('').astype(str).str.strip()
    df['ADDRESS'] = df['ADDRESS'].fillna('').str.strip()
    df['POSITION'] = df['POSITION'].fillna('').str.strip().str.upper()
    df['STATUS'] = df['STATUS'].fillna('').str.strip().str.upper()
    df['BIRTH DATE'] = pd.to_datetime(df['BIRTH DATE'], errors='coerce')
    df['BIRTH DATE'] = df['BIRTH DATE'].map(lambda x: x.strftime('%Y-%m-%d'))
    df['START DATE'] = pd.to_datetime(df['START DATE'], errors='coerce')
    df['START DATE'] = df['START DATE'].map(lambda x: x.strftime('%Y-%m-%d'))

    #
    if 'REGULAR DATE' in df.columns:
        df['REGULAR DATE'] = pd.to_datetime(
            df['REGULAR DATE'], errors='coerce')
        df['REGULAR DATE'] = df['REGULAR DATE'].map(
            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None)
    if 'SEPARATION DATE' in df.columns:
        df['SEPARATION DATE'] = pd.to_datetime(
            df['SEPARATION DATE'], errors='coerce')
        df['SEPARATION DATE'] = df['SEPARATION DATE'].map(
            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None)

    # Validate required columns should have values
    for col in required_columns:
        for _, row in df.iterrows():
            if row[col] == '':
                raise CommandError(f"Missing values in some {col} rows.")

    # check columns that should be unique
    columns_to_check = ['COMPANY ID']
    for column in columns_to_check:
        column_records = df[column].unique()
        field_name = 'name'
        if column == 'COMPANY ID':
            field_name = 'company_id'
    if mode == 'INSERT':
        should_be('NOT EXISTING', Employee, 'Employee',
                  field_name, column_records)
    elif mode == 'UPDATE':
        should_be('EXISTING', Employee, 'Employee', field_name, column_records)

    # Validate gender and boolean fields
    if not df['GENDER'].isin(['MALE', 'FEMALE']).all():
        raise CommandError("Invalid GENDER value. Must be 'MALE' or 'FEMALE'.")

    # a single blank value will auto convert every value to float. As of now, this is how we clean it.
    # df['IS LOCAL'] = df['IS LOCAL'].replace({'': 'TRUE'})
    # df['IS LOCAL'] = df['IS LOCAL'].replace({'1.0': 'TRUE'})
    # df['IS LOCAL'] = df['IS LOCAL'].replace({'0.0': 'FALSE'})
    # if not df['IS LOCAL'].isin(['TRUE', 'FALSE']).all():
    #     raise CommandError("Invalid IS LOCAL value. Must be 'TRUE' or 'FALSE'.")

    # Verify if values exists
    columns_to_check = ['STATUS', 'POSITION']
    for column in columns_to_check:
        column_records = df[column].unique()
        field_name = 'name'
        if column == 'STATUS':
            model = EmployeeStatus
            model_name = 'EmployeeStatus'
        elif column == 'POSITION':
            model = EmployeeJob
            model_name = 'EmployeeJob'

        should_be('EXISTING', model, model_name, field_name, column_records)

    # Verify value ONLY IF column is exisiting in file
    columns_to_check = ['POSITION SPECIALTIES']
    for column in columns_to_check:
        if column in df.columns:
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
                if column == 'POSITION SPECIALTIES':
                    model = EmployeeJobSpecialty
                    model_name = 'EmployeeJobSpecialty'

                    # employee can have multiple EmployeeJobSpecialty as to why we need to split it
                    split_records = []
                    for record in column_records:
                        # Split the record by comma and strip any whitespace
                        split_records.extend([r.strip()
                                             for r in record.split(',')])

                    # Remove duplicates and convert to a numpy array or list
                    column_records = pd.unique(split_records)

                should_be('EXISTING', model, model_name,
                          field_name, column_records)

    return df


def insert_excel_employees(df):

    # First, verify and clean the input DataFrame
    df = verify_excel_employees(df, 'INSERT')

    # Load foreign key references
    foreign_keys = load_foreign_keys()

    # Insert new employees
    users = []
    employees = []
    default_password = make_password('welcome01')

    for _, row in df.iterrows():
        # Create User instance
        username = generate_username(row['FIRST NAME'])
        first_name = row['FIRST NAME']
        last_name = row['LAST NAME']
        user = User(username=username, password=default_password,
                    first_name=first_name, last_name=last_name)

        if 'EMAIL' in df.columns and pd.notnull(row['EMAIL']):
            user.email = row['EMAIL']

        users.append(user)

        # Create Employee instance
        employee = Employee(
            user=user,
            company_id=row['COMPANY ID'],
            contact='' if pd.isna(row.get('CONTACT', None)
                                  ) else row.get('CONTACT', None),
            middle_name='' if pd.isna(
                row.get('MIDDLE NAME', None)) else row.get('MIDDLE NAME', None),
            gender=row['GENDER'],
            address='' if pd.isna(row.get('ADDRESS', None)
                                  ) else row.get('ADDRESS', None),
            birth_date=parse_date(row.get('BIRTH DATE')),
            start_date=parse_date(row.get('START DATE')),
            status=foreign_keys['statuses'].get(row['STATUS'].upper()),
            position=foreign_keys['positions'].get(row['POSITION'].upper()),
            position_level=None if pd.isna(foreign_keys['levels'].get(
                row['POSITION LEVEL'], None)) else foreign_keys['levels'].get(row['POSITION LEVEL'].upper(), None),
            regular_date=parse_date(row.get('REGULAR DATE')),
            separation_date=parse_date(row.get('SEPARATION DATE')),
        )

        employees.append(employee)

    # print(f'-------hermit3---------')
    # print(users)
    # print(f'-------hermit3---------')
    # print(f'-------hermit5---------')
    # print(employees) # your model should have def __str__(self) to easily see contents for debugging
    # print(f'-------hermit5---------')

    with transaction.atomic():
        # Save users and employees
        User.objects.bulk_create(users)
        for i, employee in enumerate(employees):
            employee.user = users[i]
        Employee.objects.bulk_create(employees)

        # Add specialties to each employee after bulk creation
        for i, employee in enumerate(employees):
            # Get the corresponding row for this employee
            row = df.iloc[i]
            specialties = row.get('POSITION SPECIALTIES', '')
            if pd.notna(specialties):
                specialty_list = [specialty.strip()
                                  for specialty in specialties.split(',')]
                employee.position_specialties.add(
                    *EmployeeJobSpecialty.objects.filter(name__in=specialty_list))

    return True


def update_excel_employees(df):

    # First, verify and clean the input DataFrame
    df = verify_excel_employees(df, 'UPDATE')

    # Load foreign key references
    foreign_keys = load_foreign_keys()

    # Prepare lists for bulk updates
    users_to_update = []
    employees_to_update = []

    try:
        with transaction.atomic():
            for _, row in df.iterrows():
                try:
                    # Fetch the existing Employee record by unique identifier
                    employee = Employee.objects.select_related(
                        'user').get(company_id=row['COMPANY ID'])

                    # Update User information if necessary
                    user = employee.user
                    if 'EMAIL' in df.columns and pd.notnull(row['EMAIL']):
                        user.email = row['EMAIL']
                    if 'FIRST NAME' in df.columns and pd.notnull(row['FIRST NAME']):
                        user.first_name = row['FIRST NAME']
                    if 'LAST NAME' in df.columns and pd.notnull(row['LAST NAME']):
                        user.last_name = row['LAST NAME']

                    users_to_update.append(user)

                    # Update Employee fields
                    employee.contact = '' if pd.isna(
                        row.get('CONTACT', None)) else row.get('CONTACT', None)
                    employee.middle_name = '' if pd.isna(
                        row.get('MIDDLE NAME', None)) else row.get('MIDDLE NAME', None)
                    employee.gender = row['GENDER']
                    employee.address = '' if pd.isna(
                        row.get('ADDRESS', None)) else row.get('ADDRESS', None)
                    employee.birth_date = parse_date(row.get('BIRTH DATE'))
                    employee.start_date = parse_date(row.get('START DATE'))
                    employee.status = foreign_keys['statuses'].get(
                        row['STATUS'].upper())
                    employee.position = foreign_keys['positions'].get(
                        row['POSITION'].upper())
                    employee.position_level = None if pd.isna(foreign_keys['levels'].get(
                        row['POSITION LEVEL'], None)) else foreign_keys['levels'].get(row['POSITION LEVEL'].upper(), None)
                    employee.regular_date = parse_date(row.get('REGULAR DATE'))
                    employee.separation_date = parse_date(
                        row.get('SEPARATION DATE'))

                    employees_to_update.append(employee)

                except ObjectDoesNotExist:
                    # Handle the case where an employee does not exist, if needed
                    continue

            # Perform bulk update on Users and Employees
            # Add other fields as needed
            User.objects.bulk_update(users_to_update, [
                'email',
                'first_name',
                'last_name'
            ])
            Employee.objects.bulk_update(employees_to_update, [
                'contact',
                'middle_name',
                'gender',
                'address',
                'birth_date',
                'start_date',
                'status',
                'position',
                'position_level',
                'regular_date',
                'separation_date'
            ])

            # Update specialties for each employee
            for employee in employees_to_update:
                row = df[df['COMPANY ID'] == employee.company_id].iloc[0]
                specialties = row.get('POSITION SPECIALTIES', '')

                # Always clear existing specialties
                employee.position_specialties.clear()

                # If there are new specialties, add them
                if pd.notna(specialties) and specialties.strip() != '':
                    specialty_list = [specialty.strip()
                                      for specialty in specialties.split(',')]
                    employee.position_specialties.add(
                        *EmployeeJobSpecialty.objects.filter(name__in=specialty_list))

        return True

    except Exception as e:
        print(f"Error during update: {e}")
        return False


def handle_uploaded_file(f):
    file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', f.name)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path
