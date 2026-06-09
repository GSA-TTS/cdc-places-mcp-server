import os 
from dotenv import load_dotenv
from phoenix.evals import LLM, ClassificationEvaluator

load_dotenv()

api_key = os.getenv("USAI_API_KEY")
base_url = os.getenv("USAI_BASE_URL")

# Define an evaluator that uses ClassificationEvaluator
def match_expected_response(input, output, expected):
    """
    Evaluate the correctness of the agent's output by comparing it to the expected response.
    
    Args:
        input: The input data (dict with 'query' key)
        output: The task output (agent response)
        expected: The expected (reference) response to compare against (dict with 'responses' key)
    
    Returns:
        Classification result: "correct" or "incorrect"
    """

    # Initialize the LLM wrapper for USAi
    llm = LLM(
        provider="openai",
        client="langchain", 
        model="claude_4_5_sonnet",
        base_url=base_url + "/api/v1",
        api_key=api_key,
    )

    # Define the evaluation prompt template
    eval_template = """You are evaluating the correctness of an AI agent's response to a question about CDC PLACES data.

Question: {input}

Expected Response: {reference}

Actual Response: {output}

Compare the actual response to the expected response. Determine if the actual response is correct based on whether it:
1. Contains the key information from the expected response
2. Provides accurate and relevant information
3. Answers the question appropriately

Respond with ONLY "correct" or "incorrect" based on your evaluation."""

    # Create the ClassificationEvaluator
    classification_eval = ClassificationEvaluator(
        name="match_expected_response",
        llm=llm,
        prompt_template=eval_template,
        choices={"correct": 1, "incorrect": 0},  # Valid classification labels
        temperature=0.0,
    )

    # Extract the expected response
    expected_response = expected['responses']

    # Extract the input query
    query = input['query']
    # print(f"Evaluating output for query: {query}")

    # Prepare the evaluation input with all three components
    eval_input = {
        "input": query,
        "output": output,
        "reference": expected_response,
    }
    
    # Run the evaluation
    result = classification_eval.evaluate(eval_input)

    return result[0]
