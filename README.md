# Retro Gemini CLI

A lightweight, interactive command-line interface (CLI) for chatting with Google Gemini AI models directly from your terminal.

## Features

- **Interactive Chat**: Multiline terminal prompt with a retro layout.
- **List Models**: View all available Google Gemini models.
- **Model Selection**: Easily switch between different Gemini models.
- **Secure**: Uses environment variables to handle API keys safely.

---

## Prerequisites

- **Python 3.8+**
- **[Poetry](https://python-poetry.org/docs/#installation)** installed on your machine
- A **Google Gemini API Key** (Get one from [Google AI Studio](https://aistudio.google.com/))

---

## Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/henry-zhao-dev/retro-gemini.git
   cd retro-gemini
   ```

2. Install the project and dependencies:
   ```bash
   poetry install
   ```

3. Activate the virtual environment so the CLI command is available:
   ```bash
   eval $(poetry env activate)
   ```
   *(Note: You can also skip activation and prefix the commands below with `poetry run`, e.g., `poetry run retro-gemini`).*

---

## Setup

Set your Gemini API key as an environment variable before running the application:

**On Linux/macOS:**
```bash
export GEMINI_API_KEY="your_actual_api_key_here"
```

**On Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your_actual_api_key_here
```

**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_actual_api_key_here"
```

---

## Usage

### Start Interactive Chat

Run the app using the default model (`gemini-flash-latest`):

```bash
retro-gemini
```

### Specify a Model

Start the chat session using a specific Gemini model:

```bash
retro-gemini --model gemini-3.1-pro-preview
```

### List Available Models

Display all available Gemini models linked to your API key:

```bash
retro-gemini --list
```

### Disable Context Memory

Every turn is treated as a brand new conversation:

```bash
retro-gemini --no-history
```

---

## Chat Controls

| Key / Command | Action |
| :--- | :--- |
| `Enter` | Add a new line |
| `Esc` + `Enter` | Send message to Gemini |
| `exit` or `quit` | End the chat session |
| `Ctrl + C` / `Ctrl + D` | Force quit |
