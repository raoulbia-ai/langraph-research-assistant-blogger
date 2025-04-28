# Research Assistant Blogger

A LangGraph-powered application that helps you discover research papers on ArXiv, analyze them, and generate blog posts.

## Features

- Search for recent papers on ArXiv by topic
- Analyze paper content using LLMs
- Generate technical blog posts based on paper analysis
- Visualize paper relationships in a graph structure

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key:
   - Create a `.env` file in the project root with:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     ```
   - Or update the `api_key` field in `config.json`

## Usage

Run the application:
```bash
python app.py
```

The application will:
1. Prompt you for a research topic
2. Search for recent papers on that topic
3. Display a list of found papers
4. Offer to analyze the first paper and generate a blog post
5. Allow you to save the blog post to a file

## Project Structure

- `app.py`: Main entry point
- `src/`: Core application code
  - `main.py`: Application logic
  - `graph/`: Graph structure implementation
- `graph/`: LangGraph workflow implementation
  - `nodes.py`: Workflow nodes
  - `workflow.py`: LangGraph workflow definition
- `utils/`: Utility functions
  - `arxiv_client.py`: ArXiv API integration
- `tests/`: Test suite

## Development

Run tests:
```bash
pytest
```

## License

MIT

## Note

This is an MVP (Minimum Viable Product) built as a demonstration. For production use, additional error handling, security measures, and optimizations would be required.