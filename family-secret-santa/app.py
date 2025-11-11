import streamlit as st
import json
import random
import os

# === CONFIGURATION ===
PARTICIPANTS = [
    "Emme", "Zack", "Natalie", "Sam", "Laura", "Kirk",
    "Erin", "Dave", "Adrienne", "Caleb", "Ellie",
    "Maggie", "Joe", "Amber"
]

# Group restrictions
GROUP_1 = {"Ellie", "Adrienne", "Dave", "Erin", "Caleb"}
GROUP_2 = {"Natalie", "Emme", "Sam", "Laura", "Kirk", "Zack"}
GROUP_3 = {"Amber", "Maggie", "Joe"}

# === FILE STORAGE ===
HISTORY_FILE = "secret_santa_history.json"

# Load past assignments (2023–2024)
PAST_ASSIGNMENTS = {
    "2023": {
        "Ellie": "Sam", "Dave": "Laura", "Joe": "Zack", "Zack": "Caleb",
        "Sam": "Erin", "Kirk": "Adrienne", "Erin": "Kirk", "Maggie": "Emme",
        "Emme": "Joe", "Natalie": "Dave", "Laura": "Maggie",
        "Amber": "Ellie", "Adrienne": "Amber", "Caleb": "Natalie"
    },
    "2024": {
        "Natalie": "Ellie", "Dave": "Emme", "Emme": "Amber",
        "Adrienne": "Sam", "Ellie": "Zack", "Caleb": "Kirk",
        "Erin": "Natalie", "Maggie": "Erin", "Sam": "Maggie",
        "Zack": "Adrienne", "Laura": "Caleb", "Amber": "Dave",
        "Kirk": "Joe", "Joe": "Laura"
    }
}

# Load history (create file if not present)
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)
else:
    history = {}

# Merge static past assignments
history.update(PAST_ASSIGNMENTS)

# === FUNCTION: Get allowed recipients ===
def get_allowed_recipients(giver):
    if giver in GROUP_1:
        return {"Natalie", "Emme", "Joe", "Amber", "Maggie", "Sam", "Zack", "Laura", "Kirk"}
    elif giver in GROUP_2:
        return {"Ellie", "Adrienne", "Erin", "Dave", "Amber", "Maggie", "Joe", "Caleb"}
    elif giver in GROUP_3:
        return {"Natalie", "Emme", "Sam", "Zack", "Laura", "Kirk", "Caleb", "Ellie", "Adrienne", "Erin", "Dave"}
    else:
        return set(PARTICIPANTS)

# === FUNCTION: Generate new year ===
def generate_new_year(history):
    current_year = max(map(int, history.keys())) + 1 if history else 2025
    used_pairs = {(giver, rec) for year in history.values() for giver, rec in year.items()}
    
    # Try random permutations until valid
    for _ in range(100000):
        receivers = random.sample(PARTICIPANTS, len(PARTICIPANTS))
        assignment = dict(zip(PARTICIPANTS, receivers))
        if all(
            giver != rec and
            (giver, rec) not in used_pairs and
            rec in get_allowed_recipients(giver)
            for giver, rec in assignment.items()
        ):
            history[str(current_year)] = assignment
            with open(HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=2)
            return current_year, assignment
    return None, None

# === STREAMLIT UI ===
st.title("🎅 Family Secret Santa Generator")

if st.button("🎁 Generate Next Year's Assignments"):
    year, new_assignments = generate_new_year(history)
    if year:
        st.success(f"✅ Generated Secret Santa assignments for {year}!")
        for giver, rec in new_assignments.items():
            st.write(f"**{giver} ➜ {rec}**")
    else:
        st.error("⚠️ Could not generate a valid assignment after many attempts.")

if history:
    st.subheader("📜 Past Assignments")
    for year in sorted(history.keys(), reverse=True):
        with st.expander(f"{year}"):
            for giver, rec in history[year].items():
                st.write(f"{giver} → {rec}")