from flask import Flask
from flask_cors import CORS
from routes.pdf import pdf_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(pdf_bp)

if __name__ == "__main__":
    app.run(debug=True)
