terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }
  required_version = ">= 1.2.0"
}

provider "aws" {
  region = "us-east-1"
}

locals {
  common_tags = {
    Environment = "staging"
    ManagedBy   = "Self-Service-Provisioner-Bot"
  }
}


resource "aws_instance" "web_instance" {
  
  
  ami = "ami-0c55b159cbfafe1f0"
  
  
  
  instance_type = "t2.micro"
  
  

  tags = merge(
    local.common_tags,
    {
      Name = "web_instance"
    }
  )
}
