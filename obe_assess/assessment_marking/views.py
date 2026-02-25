import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import GradedSubmission
from .serializers import GradedSubmissionSerializer
from .grading_logic.marking_client import mark_assessment_logic # Import logic
from course_management.models import Course
from assessment_creation.models import Assessment

class GradeAssessmentView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = GradedSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            # 1. Save Files
            submission = serializer.save()
            # If course_id provided in request, attach it to the submission
            course_id = request.data.get('course_id') or request.data.get('course')
            if course_id and not submission.course:
                try:
                    course_obj = Course.objects.get(id=course_id)
                    submission.course = course_obj
                    submission.save()
                except Exception:
                    # ignore if invalid id
                    pass
            
            try:
                # 2. Get Absolute Paths
                s_path = os.path.join(settings.MEDIA_ROOT, str(submission.student_file))
                r_path = os.path.join(settings.MEDIA_ROOT, str(submission.rubric_file))

                # 3. Run Logic
                result = mark_assessment_logic(s_path, r_path)

                # 4. Save & Return
                submission.ai_result_json = result
                submission.save()

                # --- Attempt to map per_question entries to CLOs when course known ---
                try:
                    course_obj = submission.course
                    if course_obj:
                        # Build simple question->CLO map from Assessments for this course
                        qmap = []
                        assessments = Assessment.objects.filter(course=course_obj)
                        for a in assessments:
                            r = a.result_json or {}
                            qs = r.get('questions', []) if isinstance(r, dict) else []
                            for q in qs:
                                qtext = (q.get('question') or '').strip()
                                meta = q.get('meta', {}) if isinstance(q.get('meta', {}), dict) else {}
                                clo = meta.get('clo') or q.get('clo') or 'UNMAPPED'
                                qmap.append({'text': qtext, 'clo': clo})

                        per_q = submission.ai_result_json.get('per_question', {}) if isinstance(submission.ai_result_json, dict) else {}
                        for qid, qdata in per_q.items():
                            qtext = (qdata.get('question') or '').strip()
                            mapped = None
                            nq = qtext.lower()
                            for m in qmap:
                                mq = (m['text'] or '').lower()
                                if not mq:
                                    continue
                                if nq == mq or nq in mq or mq in nq:
                                    mapped = m['clo']
                                    break
                            if mapped:
                                qdata['mapped_clo'] = mapped

                        # --- NEW: compute per-CLO totals and overall totals ---
                        clo_agg = {}  # clo -> {'obtained': int, 'possible': int}
                        total_obtained = 0
                        total_possible = 0

                        for qid, qdata in per_q.items():
                            mapped_clo = qdata.get('mapped_clo') or 'UNMAPPED'
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

                            total_obtained += obtained
                            total_possible += possible

                            agg = clo_agg.setdefault(mapped_clo, {'obtained': 0, 'possible': 0})
                            agg['obtained'] += obtained
                            agg['possible'] += possible

                        # attach aggregates into ai_result_json under 'clo_summary' and update top-level summary
                        submission.ai_result_json['per_question'] = per_q
                        submission.ai_result_json['clo_summary'] = clo_agg
                        # prefer existing summary from marking logic but ensure totals are consistent with per-question data
                        summary = submission.ai_result_json.get('summary', {}) if isinstance(submission.ai_result_json.get('summary', {}), dict) else {}
                        summary_total_obtained = summary.get('total_obtained')
                        summary_total_possible = summary.get('total_possible')
                        if summary_total_obtained != total_obtained:
                            summary['total_obtained'] = total_obtained
                        if not summary_total_possible or summary_total_possible != total_possible:
                            summary['total_possible'] = total_possible
                        try:
                            summary['percentage'] = round((summary['total_obtained'] / summary['total_possible'] * 100), 2) if summary.get('total_possible', 0) > 0 else summary.get('percentage', 0)
                        except Exception:
                            pass
                        submission.ai_result_json['summary'] = summary

                        submission.save()
                except Exception as e:
                    print(f"CLO mapping skipped: {e}")
                
                return Response({"status": "success", "data": GradedSubmissionSerializer(submission).data})
            except Exception as e:
                print(f"Grading Error: {e}")
                return Response({"status": "error", "details": str(e)}, status=500)
        
        return Response(serializer.errors, status=400)


class GradedSubmissionDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, submission_id, *args, **kwargs):
        submission = get_object_or_404(GradedSubmission, id=submission_id)
        return Response(GradedSubmissionSerializer(submission).data)

class GradedSubmissionCLOAnalyticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, submission_id, *args, **kwargs):
        submission = get_object_or_404(GradedSubmission, id=submission_id)
        data = submission.ai_result_json or {}
        per_q = data.get('per_question', {}) if isinstance(data, dict) else {}
        clo_summary = data.get('clo_summary', {}) if isinstance(data.get('clo_summary', {}), dict) else {}

        # If clo_summary is missing, compute from per_question
        if not clo_summary and per_q:
            for qid, qdata in per_q.items():
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
