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
            
            # Если открыт чат с отправителем, добавляем сообщение
            if self.current_screen == "chats" and self.current_chat_id == sender_id:
                self.add_message_to_chat(sender_name, text, timestamp, is_me=False)
        
        elif message_type == 'message_sent':
            # Сообщение отправлено
            if data.get('success'):
                if self.current_screen == "chats" and self.current_chat_id:
                    self.add_message_to_chat("Вы", data.get('text'), data.get('timestamp'), is_me=True)
            else:
                self.show_notification(f"❌ Не удалось отправить сообщение: {data.get('error')}", RED_400)
        
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
        self.current_chat_id = user_id
        
        # Обновляем область чата
        self.chat_area.controls.clear()
        self.chat_area.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(username[0] if username else "?"),
                            bgcolor=BLUE_400,
                            radius=30
                        ),
                        ft.Column([
                            ft.Text(username, size=20, weight=ft.FontWeight.BOLD),
                            ft.Text("Онлайн", size=12, color=GREEN_400)
                        ], spacing=2)
                    ]),
                    ft.Divider(),
                    ft.ListView(
                        expand=True,
                        spacing=10,
                        padding=10,
                        auto_scroll=True
                    )
                ]),
                expand=True
            )
        )
        
        # Включаем поле ввода сообщения
        self.message_input.disabled = False
        self.message_input.value = ""
        
        # Включаем кнопку отправки
        send_btn = self.page.controls[0].controls[2].controls[2].controls[2]
        send_btn.disabled = False
        
        # Загружаем историю сообщений
        self.load_chat_history(user_id)
        
        self.page.update()
        self.show_notification(f"💬 Открыт чат с {username}", BLUE_400)
    
    def load_chat_history(self, user_id):
        """Загрузка истории сообщений"""
        # Получаем контейнер с историей сообщений
        chat_container = self.chat_area.controls[0].content.controls[2]
        
        # Очищаем историю
        chat_container.controls.clear()
        
        # Тестовая история (в реальности запрашивать с сервера)
        test_messages = [
            {"sender": "Вы", "text": "Привет! Как дела?", "time": "10:30", "is_me": True},
            {"sender": "Анна", "text": "Привет! Всё отлично, спасибо!", "time": "10:31", "is_me": False},
            {"sender": "Анна", "text": "Когда встретимся?", "time": "10:32", "is_me": False},
            {"sender": "Вы", "text": "Может в пятницу?", "time": "10:33", "is_me": True},
        ]
        
        for msg in test_messages:
            message_item = self.create_message_item(msg)
            chat_container.controls.append(message_item)
        
        self.page.update()
    
    def create_message_item(self, message):
        """Создание элемента сообщения"""
        if message.get('is_me', False):
            # Сообщение от меня
            return ft.Container(
                content=ft.Column([
                    ft.Text(message["sender"], size=10, color=GREY_400),
                    ft.Container(
                        content=ft.Text(message["text"], color=WHITE),
                        padding=10,
                        bgcolor=BLUE_400,
                        border_radius=10,
                        border=ft.border.all(1, BLUE_400)
                    ),
                    ft.Text(message["time"], size=10, color=GREY_400)
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                margin=ft.margin.only(left=50, right=10, top=5, bottom=5)
            )
        else:
            # Сообщение от собеседника
            return ft.Container(
                content=ft.Column([
                    ft.Text(message["sender"], size=10, color=GREY_400),
                    ft.Container(
                        content=ft.Text(message["text"], color=WHITE),
                        padding=10,
                        bgcolor=SURFACE_VARIANT,
                        border_radius=10,
                        border=ft.border.all(1, GREY_400)
                    ),
                    ft.Text(message["time"], size=10, color=GREY_400)
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START),
                margin=ft.margin.only(left=10, right=50, top=5, bottom=5)
            )
    
    def send_message(self, e):
        """Отправить сообщение"""
        if not self.current_chat_id:
            self.show_notification("❌ Выберите чат", RED_400)
            return
        
        message_text = self.message_input.value.strip()
        if not message_text:
            return
        
        # Очищаем поле ввода
        self.message_input.value = ""
        
        # Добавляем сообщение в историю
        message_data = {
            "sender": "Вы",
            "text": message_text,
            "time": datetime.now().strftime("%H:%M"),
            "is_me": True
        }
        
        message_item = self.create_message_item(message_data)
        chat_container = self.chat_area.controls[0].content.controls[2]
        chat_container.controls.append(message_item)
        
        # Отправляем через WebSocket
        if self.ws_manager and self.ws_manager.connected:
            self.ws_manager.send_json({
                "type": "send_message",
                "receiver_id": self.current_chat_id,
                "text": message_text
            })
        else:
            self.show_notification("⚠️ Сообщение сохранено локально (нет соединения)", YELLOW_400)
        
        self.page.update()
    
    def add_message_to_chat(self, sender_name, text, timestamp, is_me=False):
        """Добавить сообщение в чат"""
        if self.current_screen == "chats" and self.current_chat_id:
            message_data = {
                "sender": sender_name,
                "text": text,
                "time": timestamp if timestamp else datetime.now().strftime("%H:%M"),
                "is_me": is_me
            }
            
            message_item = self.create_message_item(message_data)
            chat_container = self.chat_area.controls[0].content.controls[2]
            chat_container.controls.append(message_item)
            self.page.update()
    
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
        self.show_screen("chats")
        self.open_chat(user_id, username)
    
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
    print(f"💻 Сборка: {APP_BUILD}")
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
    print("• Чат в реальном времени")
    print("• Разблокировка и размут пользователей")
    print("• Desktop интерфейс с раздельными панелями")
    print("=" * 60)
    
    ft.app(target=main)