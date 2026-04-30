import io
import zipfile
from unittest.mock import MagicMock, patch

from django.test import TestCase

from assessment_creation.models import Assessment, LectureMaterial
from assessment_creation.utils import (
    extract_text_from_pdf_filefield,
    generate_docx_assessment,
    generate_pdf_assessment,
    generate_zip_bundle,
)
from course_management.models import Course


class ExtractTextFromPdfTests(TestCase):
    @patch("assessment_creation.utils.fitz.open")
    def test_extract_text_from_pdf_filefield_reads_all_pages(self, mock_fitz_open):
        mock_page_1 = MagicMock()
        mock_page_1.get_text.return_value = "Page 1 "
        mock_page_2 = MagicMock()
        mock_page_2.get_text.return_value = "Page 2"
        mock_doc = MagicMock()
        mock_doc.__enter__.return_value = [mock_page_1, mock_page_2]
        mock_fitz_open.return_value = mock_doc

        django_file = MagicMock()
        django_file.read.return_value = b"%PDF-1.4"

        text = extract_text_from_pdf_filefield(django_file)

        self.assertEqual(text, "Page 1 Page 2")

    @patch("assessment_creation.utils.fitz.open", side_effect=Exception("bad pdf"))
    def test_extract_text_from_pdf_filefield_returns_empty_string_on_error(self, _mock_fitz_open):
        django_file = MagicMock()
        django_file.read.return_value = b"broken"

        text = extract_text_from_pdf_filefield(django_file)

        self.assertEqual(text, "")


class AssessmentDocumentGenerationTests(TestCase):
    def setUp(self):
        self.questions = [
            {
                "question": "Explain DFS.",
                "marks": 5,
                "answer": "Depth-first search explores one branch fully first.",
                "meta": {"clo": "CLO-1", "bloom": "C2"},
                "rubric": {"Accuracy": "2 marks", "Example": "3 marks"},
            }
        ]

    def test_generate_docx_assessment_returns_buffer(self):
        buffer = generate_docx_assessment(self.questions, "Quiz", "full")

        self.assertIsInstance(buffer, io.BytesIO)
        self.assertGreater(len(buffer.getvalue()), 0)

    def test_generate_pdf_assessment_returns_buffer(self):
        buffer = generate_pdf_assessment(self.questions, "Quiz", "questions_only")

        self.assertIsInstance(buffer, io.BytesIO)
        self.assertGreater(len(buffer.getvalue()), 0)


class ZipBundleGenerationTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(code="CS-303", title="Algorithms")
        self.material = LectureMaterial.objects.create(title="Graphs")
        self.assessment = Assessment.objects.create(
            course=self.course,
            material=self.material,
            assessment_type="Assignment",
            result_json={"questions": [{"question": "Sample"}]},
        )

    @patch("assessment_creation.utils.generate_docx_assessment")
    def test_generate_zip_bundle_contains_all_expected_docx_files(self, mock_generate_docx):
        mock_generate_docx.return_value = io.BytesIO(b"docx-content")

        zip_buffer = generate_zip_bundle(self.assessment, "docx")

        with zipfile.ZipFile(zip_buffer) as bundle:
            self.assertEqual(
                sorted(bundle.namelist()),
                [
                    "Grading_Rubrics.docx",
                    "Model_Answers.docx",
                    "Question_Paper.docx",
                ],
            )

    @patch("assessment_creation.utils.generate_pdf_assessment")
    def test_generate_zip_bundle_uses_pdf_generator_for_pdf_format(self, mock_generate_pdf):
        mock_generate_pdf.return_value = io.BytesIO(b"pdf-content")

        zip_buffer = generate_zip_bundle(self.assessment, "pdf")

        with zipfile.ZipFile(zip_buffer) as bundle:
            self.assertIn("Question_Paper.pdf", bundle.namelist())
            self.assertEqual(mock_generate_pdf.call_count, 3)
