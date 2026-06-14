
# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

For reference, a listing dict is an one item/listing, e.g., 
  {
    "id": "lst_001",
    "title": "Vintage Levi's 501 Jeans — Medium Wash",
    "description": "Classic 501s in a perfect medium wash. Some light fading at the knees which adds to the vintage look. No rips or stains.",
    "category": "bottoms",
    "style_tags": ["vintage", "classic", "denim", "streetwear"],
    "size": "W30 L30",
    "condition": "good",
    "price": 38.00,
    "colors": ["blue", "indigo"],
    "brand": "Levi's",
    "platform": "depop"
  },

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Returns a set of matching listing dicts, sorted by keyword relevance (best match first). Uses provided size and max_price to filter out listings.  

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): keywords describing what the user is looking for (e.g., "vintage graphic tee" 
- `size` (str): Size string to filter by, e.g., ("M", "W28"). Defaults to None. 
- `max_price` (float): maximum price (inclusive), eg. 50.00. Defaults to None. 

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
- result (list[dict]): listings (dict) that matches the user query

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
Returns None


---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Suggests 1 complete outfit when provided an item and wardrobe. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): a listing 
- `wardrobe` (dict): user’s wardrobe (schema is documented in wardrobe_schema.json)

**What it returns:**
<!-- Describe the return value -->
- result (str): LLM generated suggestion of matching items. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
- if `wardrobe[“items”]` is empty: call the LLM for general styling advice (what types of items pair well, what vibe it suits). Does not return an error — the flow continues to create_fit_card.
  

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Creates a catchy social media caption describing a provided outfit. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): LLM-generated outfit suggestion from suggest_outfit 
- `new_item` (dict): a listing 

**What it returns:**
<!-- Describe the return value -->
- result (str) : LLM generated text describing the outfit, e.g., “when you're feeling the 70s disco energy”  

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
The method code (not the LLM) checks whether `outfit` is empty or whitespace before calling the LLM and returns this hardcoded string directly:
- if `outfit` is empty or whitespace: `”Error message: No outfit suggestion provided. Ask user to try again.”`

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

###Logic:

A sequential flow calls the tools in order : search_listing -> suggest_outfit -> create_fit_card. Wrap around each tool call is if-else logic to handle results from the tool.  

###Pseudocode - Planning Loop:

initialize session with _new_session()
##parse user query
parse user query using LLM to extract description, size and max price (see below for details)
store result in session["parsed"]
##search listing
get search_results with search_listings(session["parsed"])
if search_results
    store search_results in session["search_results"]
else
    set session["error"]
    return
##choose item to use
select top result from session["search_results"] and store in session["selected_item"]  
##suggest outfit
load wardrobe
get suggested_outfit with suggest_outfit(session["selected_item"], wardrobe)
if suggested_outfit does not start with "Error message:"  ## "Error message:" is a hardcoded prefix, not LLM output
    store result in session["outfit_suggestion"]
else
    set session["error"] to suggested_outfit
    return session
##create fit card
get fit_card with create_fit_card(session["outfit_suggestion"], 
  session["selected_item"])
if fit_card does not start with "Error message:"  ## "Error message:" is a hardcoded prefix, not LLM output
    store result in session["fit_card"]
else
    set session["error"] to fit_card
    return session
return session

###LLM prompt to parse user query
```
Extract the exact description keywords, size, and max price from the user query {session["query"]}
The result should be a string that can be loaded as a python dictionary with json.loads():
    {"description": (str),
    "size": (str),
    "max_price": (float)
    }
If a field is not in the query, set it to 'null'. 

##Examples:
"vintage graphic tee under $30" returns {"description": "vintage graphic tee", "size": null, "max_price": 30} 
"black combat boots size 8" returns {"description": "black combat boots", "size": "8", "max_price": null}
"designer ballgown size XXS under $5" returns {"description": "designer ballgown", "size": "XXS", "max_price": 5}
```

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

Session state is maintained by the harness run_agent(), which stores state in a 'session' variable (dict). 

The appropriate arguments are extracted from 'session' and passed into the tool calls, and the results from the tool calls are saved into 'session'.   


---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | “There are no matching listings from the loaded listings. Prompt user to try a different search query.” |
| suggest_outfit | Wardrobe is empty | Call LLM for general styling advice — not an error, flow continues normally. |
| create_fit_card | Outfit input is missing or incomplete | "Inform user that provided items does not make up a complete outfit. Mentioned what items are missing, e.g., 'missing a top'. Ask user to try again.” |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

user input
    app.py 
        - builds interface with build_interface()
        - gets user query with handle_query()
      |
      |
planning loop 
    agent.py
        - initializes state management with_new_session)                    
        - run planning loop with run_agent()  <--------------------------   |
      |                                                                     |
      |                                                                     |
    tools.py                                                                |
        - search_listings(session["parsed"])                                |
        - store results in session["search_results"]                        |
        - if error, set session["error"] -----------------------------------|
      |                                                                     |
      |                                                                     |
    tools.py                                                                |
        - suggest_outfit(                                                   |
            session["selected_item"],                                      |
            session["wardrobe"])                                           |
        - store results in session["outfit_suggestion"]                     |
        - if error, set session["error"] -----------------------------------|        
      |                                                                     |
      |                                                                     |
    tools.py                                                                |
        - create_fit_card(session["outfit_suggestion"],                    |
            session["selected_item"])                                      |
        - store results in session["fit_card"]                              |
        - if error, set session["error"] -----------------------------------| 
      |                                                                     |
      |----------------------------------------------------------------------


A global configuration file (config.py) holds global paranerera such as LLM model. 

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

I’ll use Claude Code to help me implement the code. 

**Milestone 3 — Individual tool implementations:**

I’ll work through each tool in sequence -- going in the order of search_listings >  suggest_outfit > create_fit_card -- and doing manual testing after each implemention. 

For each tool, I’ll prompt the AI with the specific section and architecture flow in planning.md. 

**Milestone 4 — Planning loop and state management:**

I’ll prompt the AI with the sections on planning loop and state management. 

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 0:**
parse_user_query("I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?")

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
search_listings("vintage graphic tee", "size": None, "max_price": 30)

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
suggest_outfit(session["selected_item"], wardrobe)

**Step 3:**
<!-- Continue until the full interaction is complete -->
create_fit_card(session["outfit_suggestion"], session["selected_item"]]

**Final output to user:**
<!-- What does the user actually see at the end? -->
"Giving off the early millenial vibe" 