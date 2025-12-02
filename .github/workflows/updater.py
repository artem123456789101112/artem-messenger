# updater.py
import flet as ft
import requests
import json
import webbrowser
from datetime import datetime
import config

class UpdateManager:
    """Менеджер обновлений приложения"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.has_update = False
        self.update_info = None
        
    def check_for_updates(self, silent=False):
        """Проверка наличия обновлений"""
        try:
            print(f"🔍 Проверяем обновления для {config.APP_NAME} v{config.APP_VERSION}...")
            
            response = requests.get(
                config.GITHUB_API_URL,
                headers={"User-Agent": f"{config.APP_NAME}/{config.APP_VERSION}"},
                timeout=5
            )
            
            if response.status_code == 200:
                release_data = response.json()
                self.process_release_data(release_data, silent)
            else:
                print(f"⚠️ Не удалось проверить обновления: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            if not silent:
                print(f"📡 Ошибка сети при проверке обновлений: {e}")
        except Exception as e:
            print(f"❌ Ошибка при проверке обновлений: {e}")
    
    def process_release_data(self, release_data, silent=False):
        """Обработка данных о релизе"""
        latest_version = release_data.get("tag_name", "").lstrip('v')
        current_version = config.APP_VERSION
        
        print(f"📊 Текущая: {current_version}, Последняя: {latest_version}")
        
        # Сравниваем версии
        if self.compare_versions(current_version, latest_version) < 0:
            self.has_update = True
            self.update_info = {
                "version": latest_version,
                "name": release_data.get("name", ""),
                "body": release_data.get("body", ""),
                "published_at": release_data.get("published_at", ""),
                "download_url": None,
                "prerelease": release_data.get("prerelease", False)
            }
            
            # Ищем APK файл в ассетах
            for asset in release_data.get("assets", []):
                if asset.get("name", "").endswith(".apk"):
                    self.update_info["download_url"] = asset.get("browser_download_url")
                    break
            
            print(f"🎉 Доступно обновление до v{latest_version}!")
            
            if not silent:
                self.show_update_notification()
        else:
            if not silent:
                print("✅ У вас последняя версия")
                self.show_no_update_message()
    
    def compare_versions(self, v1, v2):
        """Сравнение версий (возвращает -1 если v1 < v2)"""
        import re
        
        def parse_version(v):
            return [int(x) for x in re.sub(r'[^0-9.]', '', v).split('.')]
        
        try:
            v1_parts = parse_version(v1)
            v2_parts = parse_version(v2)
            
            # Дополняем нулями до одинаковой длины
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (max_len - len(v1_parts))
            v2_parts += [0] * (max_len - len(v2_parts))
            
            for i in range(max_len):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1
            return 0
        except:
            return -1 if v1 < v2 else 1 if v1 > v2 else 0
    
    def show_update_notification(self):
        """Показать уведомление об обновлении"""
        if not self.update_info:
            return
        
        # Создаем баннер обновления
        update_banner = ft.Container(
            content=ft.Row([
                ft.Icon("update", color=ft.colors.WHITE),
                ft.Column([
                    ft.Text("Доступно обновление!", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Версия {self.update_info['version']}", color=ft.colors.WHITE70, size=12),
                ], expand=True, spacing=0),
                ft.IconButton(
                    icon="close",
                    icon_color=ft.colors.WHITE,
                    on_click=lambda e: self.close_banner(update_banner),
                    tooltip="Закрыть"
                ),
                ft.IconButton(
                    icon="download",
                    icon_color=ft.colors.WHITE,
                    on_click=lambda e: self.show_update_dialog(),
                    tooltip="Подробнее"
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=config.PRIMARY_COLOR,
            padding=10,
            border_radius=10,
            margin=10
        )
        
        # Добавляем в начало страницы
        if self.page.controls:
            self.page.controls.insert(0, update_banner)
            self.page.update()
    
    def close_banner(self, banner):
        """Закрыть баннер обновления"""
        if banner in self.page.controls:
            self.page.controls.remove(banner)
            self.page.update()
    
    def show_update_dialog(self):
        """Показать диалог с деталями обновления"""
        if not self.update_info:
            return
        
        # Форматируем дату
        try:
            pub_date = datetime.fromisoformat(self.update_info['published_at'].replace('Z', '+00:00'))
            date_str = pub_date.strftime("%d.%m.%Y %H:%M")
        except:
            date_str = self.update_info['published_at']
        
        # Создаем диалог
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("📱 Обновление приложения"),
            content=ft.Column([
                ft.Text(f"Доступна новая версия: {self.update_info['version']}", weight=ft.FontWeight.BOLD),
                ft.Text(f"Дата выпуска: {date_str}"),
                ft.Divider(height=10),
                ft.Text("Что нового:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(self.update_info['body'] or "Нет описания", selectable=True),
                    padding=10,
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=5,
                ) if self.update_info['body'] else ft.Text("Нет описания", italic=True),
                ft.Divider(height=10),
                ft.Text("Текущая версия: " + config.APP_VERSION, size=12, color=ft.colors.GREY),
            ], tight=True, scroll=ft.ScrollMode.AUTO, height=300),
            actions=[
                ft.TextButton("Позже", on_click=lambda e: self.close_dialog()),
                ft.TextButton("Скачать", 
                    on_click=lambda e: self.download_update(),
                    style=ft.ButtonStyle(bgcolor=ft.colors.GREEN)),
                ft.TextButton("Игнорировать эту версию",
                    on_click=lambda e: self.ignore_version(),
                    style=ft.ButtonStyle(color=ft.colors.GREY)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def show_no_update_message(self):
        """Показать сообщение об отсутствии обновлений"""
        snackbar = ft.SnackBar(
            content=ft.Text("✅ У вас установлена последняя версия приложения"),
            action="OK"
        )
        self.page.snack_bar = snackbar
        snackbar.open = True
        self.page.update()
    
    def download_update(self):
        """Скачать обновление"""
        if self.update_info and self.update_info.get('download_url'):
            webbrowser.open(self.update_info['download_url'])
            self.close_dialog()
            
            # Показываем инструкцию
            self.show_install_instructions()
        else:
            self.show_error("Ссылка для скачивания не найдена")
    
    def show_install_instructions(self):
        """Показать инструкцию по установке"""
        instructions = ft.AlertDialog(
            title=ft.Text("📲 Установка обновления"),
            content=ft.Column([
                ft.Text("Инструкция:", weight=ft.FontWeight.BOLD),
                ft.Text("1. Скачайте APK файл в браузере"),
                ft.Text("2. Откройте скачанный файл"),
                ft.Text("3. Разрешите установку из неизвестных источников (если нужно)"),
                ft.Text("4. Установите новую версию"),
                ft.Text("5. Откройте обновленное приложение"),
                ft.Divider(),
                ft.Text("После установки закройте это приложение", color=ft.colors.GREY, size=12),
            ], tight=True),
            actions=[ft.TextButton("OK", on_click=lambda e: self.close_instructions())],
        )
        
        self.page.dialog = instructions
        instructions.open = True
        self.page.update()
    
    def close_instructions(self):
        self.page.dialog.open = False
        self.page.update()
    
    def ignore_version(self):
        """Игнорировать эту версию"""
        # Можно сохранить в настройках, какую версию игнорировать
        print(f"Игнорируем версию {self.update_info['version']}")
        self.close_dialog()
    
    def close_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
    
    def show_error(self, message):
        """Показать ошибку"""
        snackbar = ft.SnackBar(
            content=ft.Text(f"❌ {message}"),
            bgcolor=config.ERROR_COLOR
        )
        self.page.snack_bar = snackbar
        snackbar.open = True
        self.page.update()

def check_on_startup(page):
    """Проверить обновления при старте приложения"""
    updater = UpdateManager(page)
    
    # Проверяем в фоне через 2 секунды после запуска
    def delayed_check():
        import time
        time.sleep(2)
        updater.check_for_updates()
    
    import threading
    threading.Thread(target=delayed_check, daemon=True).start()
    
    return updater
