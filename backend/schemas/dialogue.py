"""Closed proposal vocabulary; no free-form diagnosis or automatic action."""
from typing import Literal
from uuid import UUID

from pydantic import Field, StrictBool, field_validator

from schemas.evidence import (EvidenceFeature, PhysioEvidenceBundle,
                              StrictContract)

ExpressionId = Literal['wait_please', 'help_please', 'stop_now', 'no_thanks']
QuestionId = Literal['choose_words']

# Fixed test phrases, not field-validated AAC or inferred physiology states.
EXPRESSIONS = {
    'wait_please': '잠깐 기다려 주세요.',
    'help_please': '도와주세요.',
    'stop_now': '그만할래요.',
    'no_thanks': '안 할래요.',
}
QUESTIONS = {
    'choose_words': '지금 어떤 말이 필요한가요?',
}


class PhysioConsent(StrictContract):
    granted: StrictBool
    purpose: Literal['physio_evidence_dialogue']
    provider: Literal['gemini']
    consent_version: Literal[1]

    @field_validator('consent_version', mode='before')
    @classmethod
    def integer_version(cls, value):
        if type(value) is not int:
            raise ValueError('consent_version must be an integer')
        return value


class PhysioDialogueRequest(StrictContract):
    turn_id: UUID
    evidence: PhysioEvidenceBundle
    consent: PhysioConsent


class ProviderProposal(StrictContract):
    question_id: QuestionId
    expression_ids: list[ExpressionId] = Field(min_length=1, max_length=3)
    source_ids: list[UUID] = Field(min_length=1, max_length=4)
    facts: list[EvidenceFeature] = Field(max_length=4)


class PhysioDialogueResponse(StrictContract):
    status: Literal['proposal', 'unavailable']
    reason_code: Literal['none', 'disabled', 'consent_required',
                         'provider_unconfigured', 'invalid_request',
                         'evidence_unusable', 'evidence_stale',
                         'provider_timeout', 'provider_error',
                         'invalid_provider_response', 'consent_changed']
    turn_id: UUID | None
    bundle_id: UUID | None
    provider: Literal['gemini'] | None
    question: str
    expression_ids: list[ExpressionId]
    source_ids: list[UUID]
    facts: list[EvidenceFeature]
    limitations: list[str]
    proposal_only: Literal[True] = True
