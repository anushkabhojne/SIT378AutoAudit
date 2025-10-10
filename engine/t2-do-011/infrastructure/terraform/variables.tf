variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "aws_availability_zone" {
  description = "AWS availability zone"
  type        = string
  default     = "us-east-1a"
}

variable "admin_cidr" {
  description = "CIDR block for admin SSH access"
  type        = string
  default     = "203.0.113.0/24"
}

variable "ami_id" {
  description = "AMI ID for scanning runner"
  type        = string
  default     = "ami-0abcdef1234567890"
}

variable "instance_type" {
  description = "Instance type for scanning runner"
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "SSH key name for instance access"
  type        = string
  default     = "autoaudit-key"
}