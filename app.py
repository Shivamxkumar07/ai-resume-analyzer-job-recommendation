from flask import Flask, request, render_template, redirect, url_for
import os
import pdfplumber
from pymongo import MongoClient

app = Flask(__name__)

# ---------------- MongoDB Connection (SAFE) ----------------
MONGO_URI = os.environ.get("MONGO_URI")

if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client["resume_analyzer"]
    collection = db["results"]
else:
    collection = None
    print("⚠️ MongoDB not connected (MONGO_URI missing)")

# ---------------- Upload Folder ----------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Skills List ----------------
skills_list = [
    "python", "java", "c++", "machine learning",
    "data science", "html", "css", "javascript",
    "sql", "react", "node", "flask"
]

# ---------------- Job Roles ----------------
job_roles = {
    "Data Scientist": ["python", "machine learning", "data science"],
    "Web Developer": ["html", "css", "javascript", "react"],
    "Backend Developer": ["python", "node", "sql", "flask"],
    "Java Developer": ["java", "sql"],
    "Software Engineer": ["c++", "java", "python"]
}

# ---------------- Skill Extraction ----------------
def extract_skills(text):
    found_skills = []
    text = text.lower()

    for skill in skills_list:
        if skill in text:
            found_skills.append(skill)

    return found_skills

# ---------------- Job Recommendation ----------------
def recommend_jobs(skills):
    recommended = []

    for job, required_skills in job_roles.items():
        match_count = 0

        for skill in skills:
            if skill in required_skills:
                match_count += 1

        if match_count >= 2:
            recommended.append(job)

    return recommended

# ---------------- ATS Score ----------------
def calculate_ats_score(skills):
    score = 0

    score += len(skills) * 10

    if "python" in skills:
        score += 10
    if "machine learning" in skills:
        score += 10
    if "sql" in skills:
        score += 5

    return min(score, 100)

# ---------------- ROUTES ----------------

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Login Page
@app.route('/login')
def login():
    return render_template('login.html')

# Signup Page
@app.route('/signup')
def signup():
    return render_template('signup.html')

# Upload Page
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['resume']

        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            # Extract text
            text = ""
            if file.filename.endswith('.pdf'):
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted

            # Process
            skills = extract_skills(text)
            jobs = recommend_jobs(skills)
            ats_score = calculate_ats_score(skills)

            # Save to MongoDB
            if collection:
                collection.insert_one({
                    "skills": skills,
                    "jobs": jobs,
                    "ats_score": ats_score
                })

            return render_template(
                'result.html',
                skills=', '.join(skills),
                jobs=', '.join(jobs) if jobs else "No matching jobs found",
                score=ats_score
            )

    return render_template('upload.html')

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# Contact Page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Admin Page (optional)
@app.route('/admin')
def admin():
    if collection:
        data = list(collection.find())
    else:
        data = []
    return render_template('admin.html', data=data)

# ---------------- Run App (Render Ready) ----------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
