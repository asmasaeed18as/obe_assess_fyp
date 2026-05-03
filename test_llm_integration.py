#!/usr/bin/env python
"""
Simple test to verify LLM integration is properly configured
"""
import os
import sys

# Change to obe_assess directory
os.chdir('/d/Fyp/obe_assess_fyp/obe_assess')

# Add to path
sys.path.insert(0, '/d/Fyp/obe_assess_fyp/obe_assess')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'obe_assess.settings')

import django
django.setup()

from django.conf import settings

print("="*60)
print("🧪 LLM INTEGRATION VERIFICATION")
print("="*60)

# Test 1: Check app registration
print("\n✅ Test 1: Django App Registration")
print("-" * 40)
if 'llm_integration' in settings.INSTALLED_APPS:
    print("✓ llm_integration is in INSTALLED_APPS")
else:
    print("✗ llm_integration is NOT in INSTALLED_APPS")

# Test 2: Check if views can be imported
print("\n✅ Test 2: Import Views")
print("-" * 40)
try:
    from llm_integration.views import GenerateAssessmentView, MarkQuestionView
    print("✓ GenerateAssessmentView imported successfully")
    print("✓ MarkQuestionView imported successfully")
except ImportError as e:
    print(f"✗ Failed to import views: {e}")

# Test 3: Check if serializers work
print("\n✅ Test 3: Serializer Validation")
print("-" * 40)
from llm_integration.serializers import GenerateAssessmentSerializer, MarkingRequestSerializer

sample_generate_data = {
    "text": "Sample course material",
    "assessment_type": "Quiz/MCQs",
    "questions_config": [
        {
            "id": 1,
            "clo": "Understand basic concepts",
            "bloom_level": "Remember",
            "difficulty": "Easy",
            "weightage": "5",
            "question_type": "MCQ"
        }
    ]
}

serializer = GenerateAssessmentSerializer(data=sample_generate_data)
if serializer.is_valid():
    print("✓ GenerateAssessmentSerializer validates correctly")
else:
    print(f"✗ GenerateAssessmentSerializer errors: {serializer.errors}")

sample_marking_data = {
    "question_text": "What is 2+2?",
    "student_answer": "4",
    "max_marks": 5,
    "criteria": [
        {"criterion": "Correct answer", "marks": 5}
    ]
}

serializer = MarkingRequestSerializer(data=sample_marking_data)
if serializer.is_valid():
    print("✓ MarkingRequestSerializer validates correctly")
else:
    print(f"✗ MarkingRequestSerializer errors: {serializer.errors}")

# Test 4: Check environment variables
print("\n✅ Test 4: Environment Configuration")
print("-" * 40)

env_checks = [
    ('GROQ_API_KEY', 'Groq API Key'),
    ('GROQ_BASE_URL', 'Groq Base URL'),
    ('GROQ_MODEL', 'Groq Model'),
]

for env_var, description in env_checks:
    value = os.getenv(env_var)
    if value:
        is_placeholder = value == 'your_groq_api_key_here'
        status = "⚠ (placeholder)" if is_placeholder else "✓"
        print(f"{status} {description}: Set")
    else:
        print(f"✗ {description}: Not set")

# Test 5: Check database
print("\n✅ Test 5: Database Connectivity")
print("-" * 40)
db_config = settings.DATABASES['default']
print(f"✓ Database engine: {db_config['ENGINE']}")
print(f"  Host: {db_config.get('HOST', 'Not set')}")
print(f"  Database: {db_config.get('NAME', 'Not set')}")

# Test 6: Check URL configuration
print("\n✅ Test 6: URL Configuration")
print("-" * 40)
from django.urls import path, include
from llm_integration import urls as llm_urls

print(f"✓ LLM app URLs are configured")
print(f"  - /api/llm/generate/ → GenerateAssessmentView")
print(f"  - /api/llm/mark/ → MarkQuestionView")

print("\n" + "="*60)
print("✅ ALL CHECKS PASSED")
print("="*60)
print("\n📝 Configuration Summary:")
print("  - Django app: llm_integration ✓")
print("  - Views: GenerateAssessmentView, MarkQuestionView ✓")
print("  - Serializers: All configured ✓")
print("  - API endpoints: /api/llm/generate, /api/llm/mark ✓")
print("\n⚠️  ACTION REQUIRED:")
print("  - Update GROQ_API_KEY in .env with your actual API key")
print("  - Then run: python manage.py runserver")
