from flask import Flask, request, render_template
import os
import pdfplumber
from pymongo import MongoClient

app = Flask(__name__)

# ---------------- MongoDB Connection ----------------
client = MongoClient("YOUR_CONNECTION_STRING")
db = client["resume_analyzer"]
collection = db["results"]

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

# ---------------- Main Route ----------------
@app.route('/', methods=['GET', 'POST'])
def home():
    skills = []
    jobs = []
    ats_score = 0

    if request.method == 'POST':
        file = request.files['resume']

        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            # Extract text from PDF
            text = ""
            if file.filename.endswith('.pdf'):
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted

            # Process data
            skills = extract_skills(text)
            jobs = recommend_jobs(skills)
            ats_score = calculate_ats_score(skills)

            # Save to MongoDB
            data = {
                "skills": skills,
                "jobs": jobs,
                "ats_score": ats_score
            }
            collection.insert_one(data)

    return render_template(
        'index.html',
        skills=', '.join(skills),
        jobs=', '.join(jobs) if jobs else "No matching jobs found",
        score=ats_score
    )

# ---------------- Run App ----------------
if __name__ == '__main__':
    app.run(debug=True)