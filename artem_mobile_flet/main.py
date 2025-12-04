import flet as ft

def main(page: ft.Page):
    page.title = "ARTEM Messenger"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    # Простой интерфейс для теста
    def login_click(e):
        page.add(ft.Text(f"Welcome, {login.value}!"))
        login.visible = False
        password.visible = False
        login_btn.visible = False
    
    login = ft.TextField(label="Login", width=300)
    password = ft.TextField(label="Password", password=True, width=300)
    login_btn = ft.ElevatedButton("Login", on_click=login_click)
    
    page.add(
        ft.Column([
            ft.Text("ARTEM Messenger", size=30, weight=ft.FontWeight.BOLD),
            ft.Text("Test build successful!", size=20),
            login,
            password,
            login_btn
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
