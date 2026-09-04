output "archive_bucket" {
  value = aws_s3_bucket.archive.id
}

output "database_endpoint" {
  value     = aws_db_instance.database.endpoint
  sensitive = true
}

output "host_instance_id" {
  value = aws_instance.host.id
}

