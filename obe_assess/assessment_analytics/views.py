from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from assessment_marking.models import GradedSubmission

class SubmissionCLOAnalyticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, submission_id, *args, **kwargs):
        submission = get_object_or_404(GradedSubmission, id=submission_id)
        data = submission.ai_result_json or {}
        per_q = data.get('per_question', {}) if isinstance(data, dict) else {}
        clo_summary = data.get('clo_summary', {}) if isinstance(data.get('clo_summary', {}), dict) else {}

        # If clo_summary is missing, compute from per_question
        if not clo_summary and per_q:
            for _, qdata in per_q.items():
                clo = qdata.get('mapped_clo') or qdata.get('clo') or 'UNMAPPED'
                try:
                    obtained = int(qdata.get('marks_awarded', 0) or 0)
                except Exception:
                    try:
                        obtained = int(float(qdata.get('marks_awarded', 0) or 0))
                    except Exception:
                        obtained = 0
                try:
                    possible = int(qdata.get('max_marks', 0) or 0)
                except Exception:
                    try:
                        possible = int(float(qdata.get('max_marks', 0) or 0))
                    except Exception:
                        possible = 0

                agg = clo_summary.setdefault(clo, {'obtained': 0, 'possible': 0})
                agg['obtained'] += obtained
                agg['possible'] += possible

        # Build chart-friendly list
        chart = []
        total_obtained = 0
        total_possible = 0
        for clo, totals in sorted(clo_summary.items(), key=lambda x: x[0]):
            obtained = totals.get('obtained', 0) or 0
            possible = totals.get('possible', 0) or 0
            total_obtained += obtained
            total_possible += possible
            percent = round((obtained / possible * 100), 2) if possible > 0 else 0
            chart.append({
                'clo': clo,
                'obtained': obtained,
                'possible': possible,
                'percent': percent
            })

        return Response({
            'submission_id': str(submission.id),
            'student_name': data.get('student_name') if isinstance(data, dict) else None,
            'cms_id': data.get('cms_id') if isinstance(data, dict) else None,
            'total_obtained': total_obtained,
            'total_possible': total_possible,
            'clo_summary': clo_summary,
            'clo_chart': chart
        })
