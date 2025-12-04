# АВТОМАТИЧЕСКИЙ ЗАПУСК WORKFLOW

# Способ 1: Через веб-интерфейс (рекомендуется)
# 1. Откройте: https://github.com/artem123456789101112/artem-messenger/actions/workflows/build_apk.yml
# 2. Нажмите "Run workflow"
# 3. Ждите 1-2 часа

# Способ 2: Через API (нужен токен)
$token = "ВАШ_ТОКЕН"
$headers = @{
    "Authorization" = "token $token"
    "Accept" = "application/vnd.github.v3+json"
}
$body = @{ ref = "main" } | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.github.com/repos/artem123456789101112/artem-messenger/actions/workflows/build_apk.yml/dispatches" `
    -Method Post -Headers $headers -Body $body

echo "Workflow запущен!"
