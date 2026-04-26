from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import json

socketio = SocketIO(cors_allowed_origins="*")

class NotificationSystem:
    def __init__(self):
        self.notifications = {}
        self.online_users = {}
    
    def send_notification(self, user_id, notification_type, data):
        """Send real-time notification to user"""
        notification = {
            'type': notification_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        
        # Store in database
        self._store_notification(user_id, notification)
        
        # Emit via WebSocket
        socketio.emit('notification', notification, room=f'user_{user_id}')
    
    def _store_notification(self, user_id, notification):
        """Store notification in database"""
        from database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO notifications (user_id, type, data, timestamp)
            VALUES (?, ?, ?, GETDATE())
        """, (user_id, notification['type'], json.dumps(notification['data'])))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_user_notifications(self, user_id, limit=50):
        """Get user notifications"""
        from database import get_db_connection, fetchall_dict
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            OFFSET 0 ROWS FETCH NEXT 50 ROWS ONLY
        """, (user_id,))
        
        notifications = fetchall_dict(cursor)
        cursor.close()
        conn.close()
        
        return notifications

notifier = NotificationSystem()

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        join_room(f'user_{session["user_id"]}')
        notifier.online_users[session['user_id']] = True

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        leave_room(f'user_{session["user_id"]}')
        notifier.online_users.pop(session['user_id'], None)