
output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_id" {
  value = module.network.public_subnet_id
}

output "private_app_subnet_id" {
  value = module.network.private_app_subnet_id
}

output "private_data_subnet_id" {
  value = module.network.private_data_subnet_id
}

output "internet_gateway_id" {
  value = module.network.internet_gateway_id
}
