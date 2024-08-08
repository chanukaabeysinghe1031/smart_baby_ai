from flask import Flask, request, jsonify
import os
import openai
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)

# Load environment variables
api_key = os.getenv("OPENAI_API_KEY")

# Ensure API key is set
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

# Initialize OpenAI client
openai.api_key = api_key


@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    user_id = data.get("userId")
    question = data.get("question")

    if not user_id or not question:
        return jsonify({"message": "userId and question are required"}), 400

    try:
        # Create a thread with the question
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}],
            max_tokens=150,
        )

        answer = response.choices[0].message["content"].strip()

        return jsonify({"response": answer})

    except Exception as e:
        return jsonify({"message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
