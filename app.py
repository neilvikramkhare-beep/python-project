import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

# Import custom modules
from solver import solve_math_problem
from image_reader import extract_math_from_image
from formatter import format_result

# --- Flask Setup ---
app = Flask(__name__)

# Upload folder config
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- Helper Functions ---
def allowed_file(filename):
    """Check allowed file extensions."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Routes ---
@app.route("/", methods=["GET"])
def index():
    """Render main UI (single-page frontend)."""
    return render_template("index.html")


@app.route("/solve", methods=["POST"])
def solve():
    """
    Handles both:
    - Text input
    - Image upload (OCR)
    Returns HTML snippet (AJAX response).
    """
    math_expression = ""
    source = ""

    # --- IMAGE INPUT ---
    if "math_image" in request.files and request.files["math_image"].filename != "":
        image_file = request.files["math_image"]

        if allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)

            # Extract math from image
            math_expression = extract_math_from_image(image_path)
            source = "image"

            # Delete file after processing
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except:
                pass

        else:
            return error_html("Invalid file type. Upload PNG/JPG.")

    # --- TEXT INPUT ---
    elif "math_text" in request.form and request.form["math_text"].strip():
        math_expression = request.form["math_text"].strip()
        source = "text"

    else:
        return error_html("Please enter a math problem or upload an image.")

    # --- VALIDATION ---
    if not math_expression:
        return error_html("Could not read any math expression.")

    # --- SOLVE ---
    result_data = solve_math_problem(math_expression)

    # --- FORMAT RESULT ---
    formatted = format_result(result_data, math_expression, source)

    # --- HANDLE ERROR FROM SOLVER ---
    if formatted.get("error_message"):
        return error_html(formatted["error_message"])

    # --- BUILD HTML RESPONSE (AJAX) ---
    steps_html = ""
    for step in formatted["steps"]:
        steps_html += f"""
        <div class='step'>
            <b>{step['title']}</b><br>
            {step['explanation']}
        </div>
        """

    extra_html = ""
    if formatted["problem_type"] == "simplify":
        extra = formatted["extra_info"]
        extra_html = f"""
        <div class='step'>
            <b>Expanded:</b> {extra.get('expanded', '')}<br>
            <b>Factored:</b> {extra.get('factored', '')}
        </div>
        """

    return f"""
    <div class='result-box'>
        <h3>{formatted['type_icon']} {formatted['type_label']}</h3>

        <p><b>Source:</b> {formatted['source_label']}</p>
        <p><b>Input:</b> {formatted['original_input']}</p>
        <p><b>Answer:</b> {formatted['answer']}</p>

        {extra_html}

        {steps_html}
    </div>
    """


@app.route("/back")
def back():
    """Optional route (not needed for AJAX UI)."""
    return redirect(url_for("index"))


# --- Error HTML Helper ---
def error_html(message):
    return f"""
    <div class='result-box' style='color:red;'>
        <b>⚠️ Error:</b> {message}
    </div>
    """


# --- Run App ---
if __name__ == "__main__":
    print("🚀 Math Solver running at: http://127.0.0.1:5000")
    app.run(debug=True)
