from rest_framework import serializers
from .models import GradedSubmission

class GradedSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradedSubmission
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'ai_result_json']