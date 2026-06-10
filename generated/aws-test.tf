resource "aws_instance" "web_server_test" {
  ami           = "ami-123456"
  instance_type = "t2.micro"

  tags = {
    Name        = "ProvisionedServer"
    Environment = "test"
  }
}