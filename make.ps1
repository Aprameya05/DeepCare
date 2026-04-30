param(
    [ValidateSet("setup", "up", "down", "migrate", "seed", "test", "logs", "clean")]
    [string]$Target = "up"
)

$compose = @("docker", "compose", "-f", "clinicaliq/docker-compose.yml")

function Invoke-Compose {
    param([string[]]$Args)
    $command = $compose[0]
    $baseArgs = $compose[1..($compose.Length - 1)]
    & $command @baseArgs @Args
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

switch ($Target) {
    "setup" { Invoke-Compose @("build") }
    "up" { Invoke-Compose @("up", "-d") }
    "down" { Invoke-Compose @("down") }
    "migrate" { Invoke-Compose @("exec", "-T", "backend", "alembic", "-c", "backend/alembic.ini", "upgrade", "head") }
    "seed" {
        Invoke-Compose @("exec", "-T", "backend", "python", "-m", "backend.scripts.seed_disease_test_rules")
        Invoke-Compose @("exec", "-T", "backend", "python", "-m", "backend.scripts.seed_country_pricing")
    }
    "test" {
        Invoke-Compose @("exec", "-T", "backend", "pytest", "--cov=backend", "--cov-report=term-missing")
        Push-Location clinicaliq/frontend
        npm run test:e2e
        $code = $LASTEXITCODE
        Pop-Location
        if ($code -ne 0) { exit $code }
    }
    "logs" { Invoke-Compose @("logs", "-f") }
    "clean" { Invoke-Compose @("down", "-v", "--remove-orphans") }
}
