import streamlit as st
import datetime
from plan_builder import load_plan, build_plan, get_plan_for_date
import json

st.set_page_config(page_title="Vegetarian Breakfast Planner", page_icon="🥗", layout="centered")

st.title("🥗 Vegetarian Breakfast & Prep Planner")

# Load existing plan from Supabase
plan = load_plan()

# Session state to hold full plan JSON from build_plan
if "full_plan" not in st.session_state:
    st.session_state.full_plan = None

# Preferences input box
preferences = st.text_area(
    "Enter your meal preferences:",
    placeholder="e.g., No sugar, high protein, includes sprouts and poha",
    height=100
)

if st.button("Generate Monthly Plan"):
    if not preferences.strip():
        st.error("Please enter your preferences before generating the plan.")
    else:
        with st.spinner("Generating your plan..."):
            from plan_builder import build_plan_prompt
            plan_json = build_plan_prompt(preferences)  # ask Gemini for JSON directly
            result = build_plan(plan_json)  # save to Supabase

            if result.get("status") == "success":
                st.success("✅ Plan generated and saved to Supabase!")
                # Reload latest plan
                plan = load_plan()
                st.session_state.full_plan = plan
            else:
                st.error(f"Error: {result.get('message','Unknown error')}")

# Show today's plan
if plan:
    today = datetime.date.today()
    today_plan = get_plan_for_date(today, plan)

    # Tomorrow's plan for prep
    tomorrow = today + datetime.timedelta(days=1)
    tomorrow_plan = get_plan_for_date(tomorrow, plan)

    if today_plan:
        st.subheader(f"📌 Today's Plan ({today.strftime('%A, %d %B %Y')})")
        st.markdown(f"**Breakfast:** {today_plan.get('breakfast', 'N/A')}")
        st.markdown(f"**Method:** {today_plan.get('method', 'N/A')}")

        if tomorrow_plan:
            st.markdown(f"**Evening Prep:** {tomorrow_plan.get('prep', 'No prep')}")
        else:
            st.markdown("**Evening Prep:** No prep (end of plan).")
    else:
        st.warning("⚠️ No plan found for today. Generate a plan above.")

# Option to check another day
if plan:
    st.subheader("📅 Check another day")
    date_input = st.date_input("Select a date", value=datetime.date.today())

    selected_plan = get_plan_for_date(date_input, plan)
    next_day_plan = get_plan_for_date(date_input + datetime.timedelta(days=1), plan)

    if selected_plan:
        st.markdown(f"**Breakfast:** {selected_plan.get('breakfast', 'N/A')}")
        st.markdown(f"**Method:** {selected_plan.get('method', 'N/A')}")

        if next_day_plan:
            st.markdown(f"**Evening Prep:** {next_day_plan.get('prep', 'No prep')}")
        else:
            st.markdown("**Evening Prep:** No prep (end of plan).")
    else:
        st.warning("⚠️ No plan found for the selected date.")
