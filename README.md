# Video Transcription with Deepgram

Batch transcribe MP4 videos (and other audio/video formats) using Deepgram's Speech-to-Text API.

## Features

- Batch processes all video/audio files in a directory
- Uses Deepgram's latest `nova-3` model for high accuracy (99%+ confidence)
- Generates three output formats:
  - Plain text transcripts
  - Timestamped transcripts (with markers every 10 seconds)
  - Full JSON API responses with word-level timing data
- Smart formatting for currency, phone numbers, and emails
- Progress tracking with detailed status updates
- Automatic skip of already-transcribed files
- Error handling and retry logic
- Secure API key storage using `.env` file (automatically loaded)

## Supported Formats

- MP4 (video)
- MP3, WAV, M4A, FLAC, AAC (audio)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/mtomcal/transcribe-videos.git
cd transcribe-videos
```

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get your Deepgram API key

1. Sign up at https://console.deepgram.com/
2. Create a new API key from the dashboard
3. Copy the key

### 5. Configure your API key

The script uses a `.env` file to securely store your API key. Edit the `.env` file in the project root:

```bash
# .env file (already created)
DEEPGRAM_API_KEY=your_api_key_here
```

**Note:** The `.env` file is already in `.gitignore`, so your API key won't be committed to version control.

Alternatively, you can set the environment variable manually:

```bash
export DEEPGRAM_API_KEY='your_api_key_here'
```

## Usage

### Basic Usage

```bash
# Transcribe files in current directory
python transcribe_videos.py

# Specify input and output directories
python transcribe_videos.py -i /path/to/videos -o /path/to/transcripts

# Use different model and language (e.g., Spanish)
python transcribe_videos.py -i /path/to/videos -m nova-2 -l es

# View all options
python transcribe_videos.py --help
```

### Command-Line Options

- `-i, --input-dir` - Input directory containing video/audio files (default: current directory)
- `-o, --output-dir` - Output directory for transcripts (default: INPUT_DIR/transcripts)
- `-m, --model` - Deepgram model to use (default: nova-3)
- `-l, --language` - Language code (default: en)
- `--api-key` - Deepgram API key (can also use DEEPGRAM_API_KEY env var)

The script will:
1. Look for all video/audio files in the specified input directory
2. Create transcripts in the output directory
3. Process each file and show progress
4. Generate three files per video:
   - `{filename}_transcript.txt` - Plain text transcript
   - `{filename}_timestamped.txt` - Transcript with timestamps every 10 seconds
   - `{filename}_full_response.json` - Complete API response with word-level timing

## Configuration

You can modify these default settings in `transcribe_videos.py`:

```python
# Deepgram settings
MODEL = "nova-3"  # Latest model
LANGUAGE = "en"   # Change for other languages
SMART_FORMAT = True  # Format numbers, currency, etc.

# Processing
TIMEOUT_SECONDS = 600  # 10 minutes per file
MAX_RETRIES = 3
```

Or use command-line arguments to override defaults without editing the script.

### Optional Features

Enable speaker diarization (speaker identification):

```python
diarize=True,  # In the transcribe_file function
```

## Example Output

### Plain Transcript
```
Transcript: Chapter 1.mp4
================================================================================

Welcome to Essential Theory. In this chapter we'll explore...
```

### Timestamped Transcript
```
Timestamped Transcript: Chapter 1.mp4
================================================================================

[00:00] Welcome to Essential Theory. In this chapter we'll explore the fundamental
concepts of light and how it affects our perception.

[00:10] When we talk about seeing the light, we're referring to both the physical
properties of electromagnetic radiation...
```

## Files in This Project

- `transcribe_videos.py` - Main transcription script
- `requirements.txt` - Python dependencies (`deepgram-sdk>=3.0.0`, `python-dotenv>=1.0.0`)
- `.env` - Environment variables (API key) - **DO NOT commit this file**
- `.gitignore` - Git ignore rules (includes `.env`)
- `venv/` - Virtual environment (not committed to git)
- `README.md` - This file

## Troubleshooting

**Error: DEEPGRAM_API_KEY environment variable not set**
- Make sure your API key is set in the `.env` file
- Alternatively, export it manually: `export DEEPGRAM_API_KEY='your_key'`

**Error: No video files found**
- Check that the input directory path is correct
- Verify you have supported file formats (.mp4, .mp3, etc.)
- Use `-i` flag to specify the correct directory

**API Error 429 (Rate Limit)**
- You're hitting Deepgram's concurrent request limit (100 requests)
- The script processes files sequentially, so this shouldn't happen normally

**Timeout errors**
- Large files may need more time. Increase `TIMEOUT_SECONDS` in the config

**Warning: Could not save JSON response**
- This is usually harmless and won't affect transcripts
- The plain and timestamped transcripts will still be generated successfully

## Cost Estimation

Deepgram pricing (as of 2025):
- Nova-3 model: ~$0.0043 per minute of audio
- Example: 1 hour of video = ~$0.26
- Deepgram offers free credits for new accounts

Check current pricing at: https://deepgram.com/pricing

## Technical Details

### Deepgram SDK Version

This project uses **Deepgram Python SDK v3.0+** with the following key changes from earlier versions:

- `DeepgramClient()` initialization reads API key from environment variable automatically
- Response objects include built-in word-level timestamps by default
- Smart format enhances transcripts without disabling timestamp data
- Improved error handling with structured response objects

### Output Files

Each video generates three files in the `transcripts/` directory:

1. **`{filename}_transcript.txt`** (~10-50KB per file)
   - Plain text transcription with punctuation
   - Formatted for easy reading

2. **`{filename}_timestamped.txt`** (~10-50KB per file)
   - Same transcript with `[MM:SS]` timestamps every 10 seconds
   - Ideal for video navigation and chapter creation

3. **`{filename}_full_response.json`** (~1-2MB per file)
   - Complete API response with metadata
   - Word-level timing (start/end/confidence for every word)
   - Model information and transcription settings

## Deactivating

When done, deactivate the virtual environment:

```bash
deactivate
```
