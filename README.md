# Meal_Planner

Automated weekly meal planning with WhatsApp delivery.

## What it does
- Builds a meal plan for a month from a configurable budget
- Generates a consolidated grocery list
- Sends the daily menu and prep instructions over WhatsApp

## Requirements
- Python 3.10+
- `pip install -r requirements.txt`

## Setup
```bash
git clone https://github.com/HimanshuPatil2001/Meal_Planner.git
cd Meal_Planner
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Copy `.env.example` to `.env` and fill in the values. Never commit `.env`.

## Usage
```bash
python app.py
```

## Documentation
- [Implementation changelog](docs/04-implementation/changelog.md)
- [Portfolio plan](https://github.com/HimanshuPatil2001/HimanshuPatil2001/blob/main/docs/PORTFOLIO_PLAN.md)

## License
MIT — see [LICENSE](LICENSE).
