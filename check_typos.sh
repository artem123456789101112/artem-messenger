#!/bin/bash
# Скрипт для проверки опечаток перед запуском
echo "=== Проверка опечаток ==="

# Проверяем workflow файл
if grep -n "bulldozer" .github/workflows/ci.yml; then
    echo "❌ ОШИБКА: Найден 'bulldozer' в workflow"
    exit 1
fi

if grep -n "ARTH" .github/workflows/ci.yml; then
    echo "❌ ОШИБКА: Найден 'ARTH' в workflow"
    exit 1
fi

if grep -n "python3\.cython" .github/workflows/ci.yml; then
    echo "❌ ОШИБКА: Неправильный формат requirements в workflow"
    exit 1
fi

# Проверяем buildozer.spec
if [ -f "artem_mobile_flet/buildozer.spec" ]; then
    if grep -n "bulldozer" artem_mobile_flet/buildozer.spec; then
        echo "❌ ОШИБКА: Найден 'bulldozer' в buildozer.spec"
        exit 1
    fi
    
    if ! grep -q "requirements = python3,cython,flet" artem_mobile_flet/buildozer.spec; then
        echo "❌ ОШИБКА: Неправильные requirements в buildozer.spec"
        exit 1
    fi
fi

echo "✅ Все проверки пройдены!"
