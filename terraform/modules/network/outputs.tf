
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_id" {
  value = aws_subnet.public.id
}

output "private_app_subnet_id" {
  value = aws_subnet.private_app.id
}

output "private_data_subnet_id" {
  value = aws_subnet.private_data.id
}

output "internet_gateway_id" {
  value = aws_internet_gateway.main.id
}

output "public_route_table_id" {
  value = aws_route_table.public.id
}

output "public_security_group_id" {
  value = aws_security_group.public.id
}

output "application_security_group_id" {
  value = aws_security_group.application.id
}

output "database_security_group_id" {
  value = aws_security_group.database.id
}
