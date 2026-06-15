# tests/test_tools.py
from unittest.mock import MagicMock, patch

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_empty_wardrobe


# ── shared fixture ────────────────────────────────────────────────────────────

SAMPLE_ITEM = {
    "id": "lst_001",
    "title": "Y2K Baby Tee",
    "description": "Cute baby tee with butterfly print.",
    "category": "tops",
    "style_tags": ["y2k", "vintage"],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": ["white", "pink"],
    "brand": None,
    "platform": "depop",
}


# ── search_listings ───────────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_no_results():
    """Failure mode: no listings match — returns empty list, no exception."""
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


# ── suggest_outfit ────────────────────────────────────────────────────────────

def test_suggest_outfit_empty_wardrobe():
    """Failure mode: empty wardrobe — LLM is still called for general advice,
    but result is prefixed with 'Error message:' so the agent surfaces it as an error."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Try pairing it with high-waisted jeans and sneakers."

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("tools._get_groq_client", return_value=mock_client):
        result = suggest_outfit(SAMPLE_ITEM, get_empty_wardrobe())

    assert isinstance(result, str)
    assert result.startswith("Error message:")
    mock_client.chat.completions.create.assert_called_once()


# ── create_fit_card ───────────────────────────────────────────────────────────

def test_create_fit_card_empty_outfit():
    """Failure mode: outfit string is empty — returns hardcoded error string, no LLM call."""
    result = create_fit_card("", SAMPLE_ITEM)
    assert result.startswith("Error message:")


def test_create_fit_card_whitespace_outfit():
    """Failure mode: outfit string is whitespace-only — same guard catches it."""
    result = create_fit_card("   ", SAMPLE_ITEM)
    assert result.startswith("Error message:")
