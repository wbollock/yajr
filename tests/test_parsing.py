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


def test_parse_whitespace_only_returns_empty():
    # Tabs, spaces, and newlines with no real content should be empty.
    assert parse_data_blob("   \t\n\t  \n") == {}


def test_parse_yaml_null_returns_empty():
    # A YAML null/empty document should produce an empty mapping, not raise.
    assert parse_data_blob("null") == {}
    assert parse_data_blob("~") == {}


def test_parse_yaml_scalar_raises():
    # A bare scalar (not a mapping) must be rejected.
    with pytest.raises(ValueError, match="mapping"):
        parse_data_blob("just_a_string")


def test_parse_invalid_yaml_raises():
    # Structurally broken YAML that is also not JSON must raise ValueError.
    with pytest.raises(ValueError, match="Data parse error"):
        parse_data_blob("{unclosed: brace")


def test_parse_json_takes_priority_over_yaml():
    # Input that is valid JSON must be parsed as JSON (not YAML).
    result = parse_data_blob('{"a": 1, "b": true}')
    assert result == {"a": 1, "b": True}


def test_parse_tab_in_json_string_value_preserved():
    # Only leading (indentation) tabs are replaced; a tab inside a JSON string
    # value is mid-line and must be left intact.
    raw = '{"key": "val\twith tab"}'
    result = parse_data_blob(raw)
    assert result["key"] == "val\twith tab"
