import flet as ft

def main(page: ft.Page):
    page.title = "ARTEM Messenger"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.add(ft.Text("ARTEM Messenger", size=30, weight=ft.FontWeight.BOLD))
    page.add(ft.Text("Simple build test", size=20))
    page.add(ft.Text("Should work now!", size=20, color=ft.colors.GREEN))
    
    def btn_click(e):
        page.add(ft.Text("Button clicked!"))

    page.add(ft.ElevatedButton("Test Button", on_click=btn_click))

ft.app(target=main)
