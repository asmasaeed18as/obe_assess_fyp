#!/usr/bin/env python
"""
Direct verification of LLM integration
"""
import os
import sys

# Add path
sys.path.insert(0, r'D:\Fyp\obe_assess_fyp\obe_assess')
os.chdir(r'D:\Fyp\obe_assess_fyp\obe_assess')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'obe_assess.settings')

import django
django.setup()

# Now run tests
from django.conf import settings

print("LLM Integration Verification")
print("=" * 50)

# Test imports
try:
    from llm_integration.views import GenerateAssessmentView, MarkQuestionView
    from llm_integration.serializers import GenerateAssessmentSerializer, MarkingRequestSerializer
    from llm_integration.utils import parse_and_clean_assessment
    print("[PASS] All imports successful")
except Exception as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Test app registration
if 'llm_integration' in settings.INSTALLED_APPS:
    print("[PASS] llm_integration in INSTALLED_APPS")
else:
    print("[FAIL] llm_integration NOT in INSTALLED_APPS")
    sys.exit(1)

# Test serializer
data = {
    "text": "Sample text",
    "assessment_type": "Quiz/MCQs",
    "questions_config": [
        {
            "id": 1,
            "clo": "test",
            "bloom_level": "Remember",
            "difficulty": "Easy",
            "weightage": "5"
        }
    ]
}

serializer = GenerateAssessmentSerializer(data=data)
if serializer.is_valid():
    print("[PASS] Serializer validation works")
else:
    print(f"[FAIL] Serializer errors: {serializer.errors}")

# Test env variables
api_key = os.getenv('GROQ_API_KEY')
base_url = os.getenv('GROQ_BASE_URL')
model = os.getenv('GROQ_MODEL')

print(f"[INFO] GROQ_API_KEY set: {bool(api_key and api_key != 'your_groq_api_key_here')}")
print(f"[INFO] GROQ_BASE_URL: {base_url}")
print(f"[INFO] GROQ_MODEL: {model}")

print("=" * 50)
print("LLM Integration is ready to test!")
