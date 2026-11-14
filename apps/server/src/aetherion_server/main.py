"""Local-only API. No authentication; use development data only."""

import os
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field, field_validator

from .store import add_observation, list_observations

app = FastAPI(
    title="AETHERION API",
    description="Local engineering prototype; not clinical decision support",
    version="0.1.0",
)


def database_path() -> Path:
    default = Path.home() / ".aetherion" / "observations.sqlite3"
    return Path(os.environ.get("AETHERION_DB_PATH", str(default)))


class ObservationIn(BaseModel):
    subject_id: str = Field(min_length=1, max_length=80)
    metric: str = Field(min_length=1, max_length=80)
    value: float
    unit: str = Field(min_length=1, max_length=40)
    source: str = Field(min_length=1, max_length=120)
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must include a time-zone offset")
        return value


@app.get("/health")
def health() -> dict[str, str]:
    return {"service": "aetherion-server", "status": "ok"}


@app.get("/api/v1/observations")
def observations(subject_id: str = Query(min_length=1, max_length=80), limit: int = Query(100, ge=1, le=500)):
    return {
        "subject_id": subject_id,
        "observations": list_observations(database_path(), subject_id, limit),
        "note": "Prototype data are unverified. No medical interpretation is provided.",
    }


@app.post("/api/v1/observations", status_code=201)
def create_observation(item: ObservationIn):
    record = item.model_dump(mode="json")
    identifier = add_observation(database_path(), record)
    return {"id": identifier, "status": "stored_unverified", "observation": record}
