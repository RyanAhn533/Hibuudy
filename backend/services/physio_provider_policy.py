"""Separate purpose gate. Never call the general LLM cascade."""
import os

from schemas.dialogue import PhysioConsent


def external_enabled():
    return os.getenv('HIBUDDY_PHYSIO_EXTERNAL_ENABLED', 'false').lower() == 'true'


def denial_reason(consent: PhysioConsent, *, provider_configured: bool):
    if not external_enabled():
        return 'disabled'
    if not consent.granted:
        return 'consent_required'
    if not provider_configured:
        return 'provider_unconfigured'
    return None
