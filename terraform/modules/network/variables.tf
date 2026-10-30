
variable "project_name" {
  description = "Project resource naming prefix"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR range"
  type        = string
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  type        = string
}

variable "private_app_subnet_cidr" {
  description = "Private application subnet CIDR"
  type        = string
}

variable "private_data_subnet_cidr" {
  description = "Private data subnet CIDR"
  type        = string
}

variable "availability_zone" {
  description = "Local simulation availability zone"
  type        = string
}
