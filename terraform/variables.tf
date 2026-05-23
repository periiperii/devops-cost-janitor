variable "aws_region" {
  description = "AWS region for LocalStack"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "NimbusKart"
}

variable "owner" {
  description = "Infrastructure owner"
  type        = string
  default     = "Priyansi"
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH access"
  type        = string
  default     = "127.0.0.1/32"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "public_subnet_1_cidr" {
  type    = string
  default = "10.20.1.0/24"
}

variable "public_subnet_2_cidr" {
  type    = string
  default = "10.20.2.0/24"
}

variable "availability_zone_1" {
  description = "Availability zone for subnet 1"
  type        = string
  default     = "us-east-1a"
}

variable "availability_zone_2" {
  description = "Availability zone for subnet 2"
  type        = string
  default     = "us-east-1b"
}
