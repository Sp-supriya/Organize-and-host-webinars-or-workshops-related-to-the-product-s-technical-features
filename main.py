import sqlite3
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import uuid

class WebinarStatus(Enum):
    SCHEDULED = "Scheduled"
    LIVE = "Live"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class WebinarType(Enum):
    PRODUCT_DEMO = "Product Demo"
    TECHNICAL_DEEP_DIVE = "Technical Deep Dive"
    HANDS_ON_WORKSHOP = "Hands-on Workshop"
    Q_AND_A = "Q&A Session"
    FEATURE_SHOWCASE = "Feature Showcase"

@dataclass
class Presenter:
    id: int
    name: str
    title: str
    bio: str
    expertise: List[str]
    email: str

@dataclass
class WebinarContent:
    title: str
    description: str
    agenda: List[str]
    prerequisites: List[str]
    resources: Dict[str, str]
    presentation_url: Optional[str] = None
    recording_url: Optional[str] = None

class WebinarManagementSystem:
    def __init__(self, db_name=":memory:"):
        self.conn = sqlite3.connect(db_name)
        self.setup_database()

    def setup_database(self):
        cursor = self.conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS webinars (
            id TEXT PRIMARY KEY,
            title TEXT,
            type TEXT,
            description TEXT,
            start_time DATETIME,
            duration_minutes INTEGER,
            max_participants INTEGER,
            status TEXT
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            name TEXT,
            company TEXT,
            job_title TEXT
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS webinar_participants (
            webinar_id TEXT,
            participant_id INTEGER,
            registration_date DATETIME,
            FOREIGN KEY (webinar_id) REFERENCES webinars (id),
            FOREIGN KEY (participant_id) REFERENCES participants (id)
        )''')

        self.conn.commit()

    def create_webinar(self, content: WebinarContent, webinar_type: WebinarType,
                      start_time: datetime, duration_minutes: int,
                      max_participants: int, presenters: List[Presenter]) -> str:
        webinar_id = str(uuid.uuid4())
        cursor = self.conn.cursor()

        cursor.execute('''
        INSERT INTO webinars (
            id, title, type, description, start_time,
            duration_minutes, max_participants, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (webinar_id, content.title, webinar_type.value, content.description,
              start_time, duration_minutes, max_participants,
              WebinarStatus.SCHEDULED.value))

        self.conn.commit()
        return webinar_id

    def register_participant(self, webinar_id: str, email: str, name: str,
                           company: str, job_title: str) -> bool:
        cursor = self.conn.cursor()

        # Insert participant
        cursor.execute('''
        INSERT OR IGNORE INTO participants (email, name, company, job_title)
        VALUES (?, ?, ?, ?)
        ''', (email, name, company, job_title))

        # Register for webinar
        cursor.execute('''
        INSERT INTO webinar_participants (webinar_id, participant_id, registration_date)
        VALUES (?, (SELECT id FROM participants WHERE email = ?), ?)
        ''', (webinar_id, email, datetime.now()))

        self.conn.commit()
        return True

    def generate_webinar_report(self, webinar_id: str) -> Dict:
        cursor = self.conn.cursor()

        cursor.execute('''
        SELECT w.*, COUNT(wp.participant_id) as registered_participants
        FROM webinars w
        LEFT JOIN webinar_participants wp ON w.id = wp.webinar_id
        WHERE w.id = ?
        GROUP BY w.id
        ''', (webinar_id,))

        webinar = cursor.fetchone()
        if not webinar:
            return {}

        return {
            'webinar_info': {
                'id': webinar[0],
                'title': webinar[1],
                'type': webinar[2],
                'status': webinar[7]
            },
            'participants': {
                'registered': webinar[8]
            }
        }

    def close(self):
        self.conn.close()

# Demo usage
async def demo_webinar_system():
    system = WebinarManagementSystem()

    content = WebinarContent(
        title="Python for Data Science",
        description="Learn Python basics for DS",
        agenda=["Intro", "Pandas", "NumPy"],
        prerequisites=["Basic Programming"],
        resources={"Guide": "https://example.com"}
    )

    presenter = Presenter(
        id=1,
        name="Jane Smith",
        title="Data Scientist",
        bio="10 years experience",
        expertise=["Python", "ML"],
        email="jane@example.com"
    )

    # Create webinar
    webinar_id = system.create_webinar(
        content=content,
        webinar_type=WebinarType.HANDS_ON_WORKSHOP,
        start_time=datetime.now() + timedelta(days=1),
        duration_minutes=120,
        max_participants=50,
        presenters=[presenter]
    )

    print(f"Created webinar with ID: {webinar_id}")

    # Register participants
    participants = [
        ("user1@test.com", "User One", "TechCorp", "Developer"),
        ("user2@test.com", "User Two", "DataCo", "Analyst"),
        ("user3@test.com", "User Three", "AILabs", "Researcher")
    ]

    for email, name, company, title in participants:
        system.register_participant(webinar_id, email, name, company, title)
        print(f"Registered participant: {name}")

    # Generate report
    report = system.generate_webinar_report(webinar_id)
    print("\nWebinar Report:")
    print(json.dumps(report, indent=2))

    system.close()

# Run the demo
await demo_webinar_system()
