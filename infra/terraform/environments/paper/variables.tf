variable "aws_account_id" {
  description = "Expected AWS account; provider authentication fails closed on mismatch."
  type        = string
  default     = "484632959006"

  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "aws_account_id must contain exactly 12 digits."
  }
}

variable "aws_region" {
  description = "AWS region selected for the PAPER stack after server-location review."
  type        = string
  default     = "eu-west-2"
}

variable "environment" {
  description = "This stack intentionally supports PAPER only."
  type        = string
  default     = "paper"

  validation {
    condition     = var.environment == "paper"
    error_message = "The deployment environment must be paper."
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.40.1.0/24"
}

variable "instance_type" {
  description = "Cost-conscious, on-demand instance type; Spot is deliberately disabled."
  type        = string
  default     = "t3.small"
}

variable "root_volume_gib" {
  type    = number
  default = 30

  validation {
    condition     = var.root_volume_gib >= 20 && var.root_volume_gib <= 100
    error_message = "root_volume_gib must be between 20 and 100 GiB."
  }
}

variable "ecr_images_to_retain" {
  type    = number
  default = 20
}

variable "allow_destructive_destroy" {
  description = "Permit emptying the PAPER data bucket and ECR repository during an explicitly approved destroy. Never set during normal apply."
  type        = bool
  default     = false
}

variable "alarm_email" {
  description = "Optional email for the single EC2 status alarm; confirmation is manual."
  type        = string
  default     = ""
}
