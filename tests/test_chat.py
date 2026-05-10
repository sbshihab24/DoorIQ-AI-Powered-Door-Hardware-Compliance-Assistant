from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import ChatMessage, ChatSession, Lead
from app.main import app


client = TestClient(app)


def test_chat_returns_placeholder_response() -> None:
    response = client.post("/chat", json={"message": "Do I need panic hardware?"})

    assert response.status_code == 200

    data = response.json()
    assert data["session_id"]
    assert data["intent"] == "egress"
    assert data["answer"]
    assert data["confidence"] == "low"
    assert data["human_review_recommended"] is True
    assert data["missing_information"] == [
        "occupancy",
        "occupant_load",
        "path_of_egress",
        "lock_type",
    ]


def test_chat_returns_product_recommendations_for_application() -> None:
    response = client.post(
        "/chat",
        json={
            "message": "What hardware do I need?",
            "building": {"application": "egress door"},
        },
    )

    assert response.status_code == 200

    data = response.json()
    product_names = [product["name"] for product in data["recommended_products"]]
    assert "Accentra 2100 Series Rim Exit Device" in product_names
    assert "600 Series Heavy Duty Door Closer" in product_names
    assert data["missing_information"] == [
        "rating",
        "occupancy",
        "use_case",
        "access_control",
    ]


def test_chat_returns_dataset_knowledge_references() -> None:
    response = client.post(
        "/chat",
        json={
            "message": "What code applies to a school entrance in my state?",
            "building": {"application": "main entrance"},
            "location": {"state": "TX"},
        },
    )

    assert response.status_code == 200

    data = response.json()
    reference_titles = [
        reference["title"] for reference in data["knowledge_references"]
    ]
    assert "Dataset Implementation Note" in reference_titles


def test_chat_persists_session_and_messages(db_session: Session) -> None:
    response = client.post(
        "/chat",
        json={
            "message": "What hardware do I need?",
            "building": {
                "building_type": "office",
                "application": "egress door",
            },
            "location": {
                "state": "TX",
                "zip_code": "75001",
            },
        },
    )

    assert response.status_code == 200
    session_id = response.json()["session_id"]

    chat_session = db_session.get(ChatSession, session_id)
    messages = (
        db_session.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id)
        .all()
    )

    assert chat_session is not None
    assert chat_session.building_type == "office"
    assert chat_session.application == "egress door"
    assert chat_session.state == "TX"
    assert chat_session.zip_code == "75001"
    assert messages[0].role == "user"
    assert messages[0].content == "What hardware do I need?"
    assert messages[1].role == "assistant"
    assert messages[1].content == response.json()["answer"]
    assert "Dataset guidance:" in messages[1].content


def test_chat_extracts_lead_from_conversation(db_session: Session) -> None:
    response = client.post(
        "/chat",
        json={
            "message": (
                "Please send me pricing for a 90-minute corridor pair. "
                "My name is Brian Lee and my email is brian@example.com."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["should_capture_lead"] is True
    assert data["lead_capture_status"]["email_collected"] is True
    assert data["lead_capture_status"]["lead_created"] is True

    chat_session = db_session.get(ChatSession, data["session_id"])
    lead = (
        db_session.query(Lead)
        .filter(Lead.session_id == data["session_id"])
        .one()
    )
    assert chat_session.email == "brian@example.com"
    assert chat_session.lead_name == "Brian Lee"
    assert chat_session.project_context["fire_rating_minutes"] == 90
    assert lead.email == "brian@example.com"
    assert lead.name == "Brian Lee"


def test_chat_remembers_project_factors_across_turns(db_session: Session) -> None:
    first_response = client.post(
        "/chat",
        json={
            "message": "I need an interior hollow metal door for a school corridor.",
        },
    )
    assert first_response.status_code == 200
    session_id = first_response.json()["session_id"]

    second_response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "It is 90 minute rated and high traffic.",
        },
    )

    assert second_response.status_code == 200
    chat_session = db_session.get(ChatSession, session_id)
    assert chat_session.building_type == "school"
    assert chat_session.project_context["application"] == "corridor opening"
    assert chat_session.project_context["fire_rating_minutes"] == 90
    assert chat_session.project_context["traffic"] == "high traffic"
    assert chat_session.project_context["material_preference"] == "hollow metal"


def test_chat_reuses_existing_session(db_session: Session) -> None:
    first_response = client.post("/chat", json={"message": "Do I need panic hardware?"})
    session_id = first_response.json()["session_id"]

    second_response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Can I use a maglock too?",
        },
    )

    assert second_response.status_code == 200
    assert second_response.json()["session_id"] == session_id

    messages = (
        db_session.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id)
        .all()
    )

    assert [message.role for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]


def test_chat_uses_follow_up_context_to_reduce_missing_information(
    db_session: Session,
) -> None:
    first_response = client.post(
        "/chat",
        json={"message": "Can I use a maglock on this egress door?"},
    )
    session_id = first_response.json()["session_id"]

    second_response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "It is a fire-rated hospital corridor in Texas ZIP 77002.",
        },
    )

    assert second_response.status_code == 200
    data = second_response.json()
    assert data["session_id"] == session_id
    assert data["intent"] == "access_control"
    assert data["missing_information"] == []

    chat_session = db_session.get(ChatSession, session_id)
    assert chat_session is not None
    assert chat_session.building_type == "hospital"
    assert chat_session.application == "hospital corridor"
    assert chat_session.state == "TX"
    assert chat_session.zip_code == "77002"
    assert chat_session.fire_rating_required is True
    assert chat_session.is_egress_path is True


def test_chat_suggests_door_families_after_school_corridor_details(
    db_session: Session,
) -> None:
    first_response = client.post(
        "/chat",
        json={"message": "I need help with doors for a school corridor renovation."},
    )
    session_id = first_response.json()["session_id"]

    client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "it is interior design",
        },
    )
    third_response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "fire rating of 60 mins",
        },
    )

    assert third_response.status_code == 200
    answer = third_response.json()["answer"]
    assert "interior school corridor" in answer
    assert "Possible products:" in answer
    assert "Fire-Rated Metal Door" in answer
    assert "Commercial Wood Door with Louver" not in answer
    assert "https://uniteddoorsandlocks.com/products/" in answer
    assert "What wall or barrier is this opening in" in answer


def test_chat_returns_links_when_user_asks_for_suggestion_links(
    db_session: Session,
) -> None:
    first_response = client.post(
        "/chat",
        json={"message": "I need help with doors for a school corridor renovation."},
    )
    session_id = first_response.json()["session_id"]

    for message in ["interior", "fire rate if 90 mins", "light"]:
        client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": message,
            },
        )

    link_response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "where are suggestions link",
        },
    )

    answer = link_response.json()["answer"]
    assert "interior school corridor" in answer
    assert "Possible products:" in answer
    assert "https://uniteddoorsandlocks.com/products/" in answer


def test_chat_returns_product_links_after_wall_context_completes_recommendation(
    db_session: Session,
) -> None:
    first_response = client.post(
        "/chat",
        json={"message": "I need help with doors for a school corridor renovation."},
    )
    session_id = first_response.json()["session_id"]

    for message in ["interior", "fire rate of 90 mins", "corridor wall"]:
        response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": message,
            },
        )

    answer = response.json()["answer"]
    assert "interior school corridor" in answer
    assert "Recommended products:" in answer
    assert "https://uniteddoorsandlocks.com/products/" in answer
    assert "Nothing else for a first-pass recommendation" in answer


def test_chat_accepts_fire_barrier_as_wall_context(
    db_session: Session,
) -> None:
    first_response = client.post(
        "/chat",
        json={"message": "I need help with doors for a school corridor renovation."},
    )
    session_id = first_response.json()["session_id"]

    for message in ["interior", "60 mins", "fire barrier"]:
        response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": message,
            },
        )

    answer = response.json()["answer"]
    assert "interior school corridor" in answer
    assert "Recommended products:" in answer
    assert "https://uniteddoorsandlocks.com/products/" in answer
    assert "What wall or barrier is this opening in" not in answer
    assert "Nothing else for a first-pass recommendation" in answer


def test_chat_captures_contact_details_and_creates_lead(
    db_session: Session,
) -> None:
    first_response = client.post(
        "/chat",
        json={"message": "Can I get a quote for this egress hardware?"},
    )
    session_id = first_response.json()["session_id"]

    second_response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "My email is brian@example.com and phone is 555-123-4567.",
        },
    )

    assert second_response.status_code == 200
    data = second_response.json()
    assert data["lead_capture_status"] == {
        "email_collected": True,
        "phone_collected": True,
        "lead_created": True,
    }

    chat_session = db_session.get(ChatSession, session_id)
    leads = db_session.query(Lead).filter(Lead.session_id == session_id).all()

    assert chat_session is not None
    assert chat_session.email == "brian@example.com"
    assert chat_session.phone == "555-123-4567"
    assert len(leads) == 1
    assert leads[0].email == "brian@example.com"
    assert leads[0].phone == "555-123-4567"
