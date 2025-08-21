# plan_builder.py
import os
import datetime
import pandas as pd
from io import StringIO
import google.generativeai as genai
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Configure Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------- Helper functions ---------------- #

from collections import defaultdict
import datetime

def _records_to_plan_dict(records):
    """
    Convert Supabase rows into nested dict by week -> day -> meals list.
    Schema: id, date, meal_type, item, method, prep, quantity
    """
    plan = defaultdict(lambda: defaultdict(list))

    for row in records:
        try:
            # Parse date from string if needed
            row_date = row.get("date")
            if isinstance(row_date, str):
                row_date = datetime.datetime.strptime(row_date, "%Y-%m-%d").date()

            day_name = row_date.strftime("%A").lower()
            week_num = (row_date.day - 1) // 7 + 1
            week_key = f"week{week_num}"

            meal_entry = {
                "meal_type": row.get("meal_type", ""),
                "item": row.get("item", ""),
                "method": row.get("method", ""),
                "prep": row.get("prep", ""),
                "quantity": row.get("quantity", "")
            }

            plan[week_key][day_name].append(meal_entry)

        except Exception as e:
            print(f"⚠ Error parsing row {row}: {e}")

    return dict(plan)



def load_plan():
    """Fetch the month plan directly from Supabase table."""
    try:
        response = supabase.table("meal_plan").select("*").execute()
        records = response.data
        plan = _records_to_plan_dict(records)
        if plan:
            return plan
    except Exception as e:
        print(f"❌ Error loading from Supabase: {e}")

    return {}


def _extract_text_from_gemini(response):
    """Extract plain CSV text from Gemini API response."""
    text_output = ""
    if hasattr(response, "text") and response.text:
        text_output = response.text
    elif hasattr(response, "candidates") and response.candidates:
        parts = response.candidates[0].content.parts
        text_output = "".join(part.text for part in parts if hasattr(part, "text"))
    text_output = text_output.strip()
    if text_output.startswith("```"):
        text_output = text_output.split("\n", 1)[1]
    if text_output.endswith("```"):
        text_output = text_output.rsplit("\n", 1)[0]
    return text_output.strip()


def build_plan_prompt(preferences: str) -> str:
    """Use Gemini to generate a CSV plan with columns: date,meal_type,item,method,prep,quantity."""
    today = datetime.date.today()
    month_name = today.strftime("%B %Y")
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
        f"You are a helpful planner. Generate a full vegetarian meal plan for the month of {month_name}. "
        "Output strictly in CSV format with header 'date,meal_type,item,method,prep,quantity'. "
        "Each date should have at least breakfast, lunch, and dinner rows. "
        "Use ISO date format YYYY-MM-DD for 'date'. "
        "Keep 'meal_type' one of: breakfast, lunch, dinner, snack. "
        "Keep 'method' and 'prep' short (1 sentence). "
        "Keep 'quantity' short like '1 plate', '2 bowls', etc. "
        "Avoid code fences and commentary; CSV only."
    )
    response = model.generate_content(prompt)
    return _extract_text_from_gemini(response)


def save_plan_to_excel(df: pd.DataFrame, filename: str = "meal_plan.xlsx"):
    """Save plan locally into Excel file."""
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    # Replace NaN/NA with empty strings to avoid writing literal NaN
    df = df.fillna("")
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df[["date", "meal_type", "item", "method", "prep", "quantity"]].to_excel(
            writer, sheet_name="Meal Plan", index=False
        )
    print(f"✅ Saved {filename} — {len(df)} rows.")


def save_plan_to_supabase(df: pd.DataFrame):
    """Save DataFrame rows into Supabase meal_plan table."""
    try:
        # Clear old data
        supabase.table("meal_plan").delete().neq("id", 0).execute()

        # Insert new data
        # Replace NaN/NA with empty strings so JSON encoding remains compliant
        df = df.fillna("")
        records = df.to_dict(orient="records")
        response = supabase.table("meal_plan").insert(records).execute()
        return {"status": "success", "message": f"Inserted {len(records)} rows into Supabase."}
    except Exception as e:
        return {"status": "error", "message": f"Supabase insert failed: {e}"}


def build_plan(csv_text: str):
    """Parse CSV from Gemini, save to Excel + Supabase."""
    csv_text = csv_text.strip()
    try:
        df = pd.read_csv(StringIO(csv_text))
    except Exception:
        df = pd.read_csv(StringIO(csv_text), engine="python", on_bad_lines="skip")

    # Normalize
    df.columns = [c.strip().lower() for c in df.columns]
    expected = ["date", "meal_type", "item", "method", "prep", "quantity"]
    df = df[[c for c in expected if c in df.columns]]
    # Ensure no NaN values are present prior to any serialization
    df = df.fillna("")

    # Save locally
    save_plan_to_excel(df)

    # Save to Supabase
    supabase_result = save_plan_to_supabase(df)
    if supabase_result["status"] == "error":
        return {"status": "warning", "message": f"Excel saved but Supabase update failed: {supabase_result['message']}"}

    return {"status": "success", "message": "Plan generated and saved to Excel + Supabase."}


def get_plan_for_date(date, plan):
    """Get meals for a given date from the structured plan dict."""
    day_name = date.strftime("%A").lower()  # e.g., "monday"
    week_num = (date.day - 1) // 7 + 1      # week number
    week_key = f"week{week_num}"

    return plan.get(week_key, {}).get(day_name, [])
