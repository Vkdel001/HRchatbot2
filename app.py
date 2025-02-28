from flask import Flask, request, render_template, jsonify
import os
from embedchain import App
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util

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

# Load pre-trained Sentence Transformer model for semantic similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

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
        # Query the bot
        response = elon_bot.query(question)
        
        # Check for relevance using semantic matching
        if not is_relevant_semantically(question, response):
            return jsonify({"response": "Sorry, I can only answer questions based on HR Policies."}), 200
        
        return jsonify({"response": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to check if the response is relevant to the question using semantic similarity
def is_relevant_semantically(question, response, threshold=0.75):
    # Encode the question and response into vectors
    question_embedding = model.encode(question, convert_to_tensor=True)
    response_embedding = model.encode(response, convert_to_tensor=True)
    
    # Compute cosine similarity between the question and response
    similarity_score = util.pytorch_cos_sim(question_embedding, response_embedding).item()
    
    # Check if the similarity score is above the threshold
    return similarity_score >= threshold

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
