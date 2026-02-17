from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import os, shutil


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= DATABASE =================
from database import init_db, hash_password
from models import User
from lab_prediction import predict_pancreas_stage

# ================= GEMINI =================
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.5-flash")
chat = gemini_model.start_chat(history=[])

# ================= FLASK APP =================
app = Flask(__name__)
app.secret_key = "change-this-secret"
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32MB

init_db()

# ================= HELPERS =================
def clear_folder(folder):
    if os.path.exists(folder):
        for f in os.listdir(folder):
            p = os.path.join(folder, f)
            if os.path.isfile(p):
                os.remove(p)
            elif os.path.isdir(p):
                shutil.rmtree(p)

# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.get_by_username(request.form["username"])
        if user and user["password"] == hash_password(request.form["password"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful", "success")
            return redirect(url_for("prediction"))
        flash("Invalid username or password", "error")
    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        full_name = request.form.get("full_name", "")

        if User.get_by_username(username):
            flash("Username already exists", "error")
            return redirect(url_for("signup"))

        if User.get_by_email(email):
            flash("Email already registered", "error")
            return redirect(url_for("signup"))

        user = User(username, email, hash_password(password), full_name)
        user.save()
        flash("Signup successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

# ---------- PREDICTION ----------
@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # 🔹 ALWAYS provide png_files (prevents UndefinedError)
    png_files = []

    if request.method == "POST":
        clear_folder(os.path.join(BASE_DIR, "static", "uploads"))
        clear_folder(os.path.join(BASE_DIR, "static", "output_case012"))

        # -------- IMAGE UPLOAD --------
        file = request.files["image"]
        filename = secure_filename(file.filename)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session['user_id']}_{ts}_{filename}"
        img_path = os.path.join(BASE_DIR, "static", "uploads", filename)
        file.save(img_path)

        with open(os.path.join(BASE_DIR, "file.txt"), "w") as f:
            f.write(os.path.abspath(img_path))

        # -------- RUN ANALYZER --------
        ret = os.system(f"python {os.path.join(BASE_DIR, 'Analyzer.py')}")
        if ret != 0:
            flash("Inference failed. Check Analyzer.py logs.", "error")
            return render_template("prediction.html", png_files=[])

        # -------- READ OUTPUT --------
        _, volume, shape, voxel_count, spacing, mid_slice, size_x, size_y, size_z, max_diameter = \
          open(os.path.join(BASE_DIR, "dice_vol.txt")).read().split("|")

        volume = float(volume)
        max_diameter = float(max_diameter)


        # -------- LAB MODEL --------
        stage, survival, advice = predict_pancreas_stage(
            CA19_9=float(request.form["ca19_9"]),
            Total_Bilirubin=float(request.form["total_bilirubin"]),
            ALP=float(request.form["alp"]),
            Albumin=float(request.form["albumin"]),
            NLR=float(request.form["nlr"]),
            Age=int(request.form["age"])
        )
        report = request.form['symptoms']
        # if not report.strip():
        #     report = "Radiology report text was not provided."

        # -------- GEMINI --------
        prompt = f"""
<div>

<p><b>Radiology Report:</b></p>
<p>{report}</p>

<p><b>AI Predictions (use as given):</b></p>
<ul>
  <li>Tumor volume: {float(volume)/1000:.2f} mL</li>
  <li>Tumor maximum diameter: {max_diameter:.2f} mm</li>
  <li>Lab-based predicted stage: {stage}</li>
</ul>

<p><b>Tasks:</b></p>
<ol>
  <li>Highlight only the exact phrases from the report that indicate tumor or malignancy using <mark> tags.</li>
  <li>Briefly summarize tumor size and extent using the provided imaging values.</li>
  <li>Briefly restate the lab-based stage prediction.</li>
  <li>Provide concise clinical recommendations in bullet points.</li>
</ol>

<p><b>Rules:</b></p>
<ul>
  <li>Do not validate, compare, or question predictions</li>
  <li>No TNM or staging logic</li>
  <li>No inconsistency analysis</li>
  <li>HTML only, start with &lt;div&gt;</li>
</ul>

</div>
"""


        ai_resp = chat.send_message(prompt).text

        # -------- OUTPUT IMAGES --------
        output_dir = os.path.join(BASE_DIR, "static", "output_case012")
        png_files = [
            "static/output_case012/" + f
            for f in os.listdir(output_dir)
            if f.endswith(".png")
        ]

        # -------- FIXED NUMERIC DATA --------
        data = {
            "age": int(request.form["age"]),
            "ca19_9": float(request.form["ca19_9"]),
            "total_bilirubin": float(request.form["total_bilirubin"]),
            "alp": float(request.form["alp"]),
            "albumin": float(request.form["albumin"]),
            "nlr": float(request.form["nlr"])
        }

        return render_template(
            "prediction.html",
            result=stage,
            survival=survival,
            explanation=advice,
            AI_REC=ai_resp,
            png_files=png_files,
            volume=volume,
            Shape=shape,
            voxel_count=voxel_count,
            voxel_spacing_mm=spacing,
            middle_slice_index=mid_slice,
            tumor_size_x=size_x,
            tumor_size_y=size_y,
            tumor_size_z=size_z,
            tumor_max_diameter=max_diameter,
            dice="Not applicable (no ground truth)",
            data=data
        )

    # GET request
    return render_template("prediction.html", png_files=png_files)

# ================= MAIN =================
if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "static", "uploads"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "static", "output_case012"), exist_ok=True)
    app.run(debug=True, port=5000, use_reloader=False)
