import flet as ft

def main(page: ft.Page):
    page.title = "ARTEM Messenger"
    page.add(ft.Text("Hello from ARTEM Messenger!"))
    page.add(ft.Text("Simple build test"))

ft.app(target=main)
