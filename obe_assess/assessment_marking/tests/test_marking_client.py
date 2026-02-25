from django.test import TestCase, override_settings
from unittest.mock import patch, Mock
import tempfile
import os

from assessment_marking.grading_logic import marking_client

class MarkingClientTests(TestCase):

    @patch('assessment_marking.grading_logic.marking_client.requests.post')
    def test_call_mark_api_parses_marks(self, mock_post):
        # Mock successful response from LLM service
        mock_resp = Mock()
        mock_resp.raise_for_status.return_va*ue = None
        mock_resp.json.return_value = {
            'marks_awarded': 8,
            'max_marks': 10,
            'feedback': 'Good answer.'
        }
        mock_post.return_value = mock_resp

        res = marking_client.call_mark_api("Q?", "Ans", [], 10)
        self.assertIsInstance(res, dict)
        self.assertEqual(res['marks_awarded'], 8)
        self.assertEqual(res['max_marks'], 10)
        self.assertIn('feedback', res)

    @patch('assessment_marking.grading_logic.marking_client.preprocess')
    @patch('assessment_marking.grading_logic.marking_client.requests.post')
    def test_mark_assessment_logic_creates_csv_and_summary(self, mock_post, mock_preprocess):
        # Setup preprocess outputs for student and rubric documents
        student_data = {
            'student_info': {'student_name': 'Test Student', 'cms_id': 'S1001'},
            'questions': {
                'Q1': {'question': 'What is X?', 'answer': 'A',},
                'Q2': {'question': 'Explain Y', 'answer': 'B',},
            }
        }
        rubric_data = {
            'criteria_map': {
                'Q1': [{'criterion': 'resp', 'marks': 5}],
                'Q2': [{'criterion': 'resp', 'marks': 5}],
            },
            'total_marks': 10
        }
        mock_preprocess.side_effect = [student_data, rubric_data]

        # Mock mark API to return deterministic marks
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {'marks_awarded': 4, 'max_marks': 5, 'feedback': 'ok'}
        mock_post.return_value = mock_resp

        tmpdir = tempfile.mkdtemp()
        with override_settings(MEDIA_ROOT=tmpdir):
            res = marking_client.mark_assessment_logic('/path/student.docx', '/path/rubric.docx')

            # CSV should be created
            files = os.listdir(os.path.join(tmpdir, 'grading_reports'))
            self.assertTrue(any(f.startswith('Grading_Report_') for f in files))

            # Summary keys
            self.assertIn('summary', res)
            self.assertIn('per_question', res)
            self.assertIn('per_question', res)
            self.assertIn('total_obtained', res['summary'])
            self.assertIn('total_possible', res['summary'])
            self.assertIn('percentage', res['summary'])

            # per_question entries exist for Q1 and Q2
            self.assertIn('Q1', res['per_question'])
            self.assertIn('Q2', res['per_question'])

        # cleanup
        try:
            import shutil
            shutil.rmtree(tmpdir)
        except Exception:
            pass
