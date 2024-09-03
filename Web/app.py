from flask import Flask, render_template, request, jsonify, session
import requests
import ollama
from flask_session import Session

app = Flask(__name__)

# セッションの設定
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "supersecretkey"  # セッションの暗号化キー
Session(app)

OLLAMA_API_URL = "http://localhost:11434/api/generate"


def execute_command_on_server(command: str, ssh_server_url: str) -> str:
    try:
        response = requests.post(ssh_server_url, json={"command": command})
        if response.status_code == 201:
            return response.text
        else:
            return f"Error: {response.status_code}, Message: {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"


execute_tool = {
    'type': 'function',
    'function': {
        'name': 'execute_command_on_server',
        'description': 'Executes a command on a remote Linux server via SSH, Linux distribution is CentOS Stream release 9.',
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'Executes a command (bash linux command)',
                },
            },
            'required': ['command'],
        },
    },
}


def get_ollama_response(message, system_prompt, model):
    if "chat_history" not in session:
        session["chat_history"] = []

    chat_history = session["chat_history"]

    if system_prompt:
        chat_history.append({"role": "assistant", "content": system_prompt})

    chat_history.append({"role": "user", "content": message})

    messages = [{'role': 'assistant', 'content': system_prompt}] if system_prompt else []
    messages.append({'role': 'user', 'content': message})
    args = None

    response = ollama.chat(
        model=model,  # Use the selected model
        messages=messages,
        tools=[execute_tool],
    )

    if response['message'].get('tool_calls'):
        for tool in response['message']['tool_calls']:
            args = list(tool['function']['arguments'].values())
            break  # 一つのツール呼び出しだけを処理します

        session["chat_history"] = chat_history
        return response['message']['content'], args
    else:
        ollama_message = response['message']['content']
        chat_history.append({"role": "assistant", "content": ollama_message})
        session["chat_history"] = chat_history
        return ollama_message, args


def get_final_response(messages, model):
    chat_history = session["chat_history"]
    final_response = ollama.chat(model=model, messages=messages)  # 選択されたモデルを使用
    chat_history.append({"role": "assistant", "content": final_response['message']['content']})
    session["chat_history"] = chat_history
    return final_response['message']['content']


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["user_input"]
        selected_prompt = request.form.get("selected_prompt")
        selected_model = request.form.get("selected_model")  # Get the selected model

        system_prompt = None
        if selected_prompt == "develop":
            system_prompt = "You are in development mode."
        elif selected_prompt == "test":
            system_prompt = "You are in testing mode."
        elif selected_prompt == "deploy":
            system_prompt = "You are in deployment mode."
        elif selected_prompt == "operate":
            system_prompt = "You are in operation mode."

        ollama_response, args = get_ollama_response(user_input, system_prompt, selected_model)

        return jsonify({"response": ollama_response, "args": args, "chat_history": session.get("chat_history", [])})
    return render_template("index.html", chat_history=session.get("chat_history", []))


@app.route("/execute", methods=["POST"])
def execute():
    command = request.json.get("command")
    selected_server = request.json.get("server_selection")
    selected_model = request.json.get("selected_model")  # 選択されたモデルを取得

    # SSH_SERVER_URLを動的に設定
    ssh_server_url = f"http://{selected_server}:3000/ssh"
    function_response = execute_command_on_server(command, ssh_server_url)

    # コマンド実行結果をメッセージに追加
    chat_history = session.get("chat_history", [])
    chat_history.append({"role": "tool", "content": function_response})
    session["chat_history"] = chat_history

    # 実行後に最終応答を取得
    messages = [{'role': 'tool', 'content': function_response}]
    final_response = get_final_response(messages, selected_model)  # 選択されたモデルを渡す

    return jsonify({"function_response": function_response, "final_response": final_response, "chat_history": session.get("chat_history", [])})


@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    session["chat_history"] = []  # チャット履歴をクリア
    return jsonify({"message": "Chat history cleared."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
