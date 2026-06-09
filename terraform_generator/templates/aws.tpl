resource "aws_instance" "web_server" {
  ami           = "ami-123456"
  instance_type = "t2.micro"

  tags = {
    Name = "ProvisionedServer"
  }
}