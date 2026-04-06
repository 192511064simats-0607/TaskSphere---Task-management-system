"""
╔══════════════════════════════════════════════════════════════════╗
║  TASKSPHERE — MongoDB Schema & Models                            ║
║  File: models/schemas.py                                         ║
║  MongoDB URI: mongodb://localhost:27017/tasksphere               ║
╚══════════════════════════════════════════════════════════════════╝
"""

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from bson    import ObjectId
from datetime import datetime

# ── CONNECTION ──────────────────────────────────────────────────────
client = MongoClient('mongodb://localhost:27017/')
db     = client['tasksphere']

# ════════════════════════════════════════════════════════════════════
#  COLLECTION SCHEMAS  (JSON Schema validation for MongoDB 5+)
# ════════════════════════════════════════════════════════════════════

USERS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "email", "password"],
        "properties": {
            "name":                   {"bsonType": "string",  "description": "Full name — required"},
            "email":                  {"bsonType": "string",  "description": "Unique email — required"},
            "password":               {"bsonType": "string",  "description": "Bcrypt hash — required"},
            "role":                   {"bsonType": "string",  "enum": ["admin","manager","member"]},
            "avatar":                 {"bsonType": "string"},
            "bio":                    {"bsonType": "string"},
            "phone":                  {"bsonType": "string"},
            "department":             {"bsonType": "string"},
            "dark_mode":              {"bsonType": "bool"},
            "notifications_enabled":  {"bsonType": "bool"},
            "created_at":             {"bsonType": "date"},
            "last_login":             {"bsonType": "date"},
        }
    }
}

PROJECTS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "owner_id"],
        "properties": {
            "name":        {"bsonType": "string"},
            "description": {"bsonType": "string"},
            "status":      {"bsonType": "string", "enum": ["active","on_hold","completed","archived"]},
            "priority":    {"bsonType": "string", "enum": ["low","medium","high"]},
            "owner_id":    {"bsonType": "string"},
            "members":     {"bsonType": "array",  "items": {"bsonType": "string"}},
            "deadline":    {"bsonType": "string"},
            "color":       {"bsonType": "string"},
            "created_at":  {"bsonType": "date"},
            "updated_at":  {"bsonType": "date"},
        }
    }
}

TASKS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["title"],
        "properties": {
            "title":         {"bsonType": "string"},
            "description":   {"bsonType": "string"},
            "project_id":    {"bsonType": "string"},
            "assignee_id":   {"bsonType": "string"},
            "assignee_name": {"bsonType": "string"},
            "priority":      {"bsonType": "string", "enum": ["low","medium","high"]},
            "status":        {"bsonType": "string", "enum": ["todo","in_progress","completed"]},
            "deadline":      {"bsonType": "string"},
            "tags":          {"bsonType": "array",  "items": {"bsonType": "string"}},
            "attachments":   {"bsonType": "array"},
            "created_by":    {"bsonType": "string"},
            "created_at":    {"bsonType": "date"},
            "updated_at":    {"bsonType": "date"},
        }
    }
}

COMMENTS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["task_id", "user_id", "content"],
        "properties": {
            "task_id":    {"bsonType": "string"},
            "user_id":    {"bsonType": "string"},
            "user_name":  {"bsonType": "string"},
            "content":    {"bsonType": "string"},
            "created_at": {"bsonType": "date"},
        }
    }
}

NOTIFICATIONS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["user_id", "title"],
        "properties": {
            "user_id":   {"bsonType": "string"},
            "title":     {"bsonType": "string"},
            "message":   {"bsonType": "string"},
            "type":      {"bsonType": "string", "enum": ["info","task","success","warning","danger"]},
            "read":      {"bsonType": "bool"},
            "timestamp": {"bsonType": "date"},
        }
    }
}

ACTIVITY_LOGS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["user_id", "action"],
        "properties": {
            "user_id":     {"bsonType": "string"},
            "action":      {"bsonType": "string"},
            "entity_type": {"bsonType": "string"},
            "entity_id":   {"bsonType": "string"},
            "description": {"bsonType": "string"},
            "timestamp":   {"bsonType": "date"},
        }
    }
}

FILES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["task_id", "filename", "path"],
        "properties": {
            "task_id":    {"bsonType": "string"},
            "uploaded_by":{"bsonType": "string"},
            "filename":   {"bsonType": "string"},
            "path":       {"bsonType": "string"},
            "size":       {"bsonType": "int"},
            "mimetype":   {"bsonType": "string"},
            "uploaded_at":{"bsonType": "date"},
        }
    }
}


# ════════════════════════════════════════════════════════════════════
#  CREATE COLLECTIONS + INDEXES
# ════════════════════════════════════════════════════════════════════
def setup_collections():
    existing = db.list_collection_names()

    collections_config = {
        "users":         USERS_SCHEMA,
        "projects":      PROJECTS_SCHEMA,
        "tasks":         TASKS_SCHEMA,
        "comments":      COMMENTS_SCHEMA,
        "notifications": NOTIFICATIONS_SCHEMA,
        "activity_logs": ACTIVITY_LOGS_SCHEMA,
        "files":         FILES_SCHEMA,
    }

    for name, schema in collections_config.items():
        if name not in existing:
            db.create_collection(name, validator=schema)
            print(f"  ✅ Created collection: {name}")
        else:
            # Update validator on existing collection
            db.command("collMod", name, validator=schema)
            print(f"  🔄 Updated schema: {name}")

    # ── INDEXES ──────────────────────────────────────────────────────
    db.users.create_index([("email", ASCENDING)], unique=True, name="email_unique")
    db.users.create_index([("name",  TEXT)],                   name="name_text")

    db.projects.create_index([("owner_id",  ASCENDING)], name="owner_idx")
    db.projects.create_index([("members",   ASCENDING)], name="members_idx")
    db.projects.create_index([("status",    ASCENDING)], name="status_idx")
    db.projects.create_index([("name",      TEXT), ("description", TEXT)], name="project_text")

    db.tasks.create_index([("project_id",  ASCENDING)], name="project_idx")
    db.tasks.create_index([("assignee_id", ASCENDING)], name="assignee_idx")
    db.tasks.create_index([("status",      ASCENDING)], name="status_idx")
    db.tasks.create_index([("priority",    ASCENDING)], name="priority_idx")
    db.tasks.create_index([("deadline",    ASCENDING)], name="deadline_idx")
    db.tasks.create_index([("created_at",  DESCENDING)],name="created_desc")
    db.tasks.create_index([("title",       TEXT), ("description", TEXT)], name="task_text")

    db.comments.create_index([("task_id",    ASCENDING)], name="task_idx")
    db.comments.create_index([("created_at", ASCENDING)], name="created_idx")

    db.notifications.create_index([("user_id",   ASCENDING)], name="user_idx")
    db.notifications.create_index([("read",       ASCENDING)], name="read_idx")
    db.notifications.create_index([("timestamp",  DESCENDING)],name="ts_desc")

    db.activity_logs.create_index([("user_id",   ASCENDING)],  name="user_idx")
    db.activity_logs.create_index([("entity_id",  ASCENDING)], name="entity_idx")
    db.activity_logs.create_index([("timestamp",  DESCENDING)],name="ts_desc")

    db.files.create_index([("task_id", ASCENDING)], name="task_idx")

    print("\n  ✅ All indexes created successfully\n")


# ════════════════════════════════════════════════════════════════════
#  SAMPLE DOCUMENTS  (reference / documentation)
# ════════════════════════════════════════════════════════════════════

SAMPLE_USER = {
    "_id":                   ObjectId(),
    "name":                  "Alice Johnson",
    "email":                 "alice@tasksphere.io",
    "password":              "$2b$12$...",          # bcrypt hash
    "role":                  "manager",
    "avatar":                "https://api.dicebear.com/7.x/initials/svg?seed=Alice",
    "bio":                   "Product manager with 5 years experience",
    "phone":                 "+1 555-0100",
    "department":            "Product",
    "dark_mode":             True,
    "notifications_enabled": True,
    "created_at":            datetime.utcnow(),
    "last_login":            datetime.utcnow(),
}

SAMPLE_PROJECT = {
    "_id":         ObjectId(),
    "name":        "Website Redesign 2024",
    "description": "Full overhaul of the marketing website",
    "status":      "active",          # active | on_hold | completed | archived
    "priority":    "high",            # low | medium | high
    "owner_id":    str(ObjectId()),
    "members":     [str(ObjectId()), str(ObjectId())],
    "deadline":    "2024-12-31",
    "color":       "#6366f1",
    "created_at":  datetime.utcnow(),
    "updated_at":  datetime.utcnow(),
}

SAMPLE_TASK = {
    "_id":          ObjectId(),
    "title":        "Design new landing page mockup",
    "description":  "Create hi-fi mockups in Figma for review",
    "project_id":   str(ObjectId()),
    "assignee_id":  str(ObjectId()),
    "assignee_name":"Alice Johnson",
    "priority":     "high",           # low | medium | high
    "status":       "in_progress",    # todo | in_progress | completed
    "deadline":     "2024-11-20T18:00:00",
    "tags":         ["design","figma","ui"],
    "attachments":  [],
    "created_by":   str(ObjectId()),
    "created_at":   datetime.utcnow(),
    "updated_at":   datetime.utcnow(),
}

SAMPLE_COMMENT = {
    "_id":        ObjectId(),
    "task_id":    str(ObjectId()),
    "user_id":    str(ObjectId()),
    "user_name":  "Bob Smith",
    "content":    "I've pushed the initial wireframes to Figma. Please review.",
    "created_at": datetime.utcnow(),
}

SAMPLE_NOTIFICATION = {
    "_id":       ObjectId(),
    "user_id":   str(ObjectId()),
    "title":     "New Task Assigned",
    "message":   "You've been assigned: Design new landing page mockup",
    "type":      "task",              # info | task | success | warning | danger
    "read":      False,
    "timestamp": datetime.utcnow(),
}

SAMPLE_ACTIVITY_LOG = {
    "_id":         ObjectId(),
    "user_id":     str(ObjectId()),
    "action":      "created",         # created | updated | deleted | login | moved | registered
    "entity_type": "task",
    "entity_id":   str(ObjectId()),
    "description": "Created task: Design new landing page mockup",
    "timestamp":   datetime.utcnow(),
}

SAMPLE_FILE = {
    "_id":         ObjectId(),
    "task_id":     str(ObjectId()),
    "uploaded_by": str(ObjectId()),
    "filename":    "mockup_v1.png",
    "path":        "static/uploads/mockup_v1.png",
    "size":        204800,            # bytes
    "mimetype":    "image/png",
    "uploaded_at": datetime.utcnow(),
}


# ════════════════════════════════════════════════════════════════════
#  AGGREGATION PIPELINES  (reference queries)
# ════════════════════════════════════════════════════════════════════

def get_task_stats_for_user(user_id: str):
    """Returns task counts grouped by status for a user."""
    return list(db.tasks.aggregate([
        {"$match": {"assignee_id": user_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort":  {"_id": 1}}
    ]))

def get_project_progress(project_id: str):
    """Returns completion percentage for a project."""
    return list(db.tasks.aggregate([
        {"$match": {"project_id": project_id}},
        {"$group": {
            "_id":   None,
            "total": {"$sum": 1},
            "done":  {"$sum": {"$cond": [{"$eq": ["$status","completed"]}, 1, 0]}}
        }},
        {"$project": {
            "total": 1, "done": 1,
            "pct": {"$cond": [
                {"$eq": ["$total", 0]}, 0,
                {"$multiply": [{"$divide": ["$done","$total"]}, 100]}
            ]}
        }}
    ]))

def get_weekly_completion(user_id: str):
    """Returns per-day completed task count for the last 7 days."""
    from datetime import timedelta
    now   = datetime.utcnow()
    start = now - timedelta(days=7)
    return list(db.tasks.aggregate([
        {"$match": {
            "assignee_id": user_id,
            "status": "completed",
            "updated_at": {"$gte": start}
        }},
        {"$group": {
            "_id":   {"$dateToString": {"format":"%Y-%m-%d","date":"$updated_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]))

def search_full_text(query: str):
    """Full-text search across tasks and projects."""
    task_results    = list(db.tasks.find({"$text": {"$search": query}},
                                          {"score": {"$meta":"textScore"}}).sort("score",{"$meta":"textScore"}).limit(10))
    project_results = list(db.projects.find({"$text": {"$search": query}},
                                             {"score": {"$meta":"textScore"}}).sort("score",{"$meta":"textScore"}).limit(10))
    return {"tasks": task_results, "projects": project_results}


if __name__ == "__main__":
    print("\n🚀 TaskSphere — Setting up MongoDB collections & indexes…\n")
    setup_collections()
    print("✅ Database setup complete!")
    print(f"   Collections: {db.list_collection_names()}")