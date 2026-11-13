"""
Dual-path AI layer: a real OpenAI chat-completion call when `OPENAI_API_KEY`
is set, otherwise a fully offline, deterministic stub. This lets the entire
feedback pipeline (models, migrations, seed data, generate-feedback
endpoint, tests) be built, run, and tested with zero network access and
zero cost.

Unlike several sibling AI apps, there is no embeddings step and no vector
database here - this module makes exactly one kind of call: a single chat
completion that turns (resume_text, job_description) into structured
feedback plus a cover letter draft. The default chat model is
`gpt-5.4-mini` (set via the OPENAI_CHAT_MODEL env var) - deliberately
different from the `gpt-5.6-sol` default used by some sibling apps, per
this batch's intent to exercise different model names across apps.

*** IMPORTANT ***: the stub output is NOT a real critique - it is a
reproducible, template-based string built only from the literal
resume_text/job_description passed in (distinctive snippets of each are
quoted back so the output is clearly tied to that specific input). The same
(resume_text, job_description) pair always produces the same stub output -
this determinism is relied on by tests and by the seed-data migration.
Real feedback quality requires a real OPENAI_API_KEY so
`generate_resume_feedback` calls the real chat completions API.
"""
import json
import re

from django.conf import settings

STUB_PREFIX = "[STUB AI OUTPUT — set OPENAI_API_KEY for real output]"

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z+#.]{2,}")

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has",
    "are", "was", "were", "will", "you", "your", "our", "their", "they",
    "team", "role", "job", "work", "able", "years", "year", "using",
    "experience", "skills", "strong", "ability", "including", "etc",
}


def _snippet(text: str, length: int = 160) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= length:
        return cleaned
    return cleaned[:length].rsplit(" ", 1)[0] + "..."


def _keywords(text: str) -> set[str]:
    words = {w.lower() for w in _WORD_RE.findall(text or "")}
    return {w for w in words if w not in _STOPWORDS}


def is_stub_mode() -> bool:
    return not bool(settings.OPENAI_API_KEY)


def _build_prompt(resume_text: str, job_description: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are a career coach helping a job candidate improve "
                "their resume and draft a tailored cover letter. Respond "
                "with ONLY a JSON object with exactly two string keys: "
                "\"feedback\" (a structured critique covering strengths, "
                "gaps, and suggested edits, comparing the resume against "
                "the job description) and \"cover_letter_draft\" (a "
                "tailored cover letter draft referencing specifics from "
                "both the resume and the job description). No prose "
                "outside the JSON object."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Job description:\n{job_description}\n\n"
                f"Resume:\n{resume_text}"
            ),
        },
    ]


def _parse_ai_json(content: str, resume_text: str, job_description: str) -> dict:
    """Defensively parse the model's response. Falls back gracefully (never
    raises/crashes the request) if the model doesn't return valid JSON."""
    if content:
        candidate = content.strip()
        # Strip a ```json ... ``` fence if the model wrapped the object.
        fence_match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if fence_match:
            candidate = fence_match.group(0)
        try:
            parsed = json.loads(candidate)
            feedback = parsed.get("feedback")
            cover_letter_draft = parsed.get("cover_letter_draft")
            if feedback and cover_letter_draft:
                return {
                    "feedback": str(feedback),
                    "cover_letter_draft": str(cover_letter_draft),
                }
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

    # Fall back: the model replied but not in the requested JSON shape.
    # Use the raw content as the feedback (better than nothing) and
    # generate a stub cover letter draft so the request still succeeds.
    fallback = _stub_feedback(resume_text, job_description)
    return {
        "feedback": content.strip() if content else fallback["feedback"],
        "cover_letter_draft": fallback["cover_letter_draft"],
    }


def _stub_feedback(resume_text: str, job_description: str) -> dict:
    resume_snip = _snippet(resume_text)
    job_snip = _snippet(job_description)
    resume_words = _keywords(resume_text)
    job_words = _keywords(job_description)
    overlap = sorted(resume_words & job_words)
    missing = sorted(job_words - resume_words)[:8]
    matched = overlap[:8]

    feedback_lines = [
        STUB_PREFIX,
        "",
        "Strengths:",
        f"- Your resume already highlights relevant material: \"{resume_snip}\"",
        (
            f"- Keyword overlap with the job description: {', '.join(matched)}."
            if matched
            else "- No strong keyword overlap with the job description was detected."
        ),
        "",
        "Gaps:",
        (
            f"- Terms from the job description not found in your resume: {', '.join(missing)}."
            if missing
            else "- No obvious missing keywords were detected."
        ),
        f"- Job description focus: \"{job_snip}\"",
        "",
        "Suggested edits:",
        "- Mirror the job description's terminology where it honestly matches your experience.",
        "- Quantify achievements tied to the responsibilities mentioned above.",
        "- Trim unrelated detail so the strongest matches stand out near the top.",
    ]

    cover_letter_lines = [
        STUB_PREFIX,
        "",
        "Dear Hiring Manager,",
        "",
        (
            f"I am writing to apply for this role. The posting's focus on "
            f"\"{job_snip}\" lines up closely with my background, where I have "
            f"worked on \"{resume_snip}\"."
        ),
        (
            f"In particular, my experience with {', '.join(matched)} "
            "directly supports the responsibilities described in your posting."
            if matched
            else "I am confident my background makes me a strong fit for this role."
        ),
        "",
        "I would welcome the chance to discuss how my background can contribute to your team.",
        "",
        "Sincerely,",
        "A candidate",
    ]

    return {
        "feedback": "\n".join(feedback_lines),
        "cover_letter_draft": "\n".join(cover_letter_lines),
    }


def _client():
    """An OpenAI client pointed at whichever OpenAI-compatible endpoint is configured.

    With OPENAI_BASE_URL unset this is the stock client talking to
    api.openai.com, which is what this app did before. Set it to an Azure
    OpenAI resource's `/openai/v1/` path and the same client with the same
    key reaches Azure instead - Azure serves an OpenAI-compatible surface
    there, so no AzureOpenAI client and no branching is needed.

    The import lives here rather than at module scope so that a broken or
    absent `openai` install is raised inside the caller's try block, not at
    import time. See generate_resume_feedback for why that matters.
    """
    from openai import OpenAI

    base_url = getattr(settings, "OPENAI_BASE_URL", "") or ""
    # Passing base_url=None would override the library's own default with
    # nothing, so an unset value is left out of the call entirely.
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        **({"base_url": base_url} if base_url else {}),
    )


def generate_resume_feedback(
    resume_text: str,
    job_description: str,
    *,
    allow_remote: bool = True,
) -> dict:
    """Return {"feedback": str, "cover_letter_draft": str}.

    Real path (OPENAI_API_KEY set, allow_remote): a single OpenAI
    chat-completions call using OPENAI_CHAT_MODEL, prompted to return
    structured JSON. Defensively parsed - never raises on a malformed
    response.

    Stub path (no key, allow_remote=False, or any failure on the real path):
    a deterministic, template-based result derived only from the literal
    input text - see module docstring. The same inputs always produce the
    same output.

    Pass allow_remote=False from any caller that must not depend on a
    network service - the seed-data migration does, so that applying
    migrations never reaches out to a model.

    Client construction happens *inside* the try. It used to sit outside it,
    so a dependency or configuration fault - as opposed to a call failure -
    escaped this function instead of falling back to the stub, and took the
    whole migration down with it.
    """
    if allow_remote and settings.OPENAI_API_KEY:
        try:
            client = _client()
            response = client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=_build_prompt(resume_text, job_description),
            )
            content = response.choices[0].message.content
        except Exception:  # noqa: BLE001 - never let an AI/network error crash the request
            return _stub_feedback(resume_text, job_description)
        return _parse_ai_json(content, resume_text, job_description)

    return _stub_feedback(resume_text, job_description)
