from rest_framework import serializers
from typing import List, Optional


class QuestionConfigSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    clo = serializers.CharField()
    bloom_level = serializers.CharField()
    difficulty = serializers.CharField()
    weightage = serializers.CharField()
    question_type = serializers.CharField(required=False, default="Standard")


class GenerateAssessmentSerializer(serializers.Serializer):
    text = serializers.CharField()
    assessment_type = serializers.CharField()
    questions_config = QuestionConfigSerializer(many=True)


class GradingCriterionSerializer(serializers.Serializer):
    criterion = serializers.CharField()
    marks = serializers.IntegerField()


class MarkingRequestSerializer(serializers.Serializer):
    question_text = serializers.CharField()
    student_answer = serializers.CharField()
    max_marks = serializers.IntegerField()
    criteria = GradingCriterionSerializer(many=True, required=False)
