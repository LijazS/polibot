# Infrastructure

Local development uses Docker Compose with the application and PostgreSQL. The app
container runs as a non-root user and defaults to paper mode. CI validates only; it
has no secrets or deployment privileges.

The PAPER stack targets the explicitly discovered AWS account and `us-east-1`. It
creates a dedicated low-cost VPC with one public subnet used only for outbound access,
an EC2 host with no inbound rules or SSH key, an immutable ECR repository, a private
encrypted/versioned S3 data and deployment-artifact bucket, SSM administration, and
CloudWatch bootstrap/deployment logs plus an EC2 status alarm. PostgreSQL is a local
Docker service with a named EBS-backed volume and no published port.

GitHub Actions authenticates through the existing account-wide GitHub OIDC provider.
Separate repository/environment-scoped roles divide Terraform from image/deployment
permissions. Terraform state uses a separately bootstrapped encrypted/versioned S3
bucket and native S3 lockfile. Deployment is manual, serialized, protected by the
`paper` GitHub environment, tied to `main`, and uses the exact commit SHA plus the ECR
digest returned after push.

There is no NAT gateway, load balancer, RDS, Lambda core loop, EKS, SSH, static AWS
key, publicly reachable app/database, or geographic-restriction workaround. No apply
has occurred. Backups/restores, cost alarms, host replacement, and sustained runtime
behavior still require operator exercises.
