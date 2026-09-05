param(
    [string]$Profile = "browser-login"
)

$ErrorActionPreference = "Stop"
$AccountId = "484632959006"
$ProviderArn = "arn:aws:iam::484632959006:oidc-provider/token.actions.githubusercontent.com"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$ActualAccount = aws sts get-caller-identity --profile $Profile --query Account --output text
if ($LASTEXITCODE -ne 0 -or $ActualAccount -ne $AccountId) {
    throw "Wrong or unavailable AWS account. Expected $AccountId; got $ActualAccount"
}

$ProviderAudience = aws iam get-open-id-connect-provider --profile $Profile --open-id-connect-provider-arn $ProviderArn --query "ClientIDList[?@=='sts.amazonaws.com'] | [0]" --output text
if ($LASTEXITCODE -ne 0 -or $ProviderAudience -ne "sts.amazonaws.com") {
    throw "The existing GitHub OIDC provider is absent or has the wrong audience."
}

$Roles = @(
    @{
        Name = "polibot-github-infra"
        Trust = "github-infra-role-trust.json"
        PolicyName = "polibot-paper-infra"
        Policy = "github-infra-role-policy.json"
    },
    @{
        Name = "polibot-github-deploy"
        Trust = "github-deploy-role-trust.json"
        PolicyName = "polibot-paper-deploy"
        Policy = "github-deploy-role-policy.json"
    }
)

foreach ($Role in $Roles) {
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    aws iam get-role --profile $Profile --role-name $Role.Name *> $null
    $GetRoleExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousErrorActionPreference
    if ($GetRoleExitCode -eq 0) {
        throw "Role $($Role.Name) already exists. Inspect it instead of overwriting it."
    }
    aws iam create-role --profile $Profile --role-name $Role.Name --assume-role-policy-document "file://$ScriptDir/$($Role.Trust)" --tags Key=Project,Value=polibot Key=Environment,Value=paper Key=ManagedBy,Value=manual-bootstrap
    if ($LASTEXITCODE -ne 0) { throw "Failed to create $($Role.Name)" }
    aws iam put-role-policy --profile $Profile --role-name $Role.Name --policy-name $Role.PolicyName --policy-document "file://$ScriptDir/$($Role.Policy)"
    if ($LASTEXITCODE -ne 0) { throw "Failed to attach policy to $($Role.Name)" }
}

Write-Output "Created repository/environment-scoped GitHub OIDC roles."
Write-Output "arn:aws:iam::484632959006:role/polibot-github-infra"
Write-Output "arn:aws:iam::484632959006:role/polibot-github-deploy"
