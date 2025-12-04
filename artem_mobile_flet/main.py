import flet as ft

def main(page: ft.Page):
    page.title = "ARTEM Messenger"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.add(ft.Text("ARTEM Messenger", size=30, weight=ft.FontWeight.BOLD))
    page.add(ft.Text("Libffi fix applied", size=20))
    page.add(ft.Text("This should build now!", size=20, color=ft.colors.GREEN))
    
    def test_click(e):
        page.add(ft.Text("Test passed! APK works!"))

    page.add(ft.ElevatedButton("Test Button", on_click=test_click))

ft.app(target=main)
