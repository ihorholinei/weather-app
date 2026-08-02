module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "weather-app-eks"
  cluster_version = "1.31"

  enable_cluster_creator_admin_permissions = true
  cluster_endpoint_public_access           = true

  vpc_id     = aws_vpc.main.id
  subnet_ids = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  eks_managed_node_groups = {
    default = {
      min_size     = 2
      max_size     = 2
      desired_size = 2

      instance_types = ["t3.micro"]
      
      # Перемикаємо на ON_DEMAND, щоб обійти конфліктний Spot API кастомний фільтр
      # Для t3.medium різниця в ціні за пару годин тесту — буквально кілька центів
      capacity_type  = "ON_DEMAND"

      # Переконуємося, що ноди в Public Subnet отримують IP для зв'язку з EKS API
      associate_public_ip_address = true
    }
  }

  tags = {
    Environment = "dev"
    Terraform   = "true"
  }
}