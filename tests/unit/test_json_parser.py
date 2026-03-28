"""Unit tests for the JSON parser utility."""

import pytest
from casp.utils.json_parser import extract_json


def test_raw_json_object():
    result = extract_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_json_in_code_fence():
    text = '```json\n{"key": "value"}\n```'
    assert extract_json(text) == {"key": "value"}


def test_json_in_plain_fence():
    text = '```\n{"key": "value"}\n```'
    assert extract_json(text) == {"key": "value"}


def test_json_embedded_in_prose():
    text = 'Here is the result:\n\n{"key": "value"}\n\nHope this helps!'
    assert extract_json(text) == {"key": "value"}


def test_json_array():
    result = extract_json('[1, 2, 3]')
    assert result == [1, 2, 3]


def test_invalid_json_raises():
    with pytest.raises(ValueError, match="Could not extract"):
        extract_json("This is just plain text with no JSON")
