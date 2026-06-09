resource "aws_instance" "web_server_{{ENV_NAME}}" {
  ami           = "ami-123456"
  instance_type = "{{INSTANCE_TYPE}}"

  tags = {
    Name        = "ProvisionedServer"
    Environment = "{{ENV_NAME}}"
  }
}