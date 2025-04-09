from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import Curriculum
from .excel import ExcelProcessor
import json
import tempfile
import os

# Create your views here.

class ExcelUploadView(View):
    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return HttpResponseBadRequest('No file uploaded')
            
        excel_file = request.FILES['file']
        preview_only = request.POST.get('preview', 'true').lower() == 'true'
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            for chunk in excel_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
            
        try:
            processor = ExcelProcessor()
            data, warnings = processor.preview_data(temp_path)
            
            if preview_only:
                response_data = {
                    'status': 'preview',
                    'warnings': warnings,
                    'data': data
                }
            else:
                # Create or update curriculum
                curriculum_code = os.path.splitext(excel_file.name)[0]
                curriculum, created = Curriculum.objects.update_or_create(
                    curriculum_code=curriculum_code,
                    defaults={'courses_data': data}
                )
                
                response_data = {
                    'status': 'success',
                    'message': f'{"Created" if created else "Updated"} curriculum {curriculum_code}',
                    'warnings': warnings,
                    'curriculum_code': curriculum_code
                }
                
            return JsonResponse(response_data)
            
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing file: {str(e)}'
            }, status=500)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class ExcelDownloadView(View):
    def get(self, request, curriculum_code, *args, **kwargs):
        curriculum = get_object_or_404(Curriculum, curriculum_code=curriculum_code)
        
        try:
            processor = ExcelProcessor()
            
            # Create temporary file for Excel export
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                temp_path = temp_file.name
            
            # Export curriculum data to Excel
            processor.export_excel(curriculum.courses_data, temp_path)
            
            # Read the file and create response
            with open(temp_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{curriculum_code}.xlsx"'
                return response
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error exporting file: {str(e)}'
            }, status=500)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class ExcelTemplateView(View):
    def get(self, request, *args, **kwargs):
        try:
            processor = ExcelProcessor()
            
            # Create temporary file for template
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                temp_path = temp_file.name
            
            # Generate template file
            processor.generate_template(temp_path)
            
            # Read the file and create response
            with open(temp_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="curriculum_template.xlsx"'
                return response
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error generating template: {str(e)}'
            }, status=500)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
