# The input variables of the infrastructure.

variable "aws_region" {
  description = "The AWS region for every resource."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "The name prefix of each resource."
  type        = string
  default     = "stockroom"
}

variable "environment" {
  description = "The name of the environment."
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "The name of the student. This tag identifies the resources."
  type        = string
  default     = "kartavya37"
}

variable "vpc_cidr" {
  description = "The address range of the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "The address ranges of the public subnets. The list has two items."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "The address ranges of the private subnets. The list has two items."
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "kubernetes_version" {
  description = "The version of the EKS control plane."
  type        = string
  default     = "1.31"
}

variable "node_instance_type" {
  description = "The EC2 instance type of each worker node."
  type        = string
  default     = "t3.medium"
}

variable "node_desired_size" {
  description = "The number of worker nodes at the start."
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "The minimum number of worker nodes."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "The maximum number of worker nodes."
  type        = number
  default     = 4
}
