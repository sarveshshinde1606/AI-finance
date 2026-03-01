
import os
import json
import re
from dotenv import load_dotenv

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Max, Sum

from google import genai

from .models import UserProfile, UserProgress


GEMINI_API_KEY = "AIzaSyBZ3-G9jRec9s2gP0Vr5TML_gT4X08j_yk"
GEMINI_MODEL = "gemini-2.5-flash"

def index(request):
    return render(request, "index.html")

def planning_panel(request):
    return render(request, "planning_panel.html")

def about(request):
    return render(request, "about.html")

def master(request):
    return render(request, "master.html")


# =========================
# REGISTER
# =========================
def register(request):
    if request.method == "POST":
        user = User.objects.create_user(
            username=request.POST["username"],
            email=request.POST["email"],
            password=request.POST["password1"],
        )
        UserProfile.objects.create(user=user, age=int(request.POST["age"]))
        return redirect("login1")
    return render(request, "register.html")


from .models import UserProfile

def login1(request):

    error_message = None

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )

        if user:
            try:
                profile = UserProfile.objects.get(user=user)
                age = profile.age

                login(request, user)

                # 🎓 Age 16–25 → Main Learning Dashboard
                if 16 <= age <= 25:
                    return redirect("main_dashboard")

                # 💼 Age 26–40 → Budget Dashboard
                elif 26 <= age <= 40:
                    return redirect("budget_dashboard")

                # ❌ Other ages → Show error
                else:
                    logout(request)
                    error_message = "Access not allowed for your age group."

            except UserProfile.DoesNotExist:
                error_message = "User profile not found."

        else:
            error_message = "Invalid username or password."

    return render(request, "login.html", {
        "error_message": error_message
    })



def logout_view(request):
    logout(request)
    return redirect("login1")


# =========================
# MAIN DASHBOARD (AGE RESTRICTED)
# =========================
@login_required
def main_dashboard(request):

    profile = UserProfile.objects.get(user=request.user)

    if not (16 <= profile.age <= 25):
        return render(request, "access_denied.html", {
            "message": "Dashboard access allowed only for users age between 16 and 25."
        })

    return render(request, "main_dashboard.html", {
        "username": request.user.username,
        "age": profile.age
    })


def generate_finance_content(topic):
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    Explain "{topic}" in beginner-friendly format:

    1. Definition
    2. Example
    3. Advantages
    4. Disadvantages
    5. Who should invest
    6. Tips

    Use simple language.
    """

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"⚠ Error generating content: {str(e)}"


# ===============================
# Gemini Video Suggestions
# ===============================
def generate_video_suggestions(topic):
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    Suggest 4 beginner-friendly animated YouTube videos about {topic}.
    Return JSON list in this format:
    [
      {{
        "title": "Video Title",
        "video_id": "YouTubeVideoID"
      }}
    ]
    Only return JSON.
    """

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        text = response.text.strip()

        import json, re

        match = re.search(r'\[.*\]', text, re.DOTALL)

        videos = []

        if match:
            data = json.loads(match.group())

            for item in data:
                video_id = item["video_id"].strip()

                videos.append({
                    "title": item["title"],
                    "embed_url": f"https://www.youtube.com/embed/{video_id}"
                })

        return videos

    except Exception as e:
        print("Video generation error:", e)
        return []


# ===============================
# MAIN LEARNING DASHBOARD
# ===============================
@login_required
def learning_dashboard(request):

    profile = UserProfile.objects.get(user=request.user)

    # Instead of access_denied.html → show message directly
    if not (16 <= profile.age <= 25):
        return render(request, "learning.html", {
            "content": "⚠ Learning Panel allowed only for age 16–25.",
            "videos": [],
            "books": [],
            "references": []
        })

    content = None
    videos = []
    books = []
    references = []

    if request.method == "POST":
        topic = request.POST.get("topic")

        if topic:
            content = generate_finance_content(topic)
            videos = generate_video_suggestions(topic)

    return render(request, "learning.html", {
        "content": content,
        "videos": videos,
        "books": books,
        "references": references
    })

# =========================
# GENERATE 5 QUESTION GAME QUIZ
# =========================
def generate_level_quiz(topic, level):
    
    prompt = f"""
    Generate exactly 5 MCQ questions about {topic}.
    Difficulty: {level}.

    Return ONLY valid JSON list in this format:

    [
      {{
        "question": "Question text",
        "options": ["A", "B", "C", "D"],
        "answer": "Correct Option"
      }}
    ]
    """

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        text = response.text.strip()

        match = re.search(r'\[.*\]', text, re.DOTALL)

        if match:
            return json.loads(match.group())

        return []

    except Exception as e:
        print("Quiz generation error:", e)
        return []


# =========================
# GAMIFICATION PANEL
# =========================

@login_required
def gamification_panel(request):

    quiz = None
    score = None
    badge = None

    if request.method == "POST":

        if "start_game" in request.POST:
            topic = request.POST.get("topic")
            level = request.POST.get("level")

            quiz = generate_level_quiz(topic, level)
            request.session["quiz"] = quiz
            request.session["topic"] = topic

        elif "submit_quiz" in request.POST:
            quiz = request.session.get("quiz")
            topic = request.session.get("topic")

            correct = 0

            for i, q in enumerate(quiz):
                selected = request.POST.get(f"q{i}")
                if selected == q["answer"]:
                    correct += 1

            score = correct

            # SAVE PROGRESS
            UserProgress.objects.create(
                user=request.user,
                topic=topic,
                panel_type="game",
                score=score,
                total_questions=5,
                xp_earned=score * 3
            )

            if score == 5:
                badge = "🥇 Gold Badge"
            elif score >= 3:
                badge = "🥈 Silver Badge"
            else:
                badge = "🥉 Bronze Badge"

    return render(request, "gamification.html", {
        "quiz": quiz,
        "score": score,
        "badge": badge
    })

# =========================
# GENERATE 10 QUESTION AI QUIZ
# =========================
def generate_ai_quiz(topic, difficulty):
    
    prompt = f"""
    Generate exactly 10 MCQ questions about {topic}.
    Difficulty: {difficulty}.

    Return ONLY valid JSON list in this format:

    [
      {{
        "question": "Question text",
        "options": ["A", "B", "C", "D"],
        "answer": "Correct Option"
      }}
    ]
    """

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        text = response.text.strip()

        match = re.search(r'\[.*\]', text, re.DOTALL)

        if match:
            return json.loads(match.group())

        return []

    except Exception as e:
        print("AI Quiz generation error:", e)
        return []


# =========================
# QUIZ PANEL
# =========================
@login_required
def quiz_panel(request):

    quiz = None
    score = None

    if request.method == "POST":

        if "generate_quiz" in request.POST:
            topic = request.POST.get("topic")
            difficulty = request.POST.get("difficulty")

            quiz = generate_ai_quiz(topic, difficulty)
            request.session["ai_quiz"] = quiz
            request.session["topic"] = topic

        elif "submit_quiz" in request.POST:
            quiz = request.session.get("ai_quiz")
            topic = request.session.get("topic")

            correct = 0

            for i, q in enumerate(quiz):
                selected = request.POST.get(f"q{i}")
                if selected == q["answer"]:
                    correct += 1

            score = correct

            # SAVE PROGRESS
            UserProgress.objects.create(
                user=request.user,
                topic=topic,
                panel_type="quiz",
                score=score,
                total_questions=10,
                xp_earned=score * 5
            )

    return render(request, "quiz.html", {
        "quiz": quiz,
        "score": score
    })


# =========================
# PROGRESS DASHBOARD + AI REPORT
# =========================
@login_required
def progress_dashboard(request):

    records = UserProgress.objects.filter(user=request.user).order_by('-created_at')

    total_attempts = records.count()
    avg_score = records.aggregate(Avg('score'))['score__avg'] or 0
    best_score = records.aggregate(Max('score'))['score__max'] or 0
    total_xp = records.aggregate(Sum('xp_earned'))['xp_earned__sum'] or 0

    avg_score = round(avg_score, 2)

    prompt = f"""
    Generate personalized performance report for {request.user.username}.

    Attempts: {total_attempts}
    Average Score: {avg_score}
    Best Score: {best_score}
    Total XP: {total_xp}

    Provide:
    - Strengths
    - Weaknesses
    - Improvement tips
    - Motivation
    """

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        ai_report = response.text

    except Exception as e:
        print("AI Report Error:", e)
        ai_report = "AI Report generation failed."

    return render(request, "progress_dashboard.html", {
        "records": records,
        "username": request.user.username,
        "total_attempts": total_attempts,
        "avg_score": avg_score,
        "best_score": best_score,
        "total_xp": total_xp,
        "ai_report": ai_report
    })


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from django.http import HttpResponse
from io import BytesIO
from datetime import datetime

@login_required
def download_progress_report(request):

    records = UserProgress.objects.filter(user=request.user)

    total_attempts = records.count()
    avg_score = records.aggregate(Avg('score'))['score__avg'] or 0
    best_score = records.aggregate(Max('score'))['score__max'] or 0
    total_xp = records.aggregate(Sum('xp_earned'))['xp_earned__sum'] or 0

    avg_score = round(avg_score, 2)

    # Generate AI Report
    prompt = f"""
    Generate personalized performance report for {request.user.username}.
    Attempts: {total_attempts}
    Average Score: {avg_score}
    Best Score: {best_score}
    Total XP: {total_xp}
    """

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response_ai = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        ai_report = response_ai.text

    except Exception as e:
        print("Download Report AI Error:", e)
        ai_report = "AI report generation failed."

    # PDF generation
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("AI Financial Learning Progress Report", styles['Heading1']))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"User: {request.user.username}", styles['Normal']))
    elements.append(Paragraph(f"Generated On: {datetime.now().strftime('%d %B %Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    data = [
        ["Total Attempts", total_attempts],
        ["Average Score", avg_score],
        ["Best Score", best_score],
        ["Total XP", total_xp],
    ]

    table = Table(data, colWidths=[3 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph("AI Performance Analysis", styles['Heading2']))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(ai_report, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Progress_Report.pdf"'

    return response


@login_required
def budget_dashboard(request):

    profile = UserProfile.objects.get(user=request.user)

    if not (26 <= profile.age <= 40):
        return render(request, "login.html", {
            "error_message": "Budget Dashboard allowed only for age 26–40."
        })

    return render(request, "budget_dashboard.html", {
        "username": request.user.username,
        "age": profile.age
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from google import genai


@login_required
def personalized_budgeting(request):

    result = None
    detected_risk = None

    if request.method == "POST":

        monthly_income = request.POST.get("income")
        monthly_expenses = request.POST.get("expenses")
        current_savings = request.POST.get("savings")
        financial_goal = request.POST.get("goal")

        surplus = int(monthly_income) - int(monthly_expenses)

        prompt = f"""
        You are a professional financial advisor.

        User Details:
        Monthly Income: ₹{monthly_income}
        Monthly Expenses: ₹{monthly_expenses}
        Current Savings: ₹{current_savings}
        Monthly Surplus: ₹{surplus}
        Financial Goal: {financial_goal}

        Step 1: First determine user's risk profile (Low / Moderate / High)
        based on income stability, savings ratio and surplus.

        Step 2: Create structured financial plan in this format:

        DETECTED RISK PROFILE:
        ---
        BUDGET BREAKDOWN:
        ---
        EMERGENCY FUND STRATEGY:
        ---
        INVESTMENT PLAN:
        ---
        ASSET ALLOCATION (%):
        ---
        SHORT TERM PLAN:
        ---
        LONG TERM PLAN:
        ---
        FINAL RECOMMENDATION:
        """

        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt
            )

            result = response.text

            # Detect risk profile
            if result:
                if "Low" in result:
                    detected_risk = "Low"
                elif "Moderate" in result:
                    detected_risk = "Moderate"
                elif "High" in result:
                    detected_risk = "High"

        except Exception as e:
            print("Budget AI Error:", e)
            result = "AI budget generation failed."

    return render(request, "personalized_budget.html", {
        "result": result,
        "detected_risk": detected_risk
    })

@login_required
def investment_recommendation(request):

    recommendation = None
    detected_risk = None

    if request.method == "POST":

        monthly_income = request.POST.get("income")
        monthly_savings = request.POST.get("savings")
        investment_amount = request.POST.get("investment_amount")
        time_horizon = request.POST.get("time_horizon")
        goal = request.POST.get("goal")

        prompt = f"""
        You are a certified Indian financial investment advisor.

        User Financial Details:
        - Monthly Income: ₹{monthly_income}
        - Monthly Savings: ₹{monthly_savings}
        - Amount Available for Investment: ₹{investment_amount}
        - Investment Time Horizon: {time_horizon}
        - Financial Goal: {goal}

        Step 1: Detect Risk Profile (Low / Moderate / High)

        Step 2: Provide structured investment advice in this format:

        DETECTED RISK PROFILE:
        ---
        SUGGESTED INVESTMENT TYPES:
        ---
        ASSET ALLOCATION (% split):
        ---
        SIP / Lumpsum Strategy:
        ---
        Short Term Strategy:
        ---
        Long Term Strategy:
        ---
        Expected Return Outlook:
        ---
        Risk Management Advice:
        ---
        Final Summary Recommendation:
        """

        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt
            )

            recommendation = response.text

            # Risk Detection
            if recommendation:
                if "Low" in recommendation:
                    detected_risk = "Low"
                elif "Moderate" in recommendation:
                    detected_risk = "Moderate"
                elif "High" in recommendation:
                    detected_risk = "High"

        except Exception as e:
            print("Investment AI Error:", e)
            recommendation = "AI investment recommendation failed."

    return render(request, "investment_recommendation.html", {
        "recommendation": recommendation,
        "detected_risk": detected_risk
    })
    
    
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from google import genai

@login_required
def ai_assistant(request):

    # Initialize chat history
    if "chat_history" not in request.session:
        request.session["chat_history"] = []

    # =============================
    # CLEAR CHAT
    # =============================
    if request.method == "POST" and request.POST.get("clear_chat") == "1":
        request.session["chat_history"] = []
        request.session.modified = True
        return redirect("ai_assistant")

    chat_history = request.session.get("chat_history", [])

    # =============================
    # NEW QUESTION
    # =============================
    if request.method == "POST" and request.POST.get("question"):

        user_question = request.POST.get("question")

        prompt = f"""
        You are a professional financial advisor AI.

        Rules:
        - Keep answer short (max 6–8 lines)
        - Use bullet points
        - Make it easy to read
        - Avoid long paragraphs

        User Question:
        {user_question}
        """

        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt
            )

            ai_reply = response.text.strip()

        except Exception as e:
            print("AI Assistant Error:", e)
            ai_reply = "⚠ AI Assistant is currently unavailable. Please try again."

        chat_history.append({
            "user": user_question,
            "ai": ai_reply
        })

        request.session["chat_history"] = chat_history
        request.session.modified = True

    return render(request, "ai_assistant.html", {
        "chat_history": request.session.get("chat_history", [])
    })


from .models import HumanAssistantRequest
from django.contrib.auth.decorators import login_required
import requests


@login_required
def human_assistant(request):

    message = None

    if request.method == "POST":
        subject = request.POST.get("subject")
        user_message = request.POST.get("message")

        HumanAssistantRequest.objects.create(
            user=request.user,
            subject=subject,
            message=user_message
        )

        message = "Your request has been sent successfully."

    requests_history = HumanAssistantRequest.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, "human_assistant.html", {
        "message": message,
        "requests_history": requests_history
    })


from django.contrib import messages

def custom_admin_login(request):

    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username == "admin" and password == "admin123":
            request.session["is_admin"] = True
            return redirect("custom_admin_dashboard")
        else:
            error = "Invalid admin credentials"

    return render(request, "custom_admin_login.html", {"error": error})


# =========================
# CUSTOM ADMIN DASHBOARD
# =========================
def custom_admin_dashboard(request):

    if not request.session.get("is_admin"):
        return redirect("custom_admin_login")

    requests_list = HumanAssistantRequest.objects.all().order_by('-created_at')

    return render(request, "custom_admin_dashboard.html", {
        "requests_list": requests_list
    })


# =========================
# UPDATE REQUEST STATUS (ONLY ONE VERSION)
# =========================
from django.shortcuts import get_object_or_404, redirect
from .models import HumanAssistantRequest

def update_request_status(request, request_id):

    if not request.session.get("is_admin"):
        return redirect("custom_admin_login")

    request_obj = get_object_or_404(HumanAssistantRequest, id=request_id)

    if request.method == "POST":

        new_status = request.POST.get("status")
        remark = request.POST.get("remark")

        print("DEBUG STATUS:", new_status)   # ← Add this for debugging

        if new_status in ["Approved", "Rejected"]:
            request_obj.status = new_status

        request_obj.admin_remark = remark if remark else ""
        request_obj.save()

    return redirect("custom_admin_dashboard")



# =========================
# ADMIN LOGOUT
# =========================
def custom_admin_logout(request):
    request.session.flush()
    return redirect("custom_admin_login")
# =========================
# PROXY SCANNER
# =========================
@login_required
def proxy_scanner(request):

    proxy_status = None
    ip_address = request.META.get("REMOTE_ADDR")

    try:
        # Basic Proxy Check (Simple Detection)
        headers = request.META

        if headers.get("HTTP_X_FORWARDED_FOR") or headers.get("HTTP_VIA"):
            proxy_status = "⚠ Proxy or VPN Detected"
        else:
            proxy_status = "✅ Secure Connection"

    except:
        proxy_status = "Unable to detect proxy status."

    return render(request, "proxy_scanner.html", {
        "ip_address": ip_address,
        "proxy_status": proxy_status
    })

from django.shortcuts import get_object_or_404
from .models import HumanAssistantRequest


@login_required
def admin_panel(request):

    if not request.user.is_staff:
        return render(request, "access_denied.html", {
            "message": "Admin access only."
        })

    requests_list = HumanAssistantRequest.objects.all().order_by('-created_at')

    return render(request, "admin_panel.html", {
        "requests_list": requests_list
    })

