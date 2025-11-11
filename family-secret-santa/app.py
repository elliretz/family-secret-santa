import json
import random
import os
import streamlit as st

# --- CONFIG ---
DATA_FILE = "previous_years.json"

# --- PARTICIPANTS ---
participants = [
    "Emme", "Zack", "Natalie", "Sam", "Laura", "Kirk",
    "Erin", "Dave", "Adrienne", "Caleb", "Ellie", "Maggie", "Joe", "Amber"
]

# --- BUILT-IN PREVIOUS YEARS (through 2024 only) ---
default_previous_years = {
    "2023": {
        "Ellie": "Sam",
        "Dave": "Laura",
        "Joe": "Zack",
        "Zack": "Caleb",
        "Sam": "Erin",
        "Kirk": "Adrienne",
        "Erin": "Kirk",
        "Maggie": "Emme",
        "Emme": "Joe",
        "Natalie": "Dave",
        "Laura": "Maggie",
        "Amber": "Ellie",
        "Adrienne": "Amber",
        "Caleb": "Natalie"
    },
    "2024": {
        "Natalie": "Ellie",
        "Dave": "Emme",
        "Emme": "Amber",
        "Adrienne": "Sam",
        "Ellie": "Zack",
        "Caleb": "Kirk",
        "Erin": "Natalie",
        "Maggie": "Erin",
        "Sam": "Maggie",
        "Zack": "Adrienne",
        "Laura": "Caleb",
        "Amber": "Dave",
        "Kirk": "Joe",
        "Joe": "Laura"
    }
}

# --- LOAD EXISTING FILE OR DEFAULT DATA ---
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        previous_years = json.load(f)
else:
    previous_years = default_previous_years

# --- RESTRICTIONS ---
restricted_groups = {
    "group1": ["Ellie", "Adrienne", "Dave", "Erin", "Caleb"],
    "group2": ["Natalie", "Emme", "Sam", "Laura", "Kirk", "Zack"],
    "group3": ["Amber", "Maggie", "Joe"],
}

restrictions = {}
for name in participants:
    if name in restricted_groups["group1"]:
        restrictions[name] = ["Natalie", "Emme", "Joe", "Amber", "Maggie", "Sam", "Zack", "Laura", "Kirk"]
    elif name in restricted_groups["group2"]:
        restrictions[name] = ["Ellie", "Adrienne", "Erin", "Dave", "Amber", "Maggie", "Joe", "Caleb"]
    else:
        restrictions[name] = ["Natalie", "Emme", "Sam", "Zack", "Laura", "Kirk", "Caleb", "Ellie", "Adrienne", "Erin", "Dave"]

# --- VALIDATION ---
def valid_assignment(assignments, prev_years):
    for giver, receiver in assignments.items():
        if giver == receiver:
            return False
        if receiver not in restrictions[giver]:
            return False
        for year in prev_years.values():
            if giver in year and year[giver] == receiver:
                return False
    return True


# --- GENERATOR ---
def generate_assignment(prev_years):
    givers = participants.copy()
    receivers = participants.copy()
    for _ in range(10000):
        random.shuffle(receivers)
        assignments = dict(zip(givers, receivers))
        if valid_assignment(assignments, prev_years):
            return assignments
    return None


# --- STREAMLIT UI ---
st.set_page_config(page_title="🎁 Family Secret Santa", layout="centered")
st.title("🎄 Family Secret Santa Generator")

current_year = st.number_input("Enter the year to generate for:", min_value=2025, max_value=2100, step=1)

if str(current_year) in previous_years:
    st.warning(f"Assignments for {current_year} are already locked in.")
    st.json(previous_years[str(current_year)])
else:
    if st.button("🎲 Generate New Secret Santa"):
        assignments = generate_assignment(previous_years)
        if assignments:
            st.session_state["new_assignments"] = assignments
            st.success("✅ New Secret Santa list generated!")
            st.json(assignments)
        else:
            st.error("❌ Could not generate a valid assignment. Try again or check restrictions.")

    if "new_assignments" in st.session_state:
        if st.button("🔒 Confirm and Lock In This Year"):
            previous_years[str(current_year)] = st.session_state["new_assignments"]
            with open(DATA_FILE, "w") as f:
                json.dump(previous_years, f, indent=2)
            st.success(f"🎉 Secret Santa assignments for {current_year} have been saved!")
