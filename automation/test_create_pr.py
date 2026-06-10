import pathlib
from automation import create_pr


def test_generate_infra_files(tmp_path, monkeypatch):
    monkeypatch.setattr(create_pr, "ROOT", tmp_path)
    monkeypatch.setattr(create_pr, "generate", lambda env_type, env_name: f"generated-{env_type}-{env_name}")

    generated_files = create_pr.generate_infra_files(env_types=["docker"], env_names=["dev"])
    assert len(generated_files) == 1
    generated_file = generated_files[0]
    assert generated_file.exists()
    assert generated_file.read_text(encoding="utf-8") == "generated-docker-dev"
    assert generated_file.name == "docker-dev.yml"
