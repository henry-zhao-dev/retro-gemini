# Retro Gemini CLI

A lightweight, interactive command-line interface (CLI) for chatting with Google Gemini AI models directly from your terminal.

## Features

- **Interactive Chat**: Multiline terminal prompt with a retro layout.
- **List Models**: View all available Google Gemini models.
- **Model Selection**: Switch models for one session or save a new default.
- **Secure**: Uses environment variables to handle API keys safely.

---

## Prerequisites

- **Python 3.11+**
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

## Configure your API Key

Create a `.env` file in the root directory of this project and add your Gemini API key:

```env
GEMINI_API_KEY="your_actual_api_key"
```

---

## Usage

### Start Interactive Chat

Run the app using the saved default model. On first use, the default is
`gemini-flash-lite-latest`:

```bash
retro-gemini
```

### Specify a Model

Start the current chat session using a specific Gemini model. This does not
change the saved default:

```bash
retro-gemini --model gemini-3.1-pro-preview
```

### Set the Default Model

Save a model as the default for future sessions:

```bash
retro-gemini --default-model gemini-3.1-pro-preview
```

The model must appear in the output of `retro-gemini --list`. You can still
override the saved default for a single session with `--model`.

### List Available Models

Display all available Gemini models linked to your API key:

```bash
retro-gemini --list
```

### Disable Context Memory

Every turn is treated as a brand new conversation:

```bash
retro-gemini --no-context
```

---

## Chat Controls

| Key / Command | Action |
| :--- | :--- |
| `Enter` | Add a new line |
| `Esc` + `Enter` | Send message to Gemini |
| `exit` or `quit` | End the chat session |
| `Ctrl + C` / `Ctrl + D` | Force quit |
