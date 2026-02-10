"""
Main CLI entry point for Deep Research Assistant
Uses the modular agents from src/
"""
import asyncio
import uuid
import argparse
import sys
from src.agents.orchestrator import run_research_workflow
from src.models import ResearchStatus
from src.utils.config import Config, ConfigError
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

async def query_mode(query: str):
    """Query the modular research system via CLI"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    
    # Load configuration
    try:
        Config.load()
    except ConfigError as e:
        print(f"Error: {e}")
        return

    query_id = str(uuid.uuid4())
    
    def cli_stream_callback(event):
        """Simple callback to show progress in CLI"""
        if event.event_type == "status":
            msg = event.data.get("message", "")
            agent = f"[{event.agent.upper()}] " if event.agent else ""
            print(f"{agent}{msg}")
        elif event.event_type == "source":
            source = event.data.get("source", {})
            title = source.get("title", "Unknown Source")
            url = source.get("url", "")
            print(f"  - Found: {title} ({url})")
        elif event.event_type == "error":
            print(f"Error: {event.data.get('error')}")

    try:
        final_state = await run_research_workflow(
            query=query,
            query_id=query_id,
            stream_callback=cli_stream_callback
        )
        
        if final_state.status == ResearchStatus.COMPLETED:
            print(f"\n{'='*60}")
            print("FINAL REPORT")
            print(f"{'='*60}\n")
            print(final_state.final_report)
            print(f"\n{'='*60}")
            print(f"Sources used: {len(final_state.verified_sources)}")
            print(f"Execution time: {final_state.execution_time_seconds:.2f}s")
            print(f"{'='*60}")
        elif final_state.status == ResearchStatus.FAILED:
            print(f"\nResearch failed: {final_state.error_message}")
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")

async def interactive_mode():
    """Interactive CLI mode"""
    print("Deep Research Assistant - Interactive CLI")
    print("Enter your research questions below. Type 'exit' to quit.\n")
    
    while True:
        try:
            query = input("Research Question: ").strip()
            if query.lower() in ["exit", "quit", "q"]:
                break
            if not query:
                continue
                
            await query_mode(query)
            print("\n" + "-"*60 + "\n")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

async def main():
    parser = argparse.ArgumentParser(description="Deep Research Assistant CLI")
    parser.add_argument("--query", type=str, help="Research question to answer")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.query:
        await query_mode(args.query)
    elif args.interactive or len(sys.argv) == 1:
        await interactive_mode()

if __name__ == "__main__":
    asyncio.run(main())
