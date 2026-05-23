module "network" {
  source               = "./modules/network"
  vpc_cidr             = var.vpc_cidr
  public_subnet_1_cidr = var.public_subnet_1_cidr
  public_subnet_2_cidr = var.public_subnet_2_cidr
  availability_zone_1  = var.availability_zone_1
  availability_zone_2  = var.availability_zone_2
  common_tags          = local.common_tags
}

resource "aws_security_group" "web_sg" {
  name        = "web-security-group"
  description = "Security group for NimbusKart web tier"
  vpc_id      = module.network.vpc_id

  ingress {
    description = "HTTP access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS access"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "web-security-group"
    }
  )
}

resource "aws_instance" "web_1" {
  ami                    = "ami-12345678"
  instance_type          = "t3.micro"
  subnet_id              = module.network.public_subnet_1_id
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  tags = merge(
    local.common_tags,
    {
      Name = "web-instance-1"
      Tier = "web"
    }
  )
}

resource "aws_instance" "web_2" {
  ami                    = "ami-12345678"
  instance_type          = "t3.micro"
  subnet_id              = module.network.public_subnet_2_id
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  tags = merge(
    local.common_tags,
    {
      Name = "web-instance-2"
      Tier = "web"
    }
  )
}

resource "aws_s3_bucket" "app_logs" {
  bucket = "nimbuskart-app-logs"

  tags = merge(
    local.common_tags,
    {
      Name = "app-logs-bucket"
    }
  )
}


resource "aws_s3_bucket_versioning" "app_logs_versioning" {
  bucket = aws_s3_bucket.app_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

/*
resource "aws_s3_bucket_lifecycle_configuration" "app_logs_lifecycle" {
  bucket = aws_s3_bucket.app_logs.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
*/

resource "aws_ebs_volume" "orphan_volume" {
  availability_zone = var.availability_zone_1
  size              = 10

  tags = merge(
    local.common_tags,
    {
      Name = "orphan-ebs-volume"
      Protected = "true"
    }
  )
}

resource "aws_instance" "stopped_instance" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"

  subnet_id = module.network.public_subnet_1_id

  tags = merge(
    local.common_tags,
    {
      Name = "stopped-instance"
    }
  )
}

resource "aws_eip" "unused_eip" {

  tags = merge(
    local.common_tags,
    {
      Name = "unused-eip"
    }
  )
}
