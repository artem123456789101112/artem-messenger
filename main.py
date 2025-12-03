# main.py - клиентское приложение (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import flet as ft
import threading
import json
import time
import sys
import os
import hashlib
from datetime import datetime
import asyncio
import websockets

# =============== НАСТРОЙКИ ПРИЛОЖЕНИЯ ===============
APP_NAME = "ARTEM Messenger Pro"
APP_VERSION = "3.1.0"
APP_BUILD = "20241218.001"
GITHUB_REPO = "artem123456789101112/artem-messenger"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
SERVER_IP = "localhost"
SERVER_PORT = 8765

# =============== ЦВЕТА ===============
BLUE_400 = "#60A5FA"
RED_400 = "#F87171"
GREEN_400 = "#34D399"
YELLOW_400 = "#FBBF24"
PURPLE_400 = "#A78BFA"
TEAL_400 = "#2DD4BF"
GREY_400 = "#9CA3AF"
GREY_500 = "#6B7280"
WHITE = "#FFFFFF"
BLACK = "#000000"
SURFACE_VARIANT = "#1E293B"
BACKGROUND = "#0F172A"
ON_SURFACE = "#E2E8F0"

# =============== КЛАСС WebSocketManager ===============
class WebSocketManager:
    """Управление WebSocket соединением"""
    
    def __init__(self, on_connect, on_message, on_error):
        self.on_connect = on_connect
        self.on_message = on_message
        self.on_error = on_error
        self.connected = False
        self.running = False
        self.ws = None
        self.server_ip = SERVER_IP
        self.server_port = SERVER_PORT
        self.user_id = None
        self.username = None
        self.usertag = None
        self.session_token = None
        self.is_admin = False
        self.is_owner = False
        self.user_profile = None
    
    def start(self, auth_data):
        """Запуск соединения с аутентификацией"""
        async def connect():
            try:
                server_url = f"ws://{self.server_ip}:{self.server_port}"
                print(f"🔄 Подключение к {server_url}")
                
                # Подключаемся к серверу
                self.ws = await websockets.connect(
                    server_url,
                    ping_interval=20,
                    ping_timeout=20
                )
                
                # Отправляем данные аутентификации
                await self.ws.send(json.dumps(auth_data))
                
                # Получаем ответ
                response = await self.ws.recv()
                data = json.loads(response)
                
                if data.get('type') in ['login_success', 'register_success']:
                    self.connected = True
                    self.running = True
                    self.user_id = data.get('user_id')
                    self.username = data.get('username')
                    self.usertag = data.get('tag')
                    self.session_token = data.get('session_token')
                    self.is_admin = data.get('is_admin', False)
                    self.is_owner = data.get('is_owner', False)
                    
                    self.on_connect(True, f"Успешно подключено как {self.username}")
                    
                    # Получаем начальные данные
                    while self.running:
                        try:
                            message = await self.ws.recv()
                            try:
                                msg_data = json.loads(message)
                                self.on_message(msg_data)
                            except:
                                self.on_message({"text": message})
                                
                        except websockets.exceptions.ConnectionClosed:
                            print("🔌 Соединение закрыто")
                            self.connected = False
                            self.running = False
                            break
                        except Exception as e:
                            print(f"Ошибка приема: {e}")
                            await asyncio.sleep(1)
                else:
                    error_msg = data.get('error', 'Ошибка аутентификации')
                    self.on_connect(False, error_msg)
                
            except Exception as e:
                error_msg = f"❌ Ошибка подключения: {str(e)}"
                print(error_msg)
                self.on_connect(False, error_msg)
                self.on_error(str(e))
        
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(connect())
        finally:
            loop.close()
            self.connected = False
    
    def send_json(self, data):
        """Отправка JSON данных"""
        if not self.connected or not self.ws:
            return False
        
        async def send():
            try:
                await self.ws.send(json.dumps(data))
                return True
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
                return False
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(send())
            loop.close()
            return result
        except:
            return False
    
    def stop(self):
        """Остановка соединения"""
        self.running = False
        self.connected = False
        if self.ws:
            asyncio.run(self.ws.close())

# =============== КЛАСС ОБНОВЛЕНИЙ ===============
class UpdateManager:
    """Менеджер обновлений приложения"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.has_update = False
        self.update_info = None
        
    def check_for_updates(self, silent=True):
        """Проверка наличия обновлений"""
        try:
            print(f"🔍 Проверяем обновления для {APP_NAME} v{APP_VERSION}...")
            
            import requests
            response = requests.get(
                GITHUB_API_URL,
                headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"},
                timeout=5
            )
            
            if response.status_code == 200:
                release_data = response.json()
                self.process_release_data(release_data, silent)
            else:
                if not silent:
                    print(f"⚠️ Не удалось проверить обновления: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            if not silent:
                print(f"📡 Ошибка сети при проверке обновлений: {e}")
        except Exception as e:
            print(f"❌ Ошибка при проверке обновлений: {e}")
    
    def process_release_data(self, release_data, silent=False):
        """Обработка данных о релизе"""
        latest_version = release_data.get("tag_name", "").lstrip('v')
        current_version = APP_VERSION
        
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
                self.show_update_banner()
        else:
            if not silent:
                print("✅ У вас последняя версия")
                self.show_no_update_message()
    
    def compare_versions(self, v1, v2):
        """Сравнение версий"""
        import re
        
        def parse_version(v):
            return [int(x) for x in re.sub(r'[^0-9.]', '', v).split('.')]
        
        try:
            v1_parts = parse_version(v1)
            v2_parts = parse_version(v2)
            
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
    
    def show_update_banner(self):
        """Показать баннер об обновлении"""
        if not self.update_info:
            return
        
        # Добавляем баннер только если его еще нет
        for control in self.page.controls:
            if hasattr(control, 'bgcolor') and control.bgcolor == GREEN_400:
                return
        
        update_banner = ft.Container(
            content=ft.Row([
                ft.Icon("update", color=WHITE, size=16),
                ft.Text("Доступно обновление!", 
                       color=WHITE, 
                       size=12,
                       weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon="close",
                    icon_color=WHITE,
                    icon_size=16,
                    on_click=lambda e: self.close_banner(update_banner),
                    tooltip="Закрыть"
                ),
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor=GREEN_400,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=5,
            margin=ft.margin.only(bottom=5),
            on_click=lambda e: self.show_update_dialog()
        )
        
        self.page.add(update_banner)
        self.page.update()
    
    def show_update_dialog(self):
        """Показать диалог обновления"""
        if not self.update_info:
            return
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("📱 Обновление приложения"),
            content=ft.Column([
                ft.Text(f"Доступна новая версия: {self.update_info['version']}", 
                       weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                ft.Text("Что нового:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(self.update_info['body'] or "Нет описания", selectable=True),
                    padding=10,
                    bgcolor=SURFACE_VARIANT,
                    border_radius=5,
                ) if self.update_info['body'] else ft.Text("Нет описания", italic=True),
                ft.Divider(height=10),
                ft.Text(f"Текущая версия: {APP_VERSION}", size=12, color=GREY_400),
            ], tight=True, scroll=ft.ScrollMode.AUTO, height=300),
            actions=[
                ft.TextButton("Позже", on_click=lambda e: self.close_dialog()),
                ft.TextButton("Скачать", 
                    on_click=lambda e: self.download_update(),
                    style=ft.ButtonStyle(bgcolor=GREEN_400)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def close_banner(self, banner):
        """Закрыть баннер"""
        self.page.controls.remove(banner)
        self.page.update()
    
    def close_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
    
    def download_update(self):
        """Скачать обновление"""
        if self.update_info and self.update_info.get('download_url'):
            import webbrowser
            webbrowser.open(self.update_info['download_url'])
            self.close_dialog()
        else:
            self.show_error("Ссылка для скачивания не найдена")
    
    def show_error(self, message):
        """Показать ошибку"""
        snackbar = ft.SnackBar(
            content=ft.Text(f"❌ {message}"),
            bgcolor=RED_400
        )
        self.page.snack_bar = snackbar
        snackbar.open = True
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
    
    def show_update_notification(self):
        """Показать уведомление об обновлении"""
        dialog = self.show_update_dialog()
        return dialog

def check_updates_on_startup(page):
    """Проверить обновления при старте приложения"""
    updater = UpdateManager(page)
    
    def delayed_check():
        time.sleep(3)
        updater.check_for_updates(silent=True)
    
    threading.Thread(target=delayed_check, daemon=True).start()
    
    return updater

# =============== ОСНОВНОЙ КЛАСС ПРИЛОЖЕНИЯ ===============
class MessengerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        self.setup_ui()
        
        # Менеджер обновлений
        self.updater = check_updates_on_startup(page)
        
        # WebSocket менеджер
        self.ws_manager = None
        self.user_id = None
        self.username = None
        self.usertag = None
        self.is_admin = False
        self.is_owner = False
        self.user_profile = None
        
        # Сохранение токена
        self.load_session_token()
        
        # Текущий экран
        self.current_screen = "login"
        self.current_chat_id = None
        
    def setup_page(self):
        self.page.title = f"{APP_NAME} v{APP_VERSION}"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        self.page.window_width = 400
        self.page.window_height = 800
        self.page.window_resizable = False
        self.page.bgcolor = BACKGROUND
        
    def setup_ui(self):
        # Экран входа
        self.login_screen = self.create_login_screen()
        
        # Экран регистрации
        self.register_screen = self.create_register_screen()
        
        # Экран главного меню
        self.main_menu_screen = self.create_main_menu_screen()
        
        # Экран профиля
        self.profile_screen = self.create_profile_screen()
        
        # Экран чатов
        self.chats_screen = self.create_chats_screen()
        
        # Экран поиска пользователей
        self.search_screen = self.create_search_screen()
        
        # Экран админ-панели
        self.admin_screen = self.create_admin_screen()
        
        # Начинаем с экрана входа или пытаемся восстановить сессию
        if hasattr(self, 'session_token') and self.session_token:
            self.restore_session()
        else:
            self.show_screen("login")
    
    def load_session_token(self):
        """Загрузка сохраненного токена сессии"""
        try:
            import os
            config_dir = os.path.expanduser("~/.artem_messenger")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "session.json")
            
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.session_token = config.get('session_token')
                    print(f"📝 Загружен токен сессии: {self.session_token[:10]}...")
        except Exception as e:
            print(f"❌ Ошибка загрузки токена: {e}")
            self.session_token = None
    
    def save_session_token(self, token):
        """Сохранение токена сессии"""
        try:
            import os
            import json
            config_dir = os.path.expanduser("~/.artem_messenger")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "session.json")
            
            with open(config_file, 'w') as f:
                json.dump({'session_token': token}, f)
            self.session_token = token
            print(f"💾 Токен сессии сохранен")
        except Exception as e:
            print(f"❌ Ошибка сохранения токена: {e}")
    
    def clear_session_token(self):
        """Очистка токена сессии"""
        try:
            import os
            config_dir = os.path.expanduser("~/.artem_messenger")
            config_file = os.path.join(config_dir, "session.json")
            
            if os.path.exists(config_file):
                os.remove(config_file)
            self.session_token = None
            print("🗑️ Токен сессии удален")
        except Exception as e:
            print(f"❌ Ошибка удаления токена: {e}")
    
    def restore_session(self):
        """Восстановление сессии"""
        if not self.session_token:
            self.show_screen("login")
            return
        
        # Создаем WebSocket менеджер
        self.ws_manager = WebSocketManager(
            on_connect=self.on_connect,
            on_message=self.on_message,
            on_error=self.on_error
        )
        
        # Пытаемся восстановить сессию
        auth_data = {
            "type": "session",
            "session_token": self.session_token
        }
        
        self.login_status.value = "Восстанавливаем сессию..."
        self.login_status.color = BLUE_400
        self.page.update()
        
        thread = threading.Thread(target=self.ws_manager.start, args=(auth_data,), daemon=True)
        thread.start()
    
    def create_login_screen(self):
        """Создаем экран входа"""
        self.login_identifier = ft.TextField(
            label="Имя, тэг или email",
            hint_text="Введите username, @tag или email",
            width=300,
            border_radius=10,
            autofocus=True,
            prefix_icon="person"
        )
        
        self.login_password = ft.TextField(
            label="Пароль",
            password=True,
            can_reveal_password=True,
            width=300,
            border_radius=10,
            prefix_icon="lock"
        )
        
        login_btn = ft.ElevatedButton(
            text="ВОЙТИ",
            icon="login",
            width=300,
            height=45,
            on_click=self.login_user,
            style=ft.ButtonStyle(bgcolor=BLUE_400)
        )
        
        register_btn = ft.TextButton(
            text="Создать аккаунт",
            on_click=lambda e: self.show_screen("register")
        )
        
        self.login_status = ft.Text("", color=GREY_400)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=80),
                    ft.Icon("chat_bubble", size=100, color=BLUE_400),
                    ft.Text(APP_NAME, size=36, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Версия {APP_VERSION}", size=14, color=GREY_400),
                    ft.Text(f"🌐 Сервер: {SERVER_IP}:{SERVER_PORT}", 
                           size=12, color=GREY_400, italic=True),
                    ft.Container(height=40),
                    self.login_identifier,
                    ft.Container(height=10),
                    self.login_password,
                    ft.Container(height=20),
                    login_btn,
                    ft.Container(height=10),
                    register_btn,
                    self.login_status
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center
        )
    
    def create_register_screen(self):
        """Создаем экран регистрации"""
        self.reg_username = ft.TextField(
            label="Имя пользователя *",
            hint_text="Например: Иван",
            width=300,
            border_radius=10,
            prefix_icon="person"
        )
        
        self.reg_tag = ft.TextField(
            label="Тэг *",
            hint_text="Например: ivan",
            prefix_text="@",
            width=300,
            border_radius=10,
            prefix_icon="alternate_email"
        )
        
        self.reg_email = ft.TextField(
            label="Email (необязательно)",
            hint_text="email@example.com",
            width=300,
            border_radius=10,
            prefix_icon="email"
        )
        
        self.reg_phone = ft.TextField(
            label="Телефон (необязательно)",
            hint_text="+7 999 123-45-67",
            width=300,
            border_radius=10,
            prefix_icon="phone"
        )
        
        self.reg_password = ft.TextField(
            label="Пароль *",
            password=True,
            can_reveal_password=True,
            width=300,
            border_radius=10,
            prefix_icon="lock"
        )
        
        self.reg_confirm_password = ft.TextField(
            label="Подтвердите пароль *",
            password=True,
            can_reveal_password=True,
            width=300,
            border_radius=10,
            prefix_icon="lock"
        )
        
        register_btn = ft.ElevatedButton(
            text="СОЗДАТЬ АККАУНТ",
            icon="person_add",
            width=300,
            height=45,
            on_click=self.register_user,
            style=ft.ButtonStyle(bgcolor=GREEN_400)
        )
        
        back_btn = ft.TextButton(
            text="Назад ко входу",
            icon="arrow_back",
            on_click=lambda e: self.show_screen("login")
        )
        
        self.reg_status = ft.Text("", color=GREY_400)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=40),
                    ft.Text("Регистрация", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text("* - обязательные поля", size=12, color=GREY_400),
                    ft.Container(height=20),
                    self.reg_username,
                    ft.Container(height=10),
                    self.reg_tag,
                    ft.Container(height=10),
                    self.reg_email,
                    ft.Container(height=10),
                    self.reg_phone,
                    ft.Container(height=10),
                    self.reg_password,
                    ft.Container(height=10),
                    self.reg_confirm_password,
                    ft.Container(height=20),
                    register_btn,
                    ft.Container(height=10),
                    back_btn,
                    self.reg_status
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
            ),
            alignment=ft.alignment.center
        )
    
    def create_main_menu_screen(self):
        """Создаем главное меню"""
        # Создаем текстовые элементы
        self.username_display = ft.Text("ARTEM Messenger", size=18, weight=ft.FontWeight.BOLD)
        self.usertag_display = ft.Text("Добро пожаловать!", size=12, color=GREY_400)
        
        # Карточки меню
        chats_card = ft.Container(
            content=ft.Column([
                ft.Icon("chat", size=40, color=BLUE_400),
                ft.Text("Чаты", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Ваши беседы", size=12, color=GREY_400)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=lambda e: self.show_screen("chats"),
            padding=20,
            bgcolor=SURFACE_VARIANT,
            border_radius=15,
            width=150,
            height=150
        )
        
        profile_card = ft.Container(
            content=ft.Column([
                ft.Icon("person", size=40, color=GREEN_400),
                ft.Text("Профиль", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Ваш аккаунт", size=12, color=GREY_400)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=lambda e: self.show_screen("profile"),
            padding=20,
            bgcolor=SURFACE_VARIANT,
            border_radius=15,
            width=150,
            height=150
        )
        
        search_card = ft.Container(
            content=ft.Column([
                ft.Icon("search", size=40, color=PURPLE_400),
                ft.Text("Поиск", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Найти людей", size=12, color=GREY_400)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=lambda e: self.show_screen("search"),
            padding=20,
            bgcolor=SURFACE_VARIANT,
            border_radius=15,
            width=150,
            height=150
        )
        
        admin_card = ft.Container(
            content=ft.Column([
                ft.Icon("admin_panel_settings", size=40, color=YELLOW_400),
                ft.Text("Админка", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Модерация", size=12, color=GREY_400)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=lambda e: self.show_screen("admin"),
            padding=20,
            bgcolor=SURFACE_VARIANT,
            border_radius=15,
            width=150,
            height=150,
            visible=False  # Будет показываться только админам
        )
        
        self.admin_card_ref = admin_card
        
        # Верхняя панель с пользователем
        user_header = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon("person"),
                    bgcolor=BLUE_400,
                    radius=25
                ),
                ft.Column([
                    self.username_display,
                    self.usertag_display
                ], spacing=2)
            ]),
            padding=20,
            bgcolor=SURFACE_VARIANT
        )
        
        # Кнопка выхода
        logout_btn = ft.TextButton(
            text="Выйти",
            icon="logout",
            on_click=self.logout,
            style=ft.ButtonStyle(color=RED_400)
        )
        
        return ft.Column([
            user_header,
            ft.Container(height=20),
            ft.Row([chats_card, profile_card], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ft.Container(height=20),
            ft.Row([search_card, admin_card], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ft.Container(expand=True),
            logout_btn
        ])
    
    def create_profile_screen(self):
        """Создаем экран профиля"""
        self.profile_username = ft.TextField(
            label="Имя пользователя",
            width=300,
            prefix_icon="person"
        )
        
        self.profile_tag = ft.TextField(
            label="Тэг",
            prefix_text="@",
            width=300,
            read_only=True,
            prefix_icon="alternate_email"
        )
        
        self.profile_email = ft.TextField(
            label="Email",
            width=300,
            prefix_icon="email"
        )
        
        self.profile_phone = ft.TextField(
            label="Телефон",
            width=300,
            prefix_icon="phone"
        )
        
        self.profile_bio = ft.TextField(
            label="О себе",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=300,
            prefix_icon="short_text"
        )
        
        save_btn = ft.ElevatedButton(
            text="СОХРАНИТЬ",
            icon="save",
            width=300,
            on_click=self.update_profile
        )
        
        back_btn = ft.TextButton(
            text="Назад",
            icon="arrow_back",
            on_click=lambda e: self.show_screen("main_menu")
        )
        
        self.profile_status = ft.Text("", color=GREY_400)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    ft.Text("Мой профиль", size=24, weight=ft.FontWeight.BOLD),
                    ft.Container(height=20),
                    self.profile_username,
                    ft.Container(height=10),
                    self.profile_tag,
                    ft.Container(height=10),
                    self.profile_email,
                    ft.Container(height=10),
                    self.profile_phone,
                    ft.Container(height=10),
                    self.profile_bio,
                    ft.Container(height=20),
                    save_btn,
                    ft.Container(height=10),
                    back_btn,
                    self.profile_status
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
            ),
            alignment=ft.alignment.center
        )
    
    def create_chats_screen(self):
        """Создаем экран чатов"""
        self.chats_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20
        )
        
        refresh_btn = ft.IconButton(
            icon="refresh",
            tooltip="Обновить",
            on_click=self.refresh_chats
        )
        
        new_chat_btn = ft.FloatingActionButton(
            icon="add",
            on_click=lambda e: self.show_screen("search")
        )
        
        return ft.Column([
            ft.AppBar(
                title=ft.Text("Мои чаты"),
                leading=ft.IconButton(
                    icon="arrow_back",
                    on_click=lambda e: self.show_screen("main_menu")
                ),
                actions=[refresh_btn],
                bgcolor=SURFACE_VARIANT
            ),
            ft.Container(
                content=self.chats_list,
                expand=True
            ),
            new_chat_btn
        ])
    
    def create_search_screen(self):
        """Создаем экран поиска"""
        self.search_field = ft.TextField(
            hint_text="Поиск пользователей...",
            width=300,
            border_radius=10,
            on_submit=self.search_users,
            prefix_icon="search"
        )
        
        self.search_results = ft.ListView(
            expand=True,
            spacing=10,
            padding=20
        )
        
        search_btn = ft.IconButton(
            icon="search",
            on_click=self.search_users
        )
        
        return ft.Column([
            ft.AppBar(
                title=ft.Text("Поиск пользователей"),
                leading=ft.IconButton(
                    icon="arrow_back",
                    on_click=lambda e: self.show_screen("main_menu")
                ),
                bgcolor=SURFACE_VARIANT
            ),
            ft.Container(
                content=ft.Row([
                    self.search_field,
                    search_btn
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=20
            ),
            ft.Container(
                content=self.search_results,
                expand=True
            )
        ])
    
    def create_admin_screen(self):
        """Создаем админ-панель"""
        self.admin_search_field = ft.TextField(
            hint_text="Поиск пользователя по имени или тэгу",
            width=300,
            prefix_icon="search"
        )
        
        self.admin_search_results = ft.ListView(
            expand=True,
            spacing=10,
            padding=20
        )
        
        # Форма для бана
        self.ban_reason = ft.TextField(
            label="Причина бана",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=300
        )
        
        self.ban_duration = ft.Dropdown(
            label="Срок бана",
            width=300,
            options=[
                ft.dropdown.Option("1", "1 день"),
                ft.dropdown.Option("7", "7 дней"),
                ft.dropdown.Option("30", "30 дней"),
                ft.dropdown.Option("0", "Навсегда"),
            ],
            value="1"
        )
        
        ban_btn = ft.ElevatedButton(
            text="ЗАБЛОКИРОВАТЬ",
            icon="block",
            width=300,
            style=ft.ButtonStyle(bgcolor=RED_400),
            on_click=self.ban_user
        )
        
        unban_btn = ft.ElevatedButton(
            text="РАЗБЛОКИРОВАТЬ",
            icon="lock_open",
            width=300,
            style=ft.ButtonStyle(bgcolor=GREEN_400),
            on_click=self.unban_user
        )
        
        # Форма для мута
        self.mute_duration = ft.Dropdown(
            label="Срок мута",
            width=300,
            options=[
                ft.dropdown.Option("1", "1 час"),
                ft.dropdown.Option("24", "1 день"),
                ft.dropdown.Option("168", "7 дней"),
            ],
            value="1"
        )
        
        mute_btn = ft.ElevatedButton(
            text="ЗАМУТИТЬ",
            icon="volume_off",
            width=300,
            style=ft.ButtonStyle(bgcolor=YELLOW_400),
            on_click=self.mute_user
        )
        
        unmute_btn = ft.ElevatedButton(
            text="РАЗМУТИТЬ",
            icon="volume_up",
            width=300,
            style=ft.ButtonStyle(bgcolor=GREEN_400),
            on_click=self.unmute_user
        )
        
        self.selected_user_id = None
        self.selected_user_name = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
        
        return ft.Column([
            ft.AppBar(
                title=ft.Text("Админ-панель"),
                leading=ft.IconButton(
                    icon="arrow_back",
                    on_click=lambda e: self.show_screen("main_menu")
                ),
                bgcolor=SURFACE_VARIANT
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Поиск пользователя:", size=16, weight=ft.FontWeight.BOLD),
                    self.admin_search_field,
                    ft.ElevatedButton("Найти", on_click=self.admin_search_users)
                ]),
                padding=20
            ),
            ft.Container(
                content=self.admin_search_results,
                height=200,
                border=ft.border.all(1, GREY_400),
                border_radius=10,
                margin=20
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Выбранный пользователь:", size=14),
                    self.selected_user_name,
                    ft.Divider(),
                    ft.Text("Блокировка пользователя:", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Заблокировать:", size=14),
                    self.ban_reason,
                    self.ban_duration,
                    ft.Row([
                        ban_btn,
                        unban_btn
                    ], spacing=10),
                    ft.Divider(),
                    ft.Text("Мут пользователя:", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Заглушить:", size=14),
                    self.mute_duration,
                    ft.Row([
                        mute_btn,
                        unmute_btn
                    ], spacing=10)
                ]),
                padding=20
            )
        ], scroll=ft.ScrollMode.AUTO)
    
    def show_screen(self, screen_name):
        """Показать указанный экран"""
        self.current_screen = screen_name
        
        screens = {
            "login": self.login_screen,
            "register": self.register_screen,
            "main_menu": self.main_menu_screen,
            "profile": self.profile_screen,
            "chats": self.chats_screen,
            "search": self.search_screen,
            "admin": self.admin_screen
        }
        
        self.page.clean()
        self.page.add(screens[screen_name])
        self.page.update()
        
        # Обновляем данные если нужно
        if screen_name == "main_menu":
            self.update_main_menu()
        elif screen_name == "profile":
            self.load_profile()
        elif screen_name == "chats":
            self.load_chats()
    
    def update_main_menu(self):
        """Обновить главное меню"""
        # Показываем админку только админам
        if hasattr(self, 'admin_card_ref') and self.admin_card_ref:
            self.admin_card_ref.visible = self.is_admin or self.is_owner
        
        # Обновляем имя пользователя после входа
        if hasattr(self, 'username_display') and self.username:
            self.username_display.value = self.username
        
        if hasattr(self, 'usertag_display') and self.usertag:
            self.usertag_display.value = self.usertag
        
        self.page.update()
    
    def login_user(self, e):
        """Вход пользователя"""
        identifier = self.login_identifier.value.strip()
        password = self.login_password.value.strip()
        
        if not identifier or not password:
            self.login_status.value = "Заполните все поля!"
            self.login_status.color = RED_400
            self.page.update()
            return
        
        self.login_status.value = "Подключаемся..."
        self.login_status.color = BLUE_400
        self.page.update()
        
        # Создаем WebSocket менеджер
        self.ws_manager = WebSocketManager(
            on_connect=self.on_connect,
            on_message=self.on_message,
            on_error=self.on_error
        )
        
        # Запускаем подключение
        auth_data = {
            "type": "login",
            "identifier": identifier,
            "password": password
        }
        
        thread = threading.Thread(target=self.ws_manager.start, args=(auth_data,), daemon=True)
        thread.start()
    
    def register_user(self, e):
        """Регистрация пользователя"""
        username = self.reg_username.value.strip()
        tag = self.reg_tag.value.strip()
        email = self.reg_email.value.strip() or None
        phone = self.reg_phone.value.strip() or None
        password = self.reg_password.value.strip()
        confirm_password = self.reg_confirm_password.value.strip()
        
        # Валидация
        errors = []
        if not username:
            errors.append("Введите имя пользователя")
        if not tag:
            errors.append("Введите тэг")
        if not password:
            errors.append("Введите пароль")
        if password != confirm_password:
            errors.append("Пароли не совпадают")
        if len(password) < 6:
            errors.append("Пароль должен быть не менее 6 символов")
        
        if errors:
            self.reg_status.value = "\n".join(errors)
            self.reg_status.color = RED_400
            self.page.update()
            return
        
        self.reg_status.value = "Регистрируем..."
        self.reg_status.color = BLUE_400
        self.page.update()
        
        # Создаем WebSocket менеджер
        self.ws_manager = WebSocketManager(
            on_connect=self.on_connect,
            on_message=self.on_message,
            on_error=self.on_error
        )
        
        # Запускаем подключение
        auth_data = {
            "type": "register",
            "username": username,
            "tag": tag,
            "password": password,
            "email": email if email else None,  # Явно указываем None если пусто
            "phone": phone if phone else None   # Явно указываем None если пусто
        }
        
        thread = threading.Thread(target=self.ws_manager.start, args=(auth_data,), daemon=True)
        thread.start()
    
    def on_connect(self, success, message):
        """Обработка подключения"""
        if success:
            # Сохраняем данные пользователя
            if self.ws_manager:
                self.user_id = self.ws_manager.user_id
                self.username = self.ws_manager.username
                self.usertag = self.ws_manager.usertag
                self.is_admin = self.ws_manager.is_admin
                self.is_owner = self.ws_manager.is_owner
                
                # Сохраняем токен сессии
                if self.ws_manager.session_token:
                    self.save_session_token(self.ws_manager.session_token)
            
            # Показываем главное меню
            self.show_screen("main_menu")
            
            # Показываем уведомление
            self.show_notification("✅ " + message, GREEN_400)
        else:
            # Показываем ошибку
            if self.current_screen == "login":
                self.login_status.value = f"❌ {message}"
                self.login_status.color = RED_400
                self.page.update()
            elif self.current_screen == "register":
                self.reg_status.value = f"❌ {message}"
                self.reg_status.color = RED_400
                self.page.update()
    
    def on_message(self, data):
        """Обработка входящих сообщений"""
        message_type = data.get('type')
        
        if message_type == 'profile_data':
            # Сохраняем профиль
            self.user_profile = data.get('profile', {})
            self.ws_manager.user_profile = self.user_profile
            print(f"✅ Получен профиль: {self.user_profile.get('username')}")
            
            # Обновляем профиль на экране если он открыт
            if self.current_screen == "profile":
                self.load_profile()
        
        elif message_type == 'profile_updated':
            # Обновление профиля
            if data.get('success'):
                self.user_profile = data.get('profile', {})
                self.show_notification("✅ Профиль обновлен", GREEN_400)
                if self.current_screen == "profile":
                    self.profile_status.value = "✅ Профиль обновлен"
                    self.profile_status.color = GREEN_400
                    self.page.update()
            else:
                self.show_notification(f"❌ {data.get('error')}", RED_400)
                if self.current_screen == "profile":
                    self.profile_status.value = f"❌ {data.get('error')}"
                    self.profile_status.color = RED_400
                    self.page.update()
        
        elif message_type == 'new_message':
            # Новое сообщение
            sender_id = data.get('sender_id')
            text = data.get('text')
            timestamp = data.get('timestamp')
            
            # Показываем уведомление
            sender_name = data.get('sender_name', 'Неизвестный')
            self.show_notification(f"📩 Новое сообщение от {sender_name}: {text[:30]}...", BLUE_400)
        
        elif message_type == 'users_list' or message_type == 'search_results':
            # Обновляем список пользователей в поиске
            if self.current_screen == "search":
                self.update_search_results(data.get('users', []))
        
        elif message_type == 'conversations_list':
            # Обновляем список чатов
            if self.current_screen == "chats":
                self.update_conversations(data.get('conversations', []))
        
        elif message_type == 'admin_search_results':
            # Обновляем результаты поиска в админке
            if self.current_screen == "admin":
                self.update_admin_search_results(data.get('users', []))
        
        elif message_type == 'admin_action_result':
            # Результат админского действия
            action = data.get('action')
            if data.get('success'):
                self.show_notification(f"✅ {action.capitalize()}: {data.get('message')}", GREEN_400)
            else:
                self.show_notification(f"❌ {action.capitalize()}: {data.get('message')}", RED_400)
        
        elif message_type == 'error':
            # Ошибка от сервера
            self.show_notification(f"❌ {data.get('error')}", RED_400)
    
    def on_error(self, error):
        """Обработка ошибок"""
        print(f"❌ Ошибка: {error}")
        self.show_notification(f"❌ Ошибка соединения: {error}", RED_400)
    
    def logout(self, e):
        """Выход из системы"""
        if self.ws_manager:
            self.ws_manager.stop()
        
        # Очищаем сессию
        self.clear_session_token()
        
        # Сбрасываем данные пользователя
        self.user_id = None
        self.username = None
        self.usertag = None
        self.is_admin = False
        self.is_owner = False
        self.user_profile = None
        
        # Сбрасываем отображение
        if hasattr(self, 'username_display'):
            self.username_display.value = "ARTEM Messenger"
        
        if hasattr(self, 'usertag_display'):
            self.usertag_display.value = "Добро пожаловать!"
        
        # Скрываем админку
        if hasattr(self, 'admin_card_ref') and self.admin_card_ref:
            self.admin_card_ref.visible = False
        
        # Возвращаемся на экран входа
        self.show_screen("login")
    
    def update_profile(self, e):
        """Обновление профиля"""
        if not self.ws_manager or not self.ws_manager.connected:
            self.show_notification("❌ Нет подключения к серверу", RED_400)
            return
        
        # Получаем значения (пустые строки превращаем в None)
        username = self.profile_username.value.strip() or None
        email = self.profile_email.value.strip() or None
        phone = self.profile_phone.value.strip() or None
        bio = self.profile_bio.value.strip() or None
        
        updates = {
            "type": "update_profile",
            "username": username,
            "email": email,
            "phone": phone,
            "bio": bio
        }
        
        success = self.ws_manager.send_json(updates)
        
        if not success:
            self.profile_status.value = "❌ Ошибка отправки запроса"
            self.profile_status.color = RED_400
            self.page.update()
    
    def load_profile(self):
        """Загрузка данных профиля"""
        if hasattr(self, 'user_profile') and self.user_profile:
            self.profile_username.value = self.user_profile.get('username', '')
            self.profile_tag.value = self.user_profile.get('tag', '')
            self.profile_email.value = self.user_profile.get('email', '')
            self.profile_phone.value = self.user_profile.get('phone', '')
            self.profile_bio.value = self.user_profile.get('bio', '')
            self.page.update()
    
    def load_chats(self):
        """Загрузка списка чатов"""
        if self.ws_manager and self.ws_manager.connected:
            self.ws_manager.send_json({"type": "get_conversations"})
        else:
            # Тестовые чаты (если нет соединения)
            self.update_conversations([
                {"username": "Анна", "tag": "@anna", "last_message": "Привет! Как дела?", "is_online": True},
                {"username": "Максим", "tag": "@maxim", "last_message": "Добрый день!", "is_online": False},
                {"username": "Елена", "tag": "@elena", "last_message": "Когда встретимся?", "is_online": True},
            ])
    
    def update_conversations(self, conversations):
        """Обновление списка чатов"""
        self.chats_list.controls.clear()
        
        for chat in conversations:
            username = chat.get('username', 'Неизвестный')
            tag = chat.get('tag', '')
            last_message = chat.get('last_message', '')
            is_online = chat.get('is_online', False)
            user_id = chat.get('user_id')
            
            chat_item = ft.Container(
                content=ft.Row([
                    ft.Stack([
                        ft.CircleAvatar(
                            content=ft.Text(username[0] if username else "?"),
                            bgcolor=BLUE_400
                        ),
                        ft.Container(
                            content=ft.CircleAvatar(
                                radius=5,
                                bgcolor=GREEN_400 if is_online else GREY_400
                            ),
                            alignment=ft.alignment.bottom_right,
                            width=40,
                            height=40
                        ) if is_online else None
                    ]),
                    ft.Column([
                        ft.Row([
                            ft.Text(username, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(tag, size=12, color=GREY_400)
                        ]),
                        ft.Text(last_message, size=12, color=GREY_400, max_lines=1)
                    ], expand=True, spacing=2),
                ]),
                padding=10,
                on_click=lambda e, uid=user_id, uname=username: self.open_chat(uid, uname)
            )
            self.chats_list.controls.append(chat_item)
        
        self.page.update()
    
    def refresh_chats(self, e):
        """Обновить список чатов"""
        self.load_chats()
        self.show_notification("♻️ Обновляем список чатов...", BLUE_400)
    
    def open_chat(self, user_id, username):
        """Открыть чат с пользователем"""
        self.show_notification(f"💬 Открываем чат с {username}", BLUE_400)
        # TODO: Реализовать открытие чата
    
    def search_users(self, e=None):
        """Поиск пользователей"""
        query = self.search_field.value.strip()
        
        if len(query) < 2:
            self.show_notification("Введите минимум 2 символа", YELLOW_400)
            return
        
        if self.ws_manager and self.ws_manager.connected:
            self.ws_manager.send_json({
                "type": "search_users",
                "query": query
            })
        else:
            # Тестовые результаты (если нет соединения)
            self.update_search_results([
                {"username": "Иван", "tag": "@ivan", "is_online": True},
                {"username": "Мария", "tag": "@maria", "is_online": False},
                {"username": "Алексей", "tag": "@alex", "is_online": True},
            ])
    
    def update_search_results(self, users):
        """Обновление результатов поиска"""
        self.search_results.controls.clear()
        
        for user in users:
            username = user.get('username', 'Неизвестный')
            tag = user.get('tag', '')
            is_online = user.get('is_online', False)
            user_id = user.get('id')
            
            user_item = ft.Container(
                content=ft.Row([
                    ft.Stack([
                        ft.CircleAvatar(
                            content=ft.Text(username[0] if username else "?"),
                            bgcolor=BLUE_400
                        ),
                        ft.Container(
                            content=ft.CircleAvatar(
                                radius=5,
                                bgcolor=GREEN_400 if is_online else GREY_400
                            ),
                            alignment=ft.alignment.bottom_right,
                            width=40,
                            height=40
                        ) if is_online else None
                    ]),
                    ft.Column([
                        ft.Text(username, weight=ft.FontWeight.BOLD),
                        ft.Text(tag, size=12, color=GREY_400)
                    ], expand=True),
                    ft.Text("Онлайн" if is_online else "Оффлайн", 
                           size=12, 
                           color=GREEN_400 if is_online else GREY_400)
                ]),
                padding=10,
                on_click=lambda e, uid=user_id, uname=username: self.start_chat(uid, uname)
            )
            self.search_results.controls.append(user_item)
        
        self.page.update()
    
    def start_chat(self, user_id, username):
        """Начать чат с пользователем"""
        self.show_notification(f"💬 Начинаем чат с {username}", BLUE_400)
        # TODO: Реализовать начало чата
    
    def admin_search_users(self, e):
        """Поиск пользователей для админки"""
        if not self.is_admin and not self.is_owner:
            self.show_notification("❌ Недостаточно прав", RED_400)
            return
        
        query = self.admin_search_field.value.strip()
        
        if len(query) < 2:
            self.show_notification("Введите минимум 2 символа", YELLOW_400)
            return
        
        if self.ws_manager and self.ws_manager.connected:
            self.ws_manager.send_json({
                "type": "admin_search_users",
                "query": query
            })
        else:
            self.show_notification("❌ Нет подключения к серверу", RED_400)
    
    def update_admin_search_results(self, users):
        """Обновление результатов поиска в админке"""
        self.admin_search_results.controls.clear()
        
        for user in users:
            username = user.get('username', 'Неизвестный')
            tag = user.get('tag', '')
            email = user.get('email', '')
            is_blocked = user.get('is_blocked', False)
            is_muted = user.get('is_muted', False)
            user_id = user.get('id')
            
            status = []
            if is_blocked:
                status.append("Заблокирован")
            if is_muted:
                status.append("В муте")
            status_text = ", ".join(status) if status else "Активен"
            
            user_item = ft.Container(
                content=ft.Row([
                    ft.CircleAvatar(
                        content=ft.Text(username[0] if username else "?"),
                        bgcolor=RED_400 if is_blocked else YELLOW_400 if is_muted else BLUE_400
                    ),
                    ft.Column([
                        ft.Text(username, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{tag} • {email}", size=12, color=GREY_400)
                    ], expand=True),
                    ft.Text(status_text, 
                           size=12, 
                           color=RED_400 if is_blocked else YELLOW_400 if is_muted else GREEN_400)
                ]),
                padding=10,
                on_click=lambda e, uid=user_id, uname=username, status=status_text: self.select_user_for_moderation(uid, uname, status)
            )
            self.admin_search_results.controls.append(user_item)
        
        self.page.update()
    
    def select_user_for_moderation(self, user_id, username, status):
        """Выбрать пользователя для модерации"""
        self.selected_user_id = user_id
        self.selected_user_name.value = f"{username} ({status})"
        self.page.update()
        self.show_notification(f"👤 Выбран пользователь: {username}", BLUE_400)
    
    def ban_user(self, e):
        """Заблокировать пользователя"""
        if not self.selected_user_id:
            self.show_notification("❌ Выберите пользователя", RED_400)
            return
        
        if not self.ws_manager or not self.ws_manager.connected:
            self.show_notification("❌ Нет подключения к серверу", RED_400)
            return
        
        reason = self.ban_reason.value.strip()
        duration_days = int(self.ban_duration.value)
        
        self.ws_manager.send_json({
            "type": "admin_ban_user",
            "user_id": self.selected_user_id,
            "reason": reason,
            "duration_days": duration_days
        })
    
    def unban_user(self, e):
        """Разблокировать пользователя"""
        if not self.selected_user_id:
            self.show_notification("❌ Выберите пользователя", RED_400)
            return
        
        if not self.ws_manager or not self.ws_manager.connected:
            self.show_notification("❌ Нет подключения к серверу", RED_400)
            return
        
        self.ws_manager.send_json({
            "type": "admin_unban_user",
            "user_id": self.selected_user_id
        })
    
    def mute_user(self, e):
        """Заглушить пользователя"""
        if not self.selected_user_id:
            self.show_notification("❌ Выберите пользователя", RED_400)
            return
        
        if not self.ws_manager or not self.ws_manager.connected:
            self.show_notification("❌ Нет подключения к серверу", RED_400)
            return
        
        duration_hours = int(self.mute_duration.value)
        
        self.ws_manager.send_json({
            "type": "admin_mute_user",
            "user_id": self.selected_user_id,
            "duration_hours": duration_hours
        })
    
    def unmute_user(self, e):
        """Размутить пользователя"""
        if not self.selected_user_id:
            self.show_notification("❌ Выберите пользователя", RED_400)
            return
        
        if not self.ws_manager or not self.ws_manager.connected:
            self.show_notification("❌ Нет подключения к серверу", RED_400)
            return
        
        self.ws_manager.send_json({
            "type": "admin_unmute_user",
            "user_id": self.selected_user_id
        })
    
    def show_notification(self, message, color):
        """Показать уведомление"""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
            duration=3000
        )
        self.page.snack_bar = snackbar
        snackbar.open = True
        self.page.update()

def main(page: ft.Page):
    app = MessengerApp(page)
    
    # Обработка закрытия окна
    def on_close():
        if app.ws_manager:
            app.ws_manager.stop()
    
    page.on_close = on_close

if __name__ == "__main__":
    print("=" * 60)
    print(f"🚀 Запуск {APP_NAME} v{APP_VERSION}")
    print(f"📱 Сборка: {APP_BUILD}")
    print(f"🌐 Сервер: {SERVER_IP}:{SERVER_PORT}")
    print(f"🔗 Репозиторий: {GITHUB_REPO}")
    print("=" * 60)
    print("📋 Функции в этой версии:")
    print("• Регистрация с тэгом (@username)")
    print("• Профиль с настройками (email, телефон, био - необязательно)")
    print("• Поиск пользователей")
    print("• Админ-панель (для модераторов)")
    print("• Обновления через GitHub")
    print("• Сохранение сессии")
    print("• Восстановление сессии при запуске")
    print("• Разблокировка и размут пользователей")
    print("=" * 60)
    
    ft.app(target=main)
    

    ft.app(target=main)

