from crewai import Agent, Task, Crew, Process
from langchain_ollama import ChatOllama

# Define your Llama model
llm = ChatOllama(
    model="llama3.1",
    base_url="http://localhost:11434"
)

# Define your agents with general role-based goals
server_engineer = Agent(
    role="Server Engineer",
    goal="Develop and investigate configurations, providing appropriate setup procedures and recommendations.",
    backstory="You're a skilled server engineer responsible for researching, developing, and configuring server environments efficiently.",
    allow_delegation=False,
    verbose=True,
    llm=llm
)

tester = Agent(
    role="Tester",
    goal="Validate development and configuration, creating suitable test plans and execution procedures.",
    backstory="You're an experienced tester focused on verifying the correctness and performance of configurations and developments.",
    allow_delegation=False,
    verbose=True,
    llm=llm
)

# Define the manager agent with a managerial goal
manager = Agent(
    role="Engineer Manager",
    goal="Review and ensure that the Server Engineer's and Tester's outputs meet the required standards from a managerial perspective.",
    backstory="You're a seasoned engineer manager responsible for overseeing team outputs, ensuring quality and alignment with project goals.",
    allow_delegation=True,
    verbose=True,
    llm=llm
)

# Define your specific task
task = Task(
    description="Install httpd server on a Linux environment, perform configuration, and conduct basic tests to ensure it is operational. Provide a summary of installation steps, testing procedures, and any issues encountered.",
    expected_output="Detailed setup steps, test plans, execution results, and a summary of findings."
)

# Instantiate your crew with a custom manager
crew = Crew(
    agents=[server_engineer, tester],
    tasks=[task],
    manager_agent=manager,
    process=Process.hierarchical
)

# Start the crew's work
result = crew.kickoff()

print(result)
