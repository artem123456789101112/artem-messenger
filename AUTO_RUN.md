# Этот скрипт запускает workflow автоматически через GitHub API

# 1. Сначала дождитесь когда изменения прогрузятся (30 секунд)
# 2. Затем откройте браузер и нажмите Run workflow
# 3. ИЛИ используйте этот curl запрос для автоматического запуска:

curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/artem123456789101112/artem-messenger/actions/workflows/build.yml/dispatches \
  -d '{"ref":"main"}'

# Замените YOUR_GITHUB_TOKEN на ваш Personal Access Token
# Создайте токен здесь: https://github.com/settings/tokens
# Нужны права: repo, workflow
