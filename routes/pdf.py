from flask import Blueprint, request, send_file
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from pdf2docx import Converter
import os, io, zipfile

pdf_bp = Blueprint("pdf", __name__)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# ✅ PDF to Word
@pdf_bp.route("/api/pdf-to-word", methods=["POST"])
def pdf_to_word():
    file = request.files.get("pdf_file")
    if not file: return "No PDF file uploaded", 400

    filename = secure_filename(file.filename)
    base = os.path.splitext(filename)[0]
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_path = os.path.join(RESULT_FOLDER, f"{base}_converted.docx")
    file.save(input_path)

    try:
        cv = Converter(input_path)
        cv.convert(output_path)
        cv.close()
        os.remove(input_path)
        return send_file(output_path, as_attachment=True, download_name=f"{base}.docx")
    except Exception as e:
        return f"Conversion failed: {str(e)}", 500

# ✅ Compress PDF
@pdf_bp.route("/api/compress-pdf", methods=["POST"])
def compress_pdf():
    file = request.files.get("compress_pdf")
    if not file: return "No file uploaded", 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.compress_content_streams()

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    os.remove(input_path)

    return send_file(output_stream, as_attachment=True, download_name=f"{filename.rsplit('.',1)[0]}_compressed.pdf")

# ✅ Merge PDFs
@pdf_bp.route("/api/merge-pdf", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("merge_pdf")
    if not files: return "No PDF files uploaded", 400

    merger = PdfMerger()
    paths = []
    for f in files:
        fname = secure_filename(f.filename)
        path = os.path.join(UPLOAD_FOLDER, fname)
        f.save(path)
        paths.append(path)
        merger.append(path)

    output_path = os.path.join(RESULT_FOLDER, "merged_output.pdf")
    merger.write(output_path)
    merger.close()

    for p in paths: os.remove(p)
    return send_file(output_path, as_attachment=True, download_name="merged_output.pdf")

# ✅ Split PDF
@pdf_bp.route("/api/split-pdf", methods=["POST"])
def split_pdf():
    file = request.files.get("split_pdf")
    if not file: return "No file uploaded", 400

    fname = secure_filename(file.filename)
    base = os.path.splitext(fname)[0]
    input_path = os.path.join(UPLOAD_FOLDER, fname)
    file.save(input_path)

    reader = PdfReader(input_path)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            buffer = io.BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            zipf.writestr(f"{base}_page_{i+1}.pdf", buffer.read())

    zip_buffer.seek(0)
    os.remove(input_path)
    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name=f"{base}_split_pages.zip")

# ✅ Encrypt PDF
@pdf_bp.route("/api/encrypt-pdf", methods=["POST"])
def encrypt_pdf():
    file = request.files.get("pdf_file")
    password = request.form.get("password")
    if not file: return "No file uploaded", 400
    if not password: return "Password required", 400

    fname = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, fname)
    file.save(input_path)

    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    os.remove(input_path)

    return send_file(output_stream, as_attachment=True, download_name=f"{fname.rsplit('.',1)[0]}_encrypted.pdf")

# ✅ Decrypt PDF
@pdf_bp.route("/api/decrypt-pdf", methods=["POST"])
def decrypt_pdf():
    file = request.files.get("pdf_file")
    password = request.form.get("password")
    if not file: return "No file uploaded", 400
    if not password: return "Password required", 400

    fname = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, fname)
    file.save(input_path)

    try:
        reader = PdfReader(input_path)
        if not reader.is_encrypted: return "PDF is not encrypted", 400
        if not reader.decrypt(password): return "Incorrect password", 401

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        os.remove(input_path)

        return send_file(output_stream, as_attachment=True, download_name=f"{fname.rsplit('.',1)[0]}_decrypted.pdf")
    except Exception as e:
        os.remove(input_path)
        return f"Decryption failed: {str(e)}", 500

# ✅ Rotate PDF
@pdf_bp.route("/api/rotate-pdf", methods=["POST"])
def rotate_pdf():
    file = request.files.get("pdf_file")
    angle = request.form.get("angle")
    if not file: return "No file uploaded", 400
    try:
        angle = int(angle)
        if angle % 90 != 0: return "Angle must be multiple of 90", 400
    except:
        return "Invalid angle", 400

    fname = secure_filename(file.filename)
    base = os.path.splitext(fname)[0]
    input_path = os.path.join(UPLOAD_FOLDER, fname)
    output_path = os.path.join(RESULT_FOLDER, f"{base}_rotated.pdf")
    file.save(input_path)

    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)

    with open(output_path, "wb") as f: writer.write(f)
    os.remove(input_path)

    return send_file(output_path, as_attachment=True, download_name=f"{base}_rotated.pdf")

# ✅ Extract Images
@pdf_bp.route("/api/extract-images", methods=["POST"])
def extract_images():
    file = request.files.get("pdf_file")
    if not file: return "No file uploaded", 400

    fname = secure_filename(file.filename)
    base = os.path.splitext(fname)[0]
    input_path = os.path.join(UPLOAD_FOLDER, fname)
    file.save(input_path)

    reader = PdfReader(input_path)
    images = []
    count = 1
    for page in reader.pages:
        if "/XObject" in page["/Resources"]:
            xObject = page["/Resources"]["/XObject"].get_object()
            for obj in xObject:
                item = xObject[obj]
                if item["/Subtype"] == "/Image":
                    ext = "jpg" if item["/Filter"] == "/DCTDecode" else "png"
                    data = item.get_data()
                    images.append((f"{base}_img_{count}.{ext}", data))
                    count += 1

    if not images:
        os.remove(input_path)
        return "No images found", 404

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for name, data in images:
            zipf.writestr(name, data)

    zip_buffer.seek(0)
    os.remove(input_path)

    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name=f"{base}_images.zip")
