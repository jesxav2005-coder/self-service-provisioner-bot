import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate(environment_type):

    if environment_type.lower() == "docker":
        file_path = os.path.join(BASE_DIR, "templates", "docker.tpl")

    elif environment_type.lower() == "aws":
        file_path = os.path.join(BASE_DIR, "templates", "aws.tpl")

    else:
        return "Invalid Environment Type"

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


if __name__ == "__main__":
    print("===================================")
    print(" Self-Service Provisioner Bot ")
    print("===================================")

    env_type = input("Enter environment type (docker/aws): ")
    env_name = input("Enter environment name (dev/test/staging): ")

    print(f"\nGenerating {env_type.upper()} template for {env_name.upper()} environment...\n")
    print(generate(env_type))