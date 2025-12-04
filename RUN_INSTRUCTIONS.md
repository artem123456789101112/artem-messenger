# 🚀 ИНСТРУКЦИЯ ДЛЯ ЗАПУСКА

## Workflow создан без ошибок YAML:
- Файл: `.github/workflows/android_build.yml`
- Простой синтаксис
- Автоматический фикс libffi
- Использует NDK 23c для стабильности

## Запуск сборки:
1. Откройте: https://github.com/artem123456789101112/artem-messenger/actions/workflows/android_build.yml
2. Нажмите "Run workflow"
3. Ждите 60-120 минут

## Если будет ошибка libffi:
- Workflow автоматически обнаружит ошибку
- Применит патч для libffi
- Повторит сборку

## Результат:
- APK файл появится в Artifacts
- Логи сборки будут доступны для скачивания

## Важные параметры:
- Python 3.11
- NDK 23c (стабильная версия)
- Android API 33
- Flet 0.21.2
