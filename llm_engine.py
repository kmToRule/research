import os
import json
from dotenv import load_dotenv
from chunker import chunk_text
from nlp_utils import find_sentences_with_keywords, clean_sentence

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# ---------------- LOCAL SIGNAL EXTRACTOR ---------------- #

def extract_signals_local(text):

    positives_kw = [
        "strong demand", "growth", "expansion", "order visibility",
        "margin improvement", "opportunity", "improving"
    ]

    concerns_kw = [
        "working capital", "receivable", "risk", "delay",
        "pressure", "uncertain", "challenge"
    ]

    guidance_kw = ["guidance", "expect", "outlook", "trajectory"]
    capacity_kw = ["capacity", "utilization", "committed"]
    growth_kw = ["expansion", "new", "initiative", "integration", "investment"]

    return {
        "positives": find_sentences_with_keywords(text, positives_kw),
        "concerns": find_sentences_with_keywords(text, concerns_kw),
        "guidance": find_sentences_with_keywords(text, guidance_kw, 3),
        "capacity": find_sentences_with_keywords(text, capacity_kw, 2),
        "growth": find_sentences_with_keywords(text, growth_kw, 3)
    }


# ---------------- LOCAL AGGREGATOR ---------------- #

def clean_list(sentences, limit):
    out = []
    for s in sentences:
        cs = clean_sentence(s)
        if cs:
            out.append(cs)
        if len(out) >= limit:
            break
    return out


def local_pipeline(full_text):
    chunks = chunk_text(full_text)

    all_pos, all_con = [], []
    all_guidance, all_capacity, all_growth = [], [], []

    for ch in chunks:
        sig = extract_signals_local(ch)

        all_pos += sig["positives"]
        all_con += sig["concerns"]
        all_guidance += sig["guidance"]
        all_capacity += sig["capacity"]
        all_growth += sig["growth"]

    # ---- Clean + Deduplicate ----
    positives = list(dict.fromkeys([p.lower() for p in all_pos]))
    concerns = list(dict.fromkeys([c.lower() for c in all_con]))

    positives = positives[:5]
    concerns = concerns[:5]

    growth_text = [
        g for g in list(dict.fromkeys(all_growth))
        if len(g.split()) > 6
    ][:3]


    if not positives:
        positives = ["No clear positive signals detected"]

    if not concerns:
        concerns = ["No major concerns highlighted"]

    # ---- Tone ----
    if len(positives) >= 3 and len(positives) > len(concerns):
        tone = "Optimistic"
    elif len(concerns) >= 3 and len(concerns) > len(positives):
        tone = "Cautious"
    elif len(positives) >= 1:
        tone = "Slightly Positive"
    else:
        tone = "Neutral"

    # ---- Confidence ----
    signal_count = len(positives) + len(concerns)
    if signal_count >= 7:
        confidence = "High"
    elif signal_count >= 4:
        confidence = "Medium"
    else:
        confidence = "Low"

    # ---- Guidance ----
    guidance_clean = clean_list(all_guidance, 3)

    revenue_g = guidance_clean[0] if len(guidance_clean) > 0 else "No explicit revenue guidance"
    margin_g = guidance_clean[1] if len(guidance_clean) > 1 else "No explicit margin guidance"
    capex_g = guidance_clean[2] if len(guidance_clean) > 2 else "No explicit capex guidance"

    # ---- Capacity ----
    capacity_clean = clean_list(all_capacity, 1)
    capacity_text = capacity_clean[0] if capacity_clean else "Capacity trend not clearly mentioned"

    # ---- Growth ----
    if not growth_text:
        growth_text = ["No clear growth initiatives detected"]

    return {
        "management_tone": tone,
        "confidence_level": confidence,
        "key_positives": positives,
        "key_concerns": concerns,
        "forward_guidance": {
            "revenue": revenue_g,
            "margin": margin_g,
            "capex": capex_g
        },
        "capacity_utilization": capacity_text,
        "growth_initiatives": growth_text,
        "mode": "LOCAL_ADVANCED"
    }


# ---------------- OPENAI PRODUCTION PIPELINE ---------------- #

def openai_pipeline(full_text):
    from openai import OpenAI
    print("API KEY LOADED:", bool(api_key))
    client = OpenAI(api_key=api_key)
    print("OPENAI CALL MADE")

    MAX_CHUNKS = 12   # safety cap
    chunks = chunk_text(full_text)[:MAX_CHUNKS]

    insights = []

    for ch in chunks:
        PROMPT = """
You are a professional equity research analyst.

ONLY extract information EXPLICITLY present in the transcript.
DO NOT assume, infer, or hallucinate anything.

If a section is missing, return: "Not mentioned in transcript".

Ignore:
- Moderator speech
- Greetings / thanks
- Q&A noise
- Disclaimers
- Irrelevant discussion

Return STRICT JSON:

{
 "tone": "optimistic / cautious / neutral / pessimistic",
 "positives": [],
 "concerns": [],
 "guidance_revenue": "",
 "guidance_margin": "",
 "guidance_capex": "",
 "capacity_trend": "",
 "initiatives": []
}

Rules:
- Keep points SHORT (1 sentence max)
- Investor-focused only
- No long text
- No explanations
"""



        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": PROMPT + ch}],
                temperature=0
            )

            content = response.choices[0].message.content.strip()

            # --- Remove ```json ``` wrapper if present ---
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()

            try:
                insights.append(json.loads(content))
            except Exception as e:
                print("JSON PARSE ERROR AFTER CLEAN:", content)


        except:
            continue

    if not insights:
        return local_pipeline(full_text)

    # ---- Aggregate ----
    tone_counts = {}
    pos, con, init = [], [], []
    rev, mar, cap, capu = [], [], [], []

    for ins in insights:
        t = ins.get("tone", "Neutral")
        tone_counts[t] = tone_counts.get(t, 0) + 1

        pos += ins.get("positives", [])
        con += ins.get("concerns", [])
        init += ins.get("initiatives", [])

        if ins.get("guidance_revenue"):
            rev.append(ins["guidance_revenue"])
        if ins.get("guidance_margin"):
            mar.append(ins["guidance_margin"])
        if ins.get("guidance_capex"):
            cap.append(ins["guidance_capex"])
        if ins.get("capacity_trend"):
            capu.append(ins["capacity_trend"])

    final_tone = max(tone_counts, key=tone_counts.get)

    return {
        "management_tone": final_tone.lower(),

        "confidence_level": "high",

        "key_positives": list(dict.fromkeys(pos))[:5] or ["Not clearly mentioned"],

        "key_concerns": list(dict.fromkeys(con))[:5] or ["Not clearly mentioned"],

        "forward_guidance": {
            "revenue": rev[0] if rev else "Not mentioned in transcript",
            "margin": mar[0] if mar else "Not mentioned in transcript",
            "capex": cap[0] if cap else "Not mentioned in transcript"
        },

        "capacity_utilization": capu[0] if capu else "Not mentioned in transcript",

        "growth_initiatives": list(dict.fromkeys(init))[:3] or ["Not mentioned in transcript"],

        "mode": "OPENAI_PRODUCTION"
    }



# ---------------- HYBRID CONTROLLER ---------------- #

def analyze_transcript(text,mode):

    if mode.startswith("LOCAL"):
        return local_pipeline(text)

    if mode.startswith("OPENAI"):
        if not api_key:
            return local_pipeline(text)
        return openai_pipeline(text)

    # AUTO MODE
    if not api_key:
        return local_pipeline(text)

    try:
        return openai_pipeline(text)
    except:
        return local_pipeline(text)
