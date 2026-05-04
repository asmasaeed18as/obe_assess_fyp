from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from assessment_marking.models import GradedSubmission

def _build_clo_summary(data):
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

    return clo_summary

def _build_chart(clo_summary):
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
    return chart, total_obtained, total_possible

def _aggregate_submissions(submissions):
    combined = {}
    for submission in submissions:
        data = submission.ai_result_json or {}
        clo_summary = _build_clo_summary(data)
        for clo, totals in clo_summary.items():
            agg = combined.setdefault(clo, {'obtained': 0, 'possible': 0})
            agg['obtained'] += totals.get('obtained', 0) or 0
            agg['possible'] += totals.get('possible', 0) or 0
    chart, total_obtained, total_possible = _build_chart(combined)
    return combined, chart, total_obtained, total_possible

class SubmissionCLOAnalyticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, submission_id, *args, **kwargs):
        submission = get_object_or_404(GradedSubmission, id=submission_id)
        data = submission.ai_result_json or {}
        clo_summary = _build_clo_summary(data)
        chart, total_obtained, total_possible = _build_chart(clo_summary)

        return Response({
            'submission_id': str(submission.id),
            'student_name': data.get('student_name') if isinstance(data, dict) else None,
            'cms_id': data.get('cms_id') if isinstance(data, dict) else None,
            'total_obtained': total_obtained,
            'total_possible': total_possible,
            'clo_summary': clo_summary,
            'clo_chart': chart
        })

class BatchSubmissionCLOAnalyticsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        ids = request.data.get('submission_ids') or []
        if not isinstance(ids, list) or not ids:
            return Response({"status": "error", "details": "submission_ids must be a non-empty list."}, status=400)

        combined = {}
        for sid in ids:
            try:
                submission = GradedSubmission.objects.get(id=sid)
            except Exception:
                continue
            data = submission.ai_result_json or {}
            clo_summary = _build_clo_summary(data)
            for clo, totals in clo_summary.items():
                agg = combined.setdefault(clo, {'obtained': 0, 'possible': 0})
                agg['obtained'] += totals.get('obtained', 0) or 0
                agg['possible'] += totals.get('possible', 0) or 0

        chart, total_obtained, total_possible = _build_chart(combined)
        return Response({
            'submission_ids': ids,
            'total_obtained': total_obtained,
            'total_possible': total_possible,
            'clo_summary': combined,
            'clo_chart': chart
        })

def _detect_assessment_type(title):
    t = (title or '').lower()
    if any(w in t for w in ['quiz', 'mcq', 'mcqs']):
        return 'Quiz'
    if any(w in t for w in ['exam', 'final', 'midterm', 'mid-term', 'mid term']):
        return 'Exam'
    if any(w in t for w in ['lab', 'practical']):
        return 'Lab'
    if any(w in t for w in ['project']):
        return 'Project'
    return 'Assignment'


class AllSubmissionsCLOAnalyticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        from calendar import month_abbr as _month_abbr

        submissions = GradedSubmission.objects.all()

        clo_students = {}
        monthly_data = {}
        type_clo_raw = {}

        for s in submissions:
            ai = s.ai_result_json or {}
            per_q = ai.get('per_question', {}) if isinstance(ai, dict) else {}
            student_name = ai.get('student_name') if isinstance(ai, dict) else None
            cms_id = ai.get('cms_id') if isinstance(ai, dict) else None

            student_totals = {}
            overall_obtained = 0
            overall_possible = 0

            for qid, qdata in per_q.items():
                try:
                    obtained = int(qdata.get('marks_awarded', 0) or 0)
                except Exception:
                    obtained = 0
                try:
                    possible = int(qdata.get('max_marks', 0) or 0)
                except Exception:
                    possible = 0
                mapped_clo = qdata.get('mapped_clo') or qdata.get('clo') or 'UNMAPPED'
                agg = student_totals.setdefault(mapped_clo, {'obtained': 0, 'possible': 0})
                agg['obtained'] += obtained
                agg['possible'] += possible
                overall_obtained += obtained
                overall_possible += possible

            for clo, totals in student_totals.items():
                p, o = totals['possible'], totals['obtained']
                percent = round(o / p * 100, 2) if p > 0 else None
                clo_students.setdefault(clo, []).append(
                    {'cms_id': cms_id, 'student_name': student_name, 'percent': percent}
                )

            if overall_possible > 0:
                pct = round(overall_obtained / overall_possible * 100, 2)
                monthly_data.setdefault((s.created_at.year, s.created_at.month), []).append(pct)

            atype = _detect_assessment_type(s.title)
            type_entry = type_clo_raw.setdefault(atype, {})
            for clo, totals in student_totals.items():
                p, o = totals['possible'], totals['obtained']
                if p > 0:
                    type_entry.setdefault(clo, []).append(round(o / p * 100, 2))

        # Build clo_attainment with distributions
        clo_attainment = {}
        for clo, students in clo_students.items():
            percents = [s['percent'] for s in students if isinstance(s.get('percent'), (int, float))]
            avg = round(sum(percents) / len(percents), 2) if percents else None
            buckets = {"0-50": 0, "50-60": 0, "60-70": 0, "70-80": 0, "80-90": 0, "90-100": 0}
            for p in percents:
                if p < 50:   buckets["0-50"] += 1
                elif p < 60: buckets["50-60"] += 1
                elif p < 70: buckets["60-70"] += 1
                elif p < 80: buckets["70-80"] += 1
                elif p < 90: buckets["80-90"] += 1
                else:        buckets["90-100"] += 1
            clo_attainment[clo] = {
                'total_students': len(students),
                'average_percent': avg,
                'distribution': buckets,
            }

        clo_chart = []
        avg_values = []
        for clo, stats in sorted(clo_attainment.items()):
            avg = stats.get('average_percent')
            if isinstance(avg, (int, float)):
                avg_values.append(avg)
                clo_chart.append({'clo': clo, 'obtained': avg, 'possible': 100, 'percent': avg})
            else:
                clo_chart.append({'clo': clo, 'obtained': 0, 'possible': 100, 'percent': 0})

        historical_trend = [
            {'month': f"{_month_abbr[m]} {y}", 'avg_attainment': round(sum(pcts) / len(pcts), 2)}
            for (y, m), pcts in sorted(monthly_data.items())
        ]

        assessment_type_stats = {
            atype: {clo: round(sum(pcts) / len(pcts), 2) for clo, pcts in clo_pcts.items()}
            for atype, clo_pcts in type_clo_raw.items()
        }

        # Keep clo_summary for backward compat with other views
        combined, _, total_obtained, total_possible = _aggregate_submissions(submissions)

        return Response({
            'total_obtained': total_obtained,
            'total_possible': total_possible,
            'clo_summary': combined,
            'clo_attainment': clo_attainment,
            'clo_chart': clo_chart,
            'historical_trend': historical_trend,
            'assessment_type_stats': assessment_type_stats,
        })
