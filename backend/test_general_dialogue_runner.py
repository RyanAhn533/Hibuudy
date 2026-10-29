"""Runner isolation and capture checks; zero live model calls."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / 'research/physio/eval/run_general_dialogue.py'


def execute(tmp_path, *args):
    env = dict(os.environ, CEREBRAS_API_KEY='synthetic-inherited-secret',
               CLAUDE_API_KEY='synthetic-must-not-fallback',
               LLM_CASCADE='gemini,groq', CEREBRAS_MODEL='must-not-inherit')
    result = subprocess.run(
        [sys.executable, str(SCRIPT), '--output-root', str(tmp_path), *args],
        env=env, capture_output=True, text=True, encoding='utf-8', timeout=40,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert 'synthetic-inherited-secret' not in result.stdout + result.stderr
    assert 'synthetic-must-not-fallback' not in result.stdout + result.stderr
    summary = json.loads(result.stdout.strip().splitlines()[-1])
    data = json.loads((Path(summary['run_dir']) / 'results.json').read_text(encoding='utf-8'))
    return result, summary, data


def test_mock_runs_twelve_exact_baseline_cases_without_quality_claims(tmp_path):
    process, summary, data = execute(tmp_path)
    assert process.returncode == 0, process.stderr
    assert summary['selected_cases'] == summary['provider_attempts'] == 12
    assert summary['api_success_count'] == summary['normal_complete_count'] == 12
    assert summary['api_failure_count'] == 0
    assert data['actual_provider_call_count'] == data['external_attempt_count'] == 0
    assert data['mock_provider_call_count'] == 12
    assert data['generation_settings'] == {'max_tokens':400,'temperature':.3,
        'cascade':['cerebras'],'retry_count':0,'max_output_tokens_all_selected':4800}
    assert data['model_quality_review'] == 'not_run'
    assert all(r['decision'] is None and r['rubric_scores'] is None for r in data['results'])
    for entry in data['results'][:12]:
        assert entry['execution_status'] == 'mock_completed'
        assert entry['observed_http_status'] == 200
        assert entry['observed_model'] == 'gpt-oss-120b'
        assert entry['provider_raw_response']['finish_reason'] == 'stop'
        assert entry['provider_raw_response']['assistant_content'] == entry['displayed_response']
    assert all(entry['execution_status'] == 'not_run' for entry in data['results'][12:])
    for path in Path(summary['run_dir']).glob('*.json'):
        content = path.read_text(encoding='utf-8')
        assert 'MUST_NOT_BE_SAVED' not in content
        assert 'synthetic-inherited-secret' not in content


@pytest.mark.parametrize('status', [401, 402, 403, 429])
def test_auth_billing_or_rate_limit_stops_without_retry_or_fallback(tmp_path, status):
    process, summary, data = execute(tmp_path, '--mock-status', str(status), '--max-cases', '3')
    assert process.returncode == 3
    assert summary['provider_attempts'] == 1
    assert summary['execution_status'] == 'stopped_unreviewed'
    assert summary['api_failure_count'] == 1
    assert summary['api_success_count'] == summary['normal_complete_count'] == 0
    assert data['stop_reason'] == f'provider_http_{status}'
    first = data['results'][0]
    assert first['provider_raw_response']['http_status'] == status
    assert first['provider_raw_response']['assistant_content'] is None
    assert first['observed_http_status'] == 503
    assert first['displayed_response'] is None
    for entry in data['results'][1:3]:
        assert entry['execution_status'] == 'not_run'
        assert entry['not_run_reason'] == f'provider_http_{status}'
    assert data['actual_provider_call_count'] == 0


def test_subset_is_once_and_not_selected_cases_stay_unrun(tmp_path):
    process, summary, data = execute(tmp_path, '--case-id','G03','--case-id','G11')
    assert process.returncode == 0
    assert data['requested_case_ids'] == ['G03','G11']
    assert summary['provider_attempts'] == 2
    assert [e['case_id'] for e in data['results'] if e['execution_status'] == 'mock_completed'] == ['G03','G11']


@pytest.mark.parametrize('finish_reason', ['length', 'content_filter'])
def test_mock_preserves_incomplete_finish_metadata_and_leaves_review_pending(tmp_path, finish_reason):
    process, summary, data = execute(tmp_path, '--max-cases', '1',
                                     '--mock-finish-reason', finish_reason)
    assert process.returncode == 4
    assert summary['provider_attempts'] == 1
    assert summary['execution_status'] == 'completed_with_response_failures_unreviewed'
    assert summary['api_failure_count'] == 1
    assert summary['api_success_count'] == summary['normal_complete_count'] == 0
    first = data['results'][0]
    assert first['provider_raw_response']['finish_reason'] == finish_reason
    assert first['finish_reason_requires_review'] is True
    assert first['decision'] is None and first['rubric_scores'] is None
    # Incomplete or filtered text must never become a successful visible reply.
    assert first['observed_http_status'] == 503
    assert first['displayed_response'] is None


def test_server_failure_is_nonzero_but_preserves_results_and_continues(tmp_path):
    process, summary, data = execute(tmp_path, '--mock-status', '500', '--max-cases', '2')
    assert process.returncode == 4
    assert summary['provider_attempts'] == 2
    assert summary['stop_reason'] is None
    assert summary['execution_status'] == 'completed_with_response_failures_unreviewed'
    assert summary['api_failure_count'] == 2
    assert summary['api_success_count'] == summary['normal_complete_count'] == 0
    for entry in data['results'][:2]:
        assert entry['execution_status'] == 'response_failed_unreviewed'
        assert entry['observed_http_status'] == 503
        assert entry['displayed_response'] is None
        assert entry['decision'] is None and entry['rubric_scores'] is None
