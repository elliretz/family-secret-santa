
import json
import random
import os
import base64
from urllib.parse import quote

import requests
import streamlit as st

# ==================================================
# CONFIGURATION
# ==================================================

DATA_FILE = "previous_years.json"

# GitHub settings are configured through Streamlit Secrets.
# This allows confirmed assignments to be saved permanently.

# ==================================================
# PARTICIPANTS
# ==================================================

participants = [
    "Emme", "Zack", "Natalie", "Sam", "Laura", "Kirk",
    "Erin", "Dave", "Adrienne", "Caleb", "Ellie",
    "Maggie", "Joe", "Amber"
]

# ==================================================
# HISTORICAL ASSIGNMENTS
# ==================================================

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
    },

    "2025": {
        "Emme": "Ellie",
        "Zack": "Dave",
        "Natalie": "Erin",
        "Sam": "Caleb",
        "Laura": "Joe",
        "Kirk": "Maggie",
        "Erin": "Emme",
        "Dave": "Amber",
        "Adrienne": "Kirk",
        "Caleb": "Zack",
        "Ellie": "Natalie",
        "Maggie": "Laura",
        "Joe": "Adrienne",
        "Amber": "Sam"
    }
}

# ==================================================
# GITHUB PERMANENT STORAGE
# ==================================================

def github_settings():
    try:
        return {
            "token": st.secrets["GITHUB_TOKEN"],
            "repo": st.secrets["GITHUB_REPO"],
            "branch": st.secrets.get("GITHUB_BRANCH", "main"),
            "path": st.secrets.get("DATA_PATH", DATA_FILE)
        }
    except Exception:
        return None


def github_request(method, url, **kwargs):
    settings = github_settings()

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings['token']}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    return requests.request(
        method,
        url,
        headers=headers,
        timeout=20,
        **kwargs
    )


def load_previous_years():
    settings = github_settings()

    # GitHub storage is used when configured.
    if settings:
        encoded_path = quote(settings["path"], safe="/")

        url = (
            f"https://api.github.com/repos/"
            f"{settings['repo']}/contents/{encoded_path}"
            f"?ref={settings['branch']}"
        )

        response = github_request("GET", url)

        if response.status_code == 200:
            content = response.json()
            decoded = base64.b64decode(content["content"])
            saved_data = json.loads(decoded.decode("utf-8"))

            # Merge any missing built-in historical years.
            merged = default_previous_years.copy()
            merged.update(saved_data)

            return merged

        elif response.status_code == 404:
            # First launch: create the history file in GitHub.
            save_previous_years(default_previous_years)
            return default_previous_years.copy()

        else:
            st.error(
                "Could not load your saved assignments from GitHub. "
                f"GitHub returned: {response.status_code} "
                f"{response.text[:500]}"
            )
            st.stop()

    # Local fallback when running outside Streamlit Cloud.
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            saved_data = json.load(f)

        merged = default_previous_years.copy()
        merged.update(saved_data)
        return merged

    return default_previous_years.copy()


def save_previous_years(data):
    settings = github_settings()

    if settings:
        encoded_path = quote(settings["path"], safe="/")

        url = (
            f"https://api.github.com/repos/"
            f"{settings['repo']}/contents/{encoded_path}"
        )

        # Get the current file SHA if it already exists.
        response = github_request(
            "GET",
            url,
            params={"ref": settings["branch"]}
        )

        sha = None

        if response.status_code == 200:
            sha = response.json()["sha"]
        elif response.status_code != 404:
            raise Exception(
                f"Could not check GitHub file: {response.text[:500]}"
            )

        content = json.dumps(data, indent=2)
        encoded_content = base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8")

        payload = {
            "message": "Save Secret Santa assignments",
            "content": encoded_content,
            "branch": settings["branch"]
        }

        if sha:
            payload["sha"] = sha

        response = github_request("PUT", url, json=payload)

        if response.status_code not in (200, 201):
            raise Exception(
                f"Could not save to GitHub: {response.text[:500]}"
            )

    else:
        # Local fallback only. Streamlit Cloud needs GitHub Secrets
        # configured to provide permanent storage.
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)


# ==================================================
# GROUP RESTRICTIONS
# ==================================================

restricted_groups = {
    "group1": [
        "Ellie", "Adrienne", "Dave", "Erin", "Caleb"
    ],
    "group2": [
        "Natalie", "Emme", "Sam", "Laura", "Kirk", "Zack"
    ],
    "group3": [
        "Amber", "Maggie", "Joe"
    ]
}

restrictions = {}

for name in participants:

    if name in restricted_groups["group1"]:
        restrictions[name] = [
            "Natalie", "Emme", "Joe", "Amber",
            "Maggie", "Sam", "Zack", "Laura", "Kirk"
        ]

    elif name in restricted_groups["group2"]:
        restrictions[name] = [
            "Ellie", "Adrienne", "Erin", "Dave",
            "Amber", "Maggie", "Joe", "Caleb"
        ]

    else:
        restrictions[name] = [
            "Natalie", "Emme", "Sam", "Zack",
            "Laura", "Kirk", "Caleb", "Ellie",
            "Adrienne", "Erin", "Dave"
        ]


# ==================================================
# VALIDATION
# ==================================================

def valid_assignment(assignments, prev_years):

    if set(assignments.keys()) != set(participants):
        return False

    if len(set(assignments.values())) != len(participants):
        return False

    for giver, receiver in assignments.items():

        if giver == receiver:
            return False

        if receiver not in restrictions[giver]:
            return False

        for year in prev_years.values():
            if year.get(giver) == receiver:
                return False

    return True


# ==================================================
# ASSIGNMENT GENERATOR
# ==================================================

def generate_assignment(prev_years):

    assignments = {}
    used_receivers = set()

    def backtrack():

        if len(assignments) == len(participants):
            return True

        # Find the giver with the fewest available receivers.
        best_giver = None
        best_options = None

        for giver in participants:

            if giver in assignments:
                continue

            options = [
                receiver
                for receiver in restrictions[giver]
                if receiver not in used_receivers
                and receiver != giver
                and all(
                    year.get(giver) != receiver
                    for year in prev_years.values()
                )
            ]

            if not options:
                return False

            if best_options is None or len(options) < len(best_options):
                best_giver = giver
                best_options = options

        random.shuffle(best_options)

        for receiver in best_options:

            assignments[best_giver] = receiver
            used_receivers.add(receiver)

            if backtrack():
                return True

            del assignments[best_giver]
            used_receivers.remove(receiver)

        return False

    if backtrack():
        return assignments

    return None


# ==================================================
# STREAMLIT APP
# ==================================================

st.set_page_config(
    page_title="Family Secret Santa",
    page_icon="🎁",
    layout="centered"
)

st.title("🎄 Family Secret Santa Generator")

st.write(
    "Generate your family's Secret Santa assignments "
    "while keeping all group restrictions and past years in mind!"
)

# Load historical assignments.
try:
    previous_years = load_previous_years()
except Exception as e:
    st.error(f"Error loading assignments: {e}")
    st.stop()

# Show storage status.
if github_settings():
    st.success("Your assignments are connected to permanent GitHub storage.")
else:
    st.warning(
        "GitHub storage is not configured. "
        "Local file saving is being used instead. "
        "Configure GitHub Secrets before using this app on Streamlit Cloud."
    )

# Automatically select the next available year.
next_year = max(
    2025,
    max(int(year) for year in previous_years.keys()) + 1
)

current_year = st.number_input(
    "Select the year:",
    min_value=2025,
    max_value=2100,
    value=next_year,
    step=1
)

year_key = str(current_year)

# Clear an old pending draw when switching years.
if st.session_state.get("pending_year") != year_key:
    st.session_state.pop("new_assignments", None)
    st.session_state.pop("pending_year", None)


# ==================================================
# DISPLAY EXISTING YEAR
# ==================================================

if year_key in previous_years:

    st.warning(
        f"Assignments for {current_year} are already locked in."
    )

    st.subheader(f"🎁 {current_year} Assignments")
    st.json(previous_years[year_key])


# ==================================================
# GENERATE NEW YEAR
# ==================================================

else:

    if st.button(
        "🎲 Generate Secret Santa",
        type="primary",
        use_container_width=True
    ):

        assignments = generate_assignment(previous_years)

        if assignments:
            st.session_state["new_assignments"] = assignments
            st.session_state["pending_year"] = year_key
        else:
            st.error(
                "Could not find a valid assignment. "
                "Please check the historical data and restrictions."
            )

    # Display pending assignments.
    if (
        st.session_state.get("pending_year") == year_key
        and "new_assignments" in st.session_state
    ):

        st.subheader(f"🎁 Proposed {current_year} Assignments")

        st.info(
            "Review these assignments. You can generate another "
            "draw before confirming."
        )

        st.json(st.session_state["new_assignments"])

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "🔄 Generate Again",
                use_container_width=True
            ):
                st.session_state.pop("new_assignments", None)
                st.rerun()

        with col2:
            if st.button(
                "🔒 Confirm and Lock In",
                type="primary",
                use_container_width=True
            ):

                assignments = st.session_state["new_assignments"]

                if not valid_assignment(assignments, previous_years):
                    st.error(
                        "These assignments failed validation. "
                        "Please generate a new draw."
                    )

                else:
                    updated_history = previous_years.copy()
                    updated_history[year_key] = assignments

                    try:
                        save_previous_years(updated_history)

                        st.session_state.pop("new_assignments", None)
                        st.session_state.pop("pending_year", None)

                        st.success(
                            f"🎉 {current_year} assignments saved successfully!"
                        )

                        st.rerun()

                    except Exception as e:
                        st.error(
                            f"Could not save assignments: {e}"
                        )


# ==================================================
# VIEW ALL PREVIOUS YEARS
# ==================================================

with st.expander("📚 View All Previous Years"):

    for year in sorted(previous_years.keys()):

        st.subheader(f"🎄 {year}")

        st.json(previous_years[year])
