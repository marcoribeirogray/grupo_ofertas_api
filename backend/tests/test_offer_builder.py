from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.offer_builder import build_offer_text, ensure_default_template


def create_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return TestingSession()


def test_build_offer_text_default_structure():
    session = create_session()
    ensure_default_template(session)
    metadata = {
        "title": "Produto Exemplo",
        "store": "amazon",
        "price": "R$ 199,90",
        "price_original": "R$ 249,90",
        "benefits": ["• Frete grátis", "• Entrega rápida"],
    }
    text, context = build_offer_text(
        session=session,
        metadata=metadata,
        affiliate_url="https://exemplo.com",
        coupon="PROMO",
        template_slug=None,
        overrides={},
    )
    assert "Produto Exemplo" in text
    assert "PROMO" in text
    assert "👉" in text
    assert context["short_url"].startswith("https://go.example/")
