"""Scan context: location, profile, couple nakshatras."""
from __future__ import annotations

from dataclasses import dataclass

from vedic.panchang.vivah_nakshatra import normalize_nakshatra
from vedic.panchang.vivah_profiles import VivahProfile, get_vivah_profile


@dataclass
class VivahScanContext:
    lat: float
    lng: float
    tz_h: float
    profile: VivahProfile
    bride_nak: str | None = None
    groom_nak: str | None = None
    bride_moon_rashi: str | None = None
    groom_moon_rashi: str | None = None

    @classmethod
    def build(
        cls,
        *,
        lat: float,
        lng: float,
        tz_h: float,
        profile: str | None = None,
        bride_nak: str | None = None,
        groom_nak: str | None = None,
        bride_moon_rashi: str | None = None,
        groom_moon_rashi: str | None = None,
    ) -> VivahScanContext:
        return cls(
            lat=lat,
            lng=lng,
            tz_h=tz_h,
            profile=get_vivah_profile(profile),
            bride_nak=normalize_nakshatra(bride_nak),
            groom_nak=normalize_nakshatra(groom_nak),
            bride_moon_rashi=bride_moon_rashi,
            groom_moon_rashi=groom_moon_rashi,
        )

    @property
    def has_couple_nak(self) -> bool:
        return bool(self.bride_nak or self.groom_nak)
