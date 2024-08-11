import os
from flask import Flask, request, render_template, jsonify
from embedchain import App
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Embedchain bot
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
elon_bot = App()

# Ensure the uploads directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Route for the home page with the upload form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file uploads and bot queries
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400
    
    # Save the file to the server
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    try:
        file.save(file_path)
        # Add the PDF file to the bot
        elon_bot.add("pdf_file", file_path)
        return jsonify({"success": f"File {file.filename} successfully uploaded and added to the bot"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to handle queries to the bot
@app.route('/query', methods=['POST'])
def query_bot():
    question = request.form.get('question', '')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        response = elon_bot.query(question)
        return jsonify({"response": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
