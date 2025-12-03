# Введи токен когда попросит
$token = Read-Host "Введи GitHub Token (или нажми Enter чтобы пропустить)"

if ($token) {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Accept" = "application/vnd.github.v3+json"
    }
    
    $body = @{ ref = "main" } | ConvertTo-Json
    
    try {
        Invoke-RestMethod `
            -Uri "https://api.github.com/repos/artem123456789101112/artem-messenger/actions/workflows/build.yml/dispatches" `
            -Method Post -Headers $headers -Body $body -ContentType "application/json"
        
        Write-Host "✅ Сборка запущена!"
        Start-Process "https://github.com/artem123456789101112/artem-messenger/actions"
    }
    catch {
        Write-Host "❌ Ошибка: $_"
        Write-Host "Открываю Actions вручную..."
        Start-Process "https://github.com/artem123456789101112/artem-messenger/actions"
    }
}
else {
    Write-Host "Открываю Actions вручную..."
    Start-Process "https://github.com/artem123456789101112/artem-messenger/actions"
}

pause
