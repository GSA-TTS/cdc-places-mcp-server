import asyncio
import os 
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

# Phoenix imports for standalone server
from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register

load_dotenv()

api_key = os.getenv("USAI_API_KEY")
base_url = os.getenv("USAI_BASE_URL")

class CDCPlacesAgent:
    """Reusable CDC PLACES Agent for Phoenix experiments"""
    
    def __init__(self, project_name="cdc-places-agent", phoenix_endpoint="http://localhost:4317", prompt_version="v01"):
        self.api_key = api_key
        self.base_url = base_url
        self.project_name = project_name
        self.phoenix_endpoint = phoenix_endpoint
        self.prompt_version = prompt_version
        self.agent = None
        self.client = None
        self._initialized = False
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from file
        
        Returns:
            str: The system prompt content
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "prompts",
            f"system_prompt_{self.prompt_version}.txt"
        )
        
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(
                f"System prompt file not found: {prompt_path}\n"
                f"Please ensure system_prompt_{self.prompt_version}.txt exists in the prompts/ directory."
            )
        
        with open(prompt_path, "r") as f:
            return f.read().strip()
        
    async def initialize(self):
        """Initialize the agent with Phoenix instrumentation"""
        if self._initialized:
            return
            
        # Connect to standalone Phoenix server
        print("🔥 Connecting to Phoenix server...")
        tracer_provider = register(
            project_name=self.project_name,
            endpoint=self.phoenix_endpoint,
        )
        
        # Instrument LangChain to send traces to Phoenix
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        print("✅ LangChain instrumentation enabled")
        print(f"📊 Phoenix UI: http://localhost:6006\n")
        
        print("Initializing MCP client...")
        self.client = MultiServerMCPClient(
            {
                # "reporter_server": {
                #     "transport": "stdio",
                #     "command": "uv",
                #     "args": ["run", "src/reporter/app.py"],
                # },
                "places_server": {
                    "transport": "http",
                    "url": "http://localhost:8000/mcp",
                }
            }
        )

        print("Getting tools...")
        tools = await self.client.get_tools()

        print("Initializing model...")
        model = ChatOpenAI(
            model="claude_4_5_sonnet",
            base_url=self.base_url + "/api/v1",
            api_key=self.api_key,
            temperature=0,
        )

        print("Creating agent...")
        self.agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=self._load_system_prompt()
        )
        
        self._initialized = True
        print("✅ Agent initialized and ready\n")
    
    async def run(self, query: str) -> str:
        """Run a query through the agent and return the response"""
        if not self._initialized:
            await self.initialize()
        
        config = {"configurable": {"thread_id": "1"}}
        
        response = await self.agent.ainvoke(
            {"messages": [("user", query)]},
            config=config
        )
        
        # Extract the final message content
        return response["messages"][-1].content
    
    def create_experiment_task(self):
        """
        Create a task function for Phoenix experiments.
        
        This returns a synchronous function that Phoenix can use as a task,
        which internally handles the async agent execution.
        
        Returns:
            callable: A task function that takes an example and returns a response
            
        Example:
            >>> agent = CDCPlacesAgent()
            >>> await agent.initialize()
            >>> task = agent.create_experiment_task()
            >>> result = task(example)  # Phoenix will call this
        """
        def task(example):
            """Run each query through the CDC PLACES agent"""
            query = example.input['query']
            
            # Run the agent synchronously (Phoenix experiments expect sync functions)
            response = asyncio.run(self.run(query))
            return response
        
        return task
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            # Add any cleanup needed for MCP client
            pass

# Standalone execution for testing
async def main():
    """Test the agent standalone"""
    agent = CDCPlacesAgent()
    await agent.initialize()
    
    print("Invoking agent...")
    response = await agent.run("What is the diabetes rate in Worcester County, MA in 2022?")
    
    print("\n" + "="*80)
    print("RESPONSE:")
    print("="*80)
    print(response)
    print("="*80)
    
    print(f"\n🔍 View your traces at: http://localhost:6006")
    
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())