import flet as ft
import threading
import json
import time
import sys
import requests
import webbrowser
from datetime import datetime

# =============== НАСТРОЙКИ ПРИЛОЖЕНИЯ ===============
APP_NAME = "ARTEM Messenger"
APP_VERSION = "1.0.0"
APP_BUILD = "20241215.001"
GITHUB_REPO = "твой-username/artem-messenger"  # ЗАМЕНИ на свой репозиторий!
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# =============== ЦВЕТА ===============
BLUE_400 = ft.Colors.BLUE_400 if hasattr(ft.Colors, 'BLUE_400') else "#60A5FA"
RED_400 = ft.Colors.RED_400 if hasattr(ft.Colors, 'RED_400') else "#F87171"
GREEN_400 = ft.Colors.GREEN_400 if hasattr(ft.Colors, 'GREEN_400') else "#34D399"
YELLOW_400 = ft.Colors.YELLOW_400 if hasattr(ft.Colors, 'YELLOW_400') else "#FBBF24"
GREY_400 = ft.Colors.GREY_400 if hasattr(ft.Colors, 'GREY_400') else "#9CA3AF"
GREY_500 = ft.Colors.GREY_500 if hasattr(ft.Colors, 'GREY_500') else "#6B7280"
WHITE = ft.Colors.WHITE if hasattr(ft.Colors, 'WHITE') else "#FFFFFF"
BLACK = ft.Colors.BLACK if hasattr(ft.Colors, 'BLACK') else "#000000"
SURFACE_VARIANT = ft.Colors.SURFACE if hasattr(ft.Colors, 'SURFACE') else "#1E293B"
BACKGROUND = ft.Colors.BACKGROUND if hasattr(ft.Colors, 'BACKGROUND') else "#0F172A"
ON_SURFACE = ft.Colors.ON_SURFACE if hasattr(ft.Colors, 'ON_SURFACE') else "#E2E8F0"

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
                # В фоновом режиме показываем только баннер
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
        """Показать небольшой баннер об обновлении"""
        if not self.update_info:
            return
        
        update_banner = ft.Container(
            content=ft.Row([
                ft.Icon("update", color=ft.colors.WHITE, size=16),
                ft.Text("Доступно обновление!", 
                       color=ft.colors.WHITE, 
                       size=12,
                       weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon="close",
                    icon_color=ft.colors.WHITE,
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
        
        # Добавляем в начало страницы
        if hasattr(self.page, 'controls') and self.page.controls:
            self.page.controls.insert(0, update_banner)
            self.page.update()
    
    def show_update_notification(self):
        """Показать полное уведомление об обновлении"""
        if not self.update_info:
            return
        
        # Создаем диалог
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
                    style=ft.ButtonStyle(bgcolor=ft.colors.GREEN)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def close_banner(self, banner):
        """Закрыть баннер"""
        if banner in self.page.controls:
            self.page.controls.remove(banner)
            self.page.update()
    
    def close_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
    
    def download_update(self):
        """Скачать обновление"""
        if self.update_info and self.update_info.get('download_url'):
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

def check_updates_on_startup(page):
    """Проверить обновления при старте приложения"""
    updater = UpdateManager(page)
    
    # Проверяем в фоне через 3 секунды после запуска
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
        
        # Инициализируем менеджер обновлений
        self.updater = check_updates_on_startup(page)
        
        # WebSocket менеджер
        self.ws_manager = None
        self.user_id = None
        self.username = None
        
    def setup_page(self):
        self.page.title = f"{APP_NAME} v{APP_VERSION}"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 15
        self.page.window_width = 500
        self.page.window_height = 800
        self.page.window_resizable = True
        
    def setup_ui(self):
        # Создаем AppBar с кнопкой обновлений
        app_bar = ft.AppBar(
            title=ft.Text(APP_NAME),
            center_title=True,
            bgcolor=SURFACE_VARIANT,
            actions=[
                ft.PopupMenuButton(
                    icon="more_vert",
                    items=[
                        ft.PopupMenuItem(
                            text="Проверить обновления",
                            icon="update",
                            on_click=lambda e: self.check_updates_manual()
                        ),
                        ft.PopupMenuItem(
                            text="О приложении",
                            icon="info",
                            on_click=self.show_about_dialog
                        ),
                    ]
                )
            ]
        )
        
        # Экран входа
        self.login_container = self.create_login_screen()
        
        # Основной экран чата
        self.chat_container = self.create_chat_screen()
        
        # Начинаем с экрана входа
        self.page.add(app_bar, self.login_container)
    
    def create_login_screen(self):
        """Создаем экран входа"""
        name_field = ft.TextField(
            label="Ваше имя",
            hint_text="Введите ваше имя",
            width=300,
            autofocus=True,
            border_radius=10
        )
        
        login_btn = ft.ElevatedButton(
            text="ВОЙТИ В ЧАТ",
            icon="login",
            width=300,
            height=50,
            on_click=lambda e: self.login(name_field.value)
        )
        
        status_text = ft.Text("", color=GREY_400)
        self.login_status = status_text
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=30),
                    ft.Icon("chat_bubble", size=80, color=BLUE_400),
                    ft.Text(APP_NAME, size=32, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Версия {APP_VERSION}", size=14, color=GREY_400),
                    ft.Container(height=40),
                    name_field,
                    ft.Container(height=20),
                    login_btn,
                    status_text
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center
        )
    
    def create_chat_screen(self):
        """Создаем экран чата"""
        # История сообщений
        self.chat_history = ft.ListView(
            expand=True,
            spacing=8,
            padding=10,
            auto_scroll=True
        )
        
        # Поле ввода сообщения
        self.message_input = ft.TextField(
            hint_text="Введите сообщение...",
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=3,
            border_radius=10,
            on_submit=lambda e: self.send_message_ui()
        )
        
        # Поле ID получателя
        self.receiver_input = ft.TextField(
            hint_text="ID получателя",
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            value="123"
        )
        
        # Кнопка отправки
        send_btn = ft.IconButton(
            icon="send",
            icon_size=30,
            on_click=lambda e: self.send_message_ui(),
            bgcolor=BLUE_400,
            icon_color=WHITE,
            tooltip="Отправить"
        )
        
        # Панель ввода
        input_panel = ft.Container(
            content=ft.Row(
                [
                    self.receiver_input,
                    self.message_input,
                    send_btn
                ],
                vertical_alignment=ft.CrossAxisAlignment.END,
                spacing=10
            ),
            padding=10,
            bgcolor=SURFACE_VARIANT,
            border_radius=10
        )
        
        # Статус подключения
        self.connection_status = ft.Text(
            "🔴 Отключено",
            color=RED_400,
            size=12
        )
        
        return ft.Column(
            [
                # Заголовок
                ft.Container(
                    content=ft.Row(
                        [
                            ft.CircleAvatar(
                                content=ft.Icon("person"),
                                bgcolor=BLUE_400
                            ),
                            ft.Column(
                                [
                                    ft.Text("ARTEM Чат", size=18, weight=ft.FontWeight.BOLD),
                                    self.connection_status
                                ],
                                spacing=2
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "Обновить подключение",
                                on_click=lambda e: self.reconnect()
                            )
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=15,
                    bgcolor=SURFACE_VARIANT,
                    border_radius=10
                ),
                
                # История сообщений
                ft.Container(
                    content=self.chat_history,
                    expand=True,
                    bgcolor=BACKGROUND,
                    border_radius=10,
                    padding=5
                ),
                
                # Панель ввода
                input_panel
            ],
            expand=True
        )
    
    def login(self, username):
        """Вход в систему"""
        if not username or not username.strip():
            self.login_status.value = "Введите имя!"
            self.login_status.color = RED_400
            self.page.update()
            return
        
        self.username = username.strip()
        self.user_id = abs(hash(self.username)) % 10000
        
        self.login_status.value = f"Подключаемся как {self.username}..."
        self.login_status.color = BLUE_400
        self.page.update()
        
        # Запускаем WebSocket соединение
        self.start_websocket()
    
    def start_websocket(self):
        """Запускаем WebSocket соединение"""
        # Создаем менеджер WebSocket
        self.ws_manager = WebSocketManager(
            user_id=self.user_id,
            on_connect=self.on_connect,
            on_message=self.on_message,
            on_error=self.on_error
        )
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self.ws_manager.start, daemon=True)
        thread.start()
    
    def on_connect(self, success, message):
        """Обработка подключения"""
        if success:
            # Переключаем на экран чата
            self.page.clean()
            
            # Добавляем AppBar и контент
            app_bar = ft.AppBar(
                title=ft.Text(f"{APP_NAME} - {self.username}"),
                center_title=True,
                bgcolor=SURFACE_VARIANT,
                actions=[
                    ft.PopupMenuButton(
                        icon="more_vert",
                        items=[
                            ft.PopupMenuItem(
                                text="Проверить обновления",
                                icon="update",
                                on_click=lambda e: self.check_updates_manual()
                            ),
                            ft.PopupMenuItem(
                                text="О приложении",
                                icon="info",
                                on_click=self.show_about_dialog
                            ),
                        ]
                    )
                ]
            )
            
            self.page.add(app_bar, self.chat_container)
            
            # Обновляем статус
            self.connection_status.value = f"🟢 Подключено (ID: {self.user_id})"
            self.connection_status.color = GREEN_400
            
            # Добавляем приветственное сообщение
            self.add_message(
                sender=None,
                text=f"👋 Добро пожаловать, {self.username}!\nВаш ID: {self.user_id}\n\nДля отправки сообщения:\n1. Введите ID получателя\n2. Напишите сообщение\n3. Нажмите Enter или кнопку отправки",
                is_system=True
            )
        else:
            self.login_status.value = f"❌ Ошибка: {message}"
            self.login_status.color = RED_400
        
        self.page.update()
    
    def on_message(self, data):
        """Обработка входящих сообщений"""
        sender = data.get("from", "unknown")
        text = data.get("text", "")
        
        if sender and text:
            self.add_message(sender, text, is_outgoing=False)
        elif "error" in data:
            self.add_message(None, f"❌ Ошибка: {data['error']}", is_system=True)
    
    def on_error(self, error):
        """Обработка ошибок"""
        self.connection_status.value = "🔴 Ошибка соединения"
        self.connection_status.color = RED_400
        self.add_message(None, f"⚠️ {error}", is_system=True)
        self.page.update()
    
    def add_message(self, sender, text, is_outgoing=False, is_system=False):
        """Добавление сообщения в чат"""
        time_str = datetime.now().strftime("%H:%M")
        
        if is_system:
            # Системное сообщение
            message_row = ft.Container(
                content=ft.Text(
                    text,
                    size=12,
                    color=GREY_400,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=5
            )
        else:
            # Обычное сообщение
            bubble_color = BLUE_400 if is_outgoing else SURFACE_VARIANT
            text_color = WHITE if is_outgoing else ON_SURFACE
            sender_text = "Вы" if is_outgoing else f"ID: {sender}"
            
            message_row = ft.Row(
                [
                    ft.Container(
                        content=ft.Column([
                            ft.Text(sender_text, size=11, color=GREY_400),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(text, color=text_color),
                                    ft.Text(time_str, size=10, color=GREY_500)
                                ], spacing=2),
                                padding=10,
                                bgcolor=bubble_color,
                                border_radius=15
                            )
                        ], spacing=2),
                        padding=5
                    )
                ],
                alignment=ft.MainAxisAlignment.END if is_outgoing else ft.MainAxisAlignment.START
            )
        
        self.chat_history.controls.append(message_row)
        self.page.update()
    
    def send_message_ui(self):
        """Отправка сообщения из UI"""
        if not self.ws_manager or not self.ws_manager.connected:
            self.add_message(None, "❌ Нет подключения к серверу", is_system=True)
            return
        
        # Получаем ID получателя
        receiver_text = self.receiver_input.value.strip()
        if not receiver_text or not receiver_text.isdigit():
            self.add_message(None, "⚠️ Введите корректный ID получателя", is_system=True)
            return
        
        receiver_id = int(receiver_text)
        
        # Получаем текст сообщения
        text = self.message_input.value.strip()
        if not text:
            return
        
        # Отправляем сообщение
        success = self.ws_manager.send_message(receiver_id, text)
        
        if success:
            # Показываем у себя
            self.add_message(receiver_id, text, is_outgoing=True)
            # Очищаем поле ввода сообщения
            self.message_input.value = ""
            self.page.update()
        else:
            self.add_message(None, "❌ Не удалось отправить сообщение", is_system=True)
    
    def reconnect(self):
        """Переподключение к серверу"""
        self.connection_status.value = "🟡 Переподключаемся..."
        self.connection_status.color = YELLOW_400
        self.page.update()
        
        if self.ws_manager:
            self.ws_manager.stop()
        
        self.start_websocket()
    
    def check_updates_manual(self):
        """Ручная проверка обновлений"""
        self.updater.check_for_updates(silent=False)
    
    def show_about_dialog(self, e):
        """Показать информацию о приложении"""
        about_dialog = ft.AlertDialog(
            title=ft.Text(f"О {APP_NAME}"),
            content=ft.Column([
                ft.Text(f"Версия: {APP_VERSION}"),
                ft.Text(f"Сборка: {APP_BUILD}"),
                ft.Divider(),
                ft.Text("ARTEM Messenger - безопасный мессенджер"),
                ft.Text("Разработано с использованием Python и Flet"),
                ft.Divider(),
                ft.Text("Проверка обновлений: GitHub Releases", 
                       size=12, color=GREY_400),
                ft.Text(f"Репозиторий: {GITHUB_REPO}", 
                       size=10, color=GREY_500, selectable=True),
            ], tight=True),
            actions=[ft.TextButton("Закрыть", on_click=self.close_dialog)],
        )
        
        self.page.dialog = about_dialog
        about_dialog.open = True
        self.page.update()
    
    def close_dialog(self, e=None):
        """Закрыть диалог"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

class WebSocketManager:
    """Управление WebSocket соединением"""
    def __init__(self, user_id, on_connect, on_message, on_error):
        self.user_id = user_id
        self.on_connect = on_connect
        self.on_message = on_message
        self.on_error = on_error
        self.connected = False
        self.running = False
        self.ws = None
        self.thread = None
    
    def start(self):
        """Запуск соединения"""
        import asyncio
        import websockets
        
        async def connect():
            try:
                print(f"🔄 Подключение к ws://localhost:8765/ws/{self.user_id}")
                
                # Подключаемся к серверу
                self.ws = await websockets.connect(
                    f"ws://localhost:8765/ws/{self.user_id}",
                    ping_interval=20,
                    ping_timeout=20
                )
                
                self.connected = True
                self.running = True
                
                # Уведомляем об успешном подключении
                self.on_connect(True, "Успешно подключено")
                
                # Слушаем сообщения
                while self.running:
                    try:
                        message = await self.ws.recv()
                        
                        try:
                            data = json.loads(message)
                            self.on_message(data)
                        except:
                            self.on_message({"text": message})
                            
                    except websockets.exceptions.ConnectionClosed:
                        print("🔌 Соединение закрыто")
                        break
                    except Exception as e:
                        print(f"Ошибка приема: {e}")
                        await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Ошибка подключения: {e}")
                self.on_connect(False, str(e))
                self.on_error(str(e))
        
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(connect())
        finally:
            loop.close()
            self.connected = False
    
    def send_message(self, to_user, text):
        """Отправка сообщения"""
        if not self.connected or not self.ws:
            return False
        
        import asyncio
        
        async def send():
            try:
                await self.ws.send(json.dumps({
                    "to": to_user,
                    "text": text
                }))
                return True
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
                return False
        
        # Создаем временный event loop для отправки
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

def main(page: ft.Page):
    app = MessengerApp(page)
    
    # Обработка закрытия окна
    def on_close():
        if app.ws_manager:
            app.ws_manager.stop()
    
    page.on_close = on_close

if __name__ == "__main__":
    print("=" * 50)
    print(f"🚀 Запуск {APP_NAME} v{APP_VERSION}")
    print(f"📱 Сборка: {APP_BUILD}")
    print(f"🔗 Репозиторий: {GITHUB_REPO}")
    print("=" * 50)
    
    ft.app(target=main)