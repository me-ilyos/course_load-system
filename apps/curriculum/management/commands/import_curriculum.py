from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from curriculum.excel import ExcelProcessor
from curriculum.models import Curriculum
import os
import json

class Command(BaseCommand):
    help = 'Import curriculum data from Excel files'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str,
                          help='Excel file(s) to import')
        parser.add_argument('--preview', action='store_true',
                          help='Preview data without saving')
        parser.add_argument('--force', action='store_true',
                          help='Force import even with warnings')

    def handle(self, *args, **options):
        processor = ExcelProcessor()
        
        for file_path in options['files']:
            if not os.path.exists(file_path):
                self.stderr.write(
                    self.style.ERROR(f'File not found: {file_path}')
                )
                continue

            try:
                self.stdout.write(
                    self.style.NOTICE(f'Processing {file_path}...')
                )
                
                # Preview or import the data
                if options['preview']:
                    data, warnings = processor.preview_data(file_path)
                    
                    # Display warnings
                    if warnings:
                        self.stdout.write(
                            self.style.WARNING('\nWarnings:')
                        )
                        for warning in warnings:
                            self.stdout.write(f'  - {warning}')
                    
                    # Display preview
                    self.stdout.write('\nPreview of parsed data:')
                    for code, course in data.items():
                        self.stdout.write(f'\n{code}:')
                        self.stdout.write(
                            f"  Name: {course['name']}"
                        )
                        self.stdout.write(
                            f"  Type: {course['type']}"
                        )
                        self.stdout.write(
                            f"  Semesters: {len(course['semesters'])}"
                        )
                        
                else:
                    # Actual import
                    data, warnings = processor.preview_data(file_path)
                    
                    if warnings and not options['force']:
                        self.stdout.write(
                            self.style.WARNING('\nWarnings found:')
                        )
                        for warning in warnings:
                            self.stdout.write(f'  - {warning}')
                        self.stdout.write(
                            '\nUse --force to import anyway, or --preview to see details'
                        )
                        continue
                    
                    # Create or update curriculum
                    curriculum_code = os.path.splitext(
                        os.path.basename(file_path)
                    )[0]
                    
                    curriculum, created = Curriculum.objects.update_or_create(
                        curriculum_code=curriculum_code,
                        defaults={
                            'courses_data': data
                        }
                    )
                    
                    action = 'Created' if created else 'Updated'
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'{action} curriculum {curriculum_code} successfully'
                        )
                    )
                    
            except ValidationError as e:
                self.stderr.write(
                    self.style.ERROR(f'Validation error in {file_path}: {str(e)}')
                )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f'Error processing {file_path}: {str(e)}')
                ) 