"""Ephemeral evidence validation and minimal provider projection; no storage."""
from datetime import datetime, timedelta, timezone

from schemas.dialogue import ProviderProposal
from schemas.evidence import PhysioEvidenceBundle


def evidence_denial(bundle: PhysioEvidenceBundle, now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    if bundle.quality.status != 'usable':
        return 'evidence_unusable'
    if bundle.created_at > now + timedelta(seconds=30):
        return 'evidence_stale'
    if bundle.window.end < now - timedelta(minutes=10):
        return 'evidence_stale'
    return None


def provider_projection(bundle: PhysioEvidenceBundle):
    # No device/turn/bundle identity, absolute timestamp, raw signal, embedding,
    # checkpoint or any caller-provided free text is sent to a model.
    return {
        'data_origin': bundle.data_origin,
        'quality': bundle.quality.model_dump(mode='json'),
        'features': [f.model_dump(mode='json') for f in bundle.features],
        'personal_baseline': None,
        'predictions': [],
        'limitations': list(bundle.limitations),
    }


def validate_proposal(proposal: ProviderProposal, bundle: PhysioEvidenceBundle):
    features = {f.id: f for f in bundle.features}
    allowed_sources = {f.source_id for f in bundle.features}
    if (len(set(proposal.expression_ids)) != len(proposal.expression_ids)
            or len(set(proposal.source_ids)) != len(proposal.source_ids)
            or not set(proposal.source_ids).issubset(allowed_sources)):
        raise ValueError('duplicate or unsupported proposal reference')
    if len({f.id for f in proposal.facts}) != len(proposal.facts):
        raise ValueError('duplicate fact')
    for fact in proposal.facts:
        original = features.get(fact.id)
        if original is None or fact != original:
            raise ValueError('fact must exactly copy an input feature and its provenance')
        if fact.source_id not in proposal.source_ids:
            raise ValueError('fact source must be cited')
    return proposal
