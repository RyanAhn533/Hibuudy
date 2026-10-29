"""Bounded Gemini proposal; fixed text cannot assert inferred emotion/cause."""
import asyncio
import json

from schemas.dialogue import (EXPRESSIONS, QUESTIONS, PhysioDialogueRequest,
                              PhysioDialogueResponse, ProviderProposal)
from services.evidence_service import (evidence_denial, provider_projection,
                                       validate_proposal)
from services.physio_provider_policy import denial_reason

PROVIDER_TIMEOUT_SECONDS = 12
MAX_PROVIDER_RESPONSE_BYTES = 16_384
SYSTEM_PROMPT = '''Return only one JSON object containing question_id,
expression_ids, source_ids, facts. question_id must be choose_words;
select at most three expression_ids from wait_please, help_please,
stop_now, no_thanks. These are optional communication choices, not an inferred
state. Use only provided source_ids. facts may be [] or exact copies of supplied
feature objects. No other fields. A frozen PPG embedding and scalar summaries
are NOT emotion, stress, cause, intention, diagnosis, or evidence of support
success. There is no personal baseline or trained classifier. Never interpret
synthetic/public measurements as the current user's state. The scalar features
do not justify preferring any expression; these are test choices, not a learned
recommendation. No field-validated AAC catalog is connected in this first slice.
No actions, writing memory, tools, or automatic speech are allowed.'''


def unavailable(reason, body: PhysioDialogueRequest | None = None):
    return PhysioDialogueResponse(
        status='unavailable', reason_code=reason,
        turn_id=body.turn_id if body else None,
        bundle_id=body.evidence.bundle_id if body else None,
        provider=None, question=QUESTIONS['choose_words'],
        expression_ids=list(EXPRESSIONS), source_ids=[], facts=[],
        limitations=['not_emotion_classifier', 'no_personal_baseline'],
    )


async def propose(body: PhysioDialogueRequest, *, generate, provider_configured):
    denied = denial_reason(body.consent, provider_configured=provider_configured())
    if denied:
        return unavailable(denied, body)
    denied = evidence_denial(body.evidence)
    if denied:
        return unavailable(denied, body)
    payload = json.dumps(provider_projection(body.evidence), ensure_ascii=False,
                         allow_nan=False, separators=(',', ':'))
    try:
        raw = await asyncio.wait_for(
            generate(SYSTEM_PROMPT, payload, json_mode=True, max_tokens=600),
            timeout=PROVIDER_TIMEOUT_SECONDS,
        )
    except (asyncio.TimeoutError, TimeoutError):
        return unavailable('provider_timeout', body)
    except Exception:
        # Never log provider exception bodies, URLs, credentials or evidence.
        return unavailable('provider_error', body)
    if denial_reason(body.consent, provider_configured=provider_configured()):
        return unavailable('consent_changed', body)
    try:
        if not isinstance(raw, str) or len(raw.encode('utf-8')) > MAX_PROVIDER_RESPONSE_BYTES:
            raise ValueError('invalid response size or type')
        proposal = ProviderProposal.model_validate_json(raw)
        validate_proposal(proposal, body.evidence)
    except (ValueError, TypeError):
        return unavailable('invalid_provider_response', body)
    return PhysioDialogueResponse(
        status='proposal', reason_code='none', turn_id=body.turn_id,
        bundle_id=body.evidence.bundle_id, provider='gemini',
        question=QUESTIONS[proposal.question_id],
        expression_ids=proposal.expression_ids, source_ids=proposal.source_ids,
        facts=proposal.facts, limitations=list(body.evidence.limitations),
    )
