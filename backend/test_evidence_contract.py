"""Synthetic scalar contract regressions; never downloads a model or calls AI."""
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas.evidence import PhysioEvidenceBundle


def evidence_fixture():
    end = datetime.now(timezone.utc) - timedelta(seconds=1)
    return {
        'schema_version': 1,
        'bundle_id': '00000000-0000-4000-8000-000000000011',
        'data_origin': 'synthetic', 'created_at': end.isoformat(),
        'window': {'start': (end - timedelta(seconds=240)).isoformat(),
                   'end': end.isoformat(), 'sampling_rate_hz': 50.0,
                   'sample_count': 12000},
        'quality': {'status': 'usable', 'reasons': [], 'valid_fraction': 1.0},
        'model': {'id': 'pulseppg', 'checkpoint_sha256': 'a' * 64,
                  'embedding_dim': 512, 'adaptation': 'none'},
        'features': [{'id': 'embedding_l2_norm', 'value': 1.5,
                      'unit': 'dimensionless', 'source': 'encoder_summary',
                      'source_id': '00000000-0000-4000-8000-000000000012'}],
        'personal_baseline': None, 'predictions': [],
        'limitations': ['not_emotion_classifier', 'no_personal_baseline',
                        'synthetic_input', 'not_field_validated'],
    }


def request_fixture():
    return {'turn_id': '00000000-0000-4000-8000-000000000013',
            'evidence': evidence_fixture(),
            'consent': {'granted': True, 'purpose': 'physio_evidence_dialogue',
                        'provider': 'gemini', 'consent_version': 1}}


def test_valid_contract_and_published_schema_match():
    bundle = PhysioEvidenceBundle.model_validate(evidence_fixture())
    assert bundle.personal_baseline is None and bundle.predictions == []
    schema = json.loads((Path(__file__).parents[1] / 'contracts' /
                         'physio_evidence.v1.schema.json').read_text(encoding='utf-8'))
    schema.pop('$schema')
    assert schema == PhysioEvidenceBundle.model_json_schema()


@pytest.mark.parametrize('path,value', [
    (('schema_version',), True),
    (('schema_version',), 2),
    (('name',), 'private-name'),
    (('raw_ppg',), [0.2]),
    (('embedding',), [0.2]),
    (('coordinates',), {'lat': 37, 'lon': 127}),
    (('subject_id',), 'another-person'),
    (('window', 'sample_count'), 100),
    (('window', 'sampling_rate_hz'), '50'),
    (('window', 'sampling_rate_hz'), float('nan')),
    (('window', 'sample_count'), True),
    (('created_at',), '2026-10-01T12:00:00'),
    (('personal_baseline',), {'mean': 1}),
    (('predictions',), [{'emotion': 'happy'}]),
    (('model', 'adaptation'), 'lora'),
    (('model', 'checkpoint_sha256'), 'unknown'),
    (('quality', 'valid_fraction'), .5),
    (('quality', 'reasons'), ['private-note']),
    (('limitations',), ['no_personal_baseline']),
])
def test_invalid_or_sensitive_evidence_is_rejected(path, value):
    data = evidence_fixture()
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        PhysioEvidenceBundle.model_validate(data)


@pytest.mark.parametrize('key,value', [('value', float('inf')), ('value', True),
                                    ('value', -1), ('unit', 'bpm'),
                                    ('source', 'signal_summary'),
                                    ('id', 'stress')])
def test_feature_identity_units_and_finiteness(key, value):
    data = evidence_fixture()
    data['features'][0][key] = value
    with pytest.raises(ValidationError):
        PhysioEvidenceBundle.model_validate(data)


def test_duplicate_features_and_future_source_window_rejected():
    data = evidence_fixture()
    data['features'].append(copy.deepcopy(data['features'][0]))
    with pytest.raises(ValidationError):
        PhysioEvidenceBundle.model_validate(data)
    data = evidence_fixture()
    data['created_at'] = data['window']['start']
    with pytest.raises(ValidationError):
        PhysioEvidenceBundle.model_validate(data)


@pytest.mark.parametrize('offset_seconds,expected', [
    (-601, 'evidence_stale'), (-600, None), (30, None), (31, 'evidence_stale'),
])
def test_dialogue_freshness_matches_mobile_boundary(offset_seconds, expected):
    from services.evidence_service import evidence_denial
    now = datetime(2026, 10, 12, 12, tzinfo=timezone.utc)
    end = now + timedelta(seconds=offset_seconds)
    data = evidence_fixture()
    data['window']['start'] = (end - timedelta(seconds=240)).isoformat()
    data['window']['end'] = end.isoformat()
    data['created_at'] = end.isoformat()
    assert evidence_denial(PhysioEvidenceBundle.model_validate(data), now) == expected
