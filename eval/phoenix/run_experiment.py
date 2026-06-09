#!/usr/bin/env python3
"""
Consolidated experiment runner for Phoenix evaluation experiments.

This script replaces all the individual run_experiment.py files in each dataset directory.
Dataset configurations are defined in datasets.yaml for validation.

Usage:
    uv run eval/phoenix/run_experiment.py --dataset-name places-eval-0
    uv run eval/phoenix/run_experiment.py --dataset-name places-eval-0 --system-prompt-version v01
    uv run eval/phoenix/run_experiment.py --dataset-name places-eval-0 --experiment-description "Testing new prompt"
"""

from phoenix.client import Client
import asyncio
import argparse
import sys
import yaml
from pathlib import Path

# Import agent and judges
from agent import CDCPlacesAgent
from judges import match_expected_response, check_answer_scope


def load_datasets_config(config_path: Path) -> dict:
    """Load dataset configurations from YAML file for validation."""
    if not config_path.exists():
        print(f"Warning: Configuration file not found: {config_path}")
        return {}
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('datasets', {})


def list_available_datasets(datasets_config: dict):
    """Display all available datasets from config."""
    if not datasets_config:
        return
    
    print("\nAvailable datasets:")
    for name, config in datasets_config.items():
        desc = config.get('description', 'No description')
        print(f"  - {name}: {desc}")
    print()


def main(
    dataset_name: str,
    dataset_version_id: str = None,
    system_prompt_version: str = "v01",
    project_name: str = "cdc-places-experiments",
    phoenix_endpoint: str = "http://localhost:4317",
    experiment_description: str = None,
    experiment_metadata: dict = None,
    validate_dataset: bool = True
):
    """
    Run a Phoenix experiment with the PLACES agent.
    
    Args:
        dataset_name: Name of the Phoenix dataset to use
        dataset_version_id: Specific version ID of dataset (None for latest)
        system_prompt_version: Version identifier for the system prompt (v1, v2, v3)
        project_name: Name of the Phoenix project
        phoenix_endpoint: URL endpoint for Phoenix OTLP collector
        experiment_description: Human-readable description of the experiment
        experiment_metadata: Additional metadata to attach to the experiment
        validate_dataset: Whether to validate dataset exists in config (default True)
    
    Returns:
        The experiment result object from Phoenix
    """
    
    # Validate dataset if requested
    if validate_dataset:
        config_path = Path(__file__).parent / 'datasets.yaml'
        datasets_config = load_datasets_config(config_path)
        
        if datasets_config and dataset_name not in datasets_config:
            print(f"Warning: Dataset '{dataset_name}' not found in datasets.yaml")
            print("This may cause issues if the dataset doesn't exist in Phoenix.")
            list_available_datasets(datasets_config)
            
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                sys.exit(1)
    
    # Validate prompt version exists
    prompt_path = Path(__file__).parent / f"prompts/system_prompt_{system_prompt_version}.txt"
    if not prompt_path.exists():
        print(f"Error: System prompt file not found: {prompt_path}")
        available_prompts = list(Path(__file__).parent.glob("prompts/system_prompt_*.txt"))
        if available_prompts:
            print("\nAvailable prompt versions:")
            for p in available_prompts:
                version = p.stem.replace("system_prompt_", "")
                print(f"  - {version}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Starting Phoenix Experiment")
    print(f"{'='*60}")
    print(f"Dataset: {dataset_name}")
    if dataset_version_id:
        print(f"Dataset Version: {dataset_version_id}")
    print(f"System Prompt: {system_prompt_version}")
    print(f"Project: {project_name}")
    print(f"Phoenix Endpoint: {phoenix_endpoint}")
    print(f"{'='*60}\n")
    
    try:
        # Initialize client - automatically reads from environment variables
        print("Initializing Phoenix client...")
        client = Client()
        
        # Get the dataset
        print(f"Loading dataset '{dataset_name}'...")
        dataset_kwargs = {"dataset": dataset_name}
        if dataset_version_id:
            dataset_kwargs["version_id"] = dataset_version_id
        
        try:
            dataset = client.datasets.get_dataset(**dataset_kwargs)
            print(f"✓ Dataset loaded: {len(dataset)} examples")
        except Exception as e:
            print(f"Error loading dataset: {e}")
            print(f"\nMake sure the dataset '{dataset_name}' exists in Phoenix.")
            print("You can create it using: python create_dataset.py --dataset-name <name>")
            sys.exit(1)
        
        # Initialize the agent
        print(f"Initializing CDCPlaces agent with prompt {system_prompt_version}...")
        agent = CDCPlacesAgent(
            project_name=project_name,
            phoenix_endpoint=phoenix_endpoint,
            prompt_version=system_prompt_version
        )
        asyncio.run(agent.initialize())
        print("✓ Agent initialized")
        
        # Create the task using the agent's method
        my_task = agent.create_experiment_task()
        
        # Store the evaluators
        evaluators = [check_answer_scope, match_expected_response]
        print(f"✓ Using evaluators: {[e.__name__ for e in evaluators]}")
        
        # Prepare experiment metadata
        if experiment_metadata is None:
            experiment_metadata = {}
        experiment_metadata["system_prompt_version"] = system_prompt_version
        
        # Set default experiment description if not provided
        if experiment_description is None:
            experiment_description = (
                f"Experiment on {dataset_name} with system prompt {system_prompt_version}"
            )
        
        print(f"\nExperiment description: {experiment_description}")
        print(f"\nRunning experiment...")
        print(f"{'='*60}\n")
        
        # Run the experiment
        experiment = client.experiments.run_experiment(
            dataset=dataset,
            task=my_task,
            evaluators=evaluators,
            experiment_description=experiment_description,
            experiment_metadata=experiment_metadata
        )
        
        print(f"\n{'='*60}")
        print(f"✓ Experiment completed successfully!")
        print(f"{'='*60}")
        print(f"Experiment ID: {experiment.id if hasattr(experiment, 'id') else 'N/A'}")
        print(f"View results in Phoenix UI at: {phoenix_endpoint.replace(':4317', ':6006')}")
        print(f"{'='*60}\n")
        
        return experiment
        
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError running experiment: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Phoenix experiments with NIH Clinical Trials agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run experiment with default settings
  python run_experiment.py --dataset-name clinicaltrials-test-0
  
  # Test different system prompt versions
  python run_experiment.py --dataset-name clinicaltrials-test-0 --system-prompt-version v01
  
  # Add custom description and metadata
  python run_experiment.py --dataset-name clinicaltrials-test-0 \\
      --experiment-description "Testing boundary detection" \\
      --system-prompt-version v01
  
  # Use specific dataset version
  python run_experiment.py --dataset-name clinicaltrials-test-0 \\
      --dataset-version-id abc123def456
        """
    )
    
    parser.add_argument(
        "--dataset-name",
        type=str,
        required=True,
        help="Name of the Phoenix dataset to use (must exist in Phoenix)"
    )
    
    parser.add_argument(
        "--dataset-version-id",
        type=str,
        default=None,
        help="Specific version ID of dataset (omit for latest version)"
    )
    
    parser.add_argument(
        "--system-prompt-version",
        type=str,
        default="v01",
        choices=["v01", "v02", "v03"],
        help="Version identifier for the system prompt"
    )
    
    parser.add_argument(
        "--project-name",
        type=str,
        default="nih-clinicaltrials-experiments",
        help="Name of the Phoenix project"
    )
    
    parser.add_argument(
        "--phoenix-endpoint",
        type=str,
        default="http://localhost:4317",
        help="URL endpoint for Phoenix OTLP collector"
    )
    
    parser.add_argument(
        "--experiment-description",
        type=str,
        default=None,
        help="Human-readable description of the experiment"
    )
    
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip dataset validation against datasets.yaml"
    )
    
    parser.add_argument(
        "--list-datasets",
        action="store_true",
        help="List available datasets from datasets.yaml and exit"
    )
    
    args = parser.parse_args()
    
    # Handle --list-datasets
    if args.list_datasets:
        config_path = Path(__file__).parent / 'datasets.yaml'
        datasets_config = load_datasets_config(config_path)
        list_available_datasets(datasets_config)
        sys.exit(0)
    
    # Run the main function with parsed arguments
    experiment = main(
        dataset_name=args.dataset_name,
        dataset_version_id=args.dataset_version_id,
        system_prompt_version=args.system_prompt_version,
        project_name=args.project_name,
        phoenix_endpoint=args.phoenix_endpoint,
        experiment_description=args.experiment_description,
        validate_dataset=not args.no_validate
    )
    
    print(f"Experiment object: {experiment}")
