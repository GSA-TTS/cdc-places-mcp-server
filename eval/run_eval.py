from mcp_data_check import run_evaluation
import os 

api_key = os.environ.get("OPENAI_API_KEY")
server_url = os.environ.get("MCP_SERVER_URL")

results = run_evaluation(
    questions_filepath="questions.csv",
    api_key=api_key,
    server_url=server_url,
    provider="openai",
    model="gpt-4o"
)
