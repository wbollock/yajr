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
