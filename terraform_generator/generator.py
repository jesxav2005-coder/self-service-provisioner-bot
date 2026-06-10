import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _get_instance_type(env_name: str) -> str:
    env = env_name.lower()
    if env == "prod":
        return "t3.large"
    if env == "qa":
        return "t3.small"
    return "t2.micro"


def generate(environment_type: str, env_name: str = "dev") -> str:
    if environment_type.lower() == "docker":
        file_path = os.path.join(BASE_DIR, "templates", "docker.tpl")
    elif environment_type.lower() == "aws":
        file_path = os.path.join(BASE_DIR, "templates", "aws.tpl")
    else:
        return "Invalid Environment Type"

    with open(file_path, "r", encoding="utf-8") as file:
        template = file.read()

    if environment_type.lower() == "docker":
        return template.replace("{{ENV_NAME}}", env_name)

    return template.replace("{{ENV_NAME}}", env_name).replace(
        "{{INSTANCE_TYPE}}", _get_instance_type(env_name)
    )


if __name__ == "__main__":
    print("===================================")
    print(" Self-Service Provisioner Bot ")
    print("===================================")

    env_type = input("Enter environment type (docker/aws): ")
    env_name = input("Enter environment name (dev/test/staging): ")

    print(f"\nGenerating {env_type.upper()} template for {env_name.upper()} environment...\n")
    print(generate(env_type))