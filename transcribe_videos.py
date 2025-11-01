#!/usr/bin/env python3
"""
Deepgram Video/Audio Transcription Script
==========================================

This script transcribes all video/audio files in a directory using the Deepgram API.
It processes multiple audio/video formats and generates text transcripts with timestamps.

Installation:
    pip install -r requirements.txt

Usage:
    # Set API key (required)
    export DEEPGRAM_API_KEY="your_api_key_here"

    # Basic usage - transcribe files in current directory
    python transcribe_videos.py

    # Specify input and output directories
    python transcribe_videos.py -i /path/to/videos -o /path/to/transcripts

    # Use different model and language
    python transcribe_videos.py -i /path/to/videos -m nova-2 -l es

    # View all options
    python transcribe_videos.py --help

Features:
    - Batch processes all audio/video files in the specified directory
    - Supports multiple formats: MP4, MP3, WAV, M4A, FLAC, AAC
    - Generates timestamped transcripts
    - Saves both full transcripts and timestamped versions
    - Progress tracking with file-by-file status
    - Error handling and retry logic
    - Skips already transcribed files
    - Configurable via command-line arguments
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from deepgram import DeepgramClient
from deepgram.core.api_error import ApiError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
SUPPORTED_FORMATS = ['.mp4', '.mp3', '.wav', '.m4a', '.flac', '.aac']

# Deepgram API Configuration
MODEL = "nova-3"  # Latest model (as of 2025)
SMART_FORMAT = True  # Formats currency, phone numbers, emails for readability
LANGUAGE = "en"  # Change if needed

# File processing configuration
TIMEOUT_SECONDS = 600  # 10 minutes per file
MAX_RETRIES = 3


def setup_output_directory(output_dir: str):
    """Create output directory if it doesn't exist."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")


def get_video_files(input_dir: str):
    """Get list of all supported audio/video files in the input directory."""
    input_path = Path(input_dir)
    files = []

    for ext in SUPPORTED_FORMATS:
        files.extend(input_path.glob(f"*{ext}"))

    # Sort by filename for consistent processing order
    files.sort(key=lambda x: x.name)
    return files


def is_already_transcribed(video_file: Path, output_dir: str) -> bool:
    """Check if transcript already exists for this file."""
    transcript_file = Path(output_dir) / f"{video_file.stem}_transcript.txt"
    return transcript_file.exists()


def save_transcript(video_file: Path, response: Any, output_dir: str):
    """
    Save transcript in multiple formats:
    - Plain text transcript
    - Timestamped transcript
    - Full JSON response
    """
    base_name = video_file.stem

    # Extract transcript text
    transcript = response.results.channels[0].alternatives[0].transcript

    # Save plain transcript
    plain_file = Path(output_dir) / f"{base_name}_transcript.txt"
    with open(plain_file, 'w', encoding='utf-8') as f:
        f.write(f"Transcript: {video_file.name}\n")
        f.write(f"{'=' * 80}\n\n")
        f.write(transcript)

    print(f"  ✓ Saved plain transcript: {plain_file.name}")

    # Save timestamped transcript
    try:
        words = response.results.channels[0].alternatives[0].words

        if not words:
            print(f"  ⚠️  Warning: No word-level timestamps available in response")
        else:
            timestamped_file = Path(output_dir) / f"{base_name}_timestamped.txt"

            with open(timestamped_file, 'w', encoding='utf-8') as f:
                f.write(f"Timestamped Transcript: {video_file.name}\n")
                f.write(f"{'=' * 80}\n\n")

                current_time = 0
                line_buffer = []

                for word in words:
                    # Create timestamp markers every ~10 seconds
                    if word.start - current_time >= 10:
                        if line_buffer:
                            f.write(' '.join(line_buffer) + '\n\n')
                            line_buffer = []

                        minutes = int(word.start // 60)
                        seconds = int(word.start % 60)
                        f.write(f"[{minutes:02d}:{seconds:02d}] ")
                        current_time = word.start

                    line_buffer.append(word.punctuated_word if hasattr(word, 'punctuated_word') else word.word)

                # Write remaining words
                if line_buffer:
                    f.write(' '.join(line_buffer) + '\n')

            print(f"  ✓ Saved timestamped transcript: {timestamped_file.name}")
    except (AttributeError, TypeError) as e:
        print(f"  ⚠️  Warning: Could not create timestamped transcript: {e}")

    # Save full JSON response
    try:
        json_file = Path(output_dir) / f"{base_name}_full_response.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            # Convert response object to dict recursively
            def to_serializable(obj):
                """Convert Deepgram response objects to JSON-serializable format"""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif hasattr(obj, '__dict__'):
                    return {key: to_serializable(value) for key, value in obj.__dict__.items()}
                elif isinstance(obj, list):
                    return [to_serializable(item) for item in obj]
                elif isinstance(obj, dict):
                    return {key: to_serializable(value) for key, value in obj.items()}
                else:
                    return obj

            response_dict = to_serializable(response)
            json.dump(response_dict, f, indent=2)
        print(f"  ✓ Saved JSON response: {json_file.name}")
    except (AttributeError, TypeError, json.JSONDecodeError) as e:
        print(f"  ⚠️  Warning: Could not save JSON response: {e}")


def transcribe_file(client: DeepgramClient, video_file: Path, output_dir: str,
                    model: str = MODEL, language: str = LANGUAGE) -> bool:
    """
    Transcribe a single video/audio file.

    Returns:
        True if successful, False otherwise
    """
    print(f"\n🎬 Processing: {video_file.name}")
    print(f"  Size: {video_file.stat().st_size / (1024**2):.1f} MB")

    try:
        # Read the file
        print(f"  📖 Reading file...")
        with open(video_file, 'rb') as audio_file:
            audio_data = audio_file.read()

        # Transcribe
        print(f"  🔄 Transcribing with Deepgram (model: {model})...")
        response = client.listen.v1.media.transcribe_file(
            request=audio_data,
            model=model,
            smart_format=SMART_FORMAT,
            language=language,
            punctuate=True,
            paragraphs=True,
            utterances=True,
            diarize=False,  # Set to True if you want speaker detection
            request_options={
                "timeout_in_seconds": TIMEOUT_SECONDS,
                "max_retries": MAX_RETRIES
            }
        )

        # Get metadata
        duration = response.metadata.duration
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        print(f"  ⏱️  Duration: {minutes}m {seconds}s")
        print(f"  💬 Confidence: {response.results.channels[0].alternatives[0].confidence:.2%}")

        # Save results
        save_transcript(video_file, response, output_dir)

        print(f"  ✅ Successfully transcribed!")
        return True

    except ApiError as e:
        print(f"  ❌ API Error:")
        print(f"     Status Code: {e.status_code}")
        print(f"     Error Details: {e.body}")
        return False

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Transcribe video/audio files using Deepgram API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe files in current directory
  python transcribe_videos.py

  # Specify input and output directories
  python transcribe_videos.py -i /path/to/videos -o /path/to/transcripts

  # Use a different model and language
  python transcribe_videos.py -i /path/to/videos -m nova-2 -l es

Environment Variables:
  DEEPGRAM_API_KEY    Your Deepgram API key (required)
                      Get one from: https://console.deepgram.com/
        """
    )

    parser.add_argument(
        '-i', '--input-dir',
        type=str,
        default='.',
        help='Input directory containing video/audio files (default: current directory)'
    )

    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default=None,
        help='Output directory for transcripts (default: INPUT_DIR/transcripts)'
    )

    parser.add_argument(
        '-m', '--model',
        type=str,
        default=MODEL,
        help=f'Deepgram model to use (default: {MODEL})'
    )

    parser.add_argument(
        '-l', '--language',
        type=str,
        default=LANGUAGE,
        help=f'Language code (default: {LANGUAGE})'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='Deepgram API key (can also use DEEPGRAM_API_KEY env var)'
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    # Parse arguments
    args = parse_arguments()

    print("=" * 80)
    print("🎙️  Deepgram Video Transcription Script")
    print("=" * 80)

    # Check for API key
    api_key = args.api_key or os.environ.get('DEEPGRAM_API_KEY')
    if not api_key:
        print("\n❌ Error: DEEPGRAM_API_KEY not provided!")
        print("\nPlease provide your API key either:")
        print("  1. Via environment variable: export DEEPGRAM_API_KEY='your_api_key_here'")
        print("  2. Via command-line flag: --api-key YOUR_KEY")
        print("\nGet your API key from: https://console.deepgram.com/")
        return

    print(f"✓ API key found")

    # Set up directories
    input_dir = os.path.abspath(args.input_dir)
    output_dir = args.output_dir or os.path.join(input_dir, 'transcripts')
    output_dir = os.path.abspath(output_dir)

    print(f"📂 Input directory:  {input_dir}")

    # Setup
    setup_output_directory(output_dir)

    # Get files to process
    video_files = get_video_files(input_dir)

    if not video_files:
        print(f"\n⚠️  No video files found in {input_dir}")
        print(f"   Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        return

    print(f"\n📊 Found {len(video_files)} file(s) to process:")
    for vf in video_files:
        status = "⏭️  [SKIP - already transcribed]" if is_already_transcribed(vf, output_dir) else "📝 [TO DO]"
        print(f"   {status} {vf.name}")

    # Initialize Deepgram client
    print(f"\n🔌 Connecting to Deepgram API...")
    print(f"   Model: {args.model}")
    print(f"   Language: {args.language}")
    client = DeepgramClient(api_key=api_key)

    # Process files
    successful = 0
    skipped = 0
    failed = 0

    for i, video_file in enumerate(video_files, 1):
        print(f"\n{'=' * 80}")
        print(f"File {i}/{len(video_files)}")

        if is_already_transcribed(video_file, output_dir):
            print(f"⏭️  Skipping {video_file.name} (already transcribed)")
            skipped += 1
            continue

        if transcribe_file(client, video_file, output_dir, args.model, args.language):
            successful += 1
        else:
            failed += 1

    # Summary
    print(f"\n{'=' * 80}")
    print("📈 SUMMARY")
    print(f"{'=' * 80}")
    print(f"  ✅ Successfully transcribed: {successful}")
    print(f"  ⏭️  Skipped (already done):  {skipped}")
    print(f"  ❌ Failed:                   {failed}")
    print(f"  📁 Total files:              {len(video_files)}")
    print(f"\n💾 Transcripts saved to: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
