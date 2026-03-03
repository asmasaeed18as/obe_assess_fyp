from assessment_creation.models import Assessment
from .models import GradedSubmission


def map_submission_clos(submission):
    """
    Map per-question entries to CLOs for a single submission using the latest
    assessment for the submission's course. Updates clo_summary and totals.
    """
    try:
        course_obj = submission.course
        if not course_obj:
            return

        assessment = Assessment.objects.filter(course=course_obj).order_by('-created_at').first()
        qmap = []
        clo_by_index = []
        if assessment:
            r = assessment.result_json or {}
            qs = r.get('questions', []) if isinstance(r, dict) else []
            for q in qs:
                qtext = (q.get('question') or '').strip()
                meta = q.get('meta', {}) if isinstance(q.get('meta', {}), dict) else {}
                clo = meta.get('clo') or q.get('clo') or 'UNMAPPED'
                qid = q.get('id')
                qmap.append({'text': qtext, 'clo': clo, 'id': qid})
            try:
                ordered = sorted(qmap, key=lambda x: int(x.get('id')))
            except Exception:
                ordered = qmap
            clo_by_index = [item.get('clo') or 'UNMAPPED' for item in ordered]

        per_q = submission.ai_result_json.get('per_question', {}) if isinstance(submission.ai_result_json, dict) else {}
        per_q_items = list(per_q.items())
        for qid, qdata in per_q_items:
            mapped = qdata.get('mapped_clo') or qdata.get('clo')
            if not mapped:
                qtext = (qdata.get('question') or '').strip()
                nq = qtext.lower()
                for m in qmap:
                    mq = (m.get('text') or '').lower()
                    if not mq:
                        continue
                    if nq == mq or nq in mq or mq in nq:
                        mapped = m.get('clo')
                        break
            if not mapped and clo_by_index:
                try:
                    qnum = int(''.join([c for c in str(qid) if c.isdigit()])) - 1
                except Exception:
                    qnum = None
                if qnum is not None and 0 <= qnum < len(clo_by_index):
                    mapped = clo_by_index[qnum]
            # 4) Final fallback: map by iteration order if keys are non-numeric
            if not mapped and clo_by_index:
                try:
                    idx = [k for k, _ in per_q_items].index(qid)
                except Exception:
                    idx = None
                if idx is not None and 0 <= idx < len(clo_by_index):
                    mapped = clo_by_index[idx]
            if mapped:
                qdata['mapped_clo'] = mapped

        clo_agg = {}
        total_obtained = 0
        total_possible = 0

        for _, qdata in per_q.items():
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

        submission.ai_result_json['per_question'] = per_q
        submission.ai_result_json['clo_summary'] = clo_agg
        summary = submission.ai_result_json.get('summary', {}) if isinstance(submission.ai_result_json.get('summary', {}), dict) else {}
        if summary.get('total_obtained') != total_obtained:
            summary['total_obtained'] = total_obtained
        if not summary.get('total_possible') or summary.get('total_possible') != total_possible:
            summary['total_possible'] = total_possible
        try:
            summary['percentage'] = round((summary['total_obtained'] / summary['total_possible'] * 100), 2) if summary.get('total_possible', 0) > 0 else summary.get('percentage', 0)
        except Exception:
            pass
        submission.ai_result_json['summary'] = summary
        submission.save()
    except Exception:
        return


def remap_course_submissions(course):
    """
    Re-map all submissions for a course to ensure CLO mapping is up to date.
    """
    if not course:
        return 0
    count = 0
    for submission in GradedSubmission.objects.filter(course=course):
        map_submission_clos(submission)
        count += 1
    return count
