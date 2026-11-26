from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import json
import uuid
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users_db = {}


class UserAuth(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    user_id: str
    name: str
    dob: str
    age: int
    weight: float
    height: float
    gender: str
    activity_level: str
    goal: str


class MealPlanRequest(BaseModel):
    user_id: str
    allergies: str
    mealtype: str
    target_calories: int
    duration: int
    language: str


@app.post("/api/login")
def login(auth: UserAuth):
    for uid, user_data in users_db.items():
        if user_data["email"] == auth.email and user_data["password"] == auth.password:
            profile = user_data.get("profile")
            return {
                "message": "Login successful",
                "user_id": uid,
                "profile_completed": bool(profile),
                "profile": profile,
            }
    raise HTTPException(status_code=401, detail="Invalid email or password")


@app.post("/api/register")
def register(auth: UserAuth):
    for uid, user_data in users_db.items():
        if user_data["email"] == auth.email:
            raise HTTPException(status_code=400, detail="Email already exists")

    new_user_id = str(uuid.uuid4())
    users_db[new_user_id] = {
        "email": auth.email,
        "password": auth.password,
        "profile": None,
        "meal_plan": None,
    }
    return {"message": "Registration successful", "user_id": new_user_id}


@app.post("/api/calculate")
def calculate_metrics(user: UserProfile):
    if user.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    if user.gender == "Male":
        bmr = (10 * user.weight) + (6.25 * user.height) - (5 * user.age) + 5
    else:
        bmr = (10 * user.weight) + (6.25 * user.height) - (5 * user.age) - 161

    multipliers = {
        "Sedentary": 1.2,
        "Lightly active": 1.375,
        "Moderately active": 1.55,
        "Very active": 1.725,
        "Extremely active": 1.9,
    }
    tdee = bmr * multipliers.get(user.activity_level, 1.2)

    if user.goal == "gain_weight":
        target = tdee + 500
    elif user.goal == "gain_muscle":
        target = tdee + 300
    elif user.goal == "lose_weight":
        target = tdee - 500
    else:
        target = tdee

    profile_data = {
        "name": user.name,
        "dob": user.dob,
        "age": user.age,
        "weight": user.weight,
        "height": user.height,
        "gender": user.gender,
        "activity_level": user.activity_level,
        "goal": user.goal,
        "bmr": round(bmr),
        "tdee": round(tdee),
        "target_calories": round(target),
    }
    users_db[user.user_id]["profile"] = profile_data
    return {"message": "Profile saved!", "profile": profile_data}


@app.post("/api/Mealplan")
def meal_plan(request: MealPlanRequest):
    load_dotenv()
    my_key = os.getenv("GEMINI_API_KEY")
    if not my_key:
        raise HTTPException(status_code=500, detail="API Key not configured")

    client = genai.Client(api_key=my_key)

    prompt = f"""
    You are a professional nutrition AI. Generate a {request.duration}-day meal plan.
    Target Calories: {request.target_calories} kcal per day
    Allergies: {request.allergies}
    Cuisine Preference: {request.mealtype} with no pork and alcohol whatsoever

    IMPORTANT TRANSLATION RULE:
    You MUST output the values for 'type', 'name', 'category', and ingredient names in {request.language}.
    However, the JSON keys MUST remain strictly in English.

    You MUST return ONLY a valid JSON object.
    Use exactly this JSON schema:
    {{
      "days": [
        {{
          "day_number": 1,
          "meals": [
            {{
              "type": "Breakfast",
              "name": "Oatmeal",
              "calories": 400,
              "protein": 20,
              "carbs": 50,
              "fat": 10,
              "ingredients": [
                {{"name": "Oats", "quantity": 50, "unit": "g", "category": "Grains"}},
                {{"name": "Milk", "quantity": 200, "unit": "ml", "category": "Dairy"}}
              ]
            }}
          ]
        }}
      ]
    }}
    Include Breakfast, Lunch, Dinner, and 1 Snack for each day.
    Ensure daily total calories match {request.target_calories} as closely as possible.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )

        raw_text = (response.text or "").strip()
        clean_json = (
            raw_text.removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        meal_data = json.loads(clean_json)

        if request.user_id in users_db:
            users_db[request.user_id]["meal_plan"] = meal_data

        return {"meal_plan": meal_data}
    except Exception as e:
        print("Mealplan error:", repr(e))
        raise HTTPException(status_code=500, detail=f"Mealplan error: {e}")


@app.get("/")
def serve_website():
    return FileResponse("cleaneat.html")