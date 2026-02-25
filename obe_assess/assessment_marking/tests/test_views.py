from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock
import tempfile
import os

from course_management.models import Course
from assessment_marking.models import GradedSubmission

class GradeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.course = Course.objects.create(code='CS101', title='Intro')

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('assessment_marking.views.mark_assessment_logic')
    def test_grade_view_attaches_course_and_saves_ai_result(self, mock_mark_logic):
        # Mock grading result
        mock_mark_logic.return_value = {
            'student_name': 'Tester',
            'cms_id': 'S1001',
            'summary': {'total_obtained': 12, 'total_possible': 20, 'percentage': 60},
            'per_question': {'Q1': {'marks_awarded': 6, 'max_marks': 10, 'question': 'Q1?'}},
        }

        student_file = SimpleUploadedFile('student.txt', b'student content')
        rubric_file = SimpleUploadedFile('rubric.txt', b'rubric content')

        url = reverse('grade_assessment')
        resp = self.client.post(url, {
            'student_file': student_file,
            'rubric_file': rubric_file,
            'title': 'Test Grading',
            'course_id': str(self.course.id)
        }, format='multipart')

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')

        # Submission created and linked to course
        sid = data['data']['id']
        sub = GradedSubmission.objects.get(id=sid)
        self.assertIsNotNone(sub.course)
        self.assertEqual(sub.course.id, self.course.id)
        self.assertIn('summary', sub.ai_result_json)
        self.assertIn('per_question', sub.ai_result_json)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('assessment_marking.views.mark_assessment_logic')
    def test_grade_view_maps_clos_into_per_question(self, mock_mark_logic):
        # Provide assessment with question->CLO mapping
        # Create an assessment pointing to this course with result_json containing questions
        from assessment_creation.models import Assessment
        a = Assessment.objects.create(assessment_type='Quiz', course=self.course, material_id=None, result_json={
            'questions': [
                {'id': 1, 'question': 'What is X?', 'marks': 5, 'meta': {'clo': 'CLO-1'}},
                {'id': 2, 'question': 'Explain Y', 'marks': 5, 'meta': {'clo': 'CLO-2'}}
            ]
        })

        mock_mark_logic.return_value = {
            'student_name': 'Tester',
            'cms_id': 'S1001',
            'summary': {'total_obtained': 8, 'total_possible': 10, 'percentage': 80},
            'per_question': {
                'Q1': {'marks_awarded': 4, 'max_marks': 5, 'question': 'What is X?'},
                'Q2': {'marks_awarded': 4, 'max_marks': 5, 'question': 'Explain Y'}
            },
        }

        student_file = SimpleUploadedFile('student.txt', b'student content')
        rubric_file = SimpleUploadedFile('rubric.txt', b'rubric content')

        url = reverse('grade_assessment')
        resp = self.client.post(url, {
            'student_file': student_file,
            'rubric_file': rubric_file,
            'title': 'Test Grading',
            'course_id': str(self.course.id)
        }, format='multipart')

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        sid = data['data']['id']
        sub = GradedSubmission.objects.get(id=sid)

        # After view runs, ai_result_json.per_question entries should contain mapped_clo
        per_q = sub.ai_result_json.get('per_question', {})
        # Each q entry should have mapped_clo matching the assessment's meta
        mapped = [q.get('mapped_clo') for q in per_q.values()]
        self.assertIn('CLO-1', mapped)
        self.assertIn('CLO-2', mapped)

        # clo_summary should exist and aggregate totals
        self.assertIn('clo_summary', sub.ai_result_json)
        clo_summary = sub.ai_result_json['clo_summary']
        self.assertIn('CLO-1', clo_summary)
        self.assertIn('CLO-2', clo_summary)
        self.assertIn('summary', sub.ai_result_json)

