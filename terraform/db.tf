resource "aws_security_group" "db_sg" {
  name        = "weather-app-db-sg"
  description = "Allow inbound traffic for Postgres and Redis"
  vpc_id      = aws_vpc.main.id

  # Postgres port
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  # Redis port
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "weather-app-db-sg"
  }
}
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "weather-app-rds-subnet-group"
  subnet_ids = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  tags = {
    Name = "weather-app-rds-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier             = "weather-app-db"
  allocated_storage      = 20
  max_allocated_storage  = 100
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = "db.t4g.micro"
  db_name                = "weather_db"
  username               = "postgres"
  password               = "weatherpass123" # На проді ховаємо в Secrets Manager/variables
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  skip_final_snapshot    = true
  publicly_accessible    = true # Для зручного тестового підключення

  tags = {
    Name = "weather-app-postgres"
  }
}

resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "weather-app-redis-subnet-group"
  subnet_ids = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "weather-app-redis"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis_subnet_group.name
  security_group_ids   = [aws_security_group.db_sg.id]

  tags = {
    Name = "weather-app-redis"
  }
}