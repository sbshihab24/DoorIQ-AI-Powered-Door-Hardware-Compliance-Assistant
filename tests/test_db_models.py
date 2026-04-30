from app.db.models import ChatMessage, ChatSession, Lead
from app.db.session import Base


def test_db_metadata_includes_chat_and_lead_tables() -> None:
    assert set(Base.metadata.tables) >= {
        "chat_sessions",
        "chat_messages",
        "leads",
    }


def test_chat_session_relationships_are_configured() -> None:
    assert ChatSession.messages.property.mapper.class_ is ChatMessage
    assert ChatSession.leads.property.mapper.class_ is Lead


def test_chat_message_and_lead_reference_chat_session() -> None:
    chat_message_foreign_keys = {
        foreign_key.column.table.name
        for foreign_key in ChatMessage.__table__.c.session_id.foreign_keys
    }
    lead_foreign_keys = {
        foreign_key.column.table.name
        for foreign_key in Lead.__table__.c.session_id.foreign_keys
    }

    assert chat_message_foreign_keys == {"chat_sessions"}
    assert lead_foreign_keys == {"chat_sessions"}
