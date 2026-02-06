import json
import re
from typing import Any

from celery import shared_task


def parse_json_response(response: str) -> dict[str, Any]:
    """Parse a JSON response, handling markdown code blocks."""
    text = response.strip()
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def calculate_job_score(self: Any, job_id: int, resume_id: int) -> dict[str, Any]:
    """Calculate a fit score between a job and a resume using OpenAI."""
    from sisyphus.core.services import get_openai  # noqa: PLC0415
    from sisyphus.jobs.models import Job  # noqa: PLC0415
    from sisyphus.resumes.models import Resume  # noqa: PLC0415

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return {'error': 'Job not found'}

    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        job.score_task_id = ''
        job.save(update_fields=['score_task_id'])
        return {'error': 'Resume not found'}

    if not job.description:
        return {'error': 'Job has no description'}

    if not resume.text:
        return {'error': 'Resume has no extracted text'}

    openai_service = get_openai()

    system = (
        'You are a job fit analyst. Compare the resume against the job description '
        'and evaluate how well the candidate matches the role.\n\n'
        'Return a JSON object the following keys:\n'
        '- score: integer from 0-100 representing overall fit\n'
        '- explanation: one sentence explanation of why this score was assigned\n\n'
        'Be objective and realistic in your assessment. A score of 70+ indicates a strong match, '
        '50-69 is moderate, below 50 is weak.'
    )

    prompt = f"""Job Title: {job.title}
Company: {job.company.name}

Job Description:
{job.description}

---

Resume:
{resume.text}"""

    try:
        response = openai_service.complete(prompt, system)
        result = parse_json_response(response)

        job.score = result.get('score')
        job.score_explanation = result.get('explanation', '')
        job.score_task_id = ''
        job.save(update_fields=['score', 'score_explanation', 'score_task_id'])
    except json.JSONDecodeError:
        job.score_task_id = ''
        job.save(update_fields=['score_task_id'])
        return {'error': 'Failed to parse response', 'raw_response': response}
    except Exception as exc:  # noqa: BLE001
        if self.request.retries >= self.max_retries:
            job.score_task_id = ''
            job.save(update_fields=['score_task_id'])
        self.retry(exc=exc)
    else:
        return result
