# database.py
import sqlite3
import json
from datetime import datetime
import hashlib
import secrets

class Database:
    def __init__(self, db_name="artem_messenger.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
            tag TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            avatar_path TEXT,
            bio TEXT DEFAULT '',
            is_online BOOLEAN DEFAULT 0,
            last_seen TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin BOOLEAN DEFAULT 0,
            is_owner BOOLEAN DEFAULT 0,
            is_banned BOOLEAN DEFAULT 0,
            ban_reason TEXT,
            ban_until TIMESTAMP,
            is_muted BOOLEAN DEFAULT 0,
            mute_until TIMESTAMP,
            settings TEXT DEFAULT '{}'
        )
        ''')
        
        # Таблица чатов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            avatar_path TEXT,
            is_group BOOLEAN DEFAULT 0,
            is_channel BOOLEAN DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            settings TEXT DEFAULT '{}',
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
        ''')
        
        # Таблица участников чатов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            role TEXT DEFAULT 'member',
            is_muted BOOLEAN DEFAULT 0,
            notifications_enabled BOOLEAN DEFAULT 1,
            FOREIGN KEY (chat_id) REFERENCES chats(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(chat_id, user_id)
        )
        ''')
        
        # Таблица сообщений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            message_text TEXT,
            message_type TEXT DEFAULT 'text',
            file_path TEXT,
            is_edited BOOLEAN DEFAULT 0,
            edited_at TIMESTAMP,
            is_deleted BOOLEAN DEFAULT 0,
            deleted_at TIMESTAMP,
            deleted_by INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_by TEXT DEFAULT '[]',
            FOREIGN KEY (chat_id) REFERENCES chats(id),
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (deleted_by) REFERENCES users(id)
        )
        ''')
        
        # Таблица сессий (для входа)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Таблица логов действий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_type TEXT NOT NULL,
            target_id INTEGER,
            target_type TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Создаем владельца если нет пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            self.create_owner()
        
        self.conn.commit()
    
    def create_owner(self):
        """Создание владельца системы"""
        cursor = self.conn.cursor()
        owner_password = self.hash_password("admin123")  # Временный пароль
        
        cursor.execute('''
        INSERT INTO users (username, display_name, tag, password_hash, is_owner, is_admin)
        VALUES (?, ?, ?, ?, 1, 1)
        ''', ("owner", "Владелец системы", "@owner", owner_password))
        
        self.conn.commit()
        print("✅ Создан владелец системы: @owner / admin123")
    
    def hash_password(self, password):
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, password_hash):
        """Проверка пароля"""
        return self.hash_password(password) == password_hash
    
    def generate_session_token(self):
        """Генерация токена сессии"""
        return secrets.token_urlsafe(32)
    
    def register_user(self, username, tag, password, email=None, phone=None):
        """Регистрация нового пользователя"""
        cursor = self.conn.cursor()
        
        # Проверяем уникальность username и tag
        cursor.execute("SELECT id FROM users WHERE username = ? OR tag = ?", 
                      (username, tag))
        if cursor.fetchone():
            return False, "Имя пользователя или тэг уже заняты"
        
        # Проверяем формат тэга
        if not tag.startswith("@"):
            tag = "@" + tag
        
        password_hash = self.hash_password(password)
        
        try:
            cursor.execute('''
            INSERT INTO users (username, display_name, tag, password_hash, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, username, tag, password_hash, email, phone))
            
            user_id = cursor.lastrowid
            self.conn.commit()
            
            # Логируем регистрацию
            self.log_action(user_id, "register", user_id, "user", 
                          f"Зарегистрирован новый пользователь: {tag}")
            
            return True, user_id
        except Exception as e:
            return False, str(e)
    
    def login_user(self, identifier, password):
        """Вход пользователя по username/tag/email"""
        cursor = self.conn.cursor()
        
        # Ищем пользователя
        cursor.execute('''
        SELECT id, username, tag, password_hash, is_banned, ban_until 
        FROM users 
        WHERE username = ? OR tag = ? OR email = ?
        ''', (identifier, identifier, identifier))
        
        user = cursor.fetchone()
        if not user:
            return False, "Пользователь не найден"
        
        user_id, username, tag, password_hash, is_banned, ban_until = user
        
        # Проверяем бан
        if is_banned:
            if ban_until and datetime.fromisoformat(ban_until) > datetime.now():
                return False, f"Аккаунт заблокирован до {ban_until}"
            else:
                # Разбан если срок истек
                cursor.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (user_id,))
                self.conn.commit()
        
        # Проверяем пароль
        if not self.verify_password(password, password_hash):
            return False, "Неверный пароль"
        
        # Создаем сессию
        session_token = self.generate_session_token()
        expires_at = datetime.now().timestamp() + (30 * 24 * 3600)  # 30 дней
        
        cursor.execute('''
        INSERT INTO sessions (user_id, session_token, expires_at)
        VALUES (?, ?, ?)
        ''', (user_id, session_token, expires_at))
        
        # Обновляем статус онлайн
        cursor.execute('''
        UPDATE users SET is_online = 1, last_seen = ? 
        WHERE id = ?
        ''', (datetime.now(), user_id))
        
        self.conn.commit()
        
        # Логируем вход
        self.log_action(user_id, "login", user_id, "user")
        
        return True, {
            "user_id": user_id,
            "username": username,
            "tag": tag,
            "session_token": session_token,
            "is_admin": self.is_admin(user_id),
            "is_owner": self.is_owner(user_id)
        }
    
    def get_user_profile(self, user_id):
        """Получение профиля пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, username, display_name, tag, email, phone, avatar_path, 
               bio, is_online, last_seen, created_at, is_admin, is_owner,
               settings
        FROM users 
        WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        user_dict = dict(zip(columns, user))
        
        # Парсим настройки
        if user_dict['settings']:
            user_dict['settings'] = json.loads(user_dict['settings'])
        else:
            user_dict['settings'] = {}
        
        # Скрываем чувствительные данные
        user_dict.pop('email', None)
        user_dict.pop('phone', None)
        
        return user_dict
    
    def update_user_profile(self, user_id, **kwargs):
        """Обновление профиля пользователя"""
        cursor = self.conn.cursor()
        
        allowed_fields = ['display_name', 'bio', 'avatar_path', 'settings']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'settings' and isinstance(value, dict):
                    value = json.dumps(value)
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False, "Нет полей для обновления"
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, values)
        self.conn.commit()
        
        self.log_action(user_id, "update_profile", user_id, "user", 
                       f"Обновлены поля: {', '.join(updates)}")
        
        return True, "Профиль обновлен"
    
    def search_users(self, query, current_user_id):
        """Поиск пользователей"""
        cursor = self.conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute('''
        SELECT id, username, display_name, tag, avatar_path, bio, is_online
        FROM users 
        WHERE (username LIKE ? OR display_name LIKE ? OR tag LIKE ?)
          AND id != ?
          AND is_banned = 0
        LIMIT 20
        ''', (search_term, search_term, search_term, current_user_id))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'display_name': row[2],
                'tag': row[3],
                'avatar': row[4],
                'bio': row[5],
                'is_online': bool(row[6])
            })
        
        return users
    
    def create_chat(self, chat_type, name, creator_id, user_ids=None, description=""):
        """Создание чата (личный, групповой, канал)"""
        cursor = self.conn.cursor()
        
        is_group = 1 if chat_type == "group" else 0
        is_channel = 1 if chat_type == "channel" else 0
        
        cursor.execute('''
        INSERT INTO chats (name, description, is_group, is_channel, created_by)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, description, is_group, is_channel, creator_id))
        
        chat_id = cursor.lastrowid
        
        # Добавляем создателя
        cursor.execute('''
        INSERT INTO chat_members (chat_id, user_id, role)
        VALUES (?, ?, 'creator')
        ''', (chat_id, creator_id))
        
        # Добавляем других пользователей если есть
        if user_ids:
            for user_id in user_ids:
                if user_id != creator_id:
                    cursor.execute('''
                    INSERT INTO chat_members (chat_id, user_id, role)
                    VALUES (?, ?, 'member')
                    ''', (chat_id, user_id))
        
        self.conn.commit()
        
        self.log_action(creator_id, "create_chat", chat_id, "chat", 
                       f"Создан {chat_type}: {name}")
        
        return chat_id
    
    def get_user_chats(self, user_id):
        """Получение списка чатов пользователя"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT c.id, c.name, c.description, c.avatar_path, c.is_group, 
               c.is_channel, c.created_at,
               (SELECT COUNT(*) FROM chat_members WHERE chat_id = c.id) as members_count,
               (SELECT message_text FROM messages 
                WHERE chat_id = c.id AND is_deleted = 0 
                ORDER BY timestamp DESC LIMIT 1) as last_message,
               (SELECT timestamp FROM messages 
                WHERE chat_id = c.id 
                ORDER BY timestamp DESC LIMIT 1) as last_message_time
        FROM chats c
        JOIN chat_members cm ON c.id = cm.chat_id
        WHERE cm.user_id = ?
        ORDER BY last_message_time DESC
        ''', (user_id,))
        
        chats = []
        for row in cursor.fetchall():
            chats.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'avatar': row[3],
                'is_group': bool(row[4]),
                'is_channel': bool(row[5]),
                'created_at': row[6],
                'members_count': row[7],
                'last_message': row[8],
                'last_message_time': row[9]
            })
        
        return chats
    
    def send_message(self, chat_id, sender_id, message_text, message_type="text", file_path=None):
        """Отправка сообщения"""
        cursor = self.conn.cursor()
        
        # Проверяем что пользователь в чате
        cursor.execute('''
        SELECT id FROM chat_members 
        WHERE chat_id = ? AND user_id = ? AND is_muted = 0
        ''', (chat_id, sender_id))
        
        if not cursor.fetchone():
            return False, "Вы не состоите в этом чате или у вас мут"
        
        cursor.execute('''
        INSERT INTO messages (chat_id, sender_id, message_text, message_type, file_path)
        VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, sender_id, message_text, message_type, file_path))
        
        message_id = cursor.lastrowid
        self.conn.commit()
        
        self.log_action(sender_id, "send_message", message_id, "message", 
                       f"Отправлено в чат {chat_id}")
        
        return True, message_id
    
    def get_chat_messages(self, chat_id, user_id, limit=50, offset=0):
        """Получение сообщений чата"""
        cursor = self.conn.cursor()
        
        # Проверяем доступ
        cursor.execute('''
        SELECT id FROM chat_members 
        WHERE chat_id = ? AND user_id = ?
        ''', (chat_id, user_id))
        
        if not cursor.fetchone():
            return []
        
        cursor.execute('''
        SELECT m.id, m.sender_id, u.username, u.display_name, u.tag, u.avatar_path,
               m.message_text, m.message_type, m.file_path, m.is_edited, 
               m.edited_at, m.timestamp, m.read_by
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.chat_id = ? AND m.is_deleted = 0
        ORDER BY m.timestamp DESC
        LIMIT ? OFFSET ?
        ''', (chat_id, limit, offset))
        
        messages = []
        for row in cursor.fetchall():
            # Проверяем прочитано ли сообщение пользователем
            read_by = json.loads(row[12] or '[]')
            is_read = user_id in read_by
            
            # Если не прочитано - отмечаем как прочитанное
            if not is_read and row[1] != user_id:  # Не свои сообщения
                read_by.append(user_id)
                cursor.execute('''
                UPDATE messages SET read_by = ? WHERE id = ?
                ''', (json.dumps(read_by), row[0]))
            
            messages.append({
                'id': row[0],
                'sender_id': row[1],
                'sender_username': row[2],
                'sender_display_name': row[3],
                'sender_tag': row[4],
                'sender_avatar': row[5],
                'text': row[6],
                'type': row[7],
                'file_path': row[8],
                'is_edited': bool(row[9]),
                'edited_at': row[10],
                'timestamp': row[11],
                'is_read': is_read or row[1] == user_id
            })
        
        self.conn.commit()
        return list(reversed(messages))
    
    def is_admin(self, user_id):
        """Проверка является ли пользователь админом"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    
    def is_owner(self, user_id):
        """Проверка является ли пользователь владельцем"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_owner FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    
    def promote_to_admin(self, promoter_id, user_id):
        """Назначение администратора"""
        if not self.is_owner(promoter_id):
            return False, "Только владелец может назначать админов"
        
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users SET is_admin = 1 
        WHERE id = ? AND is_owner = 0
        ''', (user_id,))
        
        self.conn.commit()
        
        self.log_action(promoter_id, "promote_admin", user_id, "user")
        return True, "Пользователь назначен администратором"
    
    def ban_user(self, admin_id, user_id, reason="", days=0):
        """Бан пользователя"""
        if not (self.is_admin(admin_id) or self.is_owner(admin_id)):
            return False, "Недостаточно прав"
        
        if self.is_owner(user_id):
            return False, "Нельзя забанить владельца"
        
        cursor = self.conn.cursor()
        
        ban_until = None
        if days > 0:
            from datetime import datetime, timedelta
            ban_until = (datetime.now() + timedelta(days=days)).isoformat()
        
        cursor.execute('''
        UPDATE users SET is_banned = 1, ban_reason = ?, ban_until = ?
        WHERE id = ?
        ''', (reason, ban_until, user_id))
        
        # Завершаем все сессии забаненного пользователя
        cursor.execute('''
        UPDATE sessions SET is_active = 0 
        WHERE user_id = ?
        ''', (user_id,))
        
        self.conn.commit()
        
        duration = f"на {days} дней" if days > 0 else "навсегда"
        self.log_action(admin_id, "ban_user", user_id, "user", 
                       f"Забанен {duration}. Причина: {reason}")
        
        return True, f"Пользователь забанен {duration}"
    
    def mute_user(self, admin_id, user_id, chat_id, hours=1):
        """Мут пользователя в чате"""
        cursor = self.conn.cursor()
        
        # Проверяем права админа в чате
        cursor.execute('''
        SELECT role FROM chat_members 
        WHERE chat_id = ? AND user_id = ?
        ''', (chat_id, admin_id))
        
        admin_role = cursor.fetchone()
        if not admin_role or admin_role[0] not in ['admin', 'creator']:
            return False, "Недостаточно прав в этом чате"
        
        from datetime import datetime, timedelta
        mute_until = (datetime.now() + timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
        UPDATE chat_members SET is_muted = 1, mute_until = ?
        WHERE chat_id = ? AND user_id = ?
        ''', (mute_until, chat_id, user_id))
        
        self.conn.commit()
        
        self.log_action(admin_id, "mute_user", user_id, "user", 
                       f"В чате {chat_id} на {hours} часов")
        
        return True, f"Пользователь замучен на {hours} часов"
    
    def delete_message(self, deleter_id, message_id):
        """Удаление сообщения"""
        cursor = self.conn.cursor()
        
        # Получаем информацию о сообщении
        cursor.execute('''
        SELECT sender_id, chat_id FROM messages WHERE id = ?
        ''', (message_id,))
        
        message = cursor.fetchone()
        if not message:
            return False, "Сообщение не найдено"
        
        sender_id, chat_id = message
        
        # Проверяем права
        can_delete = False
        
        if sender_id == deleter_id:
            can_delete = True  # Свои сообщения
        elif self.is_admin(deleter_id) or self.is_owner(deleter_id):
            can_delete = True  # Админы
        else:
            # Проверяем права в чате
            cursor.execute('''
            SELECT role FROM chat_members 
            WHERE chat_id = ? AND user_id = ?
            ''', (chat_id, deleter_id))
            
            role = cursor.fetchone()
            if role and role[0] in ['admin', 'creator']:
                can_delete = True
        
        if not can_delete:
            return False, "Недостаточно прав"
        
        cursor.execute('''
        UPDATE messages SET is_deleted = 1, deleted_at = ?, deleted_by = ?
        WHERE id = ?
        ''', (datetime.now(), deleter_id, message_id))
        
        self.conn.commit()
        
        self.log_action(deleter_id, "delete_message", message_id, "message")
        return True, "Сообщение удалено"
    
    def log_action(self, user_id, action_type, target_id=None, target_type=None, details=""):
        """Логирование действий"""
        cursor = self.conn.cursor()
        
        # Маскируем IP в логах
        ip_address = "HIDDEN"  # Скрываем IP от пользователей
        
        cursor.execute('''
        INSERT INTO audit_log (user_id, action_type, target_id, target_type, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, action_type, target_id, target_type, details, ip_address))
        
        self.conn.commit()
    
    def get_audit_log(self, admin_id, limit=100):
        """Получение логов (только для админов)"""
        if not (self.is_admin(admin_id) or self.is_owner(admin_id)):
            return []
        
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT al.timestamp, u.username, al.action_type, al.target_type, al.details
        FROM audit_log al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()
    
    def get_statistics(self, admin_id):
        """Получение статистики (только для админов)"""
        if not (self.is_admin(admin_id) or self.is_owner(admin_id)):
            return {}
        
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_online = 1")
        stats['online_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chats")
        stats['total_chats'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        stats['total_messages'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        stats['banned_users'] = cursor.fetchone()[0]
        
        # Активность за последние 24 часа
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        cursor.execute("SELECT COUNT(*) FROM messages WHERE timestamp > ?", (yesterday,))
        stats['messages_last_24h'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE created_at > ?", (yesterday,))
        stats['new_users_last_24h'] = cursor.fetchone()[0]
        
        return stats

# Создаем глобальный экземпляр базы данных
db = Database()