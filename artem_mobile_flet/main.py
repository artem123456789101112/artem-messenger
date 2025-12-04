import flet as ft

def main(page: ft.Page):
    page.title = "ARTEM Messenger"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.add(ft.Text("ARTEM Messenger", size=30, weight=ft.FontWeight.BOLD))
    page.add(ft.Text("Build with GitHub Actions", size=20))
    page.add(ft.Text("Version 1.0", size=16))
    
    def button_click(e):
        page.add(ft.Text("Button clicked! APK работает!"))
        
    page.add(ft.ElevatedButton("Test Button", on_click=button_click))

ft.app(target=main)
