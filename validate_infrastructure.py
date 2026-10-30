import json
import os
import subprocess
import sys

ENDPOINT = "http://localhost:4568"
REGION = "us-east-1"

os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_DEFAULT_REGION"] = REGION

passed = 0
failed = 0


def check(description, condition):
    global passed, failed

    if condition:
        print(f"[PASS] {description}")
        passed += 1
    else:
        print(f"[FAIL] {description}")
        failed += 1


def aws_json(service, operation):
    command = [
        "aws",
        "--endpoint-url", ENDPOINT,
        service,
        operation,
        "--output", "json"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return json.loads(result.stdout)


def has_tcp_rule(group, port, public_cidr=None, source_group_id=None):
    for rule in group.get("IpPermissions", []):
        if (
            rule.get("IpProtocol") == "tcp"
            and rule.get("FromPort") == port
            and rule.get("ToPort") == port
        ):
            if public_cidr:
                for item in rule.get("IpRanges", []):
                    if item.get("CidrIp") == public_cidr:
                        return True

            if source_group_id:
                for item in rule.get("UserIdGroupPairs", []):
                    if item.get("GroupId") == source_group_id:
                        return True

    return False


def main():
    print("\n=== ENTERPRISE INFRASTRUCTURE VALIDATION ===\n")

    # 1. VPC
    vpcs = aws_json("ec2", "describe-vpcs")["Vpcs"]
    vpc = next(
        (item for item in vpcs
         if item.get("CidrBlock") == "10.0.0.0/16"),
        None
    )

    check("VPC with CIDR 10.0.0.0/16 exists", vpc is not None)

    if not vpc:
        raise RuntimeError("Expected VPC not found. Cannot continue.")

    vpc_id = vpc["VpcId"]

    # 2. Subnets
    subnets = aws_json("ec2", "describe-subnets")["Subnets"]
    subnets = [s for s in subnets if s.get("VpcId") == vpc_id]

    expected_cidrs = {
        "10.0.1.0/24": True,
        "10.0.2.0/24": False,
        "10.0.3.0/24": False
    }

    subnet_ids = {}

    for cidr, expected_public in expected_cidrs.items():
        subnet = next(
            (s for s in subnets if s.get("CidrBlock") == cidr),
            None
        )

        check(f"Subnet {cidr} exists", subnet is not None)

        if subnet:
            subnet_ids[cidr] = subnet["SubnetId"]
            actual_public = subnet.get("MapPublicIpOnLaunch", False)

            check(
                f"Subnet {cidr} public IP setting is "
                f"{expected_public}",
                actual_public == expected_public
            )

    # 3. Internet Gateway
    gateways = aws_json(
        "ec2", "describe-internet-gateways"
    )["InternetGateways"]

    attached_gateway = next(
        (
            gateway for gateway in gateways
            if any(
                attachment.get("VpcId") == vpc_id
                and attachment.get("State") == "available"
                for attachment in gateway.get("Attachments", [])
            )
        ),
        None
    )

    check("Internet Gateway is attached to the VPC",
          attached_gateway is not None)

    # 4. Route tables
    route_tables = aws_json(
        "ec2", "describe-route-tables"
    )["RouteTables"]

    route_tables = [
        table for table in route_tables
        if table.get("VpcId") == vpc_id
    ]

    def route_table_for_subnet(subnet_id):
        return next(
            (
                table for table in route_tables
                if any(
                    association.get("SubnetId") == subnet_id
                    for association in table.get("Associations", [])
                )
            ),
            None
        )

    public_subnet_id = subnet_ids.get("10.0.1.0/24")

    if public_subnet_id:
        public_table = route_table_for_subnet(public_subnet_id)

        public_route_ok = False

        if public_table:
            public_route_ok = any(
                route.get("DestinationCidrBlock") == "0.0.0.0/0"
                and route.get("GatewayId", "").startswith("igw-")
                for route in public_table.get("Routes", [])
            )

        check("Public subnet has default route through IGW",
              public_route_ok)

    for cidr in ["10.0.2.0/24", "10.0.3.0/24"]:
        subnet_id = subnet_ids.get(cidr)
        table = route_table_for_subnet(subnet_id) if subnet_id else None

        has_default_route = (
            any(
                route.get("DestinationCidrBlock") == "0.0.0.0/0"
                for route in table.get("Routes", [])
            )
            if table else True
        )

        check(
            f"Private subnet {cidr} has no default internet route",
            not has_default_route
        )

    # 5. Security Groups
    groups = aws_json(
        "ec2", "describe-security-groups"
    )["SecurityGroups"]

    groups = [g for g in groups if g.get("VpcId") == vpc_id]

    def find_group(name):
        return next(
            (g for g in groups if g.get("GroupName") == name),
            None
        )

    public_sg = find_group("enterprise-mti-public-sg")
    app_sg = find_group("enterprise-mti-application-sg")
    db_sg = find_group("enterprise-mti-database-sg")

    check("Public security group exists", public_sg is not None)
    check("Application security group exists", app_sg is not None)
    check("Database security group exists", db_sg is not None)

    if public_sg:
        check(
            "Public SG allows HTTP 80 from 0.0.0.0/0",
            has_tcp_rule(public_sg, 80, public_cidr="0.0.0.0/0")
        )
        check(
            "Public SG allows HTTPS 443 from 0.0.0.0/0",
            has_tcp_rule(public_sg, 443, public_cidr="0.0.0.0/0")
        )

    if public_sg and app_sg:
        check(
            "Application SG allows port 8080 from Public SG",
            has_tcp_rule(
                app_sg, 8080,
                source_group_id=public_sg["GroupId"]
            )
        )

    if app_sg and db_sg:
        check(
            "Database SG allows port 5432 from Application SG",
            has_tcp_rule(
                db_sg, 5432,
                source_group_id=app_sg["GroupId"]
            )
        )

    print("\n=== VALIDATION SUMMARY ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed:
        sys.exit(1)

    print("\nAll infrastructure checks passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\n[ERROR] {error}")
        sys.exit(1)