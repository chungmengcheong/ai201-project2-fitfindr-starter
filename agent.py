"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import json

from tools import search_listings, suggest_outfit, create_fit_card, _get_groq_client

# ── query parser ─────────────────────────────────────────────────────────────


def _parse_query(query: str) -> dict:
    """Use the LLM to extract description, size, and max_price from a natural language query."""
    client = _get_groq_client()
    prompt = (
        f'Extract the description keywords, size, and max price from this query: "{query}"\n'
        "Return a JSON object with exactly these fields: description (str), size (str or null), max_price (float or null).\n"
        "Examples:\n"
        '"vintage graphic tee under $30" → {"description": "vintage graphic tee", "size": null, "max_price": 30}\n'
        '"black combat boots size 8" → {"description": "black combat boots", "size": "8", "max_price": null}\n'
        '"designer ballgown size XXS under $5" → {"description": "designer ballgown", "size": "XXS", "max_price": 5}\n'
        "Return only the JSON object, nothing else."
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


# ── session state ─────────────────────────────────────────────────────────────


def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,  # original user query
        "parsed": {},  # extracted description / size / max_price
        "search_results": [],  # list of matching listing dicts
        "selected_item": None,  # top result, passed into suggest_outfit
        "wardrobe": wardrobe,  # user's wardrobe dict
        "outfit_suggestion": None,  # string returned by suggest_outfit
        "fit_card": None,  # string returned by create_fit_card
        "error": None,  # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """

    def print_session_state(session, step):
        """Helper function to print the current session state at each step for debugging."""
        print(f"\n=== After {step} ===")
        for key, value in session.items():
            if key == "search_results":
                print(f"{key} (count): {len(value)}")
            elif key == "wardrobe":
                print(f"{key} (item count): {len(session["wardrobe"]["items"])}")
            else:
                print(f"{key}: {value}")
        return

    # Step 1: initialize session
    session = _new_session(query, wardrobe)
    print_session_state(session, "step 1: initialize session")  # debug print

    # Step 2: parse query
    session["parsed"] = _parse_query(query)
    parsed = session["parsed"]

    print_session_state(session, "step 2: parse query")  # debug print

    # Step 3: search listings
    session["search_results"] = search_listings(
        parsed["description"],
        size=parsed.get("size"),
        max_price=parsed.get("max_price"),
    )
    if not session["search_results"]:
        session["error"] = (
            "No listings found matching your search. Try a different description, size, or price."
        )
        print_session_state(session, "step 3: search listing")  # debug print
        return session

    print_session_state(session, "step 3: search listing")  # debug print

    # Step 4: select top result
    session["selected_item"] = session["search_results"][0]

    print_session_state(session, "step 4: select top result")  # debug print

    # Step 5: suggest outfit
    outfit = suggest_outfit(session["selected_item"], session["wardrobe"])
    if outfit.startswith("Error message:"):
        session["error"] = outfit.removeprefix("Error message:").strip()
        print_session_state(session, "step 5: suggest outfit")  # debug print
        return session
    session["outfit_suggestion"] = outfit

    print_session_state(session, "step 5: suggest outft")  # debug print

    # Step 6: create fit card
    fit_card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
    if fit_card.startswith("Error message:"):
        session["error"] = fit_card.removeprefix("Error message:").strip()
        print_session_state(session, "step 6: create_fit_card")  # debug print
        return session
    session["fit_card"] = fit_card

    print_session_state(session, "step 6: create_fit_card")  # debug print

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
