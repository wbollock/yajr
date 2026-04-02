import subprocess


def test_cli_renders_template(tmp_path):
    template = tmp_path / "t.j2"
    data = tmp_path / "d.yml"

    template.write_text("hello {{ name }}", encoding="utf-8")
    data.write_text("name: world\n", encoding="utf-8")

    result = subprocess.run(
        [
            "jinja-render",
            "--mode",
            "base",
            "--template-file",
            str(template),
            "--data-file",
            str(data),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "hello world"


def test_cli_renders_tab_indented_yaml_data(tmp_path):
    """CLI uses the same parse_data_blob path as the web app; tabs must be accepted."""
    template = tmp_path / "t.j2"
    data = tmp_path / "d.yml"

    template.write_text("{{ secret.token }}", encoding="utf-8")
    # Write a literal tab character for indentation — the same input that
    # triggers the bug when pasted into the web UI.
    data.write_text("secret:\n\ttoken: abc\n", encoding="utf-8")

    result = subprocess.run(
        [
            "jinja-render",
            "--mode",
            "base",
            "--template-file",
            str(template),
            "--data-file",
            str(data),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "abc"


def _run_cli(tmp_path, template_text, data_text, extra_args=()):
    template = tmp_path / "t.j2"
    data = tmp_path / "d.yml"
    template.write_text(template_text, encoding="utf-8")
    data.write_text(data_text, encoding="utf-8")
    return subprocess.run(
        ["jinja-render", "--mode", "base", "--template-file", str(template), "--data-file", str(data), *extra_args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_cli_strict_mode_reports_undefined_variable(tmp_path):
    """--strict renders an error message (not a crash) for undefined variables."""
    result = _run_cli(tmp_path, "{{ missing }}", "x: 1", extra_args=["--strict"])
    # Renderer catches the UndefinedError and returns it as a string; exit 0.
    assert result.returncode == 0
    assert "Rendering error" in result.stdout


def test_cli_returns_nonzero_on_malformed_data(tmp_path):
    """A data file that is neither valid JSON nor valid YAML causes a non-zero exit."""
    result = _run_cli(tmp_path, "{{ x }}", "{unclosed: brace")
    assert result.returncode != 0


def test_cli_trim_blocks_removes_block_tag_newline(tmp_path):
    """--trim strips the newline after block tags, matching web-app behaviour."""
    tmpl = "{% if true %}\nhello\n{% endif %}"
    result = _run_cli(tmp_path, tmpl, "{}", extra_args=["--trim"])
    assert result.returncode == 0
    # With trim_blocks the newline after the block tag is consumed.
    assert result.stdout.strip() == "hello"
