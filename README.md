# Arxow - ArXiv Paper Analyzer

Transform dense research papers into digestible summaries using AI-powered analysis. Arxow extracts PDFs, parses them with Marker, and provides multi-level analysis to help you understand academic papers faster.

## Features

### Core Analysis
- **PDF to Markdown Conversion**: Uses Marker-PDF for high-quality extraction of text, equations, and figures
- **Multi-Pass Analysis**: Three-level reading approach (inspired by the three-pass method)
  - **First Pass** (⌨️ `1`): Quick overview, main contributions, and key findings
  - **Second Pass** (⌨️ `2`): Deeper dive into methodology, experiments, and results
  - **Third Pass** (⌨️ `3`): Critical analysis, reproducibility assessment, and detailed insights
- **Figure Extraction**: Automatically extracts and displays key diagrams and figures
- **Smart Caching**: Stores processed documents and analyses in memory for faster re-analysis

### Advanced Features
- **🧠 Deep Research Q&A**: Ask specific questions about the paper and get detailed AI-powered answers
- **📚 Citation Extraction**: Automatically extracts and analyzes all references from the paper
- **📥 Export Options**: Export analysis to Markdown or JSON format (⌨️ `e`)
- **📖 Paper Library**: Recent papers saved locally for quick re-access
- **⚡ Vim Keybindings**: Full keyboard navigation for power users
  - `j/k` - Scroll down/up
  - `g/G` - Jump to top/bottom
  - `1/2/3` - Run analysis passes
  - `Shift+D` - Toggle dark mode
  - `?` - Show keyboard shortcuts
  - `e` - Export analysis
- **🌙 Dark Mode**: Beautiful dark theme with persistent preference

### Modern UI
- **Gradient Design**: Beautiful gradients and animations
- **Responsive Layout**: Works perfectly on desktop and mobile
- **Loading States**: Clear visual feedback during processing
- **Error Handling**: Comprehensive error messages and recovery
- **Accessibility**: Full keyboard navigation and ARIA labels

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- Marker-PDF (PDF parsing)
- OpenAI API (via OpenRouter for LLM analysis)
- Pydantic (data validation)

**Frontend:**
- Next.js 15
- React 19 (RC)
- Tailwind CSS
- shadcn/ui components

## Prerequisites

- Python 3.12+
- Node.js 18+ (or Bun)
- OpenRouter API key (for LLM access)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd arxow
```

### 2. Backend Setup

```bash
cd backend

# Install uv (Python package manager) if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Create .env file
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### 3. Frontend Setup

```bash
cd frontend

# Using npm
npm install

# Or using bun (faster)
bun install

# Create .env.local file
cp .env.example .env.local
# Configure backend URL if needed (default: http://localhost:8000)
```

## Configuration

### Backend (.env)

```env
OPENROUTER_API_KEY=your_api_key_here
MODEL_NAME=google/gemini-flash-1.5  # Optional: customize the LLM model
CORS_ORIGINS=http://localhost:3000  # Comma-separated allowed origins
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

### Start the Backend

```bash
cd backend
source .venv/bin/activate  # Activate virtual environment
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000
API docs at http://localhost:8000/docs

### Start the Frontend

```bash
cd frontend
npm run dev
# or
bun dev
```

The web interface will be available at http://localhost:3000

## Usage

1. Open http://localhost:3000 in your browser
2. Upload a research paper PDF
3. Click "First Pass" to get a quick overview
4. Click "Second Pass" for deeper analysis (requires First Pass)
5. Click "Third Pass" for critical analysis (requires Second Pass)

Each pass provides:
- Structured analysis of the paper
- Extracted figures and diagrams
- Metadata about the document

## Docker Deployment (Optional)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the application at http://localhost:3000
```

## API Endpoints

### POST /upload/paper
Upload a PDF file for processing
- **Input**: multipart/form-data with PDF file
- **Output**: Document ID, metadata, and processing status

### POST /analyze/paper/{doc_id}?pass_number={1|2|3}
Analyze a processed paper
- **Input**: Document ID and pass number (1-3)
- **Output**: Analysis results, images, and metadata

## Project Structure

```
arxow/
├── backend/
│   ├── src/
│   │   └── main.py          # FastAPI application
│   ├── pyproject.toml        # Python dependencies
│   └── .env.example          # Environment template
├── frontend/
│   ├── app/
│   │   ├── page.js           # Main application page
│   │   ├── layout.js         # Root layout
│   │   └── globals.css       # Global styles
│   ├── components/
│   │   └── ui/               # shadcn/ui components
│   ├── package.json          # Node dependencies
│   └── .env.example          # Environment template
├── docker-compose.yml        # Docker orchestration
└── README.md
```

## How It Works

1. **Upload**: User uploads a PDF file
2. **Parse**: Marker-PDF converts PDF to structured markdown, extracting text, equations, tables, and figures
3. **Store**: Document is stored in memory with a unique ID
4. **Analyze**: User selects an analysis pass (1, 2, or 3)
5. **LLM Processing**: The LLM analyzes the document based on the selected pass
6. **Display**: Results are rendered in the UI with extracted figures

## Prompts Structure

The three-pass reading method:

**First Pass (5-10 minutes):**
- Title, abstract, and introduction
- Section and sub-section headings
- Conclusions
- References (glanced over)

**Second Pass (1 hour):**
- Figures, diagrams, and graphs
- Mark relevant unread references
- Grasp the content without details

**Third Pass (4-5 hours for beginners, 1 hour for experienced readers):**
- Virtually re-implement the paper
- Challenge assumptions
- Think about presentation

## Troubleshooting

**Backend won't start:**
- Ensure Python 3.12+ is installed
- Check that OPENROUTER_API_KEY is set in .env
- Install system dependencies for Marker-PDF (PyTorch, detectron2)

**Frontend can't connect to backend:**
- Verify backend is running on port 8000
- Check NEXT_PUBLIC_API_URL in .env.local
- Ensure CORS is properly configured in backend

**PDF parsing fails:**
- Some PDFs may have complex layouts
- Check backend logs for detailed error messages
- Ensure the PDF is not corrupted or password-protected

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this project for your own purposes.

## Acknowledgments

- [Marker-PDF](https://github.com/VikParuchuri/marker) for excellent PDF parsing
- [OpenRouter](https://openrouter.ai/) for LLM API access
- [shadcn/ui](https://ui.shadcn.com/) for beautiful UI components
- The three-pass reading method by S. Keshav

## Roadmap

- [ ] Persistent storage (database integration)
- [ ] User authentication and paper library
- [ ] Export analysis to PDF/Markdown
- [ ] Support for multiple LLM providers
- [ ] Batch processing of multiple papers
- [ ] Citation graph analysis
- [ ] Paper comparison tool
