# assessment_creation/serializers.py
from rest_framework import serializers
from .models import LectureMaterial, Assessment

class LectureMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = LectureMaterial
        fields = ['id', 'title', 'file', 'uploaded_at', 'extracted_text']

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = [
            'id', 
            'material', 
            'assessment_type', 
            'questions_config',  # ✅ Added: Contains the list of question settings
            'clo',               # Summary string (optional)
            'bloom_level',       # Summary string (optional)
            'created_at', 
            'result_json', 
            'pdf'
        ]
        read_only_fields = ['created_at', 'result_json', 'pdf']