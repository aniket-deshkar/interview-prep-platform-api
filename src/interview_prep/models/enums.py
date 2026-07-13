from enum import StrEnum


class ApplicationStage(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    RECRUITER_SCREEN = "recruiter_screen"
    TECHNICAL = "technical"
    MANAGERIAL = "managerial"
    HR = "hr"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class QuestionKind(StrEnum):
    DSA = "dsa"
    THEORY = "theory"
    SQL = "sql"
    NOSQL = "nosql"
    VECTOR_DB = "vector_db"
    SYSTEM_DESIGN = "system_design"
    BEHAVIOURAL = "behavioural"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Provider(StrEnum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
