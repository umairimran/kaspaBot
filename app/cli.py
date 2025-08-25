from rich.console import Console
from core import load_flexible_index, retrieve_flexible, build_flexible_prompt
from llm import generate_answer

INDEX_PATH = "../embeddings/vector_index_flexible.faiss"
console = Console()

def main():
    try:
        index, metadata = load_flexible_index(INDEX_PATH)
        console.print("[bold cyan]Kaspa Flexible RAG Chatbot CLI[/bold cyan]")
        console.print(f"📊 Total chunks: {len(metadata)}")
        console.print(f"📊 Sources: {metadata['source'].value_counts().to_dict()}")
        console.print()
    except Exception as e:
        console.print(f"[bold red]❌ Error loading flexible index: {e}[/bold red]")
        console.print("Please run: python -m app.flexible_embedder_simple")
        return
    
    while True:
        query = console.input("[green]You:[/green] ")
        if query.lower() in ["exit", "quit"]:
            break
        
        try:
            results = retrieve_flexible(query, index, metadata, k=5)
            messages = build_flexible_prompt(query, results)
            answer = generate_answer(messages)
            console.print(f"[yellow]Bot:[/yellow] {answer}")
            
            # Show sources
            if results:
                console.print("\n[dim]Sources:[/dim]")
                for i, result in enumerate(results[:3], 1):
                    source_info = f"  {i}. {result['source']}"
                    if result.get('section'):
                        source_info += f" ({result['section']})"
                    if result.get('url'):
                        source_info += f" - {result['url']}"
                    console.print(f"[dim]{source_info}[/dim]")
                console.print()
                
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

if __name__ == "__main__":
    main()
