terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }

  }

}

provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "scanning_vpc" {
  cidr_block = var.vpc_cidr
  
  tags = {
    Name = "autoaudit-scanning-vpc"
  }

}

resource "aws_subnet" "scanning_subnet" {
  vpc_id            = aws_vpc.scanning_vpc.id
  cidr_block        = var.subnet_cidr
  availability_zone = var.aws_availability_zone
  
  tags = {
    Name = "autoaudit-scanning-subnet"
  }
  
}

resource "aws_security_group" "scanning_sg" {
  name        = "autoaudit-scanning-sg"
  description = "Security group for container scanning infrastructure"
  vpc_id      = aws_vpc.scanning_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "scanning_runner" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.scanning_subnet.id
  vpc_security_group_ids = [aws_security_group.scanning_sg.id]
  key_name               = var.key_name

  tags = {
    Name = "autoaudit-scanning-runner"
  }
}