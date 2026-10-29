"""Validated wire contracts for drafts and approved plan transfer."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator

ActivityType = Literal['MORNING_BRIEFING', 'NIGHT_WRAPUP', 'GENERAL', 'ROUTINE', 'COOKING', 'MEAL', 'HEALTH', 'CLOTHING', 'LEISURE', 'REST']


class DraftItem(BaseModel):
    model_config = ConfigDict(extra='ignore', strict=True)
    time: str = Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    type: ActivityType
    task: str = Field(min_length=1, max_length=200)
    guide_script: list[StrictStr] = Field(min_length=1, max_length=20)

    @field_validator('task')
    @classmethod
    def nonblank_task(cls, value):
        if not value.strip():
            raise ValueError('task must not be blank')
        return value.strip()

    @field_validator('guide_script')
    @classmethod
    def nonblank_steps(cls, value):
        if any(not s.strip() or len(s) > 300 for s in value):
            raise ValueError('guide steps must be nonempty and short')
        return value


class DraftResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    schedule: list[DraftItem] = Field(min_length=1, max_length=100)


class TransferMenu(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: str = Field(min_length=1, max_length=200)
    image: str = Field(default='', max_length=2048)
    video_url: str = Field(default='', max_length=2048)

    @field_validator('image', 'video_url')
    @classmethod
    def public_url(cls, value):
        if value and not value.startswith('https://'):
            raise ValueError('media must use a public HTTPS URL')
        return value


class TransferItem(DraftItem):
    model_config = ConfigDict(extra='forbid', strict=True)
    # Manually approved activities may intentionally have no steps. This is
    # distinct from AI drafts, which must provide a nonempty guide.
    guide_script: list[StrictStr] = Field(max_length=20)
    id: str = Field(min_length=1, max_length=120)
    series_id: str = Field(default='', max_length=120)
    # Local paths are never part of a transfer contract.
    menus: list[TransferMenu] = Field(default_factory=list, max_length=20)
    video_url: str = Field(default='', max_length=2048)

    @field_validator('video_url')
    @classmethod
    def public_video_url(cls, value):
        return TransferMenu.public_url(value)


class PublishedPlan(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    id: str = Field(min_length=16, max_length=120)
    version_number: int = Field(ge=1)
    status: Literal['published']
    approved_by: str = Field(min_length=1, max_length=100)
    published_at: str
    date: str

    @field_validator('id')
    @classmethod
    def global_uuid(cls, value):
        parsed = UUID(value)
        if str(parsed) != value.lower():
            raise ValueError('plan id must be a canonical UUID string')
        return str(parsed)

    @field_validator('date')
    @classmethod
    def calendar_date(cls, value):
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError('date must be yyyy-MM-dd')
        return value

    @field_validator('published_at')
    @classmethod
    def timestamp(cls, value):
        if 'T' not in value:
            raise ValueError('published_at must include date and time')
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value

    @field_validator('approved_by')
    @classmethod
    def approver(cls, value):
        if not value.strip():
            raise ValueError('approver required')
        return value.strip()


class PlanEnvelope(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    schema_version: Literal[1]
    plan: PublishedPlan
    activities: list[TransferItem] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def unique_activities(self):
        ids = [item.id for item in self.activities]
        if len(set(ids)) != len(ids):
            raise ValueError('activity ids must be unique')
        return self
