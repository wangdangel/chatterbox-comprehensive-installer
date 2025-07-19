"""
Command-line interface for Chatterbox TTS.
Provides CLI commands for TTS processing and management.
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

from ..core.config import config_manager
from ..core.voice_manager import voice_manager
from ..core.processor import tts_processor
from ..core.document_parser import DocumentParser

console = Console()
document_parser = DocumentParser()


@click.group()
@click.version_option(version="1.0.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
def cli(verbose: bool, config: Optional[str]):
    """Chatterbox TTS - Advanced Text-to-Speech CLI."""
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load custom config if provided
    if config:
        config_manager.load_config_from_file(config)


@cli.command()
@click.argument('text')
@click.option('--voice', '-v', default='default', help='Voice ID to use')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--speed', '-s', type=float, help='Speech speed multiplier')
@click.option('--pitch', '-p', type=float, help='Pitch multiplier')
@click.option('--no-stitch', is_flag=True, help='Disable audio stitching')
@click.option('--estimate', is_flag=True, help='Show processing estimate only')
def text(text: str, voice: str, output: Optional[str], speed: Optional[float], 
         pitch: Optional[float], no_stitch: bool, estimate: bool):
    """Convert text to speech."""
    
    if estimate:
        # Show processing estimate
        estimate_data = asyncio.run(tts_processor.get_processing_estimate(text))
        
        console.print(Panel(
            f"[bold]Processing Estimate[/bold]\n\n"
            f"Characters: {estimate_data['character_count']}\n"
            f"Estimated Segments: {estimate_data['estimated_segments']}\n"
            f"Processing Time: {estimate_data['estimated_processing_time_seconds']}s\n"
            f"File Size: {estimate_data['estimated_file_size_mb']:.2f} MB",
            title="Estimate",
            border_style="blue"
        ))
        return
    
    # Validate input
    is_valid, message = tts_processor.validate_input(text)
    if not is_valid:
        console.print(f"[red]Error: {message}[/red]")
        sys.exit(1)
    
    # Process text
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing text...", total=None)
        
        try:
            audio_path = asyncio.run(tts_processor.process_text(
                text=text,
                voice_id=voice,
                output_path=output,
                speed=speed,
                pitch=pitch,
                stitch_audio=not no_stitch
            ))
            
            progress.update(task, description="Complete!")
            console.print(f"[green]✓[/green] Audio saved to: [bold]{audio_path}[/bold]")
            
        except Exception as e:
            progress.update(task, description="Failed!")
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--voice', '-v', default='default', help='Voice ID to use')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--speed', '-s', type=float, help='Speech speed multiplier')
@click.option('--pitch', '-p', type=float, help='Pitch multiplier')
@click.option('--no-stitch', is_flag=True, help='Disable audio stitching')
@click.option('--analyze', is_flag=True, help='Analyze file before processing')
def file(file_path: str, voice: str, output: Optional[str], speed: Optional[float],
         pitch: Optional[float], no_stitch: bool, analyze: bool):
    """Convert file to speech."""
    
    # Analyze file if requested
    if analyze:
        try:
            document = document_parser.parse_file(file_path)
            analysis = document_parser.create_processing_plan(document)
            
            console.print(Panel(
                f"[bold]Document Analysis[/bold]\n\n"
                f"File: {analysis['filename']}\n"
                f"Characters: {analysis['total_chars']}\n"
                f"Segments: {analysis['total_segments']}\n"
                f"Processing Time: {analysis['estimated_processing_time']}s\n"
                f"Requires Stitching: {analysis['requires_stitching']}",
                title="Analysis",
                border_style="blue"
            ))
            
            if not click.confirm("Continue with processing?"):
                return
                
        except Exception as e:
            console.print(f"[red]Analysis failed: {e}[/red]")
            sys.exit(1)
    
    # Process file
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing file...", total=None)
        
        try:
            audio_path = asyncio.run(tts_processor.process_file(
                file_path=file_path,
                voice_id=voice,
                output_path=output,
                speed=speed,
                pitch=pitch,
                stitch_audio=not no_stitch
            ))
            
            progress.update(task, description="Complete!")
            console.print(f"[green]✓[/green] Audio saved to: [bold]{audio_path}[/bold]")
            
        except Exception as e:
            progress.update(task, description="Failed!")
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=2049, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def serve(host: str, port: int, reload: bool):
    """Start the API server."""
    console.print(Panel(
        f"[bold]Starting Chatterbox TTS Server[/bold]\n\n"
        f"Host: {host}\n"
        f"Port: {port}\n"
        f"Reload: {reload}",
        title="Server",
        border_style="green"
    ))
    
    try:
        import uvicorn
        uvicorn.run(
            "chatterbox_tts.api.server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Server error: {e}[/red]")
        sys.exit(1)


@cli.command()
def voices():
    """List all available voices."""
    voices = voice_manager.list_voices()
    
    if not voices:
        console.print("[yellow]No voices available[/yellow]")
        return
    
    table = Table(title="Available Voices")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Language", style="blue")
    table.add_column("Gender", style="magenta")
    table.add_column("Status", style="yellow")
    
    for voice in voices:
        status = "✓ Downloaded" if voice.is_downloaded else "✗ Not downloaded"
        table.add_row(
            voice.id,
            voice.name,
            voice.language,
            voice.gender,
            status
        )
    
    console.print(table)


@cli.command()
@click.argument('voice_id')
def download(voice_id: str):
    """Download a voice."""
    try:
        success = voice_manager.download_voice(voice_id)
        if success:
            console.print(f"[green]✓[/green] Voice '{voice_id}' downloaded successfully")
        else:
            console.print(f"[red]✗[/red] Failed to download voice '{voice_id}'")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('voice_id')
def remove(voice_id: str):
    """Remove a voice."""
    try:
        success = voice_manager.remove_voice(voice_id)
        if success:
            console.print(f"[green]✓[/green] Voice '{voice_id}' removed successfully")
        else:
            console.print(f"[red]✗[/red] Failed to remove voice '{voice_id}'")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def config():
    """Show current configuration."""
    config_data = config_manager.config.dict()
    
    console.print(Panel(
        "[bold]Current Configuration[/bold]",
        title="Config",
        border_style="blue"
    ))
    
    def print_config(obj, prefix=""):
        for key, value in obj.items():
            if isinstance(value, dict):
                console.print(f"{prefix}[bold]{key}:[/bold]")
                print_config(value, prefix + "  ")
            else:
                console.print(f"{prefix}{key}: {value}")
    
    print_config(config_data)


@cli.command()
@click.option('--force', is_flag=True, help='Force cleanup without confirmation')
def cleanup(force: bool):
    """Clean up temporary files."""
    if not force:
        if not click.confirm("This will remove all temporary files. Continue?"):
            return
    
    try:
        temp_dir = Path(config_manager.get_path("processing", "temp"))
        output_dir = Path(config_manager.get_path("processing", "output"))
        
        removed_count = 0
        
        # Clean temp directory
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    removed_count += 1
                except OSError:
                    pass
        
        # Clean old output files (older than 1 hour)
        import time
        current_time = time.time()
        for file_path in output_dir.glob("*.wav"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > 3600:  # 1 hour
                    try:
                        file_path.unlink()
                        removed_count += 1
                    except OSError:
                        pass
        
        console.print(f"[green]✓[/green] Cleaned up {removed_count} files")
        
    except Exception as e:
        console.print(f"[red]Cleanup failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('text')
def demo(text: str):
    """Run a quick demo."""
    console.print(Panel(
        "[bold]Chatterbox TTS Demo[/bold]\n\n"
        "This will convert the provided text to speech using the default voice.",
        title="Demo",
        border_style="green"
    ))
    
    try:
        audio_path = asyncio.run(tts_processor.process_text(text))
        console.print(f"[green]✓[/green] Demo audio saved to: [bold]{audio_path}[/bold]")
        
        # Try to play the audio if possible
        try:
            import platform
            if platform.system() == "Darwin":  # macOS
                os.system(f"afplay '{audio_path}'")
            elif platform.system() == "Linux":
                os.system(f"aplay '{audio_path}'")
            elif platform.system() == "Windows":
                os.system(f"start '{audio_path}'")
            else:
                console.print("[yellow]Audio playback not supported on this platform[/yellow]")
        except Exception:
            console.print("[yellow]Could not play audio automatically[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Demo failed: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()