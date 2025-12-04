# Script to trigger GitHub Actions workflow
$token = "YOUR_TOKEN_HERE"  # Replace with your GitHub token
$repo = "artem123456789101112/artem-messenger"
$workflow = "build.yml"

$headers = @{
    "Authorization" = "token $token"
    "Accept" = "application/vnd.github.v3+json"
}

$body = @{
    "ref" = "main"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/actions/workflows/$workflow/dispatches" `
        -Method Post `
        -Headers $headers `
        -Body $body `
        -ContentType "application/json"
    
    Write-Host "✅ Workflow triggered successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host "Please run workflow manually from GitHub UI" -ForegroundColor Yellow
}
