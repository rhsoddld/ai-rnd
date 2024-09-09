from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from flask_cors import CORS
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate
import requests
import ollama
import os

# Flaskアプリケーションの設定
app = Flask(__name__)
CORS(app)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "supersecretkey"  # セッションの暗号化キー
Session(app)

# 定数とパスの設定
OLLAMA_API_URL = "http://localhost:11434/api/generate"
UPLOAD_FOLDER = './pdf/'
DB_FOLDER_PATH = "./db/"
FLASK_PORT = "5000"
SSH_PORT = "5000"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# RAG関連の設定
embedding = FastEmbedEmbeddings()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=80, length_function=len)
raw_prompt = PromptTemplate.from_template(
    """<s>[INST] You are a technical assistant good at searching documents. If you do not have an answer from the provided information say so. [/INST] </s>
    [INST] {input} Context: {context} Answer: [/INST]"""
)

# ツールの定義
execute_tool = {
    'type': 'function',
    'function': {
        'name': 'execute_command_on_server',
        'description': 'Executes a command on a remote Linux server via SSH, Linux distribution is CentOS Stream release 9.',
        'parameters': {
            'type': 'object',
            'properties': {'command': {'type': 'string', 'description': 'Executes a command (bash linux command)'}},
            'required': ['command'],
        },
    },
}

ask_pdf_tool = {
    'type': 'function',
    'function': {
        'name': 'ask_pdf_tool_handler',
        'description': 'Queries a PDF document using the Chroma vector store and retrieves relevant information.',
        'parameters': {
            'type': 'object',
            'properties': {'query': {'type': 'string', 'description': 'The query to search within the PDF content.'}},
            'required': ['query'],
        },
    },
}

def execute_command_on_server(command: str, ssh_server_url: str) -> str:
    """リモートサーバーでコマンドを実行する"""
    try:
        response = requests.post(ssh_server_url, json={"command": command})
        if response.status_code == 201:
            return response.text
        else:
            return f"Error: {response.status_code}, Message: {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def get_ollama_response(message, system_prompt, model):
    """Ollamaのチャット応答を取得する"""
    if "chat_history" not in session:
        session["chat_history"] = []
    chat_history = session["chat_history"]

    if system_prompt:
        chat_history.append({"role": "assistant", "content": system_prompt})

    chat_history.append({"role": "user", "content": message})

    messages = [{'role': 'assistant', 'content': system_prompt}] if system_prompt else []
    messages.append({'role': 'user', 'content': message})

    # ツールの実行が必要かどうかを判定
    execute_tool_flag = "execute" in message.lower()  # `execute`が含まれている場合のみ実行
    ask_pdf_tool_flag = "pdf" in message.lower() or "document" in message.lower()  # `pdf`または`document`が含まれている場合のみ実行

    # 実行が必要なツールのみをリストに含める
    tools_to_use = []
    if execute_tool_flag:
        tools_to_use.append(execute_tool)
    if ask_pdf_tool_flag:
        tools_to_use.append(ask_pdf_tool)

    # Ollamaの呼び出し
    response = ollama.chat(model=model, messages=messages, tools=tools_to_use)

    # ツールが呼び出された場合の処理
    if response['message'].get('tool_calls'):
        for tool in response['message']['tool_calls']:
            tool_name = tool['function']['name']
            args = list(tool['function']['arguments'].values())

            if tool_name == 'execute_command_on_server' and execute_tool_flag:
                print("execute_command_on_server called with args:", args)
            elif tool_name == 'ask_pdf_tool_handler' and ask_pdf_tool_flag:
                print("ask_pdf_tool_handler called with query:", args)
                ollama_message = handle_ask_pdf_tool(args, model)
                chat_history.append({"role": "assistant", "content": ollama_message})
                session["chat_history"] = chat_history
                return ollama_message, args
            break
        
        session["chat_history"] = chat_history
        return response['message']['content'], args
    else:
        ollama_message = response['message']['content']
        chat_history.append({"role": "assistant", "content": ollama_message})
        session["chat_history"] = chat_history
        return ollama_message, []

def handle_ask_pdf_tool(args, model):
    """ask_pdf_tool_handlerの呼び出しとレスポンスの整形"""
    query = args[0]

    # modelを引数として渡して関数を呼び出す
    response_answer = ask_pdf_tool_handler(query, model)

    if response_answer.get("status") == "Failed":
        ollama_message = f"Error: {response_answer['error']}"
    else:
        ollama_message = f"Answer:\n{response_answer['answer']}\n\nSources:\n"
        # for source in response_answer['sources']:
        #     ollama_message += f"- {source['source']}:\n  {source['page_content']}\n\n"

    print("Formatted response with line breaks:", ollama_message)
    return ollama_message


def get_final_response(messages, model):
    """最終応答の取得"""
    chat_history = session["chat_history"]
    final_response = ollama.chat(model=model, messages=messages)
    chat_history.append({"role": "assistant", "content": final_response['message']['content']})
    session["chat_history"] = chat_history
    return final_response['message']['content']

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["user_input"]
        selected_prompt = request.form.get("selected_prompt")
        selected_model = request.form.get("selected_model")

        # システムプロンプトの選択
        prompt_dict = {
            "develop": "You are in development mode.",
            "test": "You are in testing mode.",
            "deploy": "You are in deployment mode.",
            "operate": "You are in operation mode."
        }
        system_prompt = prompt_dict.get(selected_prompt, None)
        print(system_prompt)

        ollama_response, args = get_ollama_response(user_input, system_prompt, selected_model)
        return jsonify({"response": ollama_response, "args": args, "chat_history": session.get("chat_history", [])})
    return render_template("index.html", chat_history=session.get("chat_history", []))

@app.route("/execute", methods=["POST"])
def execute():
    command = request.json.get("command")
    selected_server = request.json.get("server_selection")
    selected_model = request.json.get("selected_model")

    ssh_server_url = f"http://{selected_server}:{SSH_PORT}/ssh"
    function_response = execute_command_on_server(command, ssh_server_url)

    chat_history = session.get("chat_history", [])
    chat_history.append({"role": "tool", "content": function_response})
    session["chat_history"] = chat_history

    messages = [{'role': 'tool', 'content': function_response}]
    final_response = get_final_response(messages, selected_model)

    return jsonify({"function_response": function_response, "final_response": final_response, "chat_history": session.get("chat_history", [])})

@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    session["chat_history"] = []
    return jsonify({"message": "Chat history cleared."})

@app.route("/pdf", methods=["POST"])
def pdfPost():
    """PDFのアップロードとベクターストアの作成"""
    try:
        file = request.files["file"]
        file_name = file.filename
        save_file = os.path.join(UPLOAD_FOLDER, file_name)
        file.save(save_file)

        loader = PDFPlumberLoader(save_file)
        docs = loader.load_and_split()
        chunks = text_splitter.split_documents(docs)

        try:
            vector_store = Chroma.from_documents(documents=chunks, embedding=embedding, persist_directory=DB_FOLDER_PATH)
            # vector_store.persist()
        except Exception as e:
            print(f"An error occurred during Chroma processing: {e}")

        return {"status": "Successfully Uploaded", "filename": file_name}
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({'status': 'Failed', 'error': str(e)}), 500

@app.route("/ask_pdf_tool", methods=["POST"])
def ask_pdf_tool_handler(query, selected_model):
    """PDFベクターストアに対するクエリの処理"""
    try:
        print(f"Received query: {query}, Model: {selected_model}")

        if not selected_model:
            print("Error: selected_model is None")
            return {"status": "Failed", "error": "selected_model is None"}

        # selected_modelを使用してLLMを選択
        llm = Ollama(model=selected_model)

        vector_store = Chroma(persist_directory=DB_FOLDER_PATH, embedding_function=embedding)
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 20, "score_threshold": 0.1}
        )

        # document_chainの作成時にselected_modelを使用
        document_chain = create_stuff_documents_chain(llm, raw_prompt)
        chain = create_retrieval_chain(retriever, document_chain)
        result = chain.invoke({"input": query})

        sources = [{"source": doc.metadata["source"], "page_content": doc.page_content} for doc in result["context"]]
        response_answer = {"answer": result["answer"], "sources": sources}
        return response_answer

    except Exception as e:
        print(f"Error occurred in ask_pdf_tool_handler: {e}")
        return {"status": "Failed", "error": str(e)}
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)