"""Evaluation asset/DTO checks only; NOT model response-quality scoring."""
import copy
from datetime import datetime
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas.dialogue import PhysioDialogueRequest
from services.evidence_service import evidence_denial


ROOT = Path(__file__).resolve().parents[1] / 'research/physio/eval'
SUITE = json.loads((ROOT / 'dialogue_cases.ko.v1.json').read_text(encoding='utf-8'))


def merge(base, patch):
    value = copy.deepcopy(base)
    for key, replacement in patch.items():
        if isinstance(replacement, dict) and isinstance(value.get(key), dict):
            value[key] = merge(value[key], replacement)
        else:
            value[key] = copy.deepcopy(replacement)
    return value


def test_eval_assets_explicitly_have_no_inference_or_reviews():
    cases = SUITE['cases']
    assert len(cases) == len({c['id'] for c in cases}) == 20
    assert sum(c['path'] == 'general_chat' for c in cases) == 12
    assert SUITE['network_authorized'] is False
    assert SUITE['status'] == 'prepared_not_model_evaluated'
    for case in cases:
        assert case['synthetic'] is True
        assert case['execution_status'] == 'not_run'
        assert case['observed_response'] is None and case['review'] is None
        assert case['human_acceptance'] and case['critical_failure_types']


def test_requests_match_current_endpoint_contracts_without_calling_models():
    from main import AgentRequest
    clock = datetime.fromisoformat(SUITE['reference_clock_utc'].replace('Z', '+00:00'))
    original = copy.deepcopy(SUITE['request_templates'])
    for case in SUITE['cases']:
        if case['path'] == 'general_chat':
            body = AgentRequest.model_validate(case['request'])
            # These cases target the API, not known app-local intent branches.
            assert not any(word in body.input for word in
                           ['전화', '엄마', '아빠', '선생님', '119', '약', '복용', '일정'])
            continue
        body = merge(SUITE['request_templates'][case['request_template']],
                     case['request_merge_patch'])
        if case['id'] == 'P07':
            with pytest.raises(ValidationError):
                PhysioDialogueRequest.model_validate(body)
            continue
        request = PhysioDialogueRequest.model_validate(body)
        assert request.evidence.data_origin == 'synthetic'
        if case['id'] in {'P04', 'P05'}:
            assert evidence_denial(request.evidence, now=clock) == case['expected_boundary']['reason_code']
        elif case['id'] == 'P06':
            assert request.consent.granted is False
        elif case['id'] == 'P08':
            # Router rejects any query before provider work (covered separately).
            assert case['query'] == {'user_id': 'synthetic-other-person'}
        else:
            assert evidence_denial(request.evidence, now=clock) is None
    assert SUITE['request_templates'] == original


def test_results_template_is_complete_and_unscored():
    template = json.loads((ROOT / 'dialogue_results.template.json').read_text(encoding='utf-8'))
    assert template['execution_status'] == 'not_run'
    assert template['actual_provider_call_count'] is None
    assert template['provider'] is None and template['model_id'] is None
    assert template['reviewers'] == []
    assert [r['case_id'] for r in template['results']] == [c['id'] for c in SUITE['cases']]
    for result in template['results']:
        assert result['execution_status'] == 'not_run'
        assert all(value is None for key, value in result.items()
                   if key not in {'case_id', 'execution_status'})
