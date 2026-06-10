from terraform_generator.generator import generate


def test_generate_docker_template():
    template = generate("docker", "dev")
    assert "services:" in template
    assert "container_name: web_server_dev" in template
    assert "ENVIRONMENT=dev" in template


def test_generate_aws_template_dev():
    template = generate("aws", "dev")
    assert "resource \"aws_instance\" \"web_server_dev\"" in template
    assert "instance_type = \"t2.micro\"" in template
    assert "Environment = \"dev\"" in template


def test_generate_aws_template_prod():
    template = generate("aws", "prod")
    assert "instance_type = \"t3.large\"" in template
    assert "Environment = \"prod\"" in template


def test_generate_invalid_type():
    assert generate("unknown", "dev") == "Invalid Environment Type"
