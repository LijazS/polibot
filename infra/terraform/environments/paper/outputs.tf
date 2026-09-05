output "aws_region" {
  value = var.aws_region
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnet_id" {
  value = aws_subnet.public.id
}

output "security_group_id" {
  value = aws_security_group.host.id
}

output "ec2_instance_id" {
  value = aws_instance.app.id
}

output "ec2_private_ip" {
  value = aws_instance.app.private_ip
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "application_data_bucket" {
  value = aws_s3_bucket.data.id
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.host.name
}

