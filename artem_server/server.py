# server.py - Простой рабочий сервер (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import asyncio
import websockets
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name="artem_messenger.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
        self.create_default_users()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            tag TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            bio TEXT,
            is_online BOOLEAN DEFAULT 0,
            is_admin BOOLEAN DEFAULT 0,
            is_owner BOOLEAN DEFAULT 0,
            is_blocked BOOLEAN DEFAULT 0,
            is_muted BOOLEAN DEFAULT 0,
            mute_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица сообщений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
        ''')
        
        # Таблица сессий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Таблица блокировок
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            blocked_user_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (blocked_user_id) REFERENCES users(id),
            UNIQUE(user_id, blocked_user_id)
        )
        ''')
        
        self.conn.commit()
        print("✅ Таблицы базы данных созданы")
    
    def create_default_users(self):
        cursor = self.conn.cursor()
        
        # Проверяем существование тестовых пользователей
        cursor.execute("SELECT COUNT(*) FROM users WHERE tag = '@artem'")
        if cursor.fetchone()[0] == 0:
            users = [
                # (username, tag, password, email, phone, bio, is_admin, is_owner, is_blocked)
                ("Артем", "@artem", "Fhntv2009vbi.", None, None, None, True, False, False),
                ("Владелец", "@owner", "admin123", "owner@example.com", "+79991234567", "Системный владелец", True, True, False),  # is_blocked = False
                ("Анна", "@anna", "password123", "anna@example.com", None, "Привет всем!", False, False, False),
                ("Максим", "@maxim", "password123", None, "+79998765432", None, False, False, False),
                ("Елена", "@elena", "password123", "elena@example.com", None, "Люблю общаться", False, False, False),
            ]
            
            for username, tag, password, email, phone, bio, is_admin, is_owner, is_blocked in users:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                cursor.execute('''
                INSERT INTO users (username, tag, password_hash, email, phone, bio, is_admin, is_owner, is_blocked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, tag, password_hash, email, phone, bio, is_admin, is_owner, is_blocked))
            
            self.conn.commit()
            print("✅ Созданы тестовые пользователи:")
            print("   @artem / Fhntv2009vbi. (админ)")
            print("   @owner / admin123 (владелец и админ)")
            print("   @anna / password123")
            print("   @maxim / password123")
            print("   @elena / password123")
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, tag, password, email=None, phone=None):
        cursor = self.conn.cursor()
        
        # Проверяем уникальность
        cursor.execute("SELECT id FROM users WHERE username = ? OR tag = ?", 
                      (username, tag))
        if cursor.fetchone():
            return False, "Имя пользователя или тэг уже заняты"
        
        if not tag.startswith("@"):
            tag = "@" + tag
        
        password_hash = self.hash_password(password)
        
        try:
            cursor.execute('''
            INSERT INTO users (username, tag, password_hash, email, phone)
            VALUES (?, ?, ?, ?, ?)
            ''', (username, tag, password_hash, email, phone))
            self.conn.commit()
            user_id = cursor.lastrowid
            return True, user_id
        except Exception as e:
            return False, str(e)
    
    def login_user(self, identifier, password):
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id, username, tag, password_hash, is_admin, is_owner, is_blocked, is_muted
        FROM users 
        WHERE username = ? OR tag = ? OR email = ?
        ''', (identifier, identifier, identifier))
        
        user = cursor.fetchone()
        if not user:
            return False, "Пользователь не найден"
        
        user_id, username, tag, password_hash, is_admin, is_owner, is_blocked, is_muted = user
        
        # Проверяем блокировку
        if is_blocked:
            return False, "Аккаунт заблокирован"
        
        if self.hash_password(password) != password_hash:
            return False, "Неверный пароль"
        
        # Создаем сессию
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        
        cursor.execute('''
        INSERT INTO sessions (user_id, session_token, expires_at)
        VALUES (?, ?, ?)
        ''', (user_id, session_token, expires_at))
        
        # Обновляем статус онлайн
        cursor.execute('UPDATE users SET is_online = 1 WHERE id = ?', (user_id,))
        self.conn.commit()
        
        return True, {
            "user_id": user_id,
            "username": username,
            "tag": tag,
            "session_token": session_token,
            "is_admin": bool(is_admin),
            "is_owner": bool(is_owner),
            "is_blocked": bool(is_blocked),
            "is_muted": bool(is_muted)
        }
    
    def unban_user(self, user_id):
        """Разблокировать пользователя"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE users 
            SET is_blocked = 0 
            WHERE id = ?
            ''', (user_id,))
            
            self.conn.commit()
            return True, "Пользователь разблокирован"
        except Exception as e:
            return False, f"Ошибка разблокировки: {str(e)}"
    
    def unmute_user(self, user_id):
        """Размутить пользователя"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE users 
            SET is_muted = 0, mute_expires_at = NULL
            WHERE id = ?
            ''', (user_id,))
            
            self.conn.commit()
            return True, "Пользователь размучен"
        except Exception as e:
            return False, f"Ошибка размута: {str(e)}"
    
    def verify_session(self, session_token):
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT u.id, u.username, u.tag, u.is_admin, u.is_owner, u.is_blocked, u.is_muted
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_token = ? AND s.expires_at > ?
        ''', (session_token, datetime.now().isoformat()))
        
        session = cursor.fetchone()
        if not session:
            return False, "Сессия истекла или недействительна"
        
        user_id, username, tag, is_admin, is_owner, is_blocked, is_muted = session
        
        # Проверяем блокировку
        if is_blocked:
            return False, "Аккаунт заблокирован"
        
        # Обновляем статус онлайн
        cursor.execute('UPDATE users SET is_online = 1 WHERE id = ?', (user_id,))
        self.conn.commit()
        
        return True, {
            "user_id": user_id,
            "username": username,
            "tag": tag,
            "session_token": session_token,
            "is_admin": bool(is_admin),
            "is_owner": bool(is_owner),
            "is_blocked": bool(is_blocked),
            "is_muted": bool(is_muted)
        }
    
    def save_message(self, sender_id, receiver_id, text):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO messages (sender_id, receiver_id, text)
        VALUES (?, ?, ?)
        ''', (sender_id, receiver_id, text))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_by_id(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, username, tag, email, phone, bio, is_online 
        FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return None
        
        return {
            "id": user[0],
            "username": user[1],
            "tag": user[2],
            "email": user[3],
            "phone": user[4],
            "bio": user[5],
            "is_online": bool(user[6])
        }
    
    def get_user_profile(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT username, tag, email, phone, bio, is_admin, is_owner, created_at
        FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return None
        
        return {
            "username": user[0],
            "tag": user[1],
            "email": user[2],
            "phone": user[3],
            "bio": user[4],
            "is_admin": bool(user[5]),
            "is_owner": bool(user[6]),
            "created_at": user[7]
        }
    
    def update_user_profile(self, user_id, username=None, email=None, phone=None, bio=None):
        cursor = self.conn.cursor()
        
        updates = []
        params = []
        
        if username is not None:
            # Проверяем уникальность username
            cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
            if cursor.fetchone():
                return False, "Имя пользователя уже занято"
            updates.append("username = ?")
            params.append(username)
        
        if email is not None:
            # Проверяем уникальность email (если указан)
            if email:
                cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
                if cursor.fetchone():
                    return False, "Email уже используется"
                updates.append("email = ?")
                params.append(email)
            else:
                updates.append("email = NULL")
        
        if phone is not None:
            # Проверяем уникальность телефона (если указан)
            if phone:
                cursor.execute("SELECT id FROM users WHERE phone = ? AND id != ?", (phone, user_id))
                if cursor.fetchone():
                    return False, "Телефон уже используется"
                updates.append("phone = ?")
                params.append(phone)
            else:
                updates.append("phone = NULL")
        
        if bio is not None:
            updates.append("bio = ?")
            params.append(bio)
        
        if not updates:
            return False, "Нет данных для обновления"
        
        params.append(user_id)
        
        try:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            self.conn.commit()
            return True, "Профиль успешно обновлен"
        except Exception as e:
            return False, f"Ошибка обновления: {str(e)}"
    
    def search_users(self, query, current_user_id):
        cursor = self.conn.cursor()
        search_term = f"%{query}%"
        
        cursor.execute('''
        SELECT id, username, tag, is_online
        FROM users 
        WHERE (username LIKE ? OR tag LIKE ?)
          AND id != ?
          AND is_blocked = 0
        LIMIT 20
        ''', (search_term, search_term, current_user_id))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "username": row[1],
                "tag": row[2],
                "is_online": bool(row[3])
            })
        
        return users
    
    def get_conversations(self, user_id):
        cursor = self.conn.cursor()
        
        # Получаем последние сообщения с каждым пользователем
        cursor.execute('''
        SELECT 
            CASE 
                WHEN sender_id = ? THEN receiver_id
                ELSE sender_id
            END as other_user_id,
            MAX(m.timestamp) as last_message_time,
            m.text as last_message,
            u.username as other_username,
            u.tag as other_tag,
            u.is_online,
            COUNT(CASE WHEN m.receiver_id = ? AND m.is_read = 0 THEN 1 END) as unread_count
        FROM messages m
        JOIN users u ON u.id = CASE 
                WHEN m.sender_id = ? THEN m.receiver_id
                ELSE m.sender_id
            END
        WHERE (m.sender_id = ? OR m.receiver_id = ?)
          AND u.is_blocked = 0
        GROUP BY other_user_id
        ORDER BY last_message_time DESC
        ''', (user_id, user_id, user_id, user_id, user_id))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                "user_id": row[0],
                "last_message_time": row[1],
                "last_message": row[2][:50] + "..." if row[2] and len(row[2]) > 50 else row[2],
                "username": row[3],
                "tag": row[4],
                "is_online": bool(row[5]),
                "unread_count": row[6]
            })
        
        return conversations
    
    def get_chat_history(self, user1_id, user2_id, limit=50):
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT 
            m.id,
            m.sender_id,
            m.receiver_id,
            m.text,
            m.timestamp,
            m.is_read,
            u.username as sender_name,
            u.tag as sender_tag
        FROM messages m
        JOIN users u ON u.id = m.sender_id
        WHERE (m.sender_id = ? AND m.receiver_id = ?)
           OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.timestamp DESC
        LIMIT ?
        ''', (user1_id, user2_id, user2_id, user1_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "sender_id": row[1],
                "receiver_id": row[2],
                "text": row[3],
                "timestamp": row[4],
                "is_read": bool(row[5]),
                "sender_name": row[6],
                "sender_tag": row[7]
            })
        
        # Помечаем сообщения как прочитанные
        cursor.execute('''
        UPDATE messages 
        SET is_read = 1 
        WHERE receiver_id = ? AND sender_id = ? AND is_read = 0
        ''', (user1_id, user2_id))
        self.conn.commit()
        
        return messages
    
    def admin_search_users(self, query):
        cursor = self.conn.cursor()
        search_term = f"%{query}%"
        
        cursor.execute('''
        SELECT id, username, tag, email, is_online, is_blocked, is_muted, created_at
        FROM users 
        WHERE username LIKE ? OR tag LIKE ? OR email LIKE ?
        LIMIT 20
        ''', (search_term, search_term, search_term))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "username": row[1],
                "tag": row[2],
                "email": row[3],
                "is_online": bool(row[4]),
                "is_blocked": bool(row[5]),
                "is_muted": bool(row[6]),
                "created_at": row[7]
            })
        
        return users
    
    def ban_user(self, user_id, reason, duration_days):
        cursor = self.conn.cursor()
        
        try:
            # Если duration_days = 0, бан навсегда
            if duration_days == 0:
                cursor.execute('''
                UPDATE users 
                SET is_blocked = 1 
                WHERE id = ?
                ''', (user_id,))
            else:
                # Для временного бана можно добавить поле ban_expires_at
                cursor.execute('''
                UPDATE users 
                SET is_blocked = 1 
                WHERE id = ?
                ''', (user_id,))
            
            self.conn.commit()
            return True, f"Пользователь заблокирован на {duration_days if duration_days > 0 else 'всегда'} дней"
        except Exception as e:
            return False, f"Ошибка бана: {str(e)}"
    
    def mute_user(self, user_id, duration_hours):
        cursor = self.conn.cursor()
        
        try:
            mute_expires = None
            if duration_hours > 0:
                mute_expires = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
            
            cursor.execute('''
            UPDATE users 
            SET is_muted = 1, mute_expires_at = ?
            WHERE id = ?
            ''', (mute_expires, user_id))
            
            self.conn.commit()
            return True, f"Пользователь заглушен на {duration_hours} часов"
        except Exception as e:
            return False, f"Ошибка мута: {str(e)}"

class ChatServer:
    def __init__(self):
        self.db = Database()
        self.connected_users = {}  # user_id -> websocket
        print("✅ База данных инициализирована")
    
    async def handler(self, websocket):
        """Обработчик WebSocket подключений (ИСПРАВЛЕНО: убран path)"""
        print(f"📡 Новое подключение")
        user_id = None
        try:
            # Ждем данные аутентификации
            message = await websocket.recv()
            data = json.loads(message)
            
            if data.get('type') == 'register':
                username = data.get('username', '').strip()
                tag = data.get('tag', '').strip()
                password = data.get('password', '')
                email = data.get('email', '').strip() or None  # None если пусто
                phone = data.get('phone', '').strip() or None  # None если пусто
                
                if not username or not tag or not password:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Заполните обязательные поля: имя, тэг, пароль"
                    }))
                    return
                
                success, result = self.db.register_user(username, tag, password, email, phone)
                
                if success:
                    user_id = result
                    self.connected_users[user_id] = websocket
                    
                    # Создаем сессию для нового пользователя
                    session_token = secrets.token_urlsafe(32)
                    expires_at = (datetime.now() + timedelta(days=30)).isoformat()
                    
                    cursor = self.db.conn.cursor()
                    cursor.execute('''
                    INSERT INTO sessions (user_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                    ''', (user_id, session_token, expires_at))
                    self.db.conn.commit()
                    
                    await websocket.send(json.dumps({
                        "type": "register_success",
                        "user_id": user_id,
                        "username": username,
                        "tag": tag,
                        "session_token": session_token,
                        "message": f"Добро пожаловать, {username}!"
                    }))
                    print(f"✅ Зарегистрирован: {username} ({tag})")
                else:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": result
                    }))
                    return
                
            elif data.get('type') == 'login':
                identifier = data.get('identifier', '').strip()
                password = data.get('password', '')
                
                if not identifier or not password:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Заполните все поля"
                    }))
                    return
                
                success, result = self.db.login_user(identifier, password)
                
                if success:
                    user_id = result['user_id']
                    self.connected_users[user_id] = websocket
                    
                    await websocket.send(json.dumps({
                        "type": "login_success",
                        **result,
                        "message": f"С возвращением, {result['username']}!"
                    }))
                    print(f"✅ Вход: {result['username']} ({result['tag']})")
                else:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": result
                    }))
                    return
            
            elif data.get('type') == 'session':
                session_token = data.get('session_token', '')
                
                if not session_token:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Токен сессии не предоставлен"
                    }))
                    return
                
                success, result = self.db.verify_session(session_token)
                
                if success:
                    user_id = result['user_id']
                    self.connected_users[user_id] = websocket
                    
                    await websocket.send(json.dumps({
                        "type": "login_success",
                        **result,
                        "message": f"С возвращением, {result['username']}!"
                    }))
                    print(f"✅ Восстановлена сессия: {result['username']}")
                else:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": result
                    }))
                    return
            
            # Если аутентификация успешна
            if user_id:
                # Отправляем данные профиля
                profile = self.db.get_user_profile(user_id)
                if profile:
                    await websocket.send(json.dumps({
                        "type": "profile_data",
                        "profile": profile
                    }))
                
                # Отправляем список пользователей
                await self.send_users_list(user_id, websocket)
                
                # Отправляем список бесед
                conversations = self.db.get_conversations(user_id)
                await websocket.send(json.dumps({
                    "type": "conversations_list",
                    "conversations": conversations
                }))
                
                # Обработка сообщений
                async for message in websocket:
                    await self.process_message(user_id, message, websocket)
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Отключен пользователь {user_id if user_id else 'unknown'}")
        except Exception as e:
            print(f"❌ Ошибка в handler: {e}")
        finally:
            if user_id:
                if user_id in self.connected_users:
                    del self.connected_users[user_id]
                # Обновляем статус оффлайн
                cursor = self.db.conn.cursor()
                cursor.execute('UPDATE users SET is_online = 0 WHERE id = ?', (user_id,))
                self.db.conn.commit()
    
    async def send_users_list(self, user_id, websocket):
        """Отправка списка пользователей"""
        try:
            users = self.db.search_users("", user_id)
            await websocket.send(json.dumps({
                "type": "users_list",
                "users": users
            }))
        except Exception as e:
            print(f"❌ Ошибка при отправке списка пользователей: {e}")
    
    async def process_message(self, sender_id, message, websocket):
        """Обработка сообщений"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'message':
                receiver_id = data.get('receiver_id')
                text = data.get('text', '').strip()
                
                if not text or not receiver_id:
                    return
                
                # Проверяем, не заблокирован ли пользователь
                user_info = self.db.get_user_by_id(sender_id)
                if not user_info:
                    return
                
                # Проверяем, не в муте ли пользователь
                user_profile = self.db.get_user_profile(sender_id)
                if user_profile and hasattr(user_profile, 'is_muted') and user_profile.get('is_muted'):
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Вы заглушены и не можете отправлять сообщения"
                    }))
                    return
                
                # Сохраняем в БД
                message_id = self.db.save_message(sender_id, receiver_id, text)
                
                # Получаем информацию об отправителе
                sender_info = self.db.get_user_by_id(sender_id)
                sender_name = sender_info['username'] if sender_info else f"User_{sender_id}"
                
                print(f"📤 Сообщение от {sender_name} к {receiver_id}: {text[:50]}...")
                
                # Отправляем подтверждение отправителю
                await websocket.send(json.dumps({
                    "type": "message_sent",
                    "message_id": message_id,
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Отправляем получателю если он онлайн
                if receiver_id in self.connected_users:
                    await self.connected_users[receiver_id].send(json.dumps({
                        "type": "new_message",
                        "sender_id": sender_id,
                        "sender_name": sender_name,
                        "text": text,
                        "timestamp": datetime.now().isoformat()
                    }))
            
            elif message_type == 'get_users':
                await self.send_users_list(sender_id, websocket)
            
            elif message_type == 'search_users':
                query = data.get('query', '').strip()
                users = self.db.search_users(query, sender_id)
                await websocket.send(json.dumps({
                    "type": "search_results",
                    "query": query,
                    "users": users
                }))
            
            elif message_type == 'get_conversations':
                conversations = self.db.get_conversations(sender_id)
                await websocket.send(json.dumps({
                    "type": "conversations_list",
                    "conversations": conversations
                }))
            
            elif message_type == 'get_chat_history':
                other_user_id = data.get('user_id')
                if other_user_id:
                    messages = self.db.get_chat_history(sender_id, other_user_id)
                    await websocket.send(json.dumps({
                        "type": "chat_history",
                        "user_id": other_user_id,
                        "messages": messages
                    }))
            
            elif message_type == 'update_profile':
                username = data.get('username')
                email = data.get('email')
                phone = data.get('phone')
                bio = data.get('bio')
                
                success, message = self.db.update_user_profile(sender_id, username, email, phone, bio)
                
                if success:
                    # Отправляем обновленный профиль
                    profile = self.db.get_user_profile(sender_id)
                    await websocket.send(json.dumps({
                        "type": "profile_updated",
                        "success": True,
                        "message": message,
                        "profile": profile
                    }))
                else:
                    await websocket.send(json.dumps({
                        "type": "profile_updated",
                        "success": False,
                        "error": message
                    }))
            
            elif message_type == 'admin_search_users':
                # Проверяем права админа
                user_profile = self.db.get_user_profile(sender_id)
                if not user_profile or (not user_profile.get('is_admin') and not user_profile.get('is_owner')):
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Недостаточно прав"
                    }))
                    return
                
                query = data.get('query', '').strip()
                users = self.db.admin_search_users(query)
                await websocket.send(json.dumps({
                    "type": "admin_search_results",
                    "users": users
                }))
            
            elif message_type == 'admin_ban_user':
                # Проверяем права админа
                user_profile = self.db.get_user_profile(sender_id)
                if not user_profile or (not user_profile.get('is_admin') and not user_profile.get('is_owner')):
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Недостаточно прав"
                    }))
                    return
                
                target_user_id = data.get('user_id')
                reason = data.get('reason', '')
                duration_days = data.get('duration_days', 1)
                
                success, message = self.db.ban_user(target_user_id, reason, duration_days)
                await websocket.send(json.dumps({
                    "type": "admin_action_result",
                    "action": "ban",
                    "success": success,
                    "message": message
                }))
            
            elif message_type == 'admin_mute_user':
                # Проверяем права админа
                user_profile = self.db.get_user_profile(sender_id)
                if not user_profile or (not user_profile.get('is_admin') and not user_profile.get('is_owner')):
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Недостаточно прав"
                    }))
                    return
                
                target_user_id = data.get('user_id')
                duration_hours = data.get('duration_hours', 1)
                
                success, message = self.db.mute_user(target_user_id, duration_hours)
                await websocket.send(json.dumps({
                    "type": "admin_action_result",
                    "action": "mute",
                    "success": success,
                    "message": message
                }))
    
            elif message_type == 'admin_unban_user':
                # Проверяем права админа
                user_profile = self.db.get_user_profile(sender_id)
                if not user_profile or (not user_profile.get('is_admin') and not user_profile.get('is_owner')):
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Недостаточно прав"
                    }))
                    return
                
                target_user_id = data.get('user_id')
                
                success, message = self.db.unban_user(target_user_id)
                await websocket.send(json.dumps({
                    "type": "admin_action_result",
                    "action": "unban",
                    "success": success,
                    "message": message
                }))
            
            elif message_type == 'admin_unmute_user':
                # Проверяем права админа
                user_profile = self.db.get_user_profile(sender_id)
                if not user_profile or (not user_profile.get('is_admin') and not user_profile.get('is_owner')):
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Недостаточно прав"
                    }))
                    return
                
                target_user_id = data.get('user_id')
                
                success, message = self.db.unmute_user(target_user_id)
                await websocket.send(json.dumps({
                    "type": "admin_action_result",
                    "action": "unmute",
                    "success": success,
                    "message": message
                }))
                
        except json.JSONDecodeError:
            print(f"⚠️ Неверный JSON: {message}")
        except Exception as e:
            print(f"❌ Ошибка в process_message: {e}")

async def main():
    server = ChatServer()
    
    print("=" * 50)
    print("🚀 ARTEM Messenger Server")
    print("🌐 Сервер запущен: ws://localhost:8765")
    print("📁 База данных: artem_messenger.db")
    print("=" * 50)
    
    # Запускаем сервер - ИСПРАВЛЕНО: убираем path из обработчика
    async with websockets.serve(server.handler, "localhost", 8765):
        print("✅ Сервер запущен и ожидает подключений...")
        await asyncio.Future()  # Бесконечное ожидание

if __name__ == "__main__":

    asyncio.run(main())