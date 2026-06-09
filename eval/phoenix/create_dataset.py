#!/usr/bin/env python3
"""
Consolidated dataset creation script for Phoenix evaluation experiments.

This script replaces all the individual create_dataset.py files in each dataset directory.
Dataset configurations are defined in datasets.yaml.

Usage:
    uv run create_dataset.py --dataset-name places-eval-0
    uv run create_dataset.py --list
    uv run create_dataset.py --dataset-name places-eval-0 --phoenix-name my-custom-name
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import yaml
from phoenix.client import Client


def load_datasets_config(config_path: Path) -> dict:
    """Load dataset configurations from YAML file."""
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('datasets', {})


def list_datasets(datasets_config: dict):
    """Display all available datasets."""
    print("\nAvailable datasets:\n")
    print(f"{'Dataset Name':<25} {'Questions':<12} {'Description'}")
    print("-" * 80)
    
    for name, config in datasets_config.items():
        csv_path = Path(__file__).parent / config['csv_path']
        try:
            df = pd.read_csv(csv_path)
            num_questions = len(df)
        except Exception:
            num_questions = "N/A"
        
        description = config.get('description', 'No description')
        print(f"{name:<25} {str(num_questions):<12} {description}")
    
    print()


def create_dataset(
    dataset_name: str,
    datasets_config: dict,
    phoenix_name: str = None,
    csv_path_override: str = None,
    dry_run: bool = False
):
    """Create and upload a dataset to Phoenix."""
    
    # Validate dataset exists in config
    if dataset_name not in datasets_config:
        print(f"Error: Dataset '{dataset_name}' not found in datasets.yaml")
        print(f"\nAvailable datasets: {', '.join(datasets_config.keys())}")
        sys.exit(1)
    
    config = datasets_config[dataset_name]
    
    # Determine CSV path
    if csv_path_override:
        csv_path = Path(csv_path_override)
    else:
        csv_path = Path(__file__).parent / config['csv_path']
    
    # Validate CSV exists
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Load data
    try:
        data = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(data)} rows from {csv_path}")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)
    
    # Get input/output keys
    input_keys = config.get('input_keys', ['query'])
    output_keys = config.get('output_keys', ['responses'])
    
    # Validate required columns exist
    required_cols = input_keys + output_keys
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        print(f"Error: Missing required columns in CSV: {missing_cols}")
        print(f"Available columns: {list(data.columns)}")
        sys.exit(1)
    
    # Use phoenix_name if provided, otherwise use dataset_name
    upload_name = phoenix_name if phoenix_name else dataset_name
    
    print(f"\nDataset configuration:")
    print(f"  Name: {upload_name}")
    print(f"  Input keys: {input_keys}")
    print(f"  Output keys: {output_keys}")
    print(f"  Description: {config.get('description', 'N/A')}")
    
    if dry_run:
        print("\n✓ Dry run successful - would upload to Phoenix as '{upload_name}'")
        return
    
    # Upload to Phoenix
    try:
        px_client = Client()
        dataset = px_client.datasets.create_dataset(
            dataframe=data,
            name=upload_name,
            input_keys=input_keys,
            output_keys=output_keys,
        )
        print(f"\n✓ Successfully uploaded dataset '{upload_name}' to Phoenix")
        print(f"  Dataset ID: {dataset.id}")
        print(f"  Version ID: {dataset.version_id}")
    except Exception as e:
        print(f"\nError uploading to Phoenix: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Create and upload Phoenix evaluation datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available datasets
  python create_dataset.py --list
  
  # Create a dataset using config from datasets.yaml
  python create_dataset.py --dataset-name reporter-test-2
  
  # Create with custom Phoenix name
  python create_dataset.py --dataset-name reporter-eval-0 --phoenix-name my-test-dataset
  
  # Dry run (validate without uploading)
  python create_dataset.py --dataset-name reporter-test-2 --dry-run
        """
    )
    
    parser.add_argument(
        '--dataset-name',
        type=str,
        help='Name of the dataset from datasets.yaml'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available datasets'
    )
    
    parser.add_argument(
        '--phoenix-name',
        type=str,
        help='Custom name for the dataset in Phoenix (defaults to dataset-name)'
    )
    
    parser.add_argument(
        '--csv-path',
        type=str,
        help='Override CSV path from config (for testing)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without uploading to Phoenix'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(__file__).parent / 'datasets.yaml'
    datasets_config = load_datasets_config(config_path)
    
    # Handle --list
    if args.list:
        list_datasets(datasets_config)
        return
    
    # Require dataset-name for other operations
    if not args.dataset_name:
        parser.error("--dataset-name is required (or use --list to see available datasets)")
    
    # Create dataset
    create_dataset(
        dataset_name=args.dataset_name,
        datasets_config=datasets_config,
        phoenix_name=args.phoenix_name,
        csv_path_override=args.csv_path,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
