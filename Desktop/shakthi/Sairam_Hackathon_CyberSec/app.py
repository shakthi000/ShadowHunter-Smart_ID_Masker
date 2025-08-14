from flask import Flask, request, render_template, send_file, url_for
from processor import process_file
import os
import zipfile
import tempfile

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
OUTPUT_FOLDER = "static/output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def upload():
    preview_imgs = []
    download_url = None

    if request.method == "POST":
        if "file" not in request.files or request.files["file"].filename == "":
            return render_template("index.html", preview_imgs=[], download_url=None, error="No file uploaded.")

        file = request.files["file"]
        mask_type = request.form.get("mask_type", "blur")
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        try:
            results = process_file(filepath, mask_type)
        except Exception as e:
            return render_template("index.html", preview_imgs=[], download_url=None, error=f"Processing failed: {e}")

        if isinstance(results, list):  # Multiple images (PDF)
            preview_imgs = [url_for("static", filename="output/" + os.path.basename(r)) for r in results]
            zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for f in results:
                    zipf.write(f, os.path.basename(f))
            download_url = url_for("download_zip", path=zip_path)
        else:
            preview_imgs = [url_for("static", filename="output/" + os.path.basename(results))]
            download_url = preview_imgs[0]

    return render_template("index.html", preview_imgs=preview_imgs, download_url=download_url, error=None)

@app.route("/download_zip")
def download_zip():
    path = request.args.get("path")
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name="masked_results.zip")
    return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True)