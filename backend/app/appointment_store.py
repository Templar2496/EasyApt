"""
Tiny SQLite appointment store (pure stdlib).
Used to make reschedule/cancel/reminders "real" for demo without hardcoding.

DB file: appointments.sqlite (in project root)
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from typing import Optional, List

DB_PATH = os.getenv("APPOINTMENTS_DB_PATH", "appointments.sqlite")


@dataclass
class Appointment:
    id: int
    email: str
    name: str
    provider: str
    starts_at_iso: str  # ISO 8601 string
    status: str  # scheduled|cancelled
    reminder_job_id: Optional[str]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                starts_at_iso TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'scheduled',
                reminder_job_id TEXT
            )
            """
        )
        conn.commit()


def create_appointment(email: str, name: str, provider: str, starts_at_iso: str) -> Appointment:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO appointments (email, name, provider, starts_at_iso, status) VALUES (?, ?, ?, ?, 'scheduled')",
            (email, name, provider, starts_at_iso),
        )
        conn.commit()
        appt_id = int(cur.lastrowid)
    return get_appointment(appt_id)


def get_appointment(appt_id: int) -> Appointment:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM appointments WHERE id = ?", (appt_id,)).fetchone()
    if row is None:
        raise KeyError(f"Appointment {appt_id} not found")
    return Appointment(
        id=int(row["id"]),
        email=row["email"],
        name=row["name"],
        provider=row["provider"],
        starts_at_iso=row["starts_at_iso"],
        status=row["status"],
        reminder_job_id=row["reminder_job_id"],
    )


def set_status(appt_id: int, status: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appt_id))
        conn.commit()


def update_starts_at(appt_id: int, starts_at_iso: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("UPDATE appointments SET starts_at_iso = ? WHERE id = ?", (starts_at_iso, appt_id))
        conn.commit()


def set_reminder_job(appt_id: int, job_id: Optional[str]) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("UPDATE appointments SET reminder_job_id = ? WHERE id = ?", (job_id, appt_id))
        conn.commit()
