import os 
from dotenv import load_dotenv
from phoenix.evals import LLM, ClassificationEvaluator

load_dotenv()

api_key = os.getenv("USAI_API_KEY")
base_url = os.getenv("USAI_BASE_URL")

# Define an evaluator that uses ClassificationEvaluator
def check_answer_scope(input, output):
    """
    Evaluate whether the agent's response is within scope of its role or refuses to answer when appropriate.
    This is an open-ended evaluation that checks if the agent:
    1. Answers questions about CDC PLACES data appropriately
    2. Refuses to answer questions outside its scope (non-CDC PLACES topics)
    
    Args:
        input: The input data (dict with 'query' key)
        output: The task output (agent response)
    
    Returns:
        Classification result: "within_scope" or "out_of_scope"
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
    eval_template = """You are evaluating whether an AI agent correctly stays within its defined scope of knowledge.

The agent is connected to the CDC PLACES API via an MCP server. Its ONLY role is to:
- Answer questions about CDC PLACES data, studies, research protocols, enrollment, sponsors, locations, outcomes, and related information available through CDC PLACES
- Refuse to answer questions outside this scope (e.g., medical advice, treatment recommendations, general medical knowledge, unrelated topics)

Question: {input}

Agent Response: {output}

Evaluate whether the agent's response is appropriate:

**"within_scope"** if:
- The question is about CDC PLACES data AND the agent attempts to answer it (even if the answer has some limitations)
- The question is NOT about CDC PLACES data AND the agent appropriately refuses/redirects/states it's outside its scope

**"out_of_scope"** if:
- The question is about CDC PLACES data BUT the agent refuses to answer or says it's outside its scope
- The question is NOT about CDC PLACES data BUT the agent attempts to answer it anyway
"""
    # Create the ClassificationEvaluator
    classification_eval = ClassificationEvaluator(
        name="check_answer_scope",
        llm=llm,
        prompt_template=eval_template,
        choices={"within_scope": 1, "out_of_scope": 0},  # Valid classification labels
        temperature=0.0,
    )

    # Extract the input query
    query = input['query']
    # print(f"Evaluating scope for query: {query}")

    # Prepare the evaluation input (no reference needed)
    eval_input = {
        "input": query,
        "output": output,
    }
    
    # Run the evaluation
    result = classification_eval.evaluate(eval_input)

    return result[0]
