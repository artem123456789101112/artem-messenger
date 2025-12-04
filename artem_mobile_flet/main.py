import flet as ft

def main(page: ft.Page):
    page.title = "ARTEM Messenger"
    page.add(ft.Text("Test App"))
    page.add(ft.Text("Build should work!"))

ft.app(target=main)
