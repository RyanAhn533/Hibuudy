"""First-slice evidence: scalar provenance, never raw PPG or embeddings."""
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (AwareDatetime, BaseModel, ConfigDict, Field, StrictInt,
                      field_validator, model_validator)


class StrictContract(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


FiniteNumber = Annotated[float, Field(strict=True, allow_inf_nan=False)]
FeatureId = Literal['signal_mean', 'signal_std', 'signal_rms', 'embedding_l2_norm']
FeatureUnit = Literal['arbitrary_unit', 'dimensionless']
Limitation = Literal[
    'not_emotion_classifier', 'no_personal_baseline', 'synthetic_input',
    'public_data_not_personal', 'resampled_input', 'device_domain_shift',
    'not_field_validated', 'noncausal_preprocessing', 'not_medical_advice',
]


class EvidenceWindow(StrictContract):
    start: AwareDatetime
    end: AwareDatetime
    sampling_rate_hz: FiniteNumber = Field(gt=0, le=1000)
    sample_count: StrictInt = Field(gt=0, le=2_000_000)

    @model_validator(mode='after')
    def consistent_window(self):
        duration = (self.end - self.start).total_seconds()
        if not 0 < duration <= 3600:
            raise ValueError('window duration must be positive and at most one hour')
        # Half-open [start, end); count is the supplied model input length.
        if abs(duration * self.sampling_rate_hz - self.sample_count) > 1:
            raise ValueError('window rate, duration and sample count disagree')
        return self


class EvidenceQuality(StrictContract):
    status: Literal['usable', 'insufficient', 'invalid']
    reasons: list[Literal['missing_samples', 'nonfinite_input', 'flat_signal',
                          'motion_artifact', 'insufficient_duration',
                          'unverified_sensor']] = Field(max_length=6)
    valid_fraction: FiniteNumber = Field(ge=0, le=1)

    @model_validator(mode='after')
    def coherent_quality(self):
        if self.status == 'usable' and (self.valid_fraction < .9 or self.reasons):
            raise ValueError('usable evidence needs high coverage and no blocking reason')
        if self.status != 'usable' and not self.reasons:
            raise ValueError('unusable evidence needs a reason')
        return self


class EvidenceModel(StrictContract):
    id: Literal['pulseppg']
    checkpoint_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    embedding_dim: StrictInt = Field(gt=0, le=8192)
    adaptation: Literal['none']


class EvidenceFeature(StrictContract):
    id: FeatureId
    unit: FeatureUnit
    source: Literal['signal_summary', 'encoder_summary']
    source_id: UUID
    value: FiniteNumber

    @model_validator(mode='after')
    def coherent_feature(self):
        is_embedding = self.id == 'embedding_l2_norm'
        if self.source != ('encoder_summary' if is_embedding else 'signal_summary'):
            raise ValueError('feature source does not match its computation')
        if self.unit != ('dimensionless' if is_embedding else 'arbitrary_unit'):
            raise ValueError('feature unit does not match its computation')
        if self.id != 'signal_mean' and self.value < 0:
            raise ValueError('scale and norm values must be nonnegative')
        return self


class PhysioEvidenceBundle(StrictContract):
    schema_version: Literal[1]
    bundle_id: UUID
    data_origin: Literal['synthetic', 'public', 'field']
    created_at: AwareDatetime
    window: EvidenceWindow
    quality: EvidenceQuality
    model: EvidenceModel
    features: list[EvidenceFeature] = Field(min_length=1, max_length=4)
    personal_baseline: None
    predictions: list[object] = Field(max_length=0)
    limitations: list[Limitation] = Field(min_length=2, max_length=9)

    @field_validator('schema_version', mode='before')
    @classmethod
    def integer_version(cls, value):
        if type(value) is not int:
            raise ValueError('schema_version must be an integer')
        return value

    @model_validator(mode='after')
    def preserve_limits(self):
        if self.created_at < self.window.end:
            raise ValueError('bundle cannot precede the source window')
        if len({f.id for f in self.features}) != len(self.features):
            raise ValueError('feature IDs must be unique')
        required = {'not_emotion_classifier', 'no_personal_baseline'}
        if self.data_origin == 'synthetic':
            required.add('synthetic_input')
        if self.data_origin == 'public':
            required.add('public_data_not_personal')
        if not required.issubset(self.limitations):
            raise ValueError('origin and model limitations must be explicit')
        if len(set(self.limitations)) != len(self.limitations):
            raise ValueError('limitations must be unique')
        return self
