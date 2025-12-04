import flet as ft

def main(page: ft.Page):
    page.title = "ARTEM Messenger"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.add(ft.Text("ARTEM Messenger", size=30, weight=ft.FontWeight.BOLD))
    page.add(ft.Text("Build with GitHub Actions", size=20))
    page.add(ft.Text("Status: SUCCESS!", size=20, color=ft.colors.GREEN))
    
    def button_click(e):
        page.add(ft.Text("Button clicked!"))
        
    page.add(ft.ElevatedButton("Click me!", on_click=button_click))

ft.app(target=main)
