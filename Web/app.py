# from flask import Flask, render_template, request, jsonify
# import requests

# app = Flask(__name__)

# # # Ollamaのエンドポイント（必要に応じて変更してください）
# # OLLAMA_API_URL = "http://localhost:11411/api/chat"

# # def get_ollama_response(message):
# #     data = {
# #         "model": "llama3",  # 使用するモデルを指定
# #         "messages": [{"role": "user", "content": message}],
# #     }
# #     response = requests.post(OLLAMA_API_URL, json=data)
# #     return response.json()["choices"][0]["message"]["content"]

# OLLAMA_API_URL = "http://localhost:11434/api/generate"

# def get_ollama_response(message):
#     data = {
#         "model": "llama3",
#         "prompt": message,
#         "stream": False
#     }
#     response = requests.post(OLLAMA_API_URL, json=data)
#     return response.json()["response"]


# @app.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         user_input = request.form["user_input"]
#         ollama_response = get_ollama_response(user_input)
#         return jsonify({"response": ollama_response})
#     return render_template("index.html")

# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Ollamaのエンドポイント（ポートを修正済み）
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# チャット履歴を保持するためのリスト
chat_history = []

def get_ollama_response(message):
    # チャット履歴に新しいユーザーのメッセージを追加
    chat_history.append({"role": "user", "content": message})
    
    # Ollamaに送信するリクエストデータ
    data = {
        "model": "llama3",
        "prompt": generate_prompt(),
        "stream": False
    }
    
    # Ollamaへのリクエスト
    response = requests.post(OLLAMA_API_URL, json=data)
    ollama_message = response.json()["response"]

    # Ollamaの応答をチャット履歴に追加
    chat_history.append({"role": "assistant", "content": ollama_message})
    
    return ollama_message

def generate_prompt():
    # チャット履歴をプロンプトとして結合
    prompt = "\n".join([f'{msg["role"]}: {msg["content"]}' for msg in chat_history])
    return prompt

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["user_input"]
        ollama_response = get_ollama_response(user_input)
        return jsonify({"response": ollama_response, "chat_history": chat_history})
    return render_template("index.html", chat_history=chat_history)

if __name__ == "__main__":
    app.run(debug=True)



