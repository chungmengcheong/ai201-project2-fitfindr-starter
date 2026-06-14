
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

A sequential flow calls the tools in order : search_listing -> suggest_outfit -> create_fit_card. Wrapped around each tool call is if-else logic to handle results from the tool and manage state.  

###Pseudocode - Planning Loop:

```
initialize session with _new_session()

#parse user query
parse user query using LLM to extract description, size and max price (see below for details)
store result in session["parsed"]

#search listing
get search_results with search_listings(session["parsed"])
if search_results
    store search_results in session["search_results"]
else
    set session["error"]
    return

#choose item to use
select top result from session["search_results"] and store in session["selected_item"]  

##suggest outfit
load wardrobe
get suggested_outfit with suggest_outfit(session["selected_item"], wardrobe)
if suggested_outfit does not start with "Error message:"  ## "Error message:" is a hardcoded prefix, not LLM output
    store result in session["outfit_suggestion"]
else
    set session["error"] to suggested_outfit
    return session

#create fit card
get fit_card with create_fit_card(session["outfit_suggestion"], 
  session["selected_item"])
if fit_card does not start with "Error message:"  ## "Error message:" is a hardcoded prefix, not LLM output
    store result in session["fit_card"]
else
    set session["error"] to fit_card
    return session

return session
```

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
| search_listings | No results match the query | Agent given response “There are no matching listings from the loaded listings. Prompt user to try a different search query.” |
| suggest_outfit | Wardrobe is empty | Call LLM for general styling advice — not an error, flow continues normally. |
| create_fit_card | Outfit input is missing or incomplete | Agent given response "Inform user that provided items does not make up a complete outfit. Mentioned what items are missing, e.g., 'missing a top'. Ask user to try again.” |

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
      V
planning loop 
    agent.py
        - initializes state management with_new_session)                    
        - run planning loop with run_agent()  <--------------------------   |
      |                                                                     |
      V                                                                     |
    tools.py                                                                |
        - search_listings(session["parsed"])                                |
        - store results in session["search_results"]                        |
        - if error, set session["error"] -----------------------------------|
      |                                                                     |
      V                                                                     |
    tools.py                                                                |
        - suggest_outfit(                                                   |
            session["selected_item"],                                      |
            session["wardrobe"])                                           |
        - store results in session["outfit_suggestion"]                     |
        - if error, set session["error"] -----------------------------------|        
      |                                                                     |
      V                                                                     |
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

I’ll work through each tool in sequence -- going in the order of search_listings >  suggest_outfit > create_fit_card. 

For each tool, I’ll prompt the AI with the specific section for the tool and architecture flow in planning.md. 

I'll sanity-check the generated code that it:
- search_listings: filters by all parameters and handles empty-results case
- suggest_outfit: returns sensible items and handles empty wardrobe input
- create_fit_card: returns a snappy caption (not product description) and handle missing outfit input  


**Milestone 4 — Planning loop and state management:**

I’ll prompt the AI with the sections on planning loop and state management. 

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Description:** FitFindr helps users find matching outfit items. The agent orchestrates a set of tools in response to a natural language request — searching listings, evaluating fit against an existing wardrobe, and generating a shareable outfit description. It fails gracefully when if given missing or incomplete information by providing helpful generic suggestions. 

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 0:**
```
parse_user_query("I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?")
```

returns:
```
{
    "description": "vintage graphic tee",
    "size": None,
    "max_price": 30.0
}
```

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
```
search_listings(description: "vintage graphic tee", "size": None, "max_price": 30)
```

returns:
```
[
  {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": ["y2k", "vintage", "graphic tee", "cottagecore"],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.00,
    "colors": ["white", "pink", "purple"],
    "brand": null,
    "platform": "depop"
  }, 
   {
    "id": "lst_006",
    "title": "Graphic Tee — 2003 Tour Bootleg Style",
    "description": "Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.",
    "category": "tops",
    "style_tags": ["graphic tee", "vintage", "grunge", "streetwear", "band tee"],
    "size": "L",
    "condition": "good",
    "price": 24.00,
    "colors": ["black"],
    "brand": null,
    "platform": "depop"
  },
    {
    "id": "lst_033",
    "title": "Vintage Band Tee — Faded Grey",
    "description": "Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.",
    "category": "tops",
    "style_tags": ["vintage", "grunge", "band tee", "graphic tee", "streetwear"],
    "size": "L",
    "condition": "fair",
    "price": 19.00,
    "colors": ["grey", "charcoal"],
    "brand": null,
    "platform": "depop"
  },
  {
    "id": "lst_003",
    "title": "Oversized Flannel Shirt — Plaid Red/Black",
    "description": "Classic oversized flannel. Great layering piece. A few tiny pulls in the fabric but nothing visible when worn.",
    "category": "tops",
    "style_tags": ["grunge", "vintage", "flannel", "streetwear", "layering"],
    "size": "XL (oversized)",
    "condition": "good",
    "price": 22.00,
    "colors": ["red", "black"],
    "brand": "Woolrich",
    "platform": "thredUp"
  },
    {
    "id": "lst_012",
    "title": "Oversized Crewneck Sweatshirt — Vintage Navy",
    "description": "Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.",
    "category": "tops",
    "style_tags": ["vintage", "basics", "oversized", "classic"],
    "size": "XL (fits oversized)",
    "condition": "good",
    "price": 20.00,
    "colors": ["navy"],
    "brand": null,
    "platform": "thredUp"
  },
    {
    "id": "lst_013",
    "title": "90s Silk Slip Dress — Floral, Midi Length",
    "description": "Delicate 90s slip dress in a muted floral print. Midi length, adjustable straps. Light snag on the side seam — not visible when worn.",
    "category": "bottoms",
    "style_tags": ["90s", "vintage", "feminine", "floral", "cottagecore"],
    "size": "M",
    "condition": "good",
    "price": 30.00,
    "colors": ["ivory", "dusty pink", "green"],
    "brand": null,
    "platform": "depop"
  },
  {
    "id": "lst_014",
    "title": "Leather Belt — Brown, Braided",
    "description": "Genuine leather braided belt. Adjustable, multiple holes. Classic Western buckle. Can be dressed up or down.",
    "category": "accessories",
    "style_tags": ["vintage", "western", "classic", "earth tones"],
    "size": "One Size (adjustable)",
    "condition": "excellent",
    "price": 12.00,
    "colors": ["brown"],
    "brand": null,
    "platform": "thredUp"
  },
  {
    "id": "lst_015",
    "title": "Vintage Graphic Hoodie — Faded Black",
    "description": "Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.",
    "category": "tops",
    "style_tags": ["vintage", "grunge", "graphic", "streetwear"],
    "size": "L",
    "condition": "fair",
    "price": 26.00,
    "colors": ["black", "charcoal"],
    "brand": null,
    "platform": "depop"
  },
    {
    "id": "lst_016",
    "title": "High-Waisted Denim Shorts — Cutoff",
    "description": "DIY cutoff denim shorts from Levi's 501s. Raw hem, slightly frayed. High-waisted. Perfect summer length.",
    "category": "bottoms",
    "style_tags": ["vintage", "denim", "summer", "classic"],
    "size": "W27",
    "condition": "good",
    "price": 24.00,
    "colors": ["light blue", "blue"],
    "brand": "Levi's",
    "platform": "poshmark"
  },
    {
    "id": "lst_020",
    "title": "Henley Long Sleeve — Washed Burgundy",
    "description": "Soft washed henley in a rich burgundy. Three-button placket. Slightly shrunken/cropped fit. 100% cotton.",
    "category": "tops",
    "style_tags": ["vintage", "basics", "earth tones", "classic"],
    "size": "M",
    "condition": "excellent",
    "price": 16.00,
    "colors": ["burgundy", "wine"],
    "brand": null,
    "platform": "thredUp"
  },
    {
    "id": "lst_021",
    "title": "Straight Leg Khaki Trousers — Olive",
    "description": "Olive straight-leg trousers. High-waisted, with a center crease. Lightweight material, great for transitional weather.",
    "category": "bottoms",
    "style_tags": ["earth tones", "classic", "minimal", "vintage"],
    "size": "W30",
    "condition": "excellent",
    "price": 29.00,
    "colors": ["olive", "green"],
    "brand": null,
    "platform": "poshmark"
  },
    {
    "id": "lst_024",
    "title": "Vintage Polo Shirt — Forest Green",
    "description": "Classic polo in forest green. Short sleeve, ribbed collar. Slightly boxy. The kind of piece that goes with everything.",
    "category": "tops",
    "style_tags": ["vintage", "preppy", "classic", "earth tones"],
    "size": "M",
    "condition": "good",
    "price": 18.00,
    "colors": ["green", "forest green"],
    "brand": "Ralph Lauren",
    "platform": "thredUp"
  },
    {
    "id": "lst_027",
    "title": "Oversized College Crewneck — Faded Red",
    "description": "Classic college-style crewneck in a beautifully faded red. No school name — just a plain athletic crewneck. Roomy fit.",
    "category": "tops",
    "style_tags": ["vintage", "athletic", "oversized", "classic"],
    "size": "XL",
    "condition": "good",
    "price": 21.00,
    "colors": ["red", "faded red"],
    "brand": null,
    "platform": "thredUp"
  },
    {
    "id": "lst_029",
    "title": "Silk Button-Down — Sage Green",
    "description": "Loose silk (feel) button-down in sage green. Long sleeve, can be worn open as a layer or fully buttoned. Very flowy.",
    "category": "tops",
    "style_tags": ["vintage", "minimal", "earth tones", "cottagecore"],
    "size": "M",
    "condition": "excellent",
    "price": 28.00,
    "colors": ["sage", "green"],
    "brand": null,
    "platform": "depop"
  },
    {
    "id": "lst_030",
    "title": "Vintage Knit Vest — Argyle Brown/Cream",
    "description": "Classic argyle knit vest in brown and cream. Fits medium. V-neck. Ideal for the dark academia or preppy vintage aesthetic.",
    "category": "tops",
    "style_tags": ["vintage", "preppy", "knitwear", "dark academia", "earth tones"],
    "size": "M",
    "condition": "good",
    "price": 25.00,
    "colors": ["brown", "cream", "tan"],
    "brand": null,
    "platform": "thredUp"
  },
    {
    "id": "lst_034",
    "title": "Bucket Hat — Reversible, Brown Plaid",
    "description": "Reversible bucket hat — plaid on one side, solid tan on the other. Unstructured brim. One size fits most.",
    "category": "accessories",
    "style_tags": ["90s", "streetwear", "vintage", "accessories"],
    "size": "One Size",
    "condition": "excellent",
    "price": 14.00,
    "colors": ["brown", "tan", "plaid"],
    "brand": null,
    "platform": "thredUp"
  },
    {
    "id": "lst_037",
    "title": "Straight Leg Black Jeans — Faded",
    "description": "Faded black straight-leg jeans. Sits at the hips, classic fit. Slightly cropped length. No rips, just natural fading.",
    "category": "bottoms",
    "style_tags": ["vintage", "classic", "grunge", "denim"],
    "size": "W28",
    "condition": "good",
    "price": 30.00,
    "colors": ["black", "faded black"],
    "brand": "Levi's",
    "platform": "thredUp"
  },
    {
    "id": "lst_038",
    "title": "Denim Vest — Medium Wash, Studded",
    "description": "Denim vest with silver stud detailing along the collar and pockets. Classic rock-inspired customization. Fits like a medium.",
    "category": "outerwear",
    "style_tags": ["grunge", "vintage", "denim", "customized", "rock"],
    "size": "M",
    "condition": "good",
    "price": 27.00,
    "colors": ["medium blue"],
    "brand": null,
    "platform": "depop"
  },
]
```

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
```
session["selected_item"] = 
  {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": ["y2k", "vintage", "graphic tee", "cottagecore"],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.00,
    "colors": ["white", "pink", "purple"],
    "brand": null,
    "platform": "depop"
  }, 
```

```
suggest_outfit(session["selected_item"], wardrobe)
```

returns: 
```
"Pair your vintage graphic tee with your baggy straight-leg jeans, dark wash and chunky white sneakers"
```

**Step 3:**
<!-- Continue until the full interaction is complete -->
```
session["outfit_suggestion"] = "Wear your vintage graphic tee with your baggy straight-leg jeans, dark wash and chunky white sneakers"
```

```
create_fit_card(session["outfit_suggestion"], session["selected_item"]]
```
returns
```
"When you need to channel the early Millenium energy"
```


**Final output to user:**
<!-- What does the user actually see at the end? -->
```
Top listing found
    Y2K Baby Tee — Butterfly Print
    $18.00 · depop · Size S/M
    Condition: excellent
    Style: y2k, vintage, graphic tee, cottagecore

    Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.

Outfit idea
    Wear your vintage graphic tee with your baggy straight-leg jeans, dark wash and chunky white sneakers

Your fit card
    When you need to channel the early Millenium energy