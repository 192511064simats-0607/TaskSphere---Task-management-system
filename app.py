import os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson import ObjectId
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tasksphere_secret_key_2024_ultra_secure'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/tasksphere'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def serialize(doc):
    if doc is None:
        return None
    doc = dict(doc)
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, datetime):
            doc[k] = v.isoformat()
        elif isinstance(v, list):
            doc[k] = [str(i) if isinstance(i, ObjectId) else i for i in v]
    return doc

def log_activity(user_id, action, entity_type, entity_id=None, description=''):
    mongo.db.activity_logs.insert_one({
        'user_id': str(user_id),
        'action': action,
        'entity_type': entity_type,
        'entity_id': str(entity_id) if entity_id else None,
        'description': description,
        'timestamp': datetime.utcnow()
    })

def send_notification(user_id, title, message, notif_type='info'):
    notif = {
        'user_id': str(user_id),
        'title': title,
        'message': message,
        'type': notif_type,
        'read': False,
        'timestamp': datetime.utcnow()
    }
    mongo.db.notifications.insert_one(notif)
    socketio.emit('notification', {
        'title': title,
        'message': message,
        'type': notif_type,
        'timestamp': datetime.utcnow().isoformat()
    }, room=str(user_id))

# ─────────────────────────────────────────
#  AUTH ROUTES
# ─────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/landing')
def landing():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data     = request.get_json() or request.form
        name     = data.get('name', '').strip()
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role     = data.get('role', 'member')

        if not all([name, email, password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        if mongo.db.users.find_one({'email': email}):
            return jsonify({'success': False, 'message': 'Email already registered'}), 400

        hashed  = bcrypt.generate_password_hash(password).decode('utf-8')
        user_id = mongo.db.users.insert_one({
            'name': name, 'email': email, 'password': hashed, 'role': role,
            'avatar': f'https://api.dicebear.com/7.x/initials/svg?seed={name}',
            'bio': '', 'phone': '', 'department': '',
            'dark_mode': True, 'notifications_enabled': True,
            'created_at': datetime.utcnow(), 'last_login': datetime.utcnow()
        }).inserted_id

        log_activity(user_id, 'registered', 'user', user_id, f'{name} joined TaskSphere')
        return jsonify({'success': True, 'message': 'Account created successfully'})

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data  = request.get_json() or request.form
        email = data.get('email', '').strip().lower()
        pwd   = data.get('password', '')

        user = mongo.db.users.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], pwd):
            session['user_id']    = str(user['_id'])
            session['user_name']  = user['name']
            session['user_email'] = user['email']
            session['user_role']  = user.get('role', 'member')
            mongo.db.users.update_one({'_id': user['_id']},
                                      {'$set': {'last_login': datetime.utcnow()}})
            log_activity(user['_id'], 'login', 'user', user['_id'],
                         f'{user["name"]} logged in')
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/projects')
@login_required
def projects():
    return render_template('projects.html')

@app.route('/tasks')
@login_required
def tasks():
    return render_template('tasks.html')

@app.route('/kanban')
@login_required
def kanban():
    return render_template('kanban.html')

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/team')
@login_required
def team():
    return render_template('team.html')

# ─────────────────────────────────────────
#  API – DASHBOARD
# ─────────────────────────────────────────
@app.route('/api/dashboard')
@login_required
def api_dashboard():
    uid = session['user_id']
    now = datetime.utcnow()
    total_projects = mongo.db.projects.count_documents({
        '$or': [{'owner_id': uid}, {'members': {'$in': [uid]}}]
    })
    total_tasks = mongo.db.tasks.count_documents({'assignee_id': uid})
    completed   = mongo.db.tasks.count_documents({'assignee_id': uid, 'status': 'completed'})
    in_progress = mongo.db.tasks.count_documents({'assignee_id': uid, 'status': 'in_progress'})
    todo        = mongo.db.tasks.count_documents({'assignee_id': uid, 'status': 'todo'})
    overdue     = mongo.db.tasks.count_documents({
        'assignee_id': uid, 'status': {'$ne': 'completed'},
        'deadline': {'$lt': now.isoformat()}
    })
    logs = [serialize(l) for l in
            mongo.db.activity_logs.find({'user_id': uid}).sort('timestamp', -1).limit(10)]
    chart_data = []
    for i in range(6, -1, -1):
        day       = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = day_start + timedelta(days=1)
        count = mongo.db.tasks.count_documents({
            'assignee_id': uid, 'status': 'completed',
            'updated_at': {'$gte': day_start.isoformat(), '$lt': day_end.isoformat()}
        })
        chart_data.append({'date': day.strftime('%b %d'), 'count': count})
    notifications = [serialize(n) for n in
                     mongo.db.notifications.find({'user_id': uid, 'read': False})
                     .sort('timestamp', -1).limit(5)]
    return jsonify({
        'total_projects': total_projects, 'total_tasks': total_tasks,
        'completed': completed, 'in_progress': in_progress,
        'todo': todo, 'overdue': overdue,
        'recent_activity': logs, 'chart_data': chart_data,
        'notifications': notifications
    })

# ─────────────────────────────────────────
#  API – PROJECTS
# ─────────────────────────────────────────
@app.route('/api/projects', methods=['GET', 'POST'])
@login_required
def api_projects():
    uid = session['user_id']
    if request.method == 'GET':
        query  = {'$or': [{'owner_id': uid}, {'members': {'$in': [uid]}}]}
        search = request.args.get('search', '')
        if search:
            query = {'$and': [query, {'name': {'$regex': search, '$options': 'i'}}]}
        projects = list(mongo.db.projects.find(query).sort('created_at', -1))
        result = []
        for p in projects:
            p = serialize(p)
            p['task_count']      = mongo.db.tasks.count_documents({'project_id': p['_id']})
            p['completed_tasks'] = mongo.db.tasks.count_documents(
                {'project_id': p['_id'], 'status': 'completed'})
            result.append(p)
        return jsonify(result)

    data    = request.get_json()
    proj_id = mongo.db.projects.insert_one({
        'name': data['name'], 'description': data.get('description', ''),
        'status': data.get('status', 'active'), 'priority': data.get('priority', 'medium'),
        'owner_id': uid, 'members': data.get('members', []),
        'deadline': data.get('deadline', ''), 'color': data.get('color', '#6366f1'),
        'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()
    }).inserted_id
    log_activity(uid, 'created', 'project', proj_id, f'Created project: {data["name"]}')
    socketio.emit('project_created',
                  {'project_id': str(proj_id), 'name': data['name']}, broadcast=True)
    return jsonify({'success': True, 'id': str(proj_id)})

@app.route('/api/projects/<project_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_project_detail(project_id):
    uid  = session['user_id']
    proj = mongo.db.projects.find_one({'_id': ObjectId(project_id)})
    if not proj:
        return jsonify({'error': 'Not found'}), 404
    if request.method == 'GET':
        p = serialize(proj)
        p['task_count']      = mongo.db.tasks.count_documents({'project_id': project_id})
        p['completed_tasks'] = mongo.db.tasks.count_documents(
            {'project_id': project_id, 'status': 'completed'})
        return jsonify(p)
    if request.method == 'PUT':
        data   = request.get_json()
        update = {k: v for k, v in data.items() if k != '_id'}
        update['updated_at'] = datetime.utcnow()
        mongo.db.projects.update_one({'_id': ObjectId(project_id)}, {'$set': update})
        log_activity(uid, 'updated', 'project', project_id, f'Updated project: {proj["name"]}')
        return jsonify({'success': True})
    mongo.db.projects.delete_one({'_id': ObjectId(project_id)})
    mongo.db.tasks.delete_many({'project_id': project_id})
    log_activity(uid, 'deleted', 'project', project_id, f'Deleted project: {proj["name"]}')
    return jsonify({'success': True})

# ─────────────────────────────────────────
#  API – TASKS
# ─────────────────────────────────────────
@app.route('/api/tasks', methods=['GET', 'POST'])
@login_required
def api_tasks():
    uid = session['user_id']
    if request.method == 'GET':
        query    = {}
        status   = request.args.get('status')
        priority = request.args.get('priority')
        project  = request.args.get('project_id')
        search   = request.args.get('search', '')
        assignee = request.args.get('assignee')
        if status:   query['status']     = status
        if priority: query['priority']   = priority
        if project:  query['project_id'] = project
        if assignee: query['assignee_id']= assignee
        if search:   query['title']      = {'$regex': search, '$options': 'i'}
        tasks = list(mongo.db.tasks.find(query).sort('created_at', -1))
        return jsonify([serialize(t) for t in tasks])

    data    = request.get_json()
    task_id = mongo.db.tasks.insert_one({
        'title':         data['title'],
        'description':   data.get('description', ''),
        'project_id':    data.get('project_id', ''),
        'assignee_id':   data.get('assignee_id', uid),
        'assignee_name': data.get('assignee_name', session['user_name']),
        'priority':      data.get('priority', 'medium'),
        'status':        data.get('status', 'todo'),
        'deadline':      data.get('deadline', ''),
        'tags':          data.get('tags', []),
        'attachments':   [],
        'created_by':    uid,
        'created_at':    datetime.utcnow(),
        'updated_at':    datetime.utcnow()
    }).inserted_id
    assignee_id = data.get('assignee_id', uid)
    if assignee_id != uid:
        send_notification(assignee_id, 'New Task Assigned',
                          f'You have been assigned: {data["title"]}', 'task')
    log_activity(uid, 'created', 'task', task_id, f'Created task: {data["title"]}')
    socketio.emit('task_created', {
        'task_id': str(task_id), 'title': data['title'],
        'assignee_id': assignee_id, 'status': data.get('status', 'todo')
    }, broadcast=True)
    return jsonify({'success': True, 'id': str(task_id)})

@app.route('/api/tasks/<task_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_task_detail(task_id):
    uid  = session['user_id']
    task = mongo.db.tasks.find_one({'_id': ObjectId(task_id)})
    if not task:
        return jsonify({'error': 'Not found'}), 404
    if request.method == 'GET':
        t = serialize(task)
        comments  = list(mongo.db.comments.find({'task_id': task_id}).sort('created_at', 1))
        t['comments'] = [serialize(c) for c in comments]
        return jsonify(t)
    if request.method == 'PUT':
        data       = request.get_json()
        old_status = task.get('status')
        update     = {k: v for k, v in data.items() if k != '_id'}
        update['updated_at'] = datetime.utcnow()
        mongo.db.tasks.update_one({'_id': ObjectId(task_id)}, {'$set': update})
        if data.get('status') == 'completed' and old_status != 'completed':
            send_notification(task['created_by'], 'Task Completed',
                              f'"{task["title"]}" has been marked complete!', 'success')
            socketio.emit('task_completed',
                          {'task_id': task_id, 'title': task['title']}, broadcast=True)
        log_activity(uid, 'updated', 'task', task_id, f'Updated task: {task["title"]}')
        socketio.emit('task_updated', {'task_id': task_id, 'update': data}, broadcast=True)
        return jsonify({'success': True})
    mongo.db.tasks.delete_one({'_id': ObjectId(task_id)})
    mongo.db.comments.delete_many({'task_id': task_id})
    log_activity(uid, 'deleted', 'task', task_id, f'Deleted task: {task["title"]}')
    socketio.emit('task_deleted', {'task_id': task_id}, broadcast=True)
    return jsonify({'success': True})

# ─────────────────────────────────────────
#  API – COMMENTS
# ─────────────────────────────────────────
@app.route('/api/tasks/<task_id>/comments', methods=['POST'])
@login_required
def add_comment(task_id):
    uid  = session['user_id']
    data = request.get_json()
    cid  = mongo.db.comments.insert_one({
        'task_id': task_id, 'user_id': uid,
        'user_name': session['user_name'],
        'content': data['content'], 'created_at': datetime.utcnow()
    }).inserted_id
    socketio.emit('new_comment', {
        'task_id': task_id, 'comment_id': str(cid),
        'user_name': session['user_name'], 'content': data['content']
    }, broadcast=True)
    return jsonify({'success': True, 'id': str(cid)})

# ─────────────────────────────────────────
#  API – KANBAN
# ─────────────────────────────────────────
@app.route('/api/kanban', methods=['GET'])
@login_required
def api_kanban():
    project_id = request.args.get('project_id', '')
    query = {'project_id': project_id} if project_id else {}
    tasks = list(mongo.db.tasks.find(query))
    board = {'todo': [], 'in_progress': [], 'completed': []}
    for t in tasks:
        t = serialize(t)
        board.get(t['status'], board['todo']).append(t)
    return jsonify(board)

@app.route('/api/kanban/move', methods=['POST'])
@login_required
def kanban_move():
    uid        = session['user_id']
    data       = request.get_json()
    task_id    = data['task_id']
    new_status = data['new_status']
    mongo.db.tasks.update_one({'_id': ObjectId(task_id)},
                              {'$set': {'status': new_status,
                                        'updated_at': datetime.utcnow()}})
    task = mongo.db.tasks.find_one({'_id': ObjectId(task_id)})
    log_activity(uid, 'moved', 'task', task_id,
                 f'Moved "{task["title"]}" to {new_status}')
    socketio.emit('kanban_move',
                  {'task_id': task_id, 'new_status': new_status}, broadcast=True)
    return jsonify({'success': True})

# ─────────────────────────────────────────
#  API – USERS / TEAM
# ─────────────────────────────────────────
@app.route('/api/users', methods=['GET'])
@login_required
def api_users():
    users = list(mongo.db.users.find({}, {'password': 0}))
    return jsonify([serialize(u) for u in users])

@app.route('/api/profile', methods=['GET', 'PUT'])
@login_required
def api_profile():
    uid = session['user_id']
    if request.method == 'GET':
        user = mongo.db.users.find_one({'_id': ObjectId(uid)}, {'password': 0})
        return jsonify(serialize(user))
    data    = request.get_json()
    allowed = ['name', 'bio', 'phone', 'department', 'dark_mode', 'notifications_enabled']
    update  = {k: v for k, v in data.items() if k in allowed}
    mongo.db.users.update_one({'_id': ObjectId(uid)}, {'$set': update})
    if 'name' in update:
        session['user_name'] = update['name']
    return jsonify({'success': True})

# ─────────────────────────────────────────
#  API – NOTIFICATIONS
# ─────────────────────────────────────────
@app.route('/api/notifications', methods=['GET'])
@login_required
def api_notifications():
    uid    = session['user_id']
    notifs = list(mongo.db.notifications.find({'user_id': uid})
                  .sort('timestamp', -1).limit(20))
    return jsonify([serialize(n) for n in notifs])

@app.route('/api/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    uid = session['user_id']
    mongo.db.notifications.update_many({'user_id': uid}, {'$set': {'read': True}})
    return jsonify({'success': True})

# ─────────────────────────────────────────
#  API – ACTIVITY LOG
# ─────────────────────────────────────────
@app.route('/api/activity', methods=['GET'])
@login_required
def api_activity():
    uid  = session['user_id']
    logs = list(mongo.db.activity_logs.find({'user_id': uid})
                .sort('timestamp', -1).limit(50))
    return jsonify([serialize(l) for l in logs])

# ─────────────────────────────────────────
#  API – CALENDAR
# ─────────────────────────────────────────
@app.route('/api/calendar', methods=['GET'])
@login_required
def api_calendar():
    uid   = session['user_id']
    month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
    tasks = list(mongo.db.tasks.find({
        'assignee_id': uid, 'deadline': {'$regex': f'^{month}'}
    }))
    projects = list(mongo.db.projects.find({
        '$or': [{'owner_id': uid}, {'members': {'$in': [uid]}}],
        'deadline': {'$regex': f'^{month}'}
    }))
    return jsonify({'tasks': [serialize(t) for t in tasks],
                    'projects': [serialize(p) for p in projects]})

# ─────────────────────────────────────────
#  API – SEARCH
# ─────────────────────────────────────────
@app.route('/api/search', methods=['GET'])
@login_required
def api_search():
    q   = request.args.get('q', '')
    uid = session['user_id']
    if not q:
        return jsonify({'tasks': [], 'projects': []})
    regex    = {'$regex': q, '$options': 'i'}
    tasks    = list(mongo.db.tasks.find({'title': regex, 'assignee_id': uid}).limit(5))
    projects = list(mongo.db.projects.find({'name': regex}).limit(5))
    return jsonify({'tasks':    [serialize(t) for t in tasks],
                    'projects': [serialize(p) for p in projects]})

# ─────────────────────────────────────────
#  SOCKET.IO
# ─────────────────────────────────────────
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        join_room(session['user_id'])
        emit('connected', {'status': 'ok', 'user': session['user_name']})

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        leave_room(session['user_id'])

@socketio.on('join_project')
def join_project(data):
    join_room(f"project_{data['project_id']}")

@socketio.on('typing')
def handle_typing(data):
    emit('user_typing',
         {'user': session.get('user_name', ''), 'task_id': data['task_id']},
         broadcast=True)

# ─────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────
if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)