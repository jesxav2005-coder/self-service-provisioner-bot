from terraform_generator.generator import generate


def test_generate_docker_template():
    template = generate("docker")
    assert "services:" in template
    assert "container_name: web_server" in template


def test_generate_aws_template():
    template = generate("aws")
    assert "resource \"aws_instance\" \"web_server\"" in template
    assert "instance_type = \"t2.micro\"" in template


def test_generate_invalid_type():
    assert generate("unknown") == "Invalid Environment Type"
