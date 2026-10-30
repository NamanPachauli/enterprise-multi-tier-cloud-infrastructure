
module "network" {
  source = "../../modules/network"

  project_name             = "enterprise-mti"
  vpc_cidr                 = "10.0.0.0/16"
  public_subnet_cidr       = "10.0.1.0/24"
  private_app_subnet_cidr  = "10.0.2.0/24"
  private_data_subnet_cidr = "10.0.3.0/24"
  availability_zone        = "us-east-1a"
}
