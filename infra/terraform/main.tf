terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  backend "s3" {
    bucket         = "omniai-terraform-state"
    key            = "infra/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "omniai-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "omniai-${var.environment}"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment != "production"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = var.environment
    Project     = "omniai"
  }
}

module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "omniai-${var.environment}"
  cluster_version = "1.30"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = var.environment != "production"

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  eks_managed_node_groups = {
    general = {
      desired_size = var.node_desired_size
      min_size     = var.node_min_size
      max_size     = var.node_max_size

      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 50
            volume_type           = "gp3"
            iops                  = 3000
            throughput            = 125
            delete_on_termination = true
          }
        }
      }

      labels = {
        node-group = "general"
      }

      tags = {
        Environment = var.environment
        "k8s.io/cluster-autoscaler/enabled" = "true"
      }
    }
  }

  tags = {
    Environment = var.environment
    Project     = "omniai"
  }
}

module "rds" {
  source = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "omniai-${var.environment}"

  engine               = "postgres"
  engine_version       = "16.3"
  family               = "postgres16"
  major_engine_version = "16"
  instance_class       = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name                = "omniai"
  username               = "omniai"
  password               = random_password.db_password.result
  port                   = 5432
  manage_master_user_password = false

  vpc_security_group_ids = [module.vpc.default_security_group_id]
  db_subnet_group_name   = module.vpc.database_subnet_group

  backup_window      = "03:00-04:00"
  maintenance_window = "Sun:04:00-Sun:05:00"

  backup_retention_period = var.db_backup_retention_days
  deletion_protection     = var.environment == "production"
  skip_final_snapshot     = var.environment != "production"

  performance_insights_enabled          = var.environment == "production"
  performance_insights_retention_period = 7

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Environment = var.environment
    Project     = "omniai"
  }
}

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "random_password" "secret_key" {
  length  = 64
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "omniai-${var.environment}"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.redis_node_type
  num_cache_nodes      = var.environment == "production" ? 2 : 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name = module.vpc.elasticache_subnet_group_name
  security_group_ids = [module.vpc.default_security_group_id]

  tags = {
    Environment = var.environment
    Project     = "omniai"
  }
}

resource "aws_s3_bucket" "storage" {
  bucket = "omniai-${var.environment}-storage"
  force_destroy = var.environment != "production"

  tags = {
    Environment = var.environment
    Project     = "omniai"
  }
}

resource "aws_s3_bucket_versioning" "storage" {
  bucket = aws_s3_bucket.storage.id
  versioning_configuration {
    status = var.environment == "production" ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "storage" {
  bucket = aws_s3_bucket.storage.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_iam_user" "storage_user" {
  name = "omniai-${var.environment}-storage"
}

resource "aws_iam_user_policy" "storage_policy" {
  name = "omniai-${var.environment}-storage-policy"
  user = aws_iam_user.storage_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.storage.arn,
          "${aws_s3_bucket.storage.arn}/*",
        ]
      }
    ]
  })
}

resource "aws_iam_access_key" "storage_key" {
  user = aws_iam_user.storage_user.name
}

resource "aws_secretsmanager_secret" "omniai_secrets" {
  name = "omniai-${var.environment}-secrets"
  recovery_window_in_days = var.environment == "production" ? 30 : 0
}

resource "aws_secretsmanager_secret_version" "omniai_secrets" {
  secret_id = aws_secretsmanager_secret.omniai_secrets.id
  secret_string = jsonencode({
    secret_key        = random_password.secret_key.result
    jwt_secret        = random_password.jwt_secret.result
    db_password       = random_password.db_password.result
    redis_host        = aws_elasticache_cluster.redis.cache_nodes[0].address
    redis_port        = aws_elasticache_cluster.redis.cache_nodes[0].port
    s3_access_key     = aws_iam_access_key.storage_key.id
    s3_secret_key     = aws_iam_access_key.storage_key.secret
    s3_bucket         = aws_s3_bucket.storage.bucket
    database_url      = "postgresql+asyncpg://omniai:${random_password.db_password.result}@${module.rds.db_instance_address}:5432/omniai"
    database_url_sync = "postgresql://omniai:${random_password.db_password.result}@${module.rds.db_instance_address}:5432/omniai"
  })
}

resource "aws_ecr_repository" "backend" {
  name = "omniai/${var.environment}/backend"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "frontend" {
  name = "omniai/${var.environment}/frontend"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}
