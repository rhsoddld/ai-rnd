from flask import Flask, render_template, request, redirect, url_for
from crewai import Agent, Task, Crew, Process
from langchain_ollama import ChatOllama
from crewai_tools import BaseTool
import requests

app = Flask(__name__)

# Define your Llama model
llm = ChatOllama(
    model="llama3.1",
    base_url="http://localhost:11434"
)

# Define global variables to store goals and backstories
server_goal = "Develop and investigate configurations, providing appropriate setup procedures and recommendations."
server_backstory = "You're a skilled server engineer responsible for researching, developing, and configuring server environments efficiently."

tester_goal = "Validate development and configuration, creating suitable test plans and execution procedures."
tester_backstory = "You're an experienced tester focused on verifying the correctness and performance of configurations and developments."

manager_goal = "Review and ensure that the Server Engineer's and Tester's outputs meet the required standards from a managerial perspective."
manager_backstory = "You're a seasoned engineer manager responsible for overseeing team outputs, ensuring quality and alignment with project goals."

# Define the tool using BaseTool
class ExecuteCommandTool(BaseTool):
    name: str = "Execute Command on Server"
    description: str = "Executes a command on a remote Linux server via SSH, Linux distribution is CentOS Stream release 9."
    
    def _run(self, command: str, ssh_server_url: str) -> str:
        """リモートサーバーでコマンドを実行する"""
        try:
            response = requests.post(ssh_server_url, json={"command": command})
            if response.status_code == 201:
                return response.text
            else:
                return f"Error: {response.status_code}, Message: {response.text}"
        except Exception as e:
            return f"Exception occurred: {str(e)}"

# Create an instance of the tool
execute_command_tool = ExecuteCommandTool()

@app.route('/', methods=['GET', 'POST'])
def index():
    global server_goal, server_backstory, tester_goal, tester_backstory, manager_goal, manager_backstory

    if request.method == 'POST':
        task_description = request.form.get('task_description')

        # Define agents with updated goals and backstories
        server_engineer = Agent(
            role="Server Engineer",
            goal=server_goal,
            backstory=server_backstory,
            allow_delegation=True,
            verbose=True,
            llm=llm,
            tools=[execute_command_tool]  # Add the tool for the agent
        )

        tester = Agent(
            role="Tester",
            goal=tester_goal,
            backstory=tester_backstory,
            allow_delegation=True,
            verbose=True,
            llm=llm,
            tools=[execute_command_tool]  # Add the tool for the agent
        )

        manager = Agent(
            role="Engineer Manager",
            goal=manager_goal,
            backstory=manager_backstory,
            allow_delegation=True,
            verbose=True,
            llm=llm
        )

        task = Task(
            description=task_description,
            expected_output="Detailed setup steps, test plans, execution results, and a summary of findings.",
        )

        crew = Crew(
            agents=[server_engineer, tester],
            tasks=[task],
            manager_agent=manager,
            process=Process.hierarchical,
            full_output=True,
            verbose=True,
        )

        crew_output = crew.kickoff()

        # Debug: Check the type and content of result
        print(f"Result Type: {type(crew_output)}, Content: {crew_output}")

        return render_template(
            'index.html',
            final_result=crew_output,
            server_goal=server_goal,
            server_backstory=server_backstory,
            tester_goal=tester_goal,
            tester_backstory=tester_backstory,
            manager_goal=manager_goal,
            manager_backstory=manager_backstory
        )

    return render_template(
        'index.html',
        server_goal=server_goal,
        server_backstory=server_backstory,
        tester_goal=tester_goal,
        tester_backstory=tester_backstory,
        manager_goal=manager_goal,
        manager_backstory=manager_backstory
    )

@app.route('/update_server', methods=['POST'])
def update_server():
    global server_goal, server_backstory
    server_goal = request.form.get('server_goal', server_goal)
    server_backstory = request.form.get('server_backstory', server_backstory)
    return redirect(url_for('index'))

@app.route('/update_tester', methods=['POST'])
def update_tester():
    global tester_goal, tester_backstory
    tester_goal = request.form.get('tester_goal', tester_goal)
    tester_backstory = request.form.get('tester_backstory', tester_backstory)
    return redirect(url_for('index'))

@app.route('/update_manager', methods=['POST'])
def update_manager():
    global manager_goal, manager_backstory
    manager_goal = request.form.get('manager_goal', manager_goal)
    manager_backstory = request.form.get('manager_backstory', manager_backstory)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
