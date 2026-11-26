# Nutriplan — Meals & Nutrition Planner

A full-stack web application that calculates daily calorie/macro targets (BMR & TDEE) and uses Google Gemini to generate structured, customizable multi-day meal plans with ingredient breakdowns.

## Features
- **User Accounts & Profiles:** Registration, login, and profile setup (`age`, `weight`, `height`, `gender`, `activity_level`, `goal`).
- **Calorie & TDEE Calculator:** Computes BMR (Mifflin-St Jeor), TDEE by activity multiplier, and goal-adjusted daily target calories.
- **Custom AI Meal Plans (`/api/Mealplan`):** Generates multi-day meal plans (Breakfast, Lunch, Dinner, and Snack) tailored to target calories, allergies, cuisine preferences (no pork/alcohol), duration, and output language, returning structured JSON with macros and ingredients.
- **Frontend Web UI:** Served directly by FastAPI via `cleaneat.html`.

## Tech Stack
- **Backend:** FastAPI, Uvicorn, Pydantic, Python `dotenv`
- **AI SDK:** `google-genai`
- **Frontend:** HTML / CSS / JavaScript (`cleaneat.html`)
