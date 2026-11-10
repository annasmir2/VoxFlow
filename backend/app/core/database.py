from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_reminder_notification_tracking() -> None:
    with engine.begin() as connection:
        if not inspect(connection).has_table("reminders"):
            return

        columns = {column["name"] for column in inspect(connection).get_columns("reminders")}
        if "notification_sent_at" not in columns:
            connection.execute(text("ALTER TABLE reminders ADD COLUMN notification_sent_at DATETIME"))


def init_db() -> None:
    from app.models.reminder import Reminder
    from app.models.task import Task

    Base.metadata.create_all(bind=engine)
    ensure_reminder_notification_tracking()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
