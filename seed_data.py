"""
╔══════════════════════════════════════════════════════════════════╗
║  TASKSPHERE — Seed Script                                        ║
║  Usage: python seed_data.py                                      ║
║  Creates demo users, projects, tasks, comments, notifications    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
sys.path.insert(0, '.')

from pymongo    import MongoClient
from flask_bcrypt import Bcrypt
from flask       import Flask
from bson        import ObjectId
from datetime    import datetime, timedelta
import random

# ── FLASK APP (for bcrypt context) ──────────────────────────────────
_app = Flask(__name__)
bcrypt = Bcrypt(_app)

client = MongoClient('mongodb://localhost:27017/')
db     = client['tasksphere']

# ── COLORS, SAMPLE DATA ─────────────────────────────────────────────
COLORS     = ['#6366f1','#06b6d4','#10b981','#f59e0b','#ef4444','#ec4899','#8b5cf6']
PRIORITIES = ['low','medium','high']
STATUSES   = ['todo','in_progress','completed']
PROJ_STAT  = ['active','on_hold','completed']
ACTIONS    = ['created','updated','moved','login']

USERS = [
    {"name":"Alice Johnson", "email":"alice@tasksphere.io",  "role":"admin",   "department":"Engineering"},
    {"name":"Bob Martinez",  "email":"bob@tasksphere.io",    "role":"manager", "department":"Product"},
    {"name":"Carol White",   "email":"carol@tasksphere.io",  "role":"member",  "department":"Design"},
    {"name":"David Kim",     "email":"david@tasksphere.io",  "role":"member",  "department":"Marketing"},
    {"name":"Eva Torres",    "email":"eva@tasksphere.io",    "role":"manager", "department":"QA"},
]

PROJECTS = [
    {"name":"Website Redesign 2024",  "description":"Full overhaul of the marketing site",        "color":"#6366f1"},
    {"name":"Mobile App v3",          "description":"New React Native application",                "color":"#06b6d4"},
    {"name":"API Integration",        "description":"Third-party API connectors and webhooks",     "color":"#10b981"},
    {"name":"Data Analytics Dashboard","description":"Real-time analytics for internal teams",     "color":"#f59e0b"},
    {"name":"Customer Portal",        "description":"Self-service portal for enterprise clients",  "color":"#ec4899"},
]

TASKS_TEMPLATES = [
    "Design landing page mockup",    "Set up CI/CD pipeline",
    "Write API documentation",       "Fix authentication bug",
    "Review pull requests",          "Update dependency packages",
    "Create onboarding flow",        "Implement dark mode",
    "Write unit tests",              "Optimize database queries",
    "Design email templates",        "Set up error monitoring",
    "Create user research report",   "Build notification system",
    "Implement file upload feature", "Configure staging environment",
    "Performance audit & fixes",     "A/B test new CTA buttons",
    "Migrate legacy data",           "Deploy to production",
    "Code review – auth module",     "Update security certificates",
    "Implement search functionality","Set up automated backups",
    "Create API rate limiting",      "Build admin dashboard",
]

COMMENTS = [
    "Looks good, pushing to review.",
    "I've started working on this. ETA: 2 days.",
    "Blocked on the API docs — @Alice can you help?",
    "Done! Please verify in staging.",
    "Needs more detail in the acceptance criteria.",
    "Merged. Closing this task.",
    "Added unit tests — coverage now at 92%.",
    "Design approved by stakeholders.",
]


def seed():
    print("\n🌱 TaskSphere — Seeding demo data…\n")

    # ── Clear existing ──────────────────────────────────────────────
    for col in ['users','projects','tasks','comments','notifications','activity_logs']:
        db[col].drop()
        print(f"  🗑  Cleared: {col}")

    # ── Users ───────────────────────────────────────────────────────
    user_ids = []
    for u in USERS:
        pw  = bcrypt.generate_password_hash("Password123!").decode('utf-8')
        uid = db.users.insert_one({
            "name":                  u["name"],
            "email":                 u["email"],
            "password":              pw,
            "role":                  u["role"],
            "avatar":                f'https://api.dicebear.com/7.x/initials/svg?seed={u["name"].replace(" ","+")}',
            "bio":                   f'{u["role"].capitalize()} at TaskSphere',
            "phone":                 f'+1 555-01{random.randint(10,99)}',
            "department":            u["department"],
            "dark_mode":             True,
            "notifications_enabled": True,
            "created_at":            datetime.utcnow() - timedelta(days=random.randint(30,180)),
            "last_login":            datetime.utcnow() - timedelta(hours=random.randint(0,48)),
        }).inserted_id
        user_ids.append(uid)
        print(f"  👤  Created user: {u['name']} ({u['email']})")

    # ── Projects ────────────────────────────────────────────────────
    project_ids = []
    for i, p in enumerate(PROJECTS):
        owner = user_ids[i % len(user_ids)]
        members = random.sample([str(u) for u in user_ids if u != owner], k=min(3, len(user_ids)-1))
        pid = db.projects.insert_one({
            "name":        p["name"],
            "description": p["description"],
            "status":      random.choice(PROJ_STAT),
            "priority":    random.choice(PRIORITIES),
            "owner_id":    str(owner),
            "members":     members,
            "deadline":    (datetime.utcnow() + timedelta(days=random.randint(10,90))).strftime('%Y-%m-%d'),
            "color":       p["color"],
            "created_at":  datetime.utcnow() - timedelta(days=random.randint(5,60)),
            "updated_at":  datetime.utcnow() - timedelta(days=random.randint(0,5)),
        }).inserted_id
        project_ids.append(pid)
        print(f"  📁  Created project: {p['name']}")

    # ── Tasks ───────────────────────────────────────────────────────
    task_ids = []
    for i, title in enumerate(TASKS_TEMPLATES):
        assignee    = random.choice(user_ids)
        project     = random.choice(project_ids)
        created_by  = random.choice(user_ids)
        created_ago = timedelta(days=random.randint(1,30))
        deadline    = datetime.utcnow() + timedelta(days=random.randint(-5, 30))

        tid = db.tasks.insert_one({
            "title":        title,
            "description":  f"Complete the following: {title.lower()}. Ensure all edge cases are handled.",
            "project_id":   str(project),
            "assignee_id":  str(assignee),
            "assignee_name": next(u["name"] for u in USERS if str(user_ids[USERS.index(u) if USERS.index(u) < len(user_ids) else 0]) or True),
            "priority":     random.choice(PRIORITIES),
            "status":       random.choice(STATUSES),
            "deadline":     deadline.isoformat(),
            "tags":         random.sample(["backend","frontend","design","qa","devops","docs"], k=random.randint(1,3)),
            "attachments":  [],
            "created_by":   str(created_by),
            "created_at":   datetime.utcnow() - created_ago,
            "updated_at":   datetime.utcnow() - timedelta(hours=random.randint(0,48)),
        }).inserted_id
        task_ids.append(tid)

        # Fix assignee_name properly
        assignee_idx = user_ids.index(assignee)
        db.tasks.update_one({'_id': tid}, {'$set': {'assignee_name': USERS[assignee_idx]['name']}})

    print(f"  ✅  Created {len(task_ids)} tasks")

    # ── Comments ────────────────────────────────────────────────────
    comment_count = 0
    for tid in random.sample(task_ids, k=min(15, len(task_ids))):
        n_comments = random.randint(1, 3)
        for _ in range(n_comments):
            user = random.choice(list(zip(user_ids, USERS)))
            db.comments.insert_one({
                "task_id":    str(tid),
                "user_id":    str(user[0]),
                "user_name":  user[1]["name"],
                "content":    random.choice(COMMENTS),
                "created_at": datetime.utcnow() - timedelta(hours=random.randint(1,72)),
            })
            comment_count += 1
    print(f"  💬  Created {comment_count} comments")

    # ── Notifications ───────────────────────────────────────────────
    notif_types = [
        ("New Task Assigned",   "You've been assigned a new task",             "task"),
        ("Task Completed",      "A task was marked as complete",               "success"),
        ("Project Update",      "Your project deadline has been updated",      "info"),
        ("Team Mention",        "Someone mentioned you in a comment",          "info"),
        ("Overdue Alert",       "You have overdue tasks requiring attention",  "warning"),
    ]
    notif_count = 0
    for uid in user_ids:
        for title, msg, ntype in random.sample(notif_types, k=random.randint(2,4)):
            db.notifications.insert_one({
                "user_id":   str(uid),
                "title":     title,
                "message":   msg,
                "type":      ntype,
                "read":      random.choice([True, False]),
                "timestamp": datetime.utcnow() - timedelta(hours=random.randint(1,168)),
            })
            notif_count += 1
    print(f"  🔔  Created {notif_count} notifications")

    # ── Activity Logs ───────────────────────────────────────────────
    log_descriptions = {
        "created": ["Created task: {}", "Created project: {}"],
        "updated": ["Updated task: {}", "Changed status of: {}"],
        "moved":   ["Moved '{}' to In Progress", "Moved '{}' to Completed"],
        "login":   ["{} logged in"],
    }
    log_count = 0
    for uid, user in zip(user_ids, USERS):
        for _ in range(random.randint(5, 15)):
            action = random.choice(list(log_descriptions.keys()))
            entity = random.choice(TASKS_TEMPLATES)
            tmpl   = random.choice(log_descriptions[action])
            db.activity_logs.insert_one({
                "user_id":     str(uid),
                "action":      action,
                "entity_type": "task",
                "entity_id":   str(random.choice(task_ids)),
                "description": tmpl.format(entity),
                "timestamp":   datetime.utcnow() - timedelta(hours=random.randint(1,240)),
            })
            log_count += 1
    print(f"  📋  Created {log_count} activity logs")

    # ── Summary ─────────────────────────────────────────────────────
    print("\n" + "═"*55)
    print("  🎉  Seed complete!\n")
    print("  LOGIN CREDENTIALS (password for all: Password123!)")
    print("  ─────────────────────────────────────────────────")
    for u in USERS:
        print(f"  {u['role'].upper():10}  {u['email']}")
    print("\n  🌐  Start server: python app.py")
    print("  🔗  Open: http://localhost:5000\n")
    print("═"*55 + "\n")


if __name__ == "__main__":
    seed()