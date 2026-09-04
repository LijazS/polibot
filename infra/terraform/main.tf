data "aws_vpc" "selected" {
  id = var.vpc_id
}

resource "aws_s3_bucket" "archive" {
  bucket_prefix = "polibot-${var.environment}-archive-"
}

resource "aws_s3_bucket_public_access_block" "archive" {
  bucket = aws_s3_bucket.archive.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "archive" {
  bucket = aws_s3_bucket.archive.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "archive" {
  bucket = aws_s3_bucket.archive.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/polibot/${var.environment}/app"
  retention_in_days = 90
}

resource "aws_security_group" "host" {
  name_prefix = "polibot-${var.environment}-host-"
  description = "Polibot host: egress only; no public ingress"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "TLS APIs via reviewed VPC egress path"
  }
}

resource "aws_security_group" "database" {
  name_prefix = "polibot-${var.environment}-database-"
  description = "PostgreSQL reachable only from the Polibot host"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.host.id]
  }
}

resource "aws_db_subnet_group" "database" {
  name_prefix = "polibot-${var.environment}-"
  subnet_ids  = var.private_subnet_ids
}

resource "aws_db_instance" "database" {
  identifier_prefix            = "polibot-${var.environment}-"
  engine                       = "postgres"
  engine_version               = "16"
  instance_class               = "db.t4g.micro"
  allocated_storage            = 20
  max_allocated_storage        = 100
  storage_encrypted            = true
  db_name                      = var.database_name
  username                     = var.database_username
  manage_master_user_password  = true
  db_subnet_group_name         = aws_db_subnet_group.database.name
  vpc_security_group_ids       = [aws_security_group.database.id]
  publicly_accessible          = false
  backup_retention_period      = 14
  deletion_protection          = true
  skip_final_snapshot          = false
  final_snapshot_identifier    = "polibot-${var.environment}-final"
  performance_insights_enabled = true
  auto_minor_version_upgrade   = true
  apply_immediately            = false
}

data "aws_iam_policy_document" "host_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "host" {
  name_prefix        = "polibot-${var.environment}-host-"
  assume_role_policy = data.aws_iam_policy_document.host_assume.json
}

data "aws_iam_policy_document" "host" {
  statement {
    sid       = "ArchiveReadWrite"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:AbortMultipartUpload"]
    resources = ["${aws_s3_bucket.archive.arn}/*"]
  }
  statement {
    sid       = "ArchiveList"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.archive.arn]
  }
  statement {
    sid       = "ApplicationLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.app.arn}:*"]
  }
}

resource "aws_iam_role_policy" "host" {
  role   = aws_iam_role.host.id
  policy = data.aws_iam_policy_document.host.json
}

resource "aws_iam_instance_profile" "host" {
  role = aws_iam_role.host.name
}

resource "aws_instance" "host" {
  ami                         = var.host_ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.host_subnet_id
  vpc_security_group_ids      = [aws_security_group.host.id]
  iam_instance_profile        = aws_iam_instance_profile.host.name
  associate_public_ip_address = false
  monitoring                  = true

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
    volume_size = 20
  }

  user_data = <<-EOT
    #!/bin/sh
    set -eu
    install -d -m 0750 /etc/polibot
    printf '%s\n' 'POLIBOT_EXECUTION_MODE=${var.environment}' > /etc/polibot/runtime.env
    printf '%s\n' 'POLIBOT_LIVE_TRADING_ENABLED=false' >> /etc/polibot/runtime.env
    chmod 0640 /etc/polibot/runtime.env
  EOT

  lifecycle {
    prevent_destroy = true
  }
}

