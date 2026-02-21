import asyncio
import yaml
from pathlib import Path
from backend.app.engine.runner import WorkflowRunner
from shared.workflow import WorkflowSpec

async def test_run():
    # Load test workflow
    with open("workflows/test_rag.yaml", "r") as f:
        spec_data = yaml.safe_load(f)
    
    spec = WorkflowSpec(**spec_data)
    runner = WorkflowRunner(spec)
    
    # Initial input
    initial_input = {"query": "LangPedia"}
    
    # Run
    outputs = await runner.run(initial_input)
    
    print("\n--- Final Outputs ---")
    print(outputs)
    
    print("\n--- Event Trace ---")
    for event in runner.events:
        print(event)

if __name__ == "__main__":
    asyncio.run(test_run())
