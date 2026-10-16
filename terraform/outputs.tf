# The values that Terraform shows after the apply command.

output "aws_region" {
  description = "The region of the infrastructure."
  value       = var.aws_region
}

output "vpc_id" {
  description = "The identifier of the VPC."
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "The identifiers of the two public subnets."
  value       = module.vpc.public_subnets
}

output "private_subnet_ids" {
  description = "The identifiers of the two private subnets."
  value       = module.vpc.private_subnets
}

output "cluster_name" {
  description = "The name of the EKS cluster."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "The address of the Kubernetes API."
  value       = module.eks.cluster_endpoint
}

output "cluster_version" {
  description = "The Kubernetes version of the control plane."
  value       = module.eks.cluster_version
}

output "node_group_name" {
  description = "The name of the managed node group."
  value       = keys(module.eks.eks_managed_node_groups)
}

output "configure_kubectl" {
  description = "Run this command to configure kubectl for the cluster."
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}
