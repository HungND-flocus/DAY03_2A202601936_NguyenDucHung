"""
SQLite database bootstrap.

JSON trong config/academic_data.json la format import/export de nhan data nhieu
truong. SQLite la database local cho backend demo.
"""

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "config" / "academic_data.json"
DB_PATH = ROOT / "data" / "academic_advisor.sqlite"


def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    with connect() as conn:
        conn.executescript(
            """
            drop table if exists advisor_students;
            drop table if exists advisors;
            drop table if exists students;
            drop table if exists course_prerequisites;
            drop table if exists track_courses;
            drop table if exists program_required_courses;
            drop table if exists programs;
            drop table if exists courses;
            drop table if exists schools;

            create table schools (
              id text primary key,
              name text not null,
              min_per_term integer,
              default_max_per_term integer,
              hard_max_per_term integer
            );

            create table courses (
              school_id text not null,
              id text not null,
              name text not null,
              description text not null,
              credits integer not null,
              terms_json text not null,
              tags_json text not null,
              difficulty integer not null,
              metadata_json text not null,
              primary key (school_id, id)
            );

            create table course_prerequisites (
              school_id text not null,
              course_id text not null,
              prerequisite_id text not null,
              primary key (school_id, course_id, prerequisite_id)
            );

            create table programs (
              school_id text not null,
              id text not null,
              name text not null,
              min_graduation_credits integer,
              metadata_json text not null,
              primary key (school_id, id)
            );

            create table program_required_courses (
              school_id text not null,
              program_id text not null,
              course_id text not null,
              primary key (school_id, program_id, course_id)
            );

            create table track_courses (
              school_id text not null,
              program_id text not null,
              track_name text not null,
              course_id text not null,
              primary key (school_id, program_id, track_name, course_id)
            );

            create table students (
              school_id text not null,
              id text not null,
              name text not null,
              year integer,
              program_id text,
              gpa real,
              completed_courses_json text not null,
              failed_courses_json text not null,
              interests_json text not null,
              career_track text,
              goal text,
              advisor_id text,
              primary key (school_id, id)
            );

            create table advisors (
              school_id text not null,
              id text not null,
              name text not null,
              primary key (school_id, id)
            );

            create table advisor_students (
              school_id text not null,
              advisor_id text not null,
              student_id text not null,
              primary key (school_id, advisor_id, student_id)
            );
            """
        )

        for school_id, school in data["schools"].items():
            limits = school["credit_limits"]
            conn.execute(
                "insert into schools values (?, ?, ?, ?, ?)",
                (school_id, school["name"], limits["min_per_term"], limits["default_max_per_term"], limits["hard_max_per_term"]),
            )
            for course_id, course in school["courses"].items():
                metadata = {k: v for k, v in course.items() if k not in {"name", "credits", "terms", "tags", "difficulty", "prerequisites"}}
                conn.execute(
                    "insert into courses values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        school_id,
                        course_id,
                        course["name"],
                        course.get("description", ""),
                        course["credits"],
                        json.dumps(course.get("terms", []), ensure_ascii=False),
                        json.dumps(course.get("tags", []), ensure_ascii=False),
                        course.get("difficulty", 3),
                        json.dumps(metadata, ensure_ascii=False),
                    ),
                )
                for prerequisite_id in course.get("prerequisites", []):
                    conn.execute(
                        "insert into course_prerequisites values (?, ?, ?)",
                        (school_id, course_id, prerequisite_id),
                    )

            for program_id, program in school["programs"].items():
                metadata = {k: v for k, v in program.items() if k not in {"name", "min_graduation_credits", "required_courses", "tracks"}}
                conn.execute(
                    "insert into programs values (?, ?, ?, ?, ?)",
                    (school_id, program_id, program["name"], program.get("min_graduation_credits"), json.dumps(metadata, ensure_ascii=False)),
                )
                for course_id in program.get("required_courses", []):
                    conn.execute("insert into program_required_courses values (?, ?, ?)", (school_id, program_id, course_id))
                for track_name, course_ids in program.get("tracks", {}).items():
                    for course_id in course_ids:
                        conn.execute("insert into track_courses values (?, ?, ?, ?)", (school_id, program_id, track_name, course_id))

            for student_id, student in school["students"].items():
                conn.execute(
                    "insert into students values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        school_id,
                        student_id,
                        student["name"],
                        student.get("year"),
                        student.get("program_id"),
                        student.get("gpa"),
                        json.dumps(student.get("completed_courses", []), ensure_ascii=False),
                        json.dumps(student.get("failed_courses", []), ensure_ascii=False),
                        json.dumps(student.get("interests", []), ensure_ascii=False),
                        student.get("career_track"),
                        student.get("goal"),
                        student.get("advisor_id"),
                    ),
                )

            for advisor_id, advisor in school["advisors"].items():
                conn.execute("insert into advisors values (?, ?, ?)", (school_id, advisor_id, advisor["name"]))
                for student_id in advisor.get("student_ids", []):
                    conn.execute("insert into advisor_students values (?, ?, ?)", (school_id, advisor_id, student_id))
    return DB_PATH


def status():
    if not DB_PATH.exists():
        init_database()
    with connect() as conn:
        return {
            "ok": True,
            "path": str(DB_PATH),
            "schools": conn.execute("select count(*) from schools").fetchone()[0],
            "courses": conn.execute("select count(*) from courses").fetchone()[0],
            "students": conn.execute("select count(*) from students").fetchone()[0],
            "programs": conn.execute("select count(*) from programs").fetchone()[0],
        }


if __name__ == "__main__":
    init_database()
    print(status())
