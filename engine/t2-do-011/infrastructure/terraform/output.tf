output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.scanning_vpc.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = aws_subnet.scanning_subnet.id
}

output "security_group_id" {
  description = "Security Group ID"
  value       = aws_security_group.scanning_sg.id
}

output "instance_public_ip" {
  description = "Public IP of scanning runner"
  value       = aws_instance.scanning_runner.public_ip
}