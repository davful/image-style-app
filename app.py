from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, send_file, url_for
import os
import openai
import base64
import requests
import uuid

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_image_with_openai(image_path, style):
    with open(image_path, "rb") as img_file:
        img_data = base64.b64encode(img_file.read()).decode("utf-8")
    prompt = "Make this into a semi-realistic cartoon" if style == "cartoon" else "Make this into a black and white vector line art"
    response = openai.Image.create_edit(
        image=img_data,
        mask=None,
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="url"
    )
    return response["data"][0]["url"]

def cache_image(url, style):
    response = requests.get(url)
    if response.status_code == 200:
        filename = f"{style}_{uuid.uuid4().hex}.png"
        path = os.path.join("static/results", filename)
        with open(path, "wb") as f:
            f.write(response.content)
        return filename
    return None

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        image = request.files["image"]
        style = request.form["style"]
        filepath = os.path.join("uploads", image.filename)
        image.save(filepath)
        try:
            result_url = generate_image_with_openai(filepath, style)
            result_file = cache_image(result_url, style)
            if result_file:
                return render_template("index.html", result_file=result_file)
            else:
                return "Error caching image."
        except Exception as e:
            return f"Error: {e}"
    return render_template("index.html")

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join("static/results", filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('static/results', exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

