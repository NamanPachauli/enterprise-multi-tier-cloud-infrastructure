
# Public tier security group
resource "aws_security_group" "public" {
  name        = "${var.project_name}-public-sg"
  description = "Security group for public load balancer tier"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Allow HTTP traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTPS traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-public-sg"
    Tier = "public"
  }
}

# Private application tier security group
resource "aws_security_group" "application" {
  name        = "${var.project_name}-application-sg"
  description = "Allow application traffic only from public tier"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Allow traffic from public tier"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.public.id]
  }

  tags = {
    Name = "${var.project_name}-application-sg"
    Tier = "private-application"
  }
}

# Private database tier security group
resource "aws_security_group" "database" {
  name        = "${var.project_name}-database-sg"
  description = "Allow database traffic only from application tier"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Allow PostgreSQL from application tier"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.application.id]
  }

  tags = {
    Name = "${var.project_name}-database-sg"
    Tier = "private-data"
  }
}
