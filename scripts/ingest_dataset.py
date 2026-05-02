from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PDF = PROJECT_ROOT / "united_doors_ai_training_dataset.pdf"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return value.strip("-")


def product(
    name: str,
    category: str,
    description: str,
    compatible_applications: list[str],
    *,
    source_url: str | None = None,
    price: float | None = None,
    fire_rating: str | None = None,
) -> dict[str, Any]:
    return {
        "id": slugify(name),
        "name": name,
        "category": category,
        "description": description,
        "compatible_applications": compatible_applications,
        "source_url": source_url,
        "starting_price_usd": price,
        "fire_rating": fire_rating,
    }


DOOR_CATALOG = [
    product("KD Drywall Frame", "frame", "Three-piece hollow metal drywall frame for interior stud-wall openings.", ["drywall frame", "interior stud wall", "commercial door", "frame"], price=160, fire_rating="Up to 90 minutes"),
    product("KD Masonry Frame", "frame", "Knocked-down masonry frame for interior or exterior masonry wall openings.", ["masonry opening", "masonry frame", "frame", "commercial door", "fire rated"], price=160, fire_rating="Up to 3 hours"),
    product("Welded Metal Frame", "frame", "Welded hollow metal frame for interior or exterior wall openings.", ["welded frame", "masonry opening", "commercial door", "fire rated"], price=191, fire_rating="Up to 3 hours"),
    product("Cased Opening Frame", "frame", "Traffic or cased opening frame for double-acting, sliding, bifold, or no-door openings.", ["cased opening", "traffic door", "sliding door", "bifold", "frame"], price=168, fire_rating="Not stated"),
    product("Hollow Metal Borrowed Lite Frame", "frame", "Four-sided borrowed lite frame for glass openings without doors.", ["borrowed lite", "glass opening", "frame", "interior", "exterior"], price=300, fire_rating="Optional up to 45 minutes"),
    product("Hollow Metal Sidelite Frame", "frame", "Hollow metal sidelite frame for door openings with one or two sidelites.", ["sidelite", "glass sidelite", "frame with sidelite", "door opening"], price=0, fire_rating="Optional up to 90 minutes"),
    product("Hollow Metal Transom Frame", "frame", "Hollow metal transom frame that can combine with sidelites.", ["transom", "sidelite", "borrowed lite", "frame"], price=0, fire_rating="Optional up to 45 minutes"),
    product("Double Egress Hollow Metal Frame", "frame", "Cross-corridor double egress frame for hospitals, schools, nursing homes, and smoke-control corridors.", ["double egress", "hospital corridor", "school corridor", "cross-corridor", "smoke corridor"], price=0, fire_rating="Up to 3 hours"),
    product("Commercial Wood Door with Louver", "door", "Interior commercial wood door with vandal-resistant Y-blade louver.", ["wood door with louver", "airflow opening", "interior", "commercial"], price=305, fire_rating="Not stated"),
    product("Commercial Wood Door with Glass", "door", "Interior commercial wood door with lite kit and glass options.", ["wood door with glass", "wood door with lite", "interior", "office", "commercial door"], price=305, fire_rating="Optional 20 minutes"),
    product("Fire-Rated Mineral Core Wood Doors", "door", "Fire-rated mineral core wood door for corridors, offices, closets, storage, stairwells, and mechanical rooms.", ["wood door", "fire rated", "stair enclosure", "corridor", "rated opening"], price=660, fire_rating="45/60/90 minutes"),
    product("Stain Grade Solid Core Wood Doors", "door", "Stain-grade solid core wood door for commercial offices and architectural interiors.", ["wood door", "solid core", "office", "interior"], price=290, fire_rating="Optional 20 minutes"),
    product("Prefinished Solid Core Wood Doors", "door", "Factory-finished stained wood door for commercial interiors and office buildings.", ["wood door", "prefinished", "office", "interior"], price=385, fire_rating="Optional 20 minutes"),
    product("Paint Grade Primed MDF Solid Core Wood Door", "door", "Paint-grade MDF/HDF solid core wood door for cost-sensitive commercial interiors.", ["wood door", "paint grade", "interior", "commercial"], price=205, fire_rating="Optional 20 minutes"),
    product("Double Doors - Hollow Metal Pairs", "door", "Hollow metal pair for commercial, industrial, and institutional double-door openings.", ["double doors", "hollow metal pair", "egress", "commercial door", "fire rated"], price=780, fire_rating="Optional up to 3 hours"),
    product("Metal Building Doors", "door", "Embossed insulated steel door for exterior commercial and metal building openings.", ["metal building", "exterior opening", "commercial", "hospitality", "steel door"], price=1084, fire_rating="Optional up to 3 hours"),
    product("2-Panel Embossed Hollow Metal Door", "door", "Two-panel embossed steel door for commercial and hospitality openings.", ["embossed hollow metal", "commercial", "hospitality", "steel door"], price=800, fire_rating="Optional up to 3 hours"),
    product("6-Panel Embossed Hollow Metal Door", "door", "Six-panel embossed hollow metal door for decorative commercial steel openings.", ["embossed hollow metal", "commercial", "steel door"], price=450, fire_rating="Optional up to 3 hours"),
    product("Hollow Metal Door with Louver", "door", "Hollow metal door with louver for commercial, industrial, and institutional airflow openings; live page should be revalidated.", ["hollow metal door with louver", "airflow opening", "commercial", "industrial"], price=470, fire_rating="Optional up to 3 hours"),
    product("Hollow Metal Door with Lite Kit & Glass", "door", "Hollow metal steel door with glass lite kit and fire-rated glazing options.", ["hollow metal door with glass", "rated door lite", "steel door", "glass"], price=480, fire_rating="Optional up to 3 hours"),
    product("Fire-Rated Metal Door", "door", "Fire-rated steel door for commercial and industrial rated openings.", ["commercial door", "fire rated", "egress", "stair enclosure", "rated opening"], price=350, fire_rating="Up to 3 hours"),
    product("Flush Commercial Hollow Metal Doors", "door", "General purpose flush hollow metal door for commercial, industrial, and institutional openings.", ["flush hollow metal", "commercial door", "industrial", "institutional"], price=327, fire_rating="Not stated"),
    product("Spartan 18PS Series Hollow Metal Door", "door", "Stock 18-gauge galvanneal steel hollow metal door made in the USA.", ["stock steel door", "hollow metal", "commercial opening"], price=395, fire_rating="UL 3 label"),
]


HARDWARE_CATALOG = [
    product("700 Series Heavy Duty Door Closer", "closer", "Premium adjustable door closer with multiple finishes.", ["closer", "commercial door", "door closer"], price=105),
    product("600 Series Heavy Duty Door Closer", "closer", "Grade 1 door closer listed for fire-door use up to 3 hours.", ["fire rated", "fire door", "egress", "commercial door", "school exit", "closer"], price=77, fire_rating="UL/ULC up to 3 hours"),
    product("800 Series Heavy Duty Door Closer", "closer", "Premium grade adjustable door closer with multiple finishes.", ["closer", "commercial door", "heavy duty"], price=116),
    product("900 Series Heavy Duty Door Closer", "closer", "Grade 1 cast steel closer with adjustable size 1-6 and backcheck.", ["closer", "fire rated", "school exit", "heavy duty", "egress"], price=169, fire_rating="UL/ULC up to 3 hours"),
    product("H4545 Series Plain Bearing Hinge", "hinge", "Square-corner plain bearing hinge furnished with metal and wood screws.", ["hinge", "plain bearing", "commercial door"], price=38),
    product("H4545 Series Ball Bearing Hinge", "hinge", "Ball bearing 4.5 x 4.5 hinge for heavier or higher-frequency commercial doors.", ["hinge", "heavy steel door", "high frequency", "commercial door", "ball bearing"], price=42),
    product("Tell Spring Hinge", "hinge", "Full mortise spring hinge with square corners.", ["spring hinge", "self closing", "commercial door", "hinge"], price=33),
    product("ML1300 Series Cortland Heavy Duty Mortise Lock", "lock", "Grade 1 heavy-duty mortise lock with advanced security features.", ["mortise lock", "lockset", "heavy duty", "commercial"], price=187),
    product("LC2600 Series Cortland Standard Duty Lock", "lock", "Grade 2 cylindrical lock with Schlage C keyway and ASA strike.", ["cylindrical lock", "lockset", "commercial"], price=62),
    product("LC2400 Series Cortland Heavy Duty Lock", "lock", "Grade 2 cylindrical lock with freewheeling clutch.", ["cylindrical lock", "lockset", "commercial"], price=51),
    product("LC1200 Series Cortland Heavy Duty Lock", "lock", "Grade 1 ADA-compliant cylindrical lock listed for 3-hour fire doors.", ["lockset", "hospital patient room", "ada hardware", "fire rated", "cylindrical lock"], price=71, fire_rating="UL listed for 3-hour fire door"),
    product("KC2300 Series Empire Heavy Duty Lock", "lock", "Grade 2 cylindrical lock with ASA strike and Schlage C keyway.", ["lockset", "cylindrical lock", "commercial"], price=52),
    product("DB2000 Series Grade 2 Standard Duty Deadbolt", "deadbolt", "Grade 2 standard duty deadbolt with adjustable backset.", ["deadbolt", "lock", "commercial"], price=37),
    product("DB1000 Series Grade 1 Heavy Duty Deadbolt", "deadbolt", "Grade 1 heavy-duty deadbolt.", ["deadbolt", "lock", "heavy duty"], price=147),
    product("Accentra 2100 Series Rim Exit Device", "exit device", "Grade 1 heavy-duty rim exit device for panic and fire-rated applications.", ["egress", "exit", "panic hardware", "panic hardware for exit", "exit device", "double doors", "fire rated"], price=1000, fire_rating="Optional up to 3-hour doors"),
    product("8300A Heavy Duty Rim Device 48 Inch", "exit device", "Grade 1 rim exit device for 28 to 36 inch doors with trim options.", ["egress", "exit", "panic hardware", "exit device", "double doors"], price=151, fire_rating="UL/ULC listed"),
    product("QCL140-E-626 Privacy Lever Lock", "lock", "Grade 1 privacy cylindrical lever lock with fire-rated latches.", ["privacy lock", "lever lock", "hospital patient room", "ada hardware"], price=259, fire_rating="Fire-rated latches"),
    product("QCL130-E-626 Passage Lever Set", "lock", "Grade 1 passage cylindrical lever set with fire-rated latches.", ["passage lock", "lever lock", "commercial", "ada hardware"], price=216.5, fire_rating="Fire-rated latches"),
    product("Schlage ALX10 SAT Saturn Grade-2 Passage Lever", "lock", "Grade 2 passage lever lock listed for use on 3-hour fire doors and ADA-compliant designs.", ["passage lock", "lever lock", "ada hardware", "fire rated"], price=129.6, fire_rating="UL listed for use on 3-hour fire doors"),
]

SOLUTION_FAMILIES = [
    product("Rim Exit Device", "exit device", "Panic or fire exit hardware family for egress doors.", ["egress", "exit", "panic hardware", "exit device", "commercial door"]),
    product("Surface Door Closer", "closer", "Self-closing hardware family for commercial and rated doors.", ["fire rated", "fire door", "egress", "commercial door", "closer"]),
    product("Automatic Door Operator", "operator", "Automatic opening support family for accessible public entrances.", ["accessible route", "entrance", "ada", "hospital entrance", "automatic operator", "operator"]),
]


CODE_FRAMEWORK = [
    {"source_or_code_family": "ICC Digital Codes / Codes by Location", "type": "jurisdiction portal", "covers": "State, county, and city code adoption and amendments.", "typical_questions": ["state code lookup", "city amendments", "adopted edition"], "source_url": "https://codes.iccsafe.org/"},
    {"source_or_code_family": "Model code: IBC Chapter 10 Means of Egress", "type": "model code", "covers": "Door swing, egress, panic hardware, locking arrangements, and exit access conditions.", "typical_questions": ["Do I need panic hardware?", "Must the door swing out?", "Can this lock on egress?"], "source_url": "https://codes.iccsafe.org/content/IBC2021P2/chapter-10-means-of-egress"},
    {"source_or_code_family": "ADA 2010 Standards Chapter 4 / Section 404", "type": "federal accessibility standard", "covers": "Accessible routes, clear width, maneuvering clearances, hardware controls, and automatic doors.", "typical_questions": ["Does this opening need ADA compliance?", "Is an operator required?", "Are revolving doors allowed?"], "source_url": "https://www.access-board.gov/ada/"},
    {"source_or_code_family": "ADA Guide: Chapter 4 Entrances, Doors, and Gates", "type": "federal guidance", "covers": "Plain-language guidance for accessible entrances and manual or automatic doors.", "typical_questions": ["How many entrances must be accessible?", "What clearances are needed?"], "source_url": "https://www.access-board.gov/ada/guides/chapter-4-entrances-doors-and-gates/"},
    {"source_or_code_family": "ICC A117.1 / state accessibility code", "type": "accessibility standard", "covers": "Technical accessibility dimensions adopted by many states through IBC.", "typical_questions": ["Maneuvering clearances", "thresholds", "reach ranges"], "source_url": "https://codes.iccsafe.org/"},
    {"source_or_code_family": "ANSI/BHMA A156 family", "type": "product standard", "covers": "Hardware performance, grade, and operation standards.", "typical_questions": ["Is this product grade 1?", "Which operator standard applies?"], "source_url": "https://buildershardware.com/"},
    {"source_or_code_family": "School / education overlay sources", "type": "program-specific", "covers": "Education occupancy agency, fire marshal, district, and AHJ requirements.", "typical_questions": ["School exit doors", "classroom locks", "lockdown hardware"], "source_url": "https://codes.iccsafe.org/codes/united-states"},
]


LOCAL_CODE_SCHEMA = [
    {"field_name": "zip", "type": "string", "required": True, "description": "User-entered ZIP used to resolve city/county/state and likely AHJ."},
    {"field_name": "state_code", "type": "string", "required": True, "description": "Two-letter state code."},
    {"field_name": "city", "type": "string", "required": False, "description": "Resolved city from ZIP or user entry."},
    {"field_name": "county", "type": "string", "required": False, "description": "Resolved county from ZIP or GIS."},
    {"field_name": "jurisdiction_name", "type": "string", "required": True, "description": "Display name for code answer."},
    {"field_name": "adopted_building_code", "type": "string", "required": True, "description": "Primary building code currently in force."},
    {"field_name": "building_code_source_url", "type": "url", "required": True, "description": "Official adoption/source page."},
    {"field_name": "adopted_fire_code", "type": "string", "required": False, "description": "Fire code if separate from building code."},
    {"field_name": "fire_code_source_url", "type": "url", "required": False, "description": "Official fire code source."},
    {"field_name": "accessibility_code", "type": "string", "required": False, "description": "Accessibility basis used in answer."},
    {"field_name": "accessibility_source_url", "type": "url", "required": False, "description": "Accessibility source."},
    {"field_name": "effective_date", "type": "date", "required": True, "description": "When local adoption became effective."},
    {"field_name": "edition_notes", "type": "string", "required": False, "description": "Free-text adoption nuance."},
    {"field_name": "local_amendments_url", "type": "url", "required": False, "description": "Municipal amendment page or code portal."},
    {"field_name": "ahj_contact", "type": "string", "required": False, "description": "Escalation contact if code conflict or ambiguity."},
    {"field_name": "last_verified_utc", "type": "datetime", "required": True, "description": "Freshness tracking for code lookup."},
]


INTENTS = [
    {"intent": "applicable_code_lookup", "required_entities": ["state", "city", "ZIP", "building type", "new vs existing"], "expected_output": "Return governing code stack and exact adoption source."},
    {"intent": "door_type_recommendation", "required_entities": ["building type", "location", "interior/exterior", "rating", "traffic", "material preference"], "expected_output": "Recommend viable door families and note exclusions."},
    {"intent": "hardware_allowance", "required_entities": ["door type", "rating", "occupancy", "use case", "access control"], "expected_output": "Recommend permitted hardware families with conditions."},
    {"intent": "egress_analysis", "required_entities": ["occupancy", "occupant load", "path of egress", "lock type"], "expected_output": "Explain swing, unlatching, panic/fire exit hardware, and exceptions."},
    {"intent": "fire_rating_analysis", "required_entities": ["wall type", "barrier type", "opening location", "occupancy"], "expected_output": "Determine likely rating path and list missing data."},
    {"intent": "accessibility_analysis", "required_entities": ["accessible route", "entrance type", "user controls", "thresholds"], "expected_output": "Explain ADA/A117.1 implications."},
    {"intent": "maglock_analysis", "required_entities": ["door type", "egress path", "occupancy", "access control intent", "rating"], "expected_output": "Return allow, conditionally allow, or not recommended with code path."},
    {"intent": "delayed_egress_analysis", "required_entities": ["occupancy", "patient/security use case", "sprinkler/alarm status"], "expected_output": "Explain when delayed egress may be permitted."},
    {"intent": "sliding_door_analysis", "required_entities": ["location", "occupancy", "accessible route", "egress function"], "expected_output": "Assess sliding, pocket, bifold, or storefront sliders."},
    {"intent": "automatic_operator_recommendation", "required_entities": ["entrance type", "accessible route", "user population", "power access"], "expected_output": "Recommend low-energy, full-power, or manual with rationale."},
    {"intent": "product_match", "required_entities": ["door type", "hardware type", "finish", "rating", "brand preference"], "expected_output": "Map requirement to matching website products."},
    {"intent": "code_section_navigation", "required_entities": ["resolved jurisdiction", "code family", "section number"], "expected_output": "Open exact code section and highlight relevant answer excerpt."},
    {"intent": "lead_capture", "required_entities": ["conversation stage", "intent value", "user engagement score"], "expected_output": "Collect email/phone without hard-blocking first answer."},
    {"intent": "quote_handoff", "required_entities": ["selected products", "jurisdiction", "contact details", "project notes"], "expected_output": "Package transcript and selected products for sales follow-up."},
]


LEAD_FLOW = [
    {"stage": "low-friction first answer", "trigger": "User asks first question", "behavior": "Give helpful answer summary immediately; do not hard-block before any value.", "crm_write": False},
    {"stage": "jurisdiction precision gate", "trigger": "User wants exact code or city/state answer", "behavior": "Request state and ZIP before exact local-code answer.", "crm_write": False},
    {"stage": "lead capture soft gate", "trigger": "User wants detailed recommendations, saved result, or quote", "behavior": "Ask for email and phone before full detailed package or downloadable result.", "crm_write": True},
    {"stage": "consent / opt-in", "trigger": "Before CRM write", "behavior": "Store consent language and timestamp.", "crm_write": True},
    {"stage": "quote handoff", "trigger": "User asks for price, quote, or product package", "behavior": "Package transcript, selected products, jurisdiction, and contact info for sales follow-up.", "crm_write": True},
    {"stage": "fallback", "trigger": "User refuses contact info", "behavior": "Continue limited chat with generic guidance; maintain goodwill.", "crm_write": False},
]


SEED_QA = [
    ("What doors and hardware are required for a hospital main entrance?", "applicable_code_lookup; door_type_recommendation; accessibility_analysis", "hospital", "main entrance", ["state + ZIP", "new vs existing", "automatic door preference"], "Door/entrance package + operator + panic/hardware + code links", True, False),
    ("What code applies to a school entrance in my state?", "applicable_code_lookup", "school", "main entrance", ["state or ZIP"], "Jurisdiction stack + exact source URLs", True, False),
    ("Can I use a magnetic lock on this type of door?", "maglock_analysis", "general", "egress door", ["jurisdiction", "occupancy", "fire rating", "egress path"], "Conditional allow / not allow + alternatives", True, True),
    ("Does this opening require handicap access?", "accessibility_analysis", "general", "opening", ["accessible route", "entrance/interior", "state/ZIP"], "Plain-language yes/no + missing data", False, False),
    ("Do I need an automatic operator on a hospital entrance door?", "automatic_operator_recommendation", "hospital", "public entrance", ["state/ZIP", "entrance count", "new vs existing"], "Manual vs low-energy vs full-power recommendation", True, False),
    ("Can a school exit door have a classroom function lock?", "hardware_allowance; egress_analysis", "school", "exit/classroom", ["jurisdiction", "door use", "lockdown intent"], "Allowed hardware families + warning flags", True, True),
    ("What fire rating does this corridor door need in a hospital?", "fire_rating_analysis", "hospital", "corridor opening", ["barrier type", "smoke/fire barrier", "jurisdiction"], "Rating path + ask for wall type if missing", True, True),
    ("Is a sliding door allowed at a school entrance?", "sliding_door_analysis", "school", "main entrance", ["jurisdiction", "accessible route", "egress function"], "Allow / not preferred + conditions", True, True),
    ("What kind of exit device can I use on a pair of steel doors?", "hardware_allowance", "general", "double doors", ["fire rating", "occupancy", "exterior/interior"], "Recommended device families + website matches", False, False),
    ("Can I use delayed egress at a memory care unit?", "delayed_egress_analysis", "healthcare", "secured unit", ["jurisdiction", "sprinkler/alarm status"], "Conditional answer + AHJ review note", True, True),
    ("What door frame should I use for a masonry opening?", "product_match", "general", "frame", ["wall type", "interior/exterior", "rating"], "Website frame options + pros/cons", False, False),
    ("What is the best door for a metal building opening?", "product_match", "general", "exterior opening", ["fire rating", "width/height", "finish"], "Website options + configuration notes", False, False),
    ("Can I put glass in a fire-rated steel door?", "fire_rating_analysis", "general", "rated door lite", ["jurisdiction", "rating", "glass size"], "Yes with listed glazing/size limits if permitted", False, True),
    ("Does an outpatient clinic restroom door need ADA hardware?", "accessibility_analysis", "healthcare", "restroom", ["jurisdiction", "new vs existing"], "ADA hardware and closer guidance", False, False),
    ("What products on your site fit a 90-minute corridor pair?", "product_match", "general", "rated pair", ["door size", "frame", "hardware need"], "Matched product list", True, False),
    ("Can I use a maglock and a panic bar together?", "maglock_analysis; hardware_allowance", "general", "egress door", ["jurisdiction", "occupancy", "rating"], "Conditional integration answer + listed hardware note", True, True),
    ("What code section covers door clear width?", "code_section_navigation", "general", "accessible route", ["jurisdiction or code family"], "Exact section + excerpt", False, False),
    ("How many public entrances must be accessible?", "accessibility_analysis", "general", "entrances", ["new vs existing"], "At least 60% in new construction + caveats", False, False),
    ("Can I use a double egress frame in a hospital corridor?", "door_type_recommendation", "hospital", "corridor", ["fire/smoke barrier info"], "Likely yes + smoke/egress caveats", True, True),
    ("What hinge should I use for a heavy steel door?", "product_match", "general", "hinge selection", ["door weight", "frequency", "closer", "exterior/interior"], "Recommended hinge rows from website", False, False),
    ("What closer is best for a rated school exit door?", "product_match", "school", "exit door", ["door size", "exterior/interior", "rating"], "600 vs 900 series guidance", False, False),
    ("Can I use a wood door on a rated stair enclosure?", "fire_rating_analysis", "general", "stair door", ["required rating", "jurisdiction"], "Probably only within allowed rating; metal for 3 hr", True, True),
    ("What lockset should I use for a hospital patient room?", "hardware_allowance; product_match", "hospital", "patient room", ["privacy", "corridor", "staff access"], "Lockset family + caveats", True, True),
    ("Can a revolving door serve as the accessible entrance?", "accessibility_analysis", "general", "public entrance", ["new vs existing"], "No; separate compliant door required", False, False),
    ("What information do you need before giving an exact answer?", "applicable_code_lookup", "general", "meta", [], "State/ZIP, building type, space type, rated/nonrated, access control intent, new/existing", False, False),
    ("Show me all frame options for a glass sidelite opening", "product_match", "general", "frame with sidelite", ["wall type", "rating"], "Website frame options table", False, False),
    ("Can I use panic hardware on a balanced door?", "egress_analysis", "general", "balanced door", ["jurisdiction", "occupancy"], "Explain push-pad requirement when panic hardware required", True, True),
    ("Do patient room doors need latch-side clearance?", "accessibility_analysis", "hospital", "patient room", ["new vs existing"], "Explain special maneuvering exception", False, False),
    ("What products fit a commercial wood door with glass?", "product_match", "general", "wood door with lite", ["rating", "finish", "hardware"], "Website product row + hardware suggestions", False, False),
    ("Can I electrify this fire-rated opening?", "hardware_allowance; fire_rating_analysis", "general", "rated opening", ["device type", "door/frame labels", "jurisdiction"], "Conditional allow + listed components only", True, True),
]


def build_seed_qa() -> list[dict[str, Any]]:
    return [
        {
            "id": f"seed-{index:03d}",
            "user_question": row[0],
            "primary_intent": row[1],
            "building_type": row[2],
            "space_type": row[3],
            "must_ask_for": row[4],
            "recommended_output": row[5],
            "need_email_phone": row[6],
            "escalate_to_human": row[7],
        }
        for index, row in enumerate(SEED_QA, start=1)
    ]


def build_knowledge_snippets(seed_qa: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snippets = [
        {"title": "Dataset Implementation Note", "source": DATASET_PDF.name, "content": "The training dataset is a structured starter dataset, not a replacement for official or licensed jurisdictional code text. Include this caveat for local code lookup and exact jurisdiction answers.", "tags": ["code", "jurisdiction", "local code", "applicable_code_lookup"]},
        {"title": "ZIP-Based Local Code Resolution", "source": DATASET_PDF.name, "content": "For questions like what code applies in my ZIP, local-code precision requires resolving ZIP to city, county, and state, then checking state adoption plus city or county amendments.", "tags": ["zip", "city", "county", "state", "jurisdiction", "applicable_code_lookup"]},
        {"title": "Product Recommendation Conditions", "source": DATASET_PDF.name, "content": "Product recommendations should be conditioned on occupancy, egress role, fire rating, accessibility path, and local amendments.", "tags": ["product_match", "hardware_allowance", "egress", "fire_rating", "accessibility"]},
        {"title": "Hospital Main Entrance Seed Case", "source": DATASET_PDF.name, "content": "For a hospital main entrance, ask for state and ZIP, new versus existing work, and automatic-door preference; cover IBC, NFPA, ADA, accessible entrance count, likely operator, storefront or entrance options, panic hardware, and code links.", "tags": ["hospital", "main entrance", "automatic_operator_recommendation", "accessibility_analysis", "applicable_code_lookup"]},
        {"title": "Maglock Seed Case", "source": DATASET_PDF.name, "content": "For magnetic locks, ask for jurisdiction, occupancy, fire rating, and egress-path role; answer should cover permissibility, release method, listed components, and fallback options.", "tags": ["maglock", "maglock_analysis", "access control", "egress", "fire rating"]},
        {"title": "Masonry Frame Seed Case", "source": DATASET_PDF.name, "content": "For a masonry opening, compare KD masonry frames and welded frames, and ask for wall type, interior or exterior use, and required rating.", "tags": ["masonry", "frame", "product_match", "kd masonry frame", "welded frame"]},
        {"title": "Fire-Rated Lite Seed Case", "source": DATASET_PDF.name, "content": "Glass in a fire-rated steel door may be possible only with listed glazing, label-compatible components, size limits, rating confirmation, and jurisdiction review.", "tags": ["fire_rating_analysis", "rated door", "glass", "lite", "steel door"]},
        {"title": "Lead Flow", "source": DATASET_PDF.name, "content": "The chatbot should give a helpful first answer without hard blocking, ask for state and ZIP for exact local code, and request email and phone for quotes, saved results, or detailed recommendation packages.", "tags": ["lead_capture", "quote_handoff", "email", "phone", "quote"]},
    ]

    for item in seed_qa:
        title = item["user_question"].rstrip("?")
        snippets.append(
            {
                "title": f"Seed QA: {title}",
                "source": DATASET_PDF.name,
                "content": (
                    f"Question: {item['user_question']} Intent: {item['primary_intent']}. "
                    f"Must ask for: {', '.join(item['must_ask_for']) or 'none'}. "
                    f"Recommended output: {item['recommended_output']}."
                ),
                "tags": [
                    *[intent.strip() for intent in item["primary_intent"].split(";")],
                    item["building_type"],
                    item["space_type"],
                ],
            }
        )

    return snippets


def write_json(file_name: str, data: Any) -> None:
    path = PROCESSED_DIR / file_name
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if not DATASET_PDF.exists():
        raise FileNotFoundError(f"Dataset PDF not found: {DATASET_PDF}")

    reader = PdfReader(DATASET_PDF)
    extracted_pages = [(page.extract_text() or "") for page in reader.pages]
    if len(reader.pages) < 20 or not any("Seed Q&A" in page for page in extracted_pages):
        raise ValueError("Dataset PDF did not look like the expected United Doors training dataset.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    seed_qa = build_seed_qa()
    products = DOOR_CATALOG + HARDWARE_CATALOG + SOLUTION_FAMILIES
    knowledge_snippets = build_knowledge_snippets(seed_qa)
    chunks = [
        {
            "id": f"chunk-{index:03d}",
            "title": snippet["title"],
            "source": snippet["source"],
            "content": snippet["content"],
            "tags": snippet["tags"],
        }
        for index, snippet in enumerate(knowledge_snippets, start=1)
    ]

    write_json("products.json", products)
    write_json("hardware.json", HARDWARE_CATALOG)
    write_json("code_framework.json", CODE_FRAMEWORK)
    write_json("local_code_schema.json", LOCAL_CODE_SCHEMA)
    write_json("intents.json", INTENTS)
    write_json("lead_flow.json", LEAD_FLOW)
    write_json("seed_qa.json", seed_qa)
    write_json("knowledge_snippets.json", knowledge_snippets)
    write_json("knowledge_chunks.json", chunks)

    print(
        json.dumps(
            {
                "pdf_pages": len(reader.pages),
                "products": len(products),
                "door_catalog": len(DOOR_CATALOG),
                "hardware_catalog": len(HARDWARE_CATALOG),
                "solution_families": len(SOLUTION_FAMILIES),
                "intents": len(INTENTS),
                "seed_qa": len(seed_qa),
                "knowledge_chunks": len(chunks),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
