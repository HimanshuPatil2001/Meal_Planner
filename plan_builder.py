# notifier.py
import os
import datetime
import argparse
from twilio.rest import Client

# ==============================
# 🔹 Twilio Setup
# ==============================
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_whatsapp_number = "whatsapp:+14155238886"  # Twilio sandbox

client = Client(account_sid, auth_token)

# Recipients (comma-separated env var recommended)
recipients = os.getenv("RECIPIENTS", "").split(",") if os.getenv("RECIPIENTS") else []


# ---------------- Helper ---------------- #
def send_whatsapp_message(body: str):
    """Send a WhatsApp message to all recipients."""
    for number in recipients:
        if number.strip():
            client.messages.create(
                body=body,
                from_=from_whatsapp_number,
                to=f"whatsapp:{number.strip()}"
            )
    print(f"✅ WhatsApp message sent to {len(recipients)} recipient(s)")


# ---------------- Notifications ---------------- #
def send_daily_plan():
    plan = load_plan()
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    today_plan = get_plan_for_date(today, plan)
    tomorrow_plan = get_plan_for_date(tomorrow, plan)

    if today_plan:
        message_lines = [f"🥗 *Today's Plan* ({today.strftime('%d %B %Y')})"]

        for meal in today_plan:
            meal_type = meal.get("meal_type", "").capitalize()
            item = meal.get("item", "N/A")
            method = meal.get("method", "N/A")
            prep = meal.get("prep", None)

            msg = f"🍽 {meal_type}: {item}\n📋 Method: {method}"
            if prep:
                msg += f"\n🛠 Prep: {prep}"
            message_lines.append(msg)

        if tomorrow_plan:
            tomorrow_preps = [m.get("prep") for m in tomorrow_plan if m.get("prep")]
            if tomorrow_preps:
                message_lines.append(
                    f"🌙 *Evening Prep for Tomorrow*: {', '.join(tomorrow_preps)}"
                )

        send_whatsapp_message("\n\n".join(message_lines))
    else:
        print("⚠ No plan found for today.")


def send_weekly_groceries():
    plan = load_plan()
    today = datetime.date.today()

    week_num = (today.day - 1) // 7 + 1
    week_key = f"week{week_num}"

    groceries = []
    if week_key in plan:
        for _, meals in plan[week_key].items():
            for m in meals:
                if m.get("prep"):
                    groceries.append(m["prep"])

    if groceries:
        message = "🛒 *Weekly Grocery List*\n" + "\n".join([f"- {item}" for item in groceries])
        send_whatsapp_message(message)
    else:
        print("⚠ No groceries found for this week.")


def send_monthly_groceries():
    plan = load_plan()
    groceries = []

    for week, days in plan.items():
        for _, meals in days.items():
            for m in meals:
                if m.get("prep"):
                    groceries.append(m["prep"])

    if groceries:
        message = "📦 *Monthly Grocery List*\n" + "\n".join([f"- {item}" for item in groceries])
        send_whatsapp_message(message)
    else:
        print("⚠ No groceries found for this month.")


# ---------------- CLI Entry ---------------- #
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--job",
        type=str,
        required=True,
        help="Which job to run: daily | weekly | monthly"
    )
    args = parser.parse_args()

    if args.job == "daily":
        send_daily_plan()
    elif args.job == "weekly":
        send_weekly_groceries()
    elif args.job == "monthly":
        send_monthly_groceries()
    else:
        print("❌ Invalid job type. Use: daily | weekly | monthly")
