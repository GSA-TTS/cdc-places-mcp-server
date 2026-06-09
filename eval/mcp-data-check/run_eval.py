from mcp_data_check import Evaluator
import os 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
server_url = os.environ.get("MCP_SERVER_URL")

# Initialize the Evaluator with the MCP server URL and OpenAI API key
evaluator = Evaluator(
    server_url=server_url,
    api_key=api_key,
    provider="openai",
    model="gpt-4o"
)

# Load questions from a CSV file, run the comparison against the MCP server, and save the results
questions = evaluator.load_questions("eval/questions.csv")
comparison = evaluator.run_comparison(questions, repeats=5, verbose=True)
output_path = evaluator.save_comparison(comparison, "./eval/results")                                                                                                                                                                                                                                  
print(f"Results saved to: {output_path}")