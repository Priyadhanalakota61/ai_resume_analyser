import json
from unittest.mock import Mock
import pytest
from pydantic import ValidationError
from app.services import gemini_analyzer as analyzer


def test_provider_schema_retains_structure_and_enum():
    schema = analyzer.provider_schema(analyzer.AnalysisInsights)
    requirement = schema['properties']['requirements']['items']
    assert requirement['properties']['status']['enum'] == ['matched', 'not_found']
    assert set(requirement['required']) == {'requirement', 'status', 'resume_evidence', 'job_evidence'}
    assert set(schema['required']) == set(analyzer.AnalysisInsights.model_fields)
    serialized = json.dumps(schema)
    for keyword in ['$ref', '$defs', 'minLength', 'maxLength', 'maxItems']:
        assert keyword not in serialized
    assert analyzer.AnalysisInsights.model_json_schema()['properties']['requirements']['maxItems'] == 40


def test_generate_uses_simple_schema_but_validates_original(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'synthetic-key')
    client = Mock()
    context = Mock()
    context.__enter__ = Mock(return_value=client)
    context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(analyzer.genai, 'Client', lambda **kw: context)
    data = dict(requirements=[], skills_found=[], skills_missing=[], suggestions=[], interview_questions=[])
    client.models.generate_content.return_value.text = json.dumps(data)
    assert analyzer.generate_structured('Synthetic prompt', analyzer.AnalysisInsights).requirements == []
    config = client.models.generate_content.call_args.kwargs['config']
    assert config['response_schema'] == analyzer.provider_schema(analyzer.AnalysisInsights)
    data['interview_questions'] = ['Synthetic question'] * 9
    client.models.generate_content.return_value.text = json.dumps(data)
    with pytest.raises(analyzer.GeminiAnalysisError, match='unexpected response format'):
        analyzer.generate_structured('Synthetic prompt', analyzer.AnalysisInsights)


def test_requirement_bounds_remain_enforced():
    with pytest.raises(ValidationError):
        analyzer.RequirementMatch(requirement='Python', status='matched', resume_evidence='Python', job_evidence='short')
