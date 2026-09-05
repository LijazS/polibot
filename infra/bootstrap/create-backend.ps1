param(
    [string]$Profile = "browser-login",
    [switch]$ResumeExisting
)

$ErrorActionPreference = "Stop"
$AccountId = "484632959006"
$Region = "us-east-1"
$Bucket = "polibot-tfstate-484632959006-us-east-1"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$ActualAccount = aws sts get-caller-identity --profile $Profile --query Account --output text
if ($LASTEXITCODE -ne 0 -or $ActualAccount -ne $AccountId) {
    throw "Wrong or unavailable AWS account. Expected $AccountId; got $ActualAccount"
}

$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
aws s3api head-bucket --profile $Profile --bucket $Bucket 2>$null
$HeadBucketExitCode = $LASTEXITCODE
$ErrorActionPreference = $PreviousErrorActionPreference
if ($HeadBucketExitCode -eq 0) {
    if (-not $ResumeExisting) {
        throw "Bucket $Bucket already exists or is accessible. Verify it, then use -ResumeExisting only to finish this bootstrap."
    }
    Write-Output "Resuming security configuration for verified bucket: $Bucket"
} else {
    aws s3api create-bucket --profile $Profile --region $Region --bucket $Bucket
    if ($LASTEXITCODE -ne 0) { throw "Failed to create state bucket" }
}

aws s3api put-public-access-block --profile $Profile --bucket $Bucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
if ($LASTEXITCODE -ne 0) { throw "Failed to block public access" }

aws s3api put-bucket-ownership-controls --profile $Profile --bucket $Bucket --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]'
if ($LASTEXITCODE -ne 0) { throw "Failed to enforce bucket-owner ownership" }

aws s3api put-bucket-versioning --profile $Profile --bucket $Bucket --versioning-configuration Status=Enabled
if ($LASTEXITCODE -ne 0) { throw "Failed to enable versioning" }

aws s3api put-bucket-encryption --profile $Profile --bucket $Bucket --server-side-encryption-configuration "file://$ScriptDir/tfstate-encryption.json"
if ($LASTEXITCODE -ne 0) { throw "Failed to enable encryption" }

aws s3api put-bucket-policy --profile $Profile --bucket $Bucket --policy "file://$ScriptDir/tfstate-bucket-policy.json"
if ($LASTEXITCODE -ne 0) { throw "Failed to apply TLS-only bucket policy" }

Write-Output "Created secured Terraform state bucket: $Bucket"
Write-Output "Expected state key: polibot/paper/terraform.tfstate"
