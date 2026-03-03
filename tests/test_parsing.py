import pytest

from jinja_parser.core.parse import parse_data_blob


def test_parse_yaml_mapping():
    assert parse_data_blob("a: 1") == {"a": 1}


def test_parse_json_mapping():
    assert parse_data_blob('{"a": 1}') == {"a": 1}


def test_parse_empty_defaults_to_empty_mapping():
    assert parse_data_blob("") == {}


def test_parse_non_mapping_fails():
    with pytest.raises(ValueError):
        parse_data_blob("- a\n- b")
