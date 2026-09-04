variable "aws_region" {
  description = "Deployment region selected after access and latency review."
  type        = string
  default     = "eu-west-2"
}

variable "environment" {
  description = "Non-live environment name."
  type        = string
  default     = "shadow"

  validation {
    condition     = contains(["paper", "shadow"], var.environment)
    error_message = "This scaffold permits paper or shadow environments only."
  }
}

variable "vpc_id" {
  description = "Existing reviewed VPC ID."
  type        = string
}

variable "private_subnet_ids" {
  description = "At least two private subnets for RDS."
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "RDS requires at least two private subnets."
  }
}

variable "host_subnet_id" {
  description = "Private subnet for the persistent application host."
  type        = string
}

variable "host_ami_id" {
  description = "Reviewed immutable AMI ID; intentionally has no default."
  type        = string
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}

variable "database_name" {
  type    = string
  default = "polibot"
}

variable "database_username" {
  description = "Non-secret database username. Password is managed by RDS."
  type        = string
  default     = "polibot_app"
}

