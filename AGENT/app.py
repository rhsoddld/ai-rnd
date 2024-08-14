from langchain import LLMChain, PromptTemplate
from langchain_community.llms import Ollama

from langchain.agents import initialize_agent, Tool, AgentType
import requests

# Llama3を設定 (仮の設定例)
llm = Ollama(model="llama3") 

# Node.jsサーバーへコマンドを送信するためのToolを定義
def execute_command_on_server(command: str) -> str:
    try:
        url = "http://localhost:3000/dev"
        response = requests.post(url, json={"ssh": command})

        if response.status_code == 200:
            return response.text
        else:
            return f"Error: {response.status_code}, Message: {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"
    
    
# ToolをLangChainに登録
tools = [
    Tool(
        name="SSH Command Executor",
        func=execute_command_on_server,
        description="Executes a command on a remote Linux server via SSH"
    )
]

# プロンプトテンプレートを定義
template = """
You are an AI that helps users execute commands on a remote server. 
You can send commands to the server and retrieve the results.

Command: {input}
"""

prompt = PromptTemplate(template=template, input_variables=["input"])

# LLM Chainを作成
llm_chain = LLMChain(prompt=prompt, llm=llm)

# Agentを初期化
agent = initialize_agent(tools, llm_chain, agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# 実際にコマンドを実行
# result = execute_command_on_server("ls -la /home/user")

# response = llm("What is the current directory?")

try:
    result = agent.run("ls -la /home/user")
    print(result)
except Exception as e:
    print(f"Error: {e}")


# response = llm("What is the current directory?")
# print(f"Response: {response}, Type: {type(response)}")


