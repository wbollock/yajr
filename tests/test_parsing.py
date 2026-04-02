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


def test_parse_yaml_tab_indented_mapping():
    # YAML forbids tabs for indentation; they should be expanded to spaces.
    data = "secret:\n\ttoken: abc"
    assert parse_data_blob(data) == {"secret": {"token": "abc"}}


def test_parse_yaml_nested_tab_indentation():
    data = "a:\n\tb:\n\t\tc: 1"
    assert parse_data_blob(data) == {"a": {"b": {"c": 1}}}


def test_parse_yaml_mixed_indentation_tabs_and_values():
    # Tabs in the user example: top-level key plus tab-indented nested keys.
    data = "art_env: production\nsecret:\n\tlinode_token: \"123\"\n\tregion: \"us-east-1\""
    result = parse_data_blob(data)
    assert result["art_env"] == "production"
    assert result["secret"]["linode_token"] == "123"
    assert result["secret"]["region"] == "us-east-1"
