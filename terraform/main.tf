# ---------------------------------------------------------------------------
# The AWS infrastructure for StockRoom.
#
#   VPC
#    ├── 2 public subnets   (the load balancer and the NAT gateway)
#    ├── 2 private subnets  (the EKS worker nodes)
#    ├── 1 internet gateway
#    └── 1 NAT gateway
#   EKS cluster
#    └── 1 managed node group
# ---------------------------------------------------------------------------

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name = "${var.project_name}-${var.environment}"

  # The cluster uses the first two availability zones of the region.
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

# ------------------------------------------------------------------- network
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.17"

  name = "${local.name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  public_subnets  = var.public_subnet_cidrs
  private_subnets = var.private_subnet_cidrs

  # One NAT gateway keeps the cost low. Production uses one gateway per zone.
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  # These tags let the AWS load balancer controller find the subnets.
  public_subnet_tags = {
    "kubernetes.io/role/elb"                  = "1"
    "kubernetes.io/cluster/${local.name}-eks" = "shared"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"         = "1"
    "kubernetes.io/cluster/${local.name}-eks" = "shared"
  }

  tags = {
    Name = "${local.name}-vpc"
  }
}

# ------------------------------------------------------------------- cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = "${local.name}-eks"
  cluster_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # The classroom demonstration needs a public API endpoint.
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # The user that makes the cluster becomes an administrator of the cluster.
  enable_cluster_creator_admin_permissions = true

  cluster_addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = {}
    eks-pod-identity-agent = {}
  }

  eks_managed_node_groups = {
    workers = {
      name = "${local.name}-workers"

      instance_types = [var.node_instance_type]
      capacity_type  = "ON_DEMAND"
      ami_type       = "AL2023_x86_64_STANDARD"

      desired_size = var.node_desired_size
      min_size     = var.node_min_size
      max_size     = var.node_max_size

      disk_size = 30

      labels = {
        role = "application"
      }
    }
  }

  tags = {
    Name = "${local.name}-eks"
  }
}
