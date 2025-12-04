# Минимальное приложение для сборки
import flet as ft

def main(page: ft.Page):
    page.title = "ARTEM Messenger"
    page.add(ft.Text("Hello! APK created successfully!"))
    page.add(ft.Text("Build with GitHub Actions"))
    page.add(ft.Text("Version 1.0"))

ft.app(target=main)
