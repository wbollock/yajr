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
