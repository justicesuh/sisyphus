from sisyphus.jobs.tasks import parse_json_response


class TestParseJsonResponse:
    """Tests for the parse_json_response utility."""

    def test_plain_json(self):
        result = parse_json_response('{"score": 80, "explanation": "Good fit"}')
        assert result == {'score': 80, 'explanation': 'Good fit'}

    def test_json_in_code_block(self):
        result = parse_json_response('```\n{"score": 75}\n```')
        assert result == {'score': 75}

    def test_json_in_labeled_code_block(self):
        result = parse_json_response('```json\n{"score": 90, "explanation": "Excellent"}\n```')
        assert result == {'score': 90, 'explanation': 'Excellent'}
