import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from items.utils import insert_excel_items_price_adjustments


class Command(BaseCommand):
    help = 'Insert new items price adjustments from a given XLSX file'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', type=str, help='The path to the XLSX file containing the employee data.')

    def handle(self, *args, **kwargs):
        filename = kwargs['filename']

        # Load the file into a DataFrame
        if filename.endswith('.csv'):
            # df = pd.read_csv(filename, engine='python',
            #                  encoding='latin-1', date_format='%Y-%m-%d')
            df = pd.read_csv(filename, engine='python')
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filename)
        else:
            raise CommandError("The file must be a XLSX format.")

        if insert_excel_items_price_adjustments(df):
            self.stdout.write(self.style.SUCCESS(
                'Successfully inserted new items price adjustments.'))
        else:
            raise CommandError(
                "Command insert_excel_items_price_adjustments fail")
