from __future__ import annotations

from dataclasses import dataclass
import re

from app.schemas.chat import ChatRequest


STATE_NAMES = {
    "texas": "TX",
    "tx": "TX",
    "california": "CA",
    "ca": "CA",
    "florida": "FL",
    "fl": "FL",
    "new york": "NY",
    "ny": "NY",
}

BUILDING_KEYWORDS = {
    "hospital": "hospital",
    "clinic": "healthcare",
    "healthcare": "healthcare",
    "memory care": "healthcare",
    "school": "school",
    "office": "office",
    "warehouse": "warehouse",
    "restaurant": "restaurant",
    "retail": "retail",
    "hotel": "hotel",
}

APPLICATION_PATTERNS = [
    (("masonry", "frame"), "masonry opening frame"),
    (("main entrance",), "main entrance"),
    (("patient room",), "patient room"),
    (("restroom",), "restroom"),
    (("classroom",), "classroom opening"),
    (("kitchen",), "kitchen opening"),
    (("corridor",), "corridor opening"),
    (("stair",), "stair opening"),
    (("egress",), "egress door"),
    (("exit door",), "egress door"),
    (("rated opening",), "rated opening"),
]

MATERIAL_TERMS = {
    "hollow metal": "hollow metal",
    "steel": "steel",
    "metal": "metal",
    "wood": "wood",
    "aluminum": "aluminum/storefront",
    "storefront": "aluminum/storefront",
    "glass": "glass",
}

HARDWARE_TERMS = {
    "panic hardware": "panic hardware",
    "panic bar": "panic hardware",
    "exit device": "exit device",
    "closer": "closer",
    "hinge": "hinges",
    "lockset": "lockset",
    "maglock": "maglock",
    "electric strike": "electric strike",
    "access control": "access control",
    "operator": "operator",
}


@dataclass(frozen=True)
class ProjectFacts:
    text: str
    building_type: str | None = None
    application: str | None = None
    location_type: str | None = None
    rating_minutes: int | None = None
    rating_required: bool | None = None
    traffic: str | None = None
    material_preference: str | None = None
    wall_or_barrier: str | None = None
    is_egress_path: bool | None = None
    accessibility_required: bool | None = None
    hardware_type: str | None = None
    access_control: bool | None = None
    occupant_load_known: bool = False
    state: str | None = None
    zip_code: str | None = None
    city: str | None = None
    new_vs_existing: bool | None = None

    @property
    def has_project_shape(self) -> bool:
        return bool(self.building_type and self.application)


def _full_text(request: ChatRequest) -> str:
    parts = [request.message]
    if request.building:
        parts.extend(
            [
                request.building.building_type or "",
                request.building.application or "",
            ]
        )
    if request.location:
        parts.extend(
            [
                request.location.state or "",
                request.location.zip_code or "",
                request.location.city or "",
            ]
        )
    return " ".join(part for part in parts if part).lower()


def _first_zip_code(text: str) -> str | None:
    match = re.search(r"\b\d{5}(?:-\d{4})?\b", text)
    return match.group(0) if match else None


def _state_from_text(text: str) -> str | None:
    for keyword, state_code in STATE_NAMES.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            return state_code
    return None


def _building_type_from_text(text: str) -> str | None:
    for keyword, building_type in BUILDING_KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            return building_type
    return None


def _application_from_text(text: str) -> str | None:
    if "hospital" in text and "corridor" in text:
        return "hospital corridor"

    for required_terms, application in APPLICATION_PATTERNS:
        if all(term in text for term in required_terms):
            return application
    return None


def _rating_minutes_from_text(text: str) -> int | None:
    match = re.search(
        r"\b(20|45|60|90)\s*(?:min|mins|minute|minutes)?\b|\b([123])\s*(?:hr|hrs|hour|hours)\b",
        text,
    )
    if not match:
        return None
    if match.group(1):
        return int(match.group(1))
    return int(match.group(2)) * 60


def _traffic_from_text(text: str) -> str | None:
    if re.search(r"\b(?:high|heavy)\s+traffic\b|\bheavy use\b|\bhigh frequency\b", text):
        return "high traffic"
    if re.search(r"\bnormal\s+traffic\b|\bnormal\b", text):
        return "normal traffic"
    if re.search(r"\blight\s+traffic\b|\blight\b|\blow frequency\b", text):
        return "light traffic"
    return None


def _location_type_from_text(text: str) -> str | None:
    if re.search(r"\b(?:interior|inside|indoor)\b", text):
        return "interior"
    if re.search(r"\b(?:exterior|outside|outdoor)\b", text):
        return "exterior"
    return None


def _material_from_text(text: str) -> str | None:
    for term, material in MATERIAL_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", text):
            return material
    if "no preference" in text:
        return "no preference"
    return None


def _hardware_from_text(text: str) -> str | None:
    for term, hardware_type in HARDWARE_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", text):
            return hardware_type
    if "hardware" in text:
        return "hardware"
    return None


def _wall_or_barrier_from_text(text: str) -> str | None:
    match = re.search(
        r"\b((?:[a-z0-9-]+\s+){0,4}(?:wall|barrier|partition|enclosure))\b",
        text,
    )
    if match:
        return " ".join(match.group(1).split())
    if re.search(r"\b(?:masonry|drywall|stud)\b", text):
        return "wall type"
    return None


CITY_NAMES = {
    "los angeles": "Los Angeles",
    "new york": "New York",
    "chicago": "Chicago",
    "houston": "Houston",
    "phoenix": "Phoenix",
    "philadelphia": "Philadelphia",
    "san antonio": "San Antonio",
    "san diego": "San Diego",
    "dallas": "Dallas",
    "san jose": "San Jose",
    "austin": "Austin",
    "san francisco": "San Francisco",
    "seattle": "Seattle",
    "denver": "Denver",
    "boston": "Boston",
    "miami": "Miami",
    "atlanta": "Atlanta",
    "las vegas": "Las Vegas",
    "portland": "Portland",
    "sacramento": "Sacramento",
}


def _city_from_text(text: str) -> str | None:
    for city_lower, city_display in CITY_NAMES.items():
        if re.search(rf"\b{re.escape(city_lower)}\b", text):
            return city_display
    return None


def extract_project_facts(request: ChatRequest) -> ProjectFacts:
    text = _full_text(request)
    building = request.building
    location = request.location

    rating_minutes = _rating_minutes_from_text(text)
    rating_required = (
        building.fire_rating_required
        if building and building.fire_rating_required is not None
        else True
        if rating_minutes is not None
        or re.search(r"\b(?:fire-rated|fire rated|fire rating|fire rate|rated opening|rated door)\b", text)
        else None
    )

    is_egress_path = (
        building.is_egress_path
        if building and building.is_egress_path is not None
        else True
        if re.search(r"\b(?:egress|exit path|exit door|means of egress)\b", text)
        else None
    )

    accessibility_required = (
        building.accessibility_required
        if building and building.accessibility_required is not None
        else True
        if re.search(r"\b(?:ada|accessible|accessibility|handicap)\b", text)
        else None
    )

    return ProjectFacts(
        text=text,
        building_type=(building.building_type if building else None) or _building_type_from_text(text),
        application=(building.application if building else None) or _application_from_text(text),
        location_type=_location_type_from_text(text),
        rating_minutes=rating_minutes,
        rating_required=rating_required,
        traffic=_traffic_from_text(text),
        material_preference=_material_from_text(text),
        wall_or_barrier=_wall_or_barrier_from_text(text),
        is_egress_path=is_egress_path,
        accessibility_required=accessibility_required,
        hardware_type=_hardware_from_text(text),
        access_control=True
        if re.search(r"\b(?:access control|maglock|electric strike|card reader|security)\b", text)
        else None,
        occupant_load_known=bool(
            re.search(r"\b(?:occupant load|occupants|people|students|staff)\b", text)
            or re.search(r"\b\d+\s*(?:occupant|person|people|students|staff)\b", text)
            or re.search(r"\boccupant load\s*(?:is|of|:)?\s*\d+", text)
            or re.search(r"\b\d{1,4}\s+(?:occupants|people)\b", text)
        ),
        state=(location.state if location else None) or _state_from_text(text),
        zip_code=(location.zip_code if location else None) or _first_zip_code(text),
        city=(location.city if location else None) or _city_from_text(text),
        new_vs_existing=(
            True
            if re.search(r"\b(?:new construction|new work)\b", text)
            else False
            if re.search(r"\b(?:existing|renovation|retrofit)\b", text)
            else None
        ),
    )
