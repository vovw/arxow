from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from marker.convert import convert_single_pdf
from marker.models import load_all_models
import tempfile
import os
from pydantic import BaseModel, Field
from typing import Dict, Optional, Union, Any, List
import json
from openai import OpenAI
from os import getenv
import base64
from PIL import Image
import io
from datetime import datetime
import logging
import requests
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment validation
OPENROUTER_API_KEY = getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.warning("OPENROUTER_API_KEY not set! API calls will fail.")

MODEL_NAME = getenv("MODEL_NAME", "google/gemini-flash-1.5")
CORS_ORIGINS = getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app = FastAPI(
    title="Arxow API",
    description="ArXiv Paper Analyzer - Extract and analyze research papers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Load models once at startup
logger.info("Loading Marker models...")
try:
    model_lst = load_all_models()
    logger.info("Marker models loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Marker models: {str(e)}")
    model_lst = None

# In-memory storage for processed documents
class ProcessedDocument:
    def __init__(self, markdown_text: str, images: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.markdown_text = markdown_text
        self.images = images
        self.metadata = metadata
        self.analyses = {}  # Store analyses for different passes
        self.citations = None  # Store extracted citations
        self.timestamp = datetime.now()

class DocumentStore:
    def __init__(self):
        self.documents: Dict[str, ProcessedDocument] = {}

    def add_document(self, doc_id: str, document: ProcessedDocument):
        self.documents[doc_id] = document

    def get_document(self, doc_id: str) -> Optional[ProcessedDocument]:
        return self.documents.get(doc_id)

    def cleanup_old_documents(self, max_age_hours: int = 24):
        current_time = datetime.now()
        for doc_id in list(self.documents.keys()):
            age = (current_time - self.documents[doc_id].timestamp).total_seconds() / 3600
            if age > max_age_hours:
                del self.documents[doc_id]

# Initialize document store
document_store = DocumentStore()

class PaperAnalysis(BaseModel):
    first_pass: Optional[Dict[str, Any]] = {}
    second_pass: Optional[Dict[str, Any]] = {}
    third_pass: Optional[Dict[str, Any]] = {}

class ImageData(BaseModel):
    image: str  # base64 encoded image
    page_number: int
    position: Dict[str, float]  # x, y coordinates

def encode_image(image: Image.Image) -> str:
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def process_images(images: Dict[str, Image.Image]) -> List[Dict[str, Any]]:
    """Process and encode images from marker output"""
    processed_images = []
    for img_key, img in images.items():
        if isinstance(img, Image.Image):
            processed_img = {
                'image': encode_image(img),
                'page_number': 1,  # You might want to extract this from img_key
                'position': {'x': 0, 'y': 0},  # Default position
                'caption': '',  # Add caption if available
                'reference': img_key  # Use the key as reference
            }
            processed_images.append(processed_img)
    return processed_images

def clean_json_response(text: str) -> str:
    """Clean the JSON response from markdown formatting"""
    text = text.strip()
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    return text.strip()

def analyze_with_llm(text: str, pass_number: int, metadata: Dict[str, Any], images: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze paper using the three-pass reading method
    Pass 1: Quick scan (5-10 min) - Overview and main contributions
    Pass 2: Deeper reading (1 hour) - Understand content without details
    Pass 3: Virtual re-implementation (1-5 hours) - Deep understanding and critical analysis
    """

    # Add metadata context to the prompts
    metadata_context = f"""Paper metadata:
- Number of pages: {metadata.get('pages', 'unknown')}
- Number of tables: {metadata.get('block_stats', {}).get('table', 0)}
- Number of code blocks: {metadata.get('block_stats', {}).get('code', 0)}
- Number of equations: {metadata.get('block_stats', {}).get('equations', {}).get('equations', 0)}
- Number of figures: {len(images)}"""

    prompts = {
        1: f"""{metadata_context}

FIRST PASS ANALYSIS (Quick Scan - 5-10 minutes)
Perform a quick scan of this research paper. Focus on:

1. Category: What type of paper is this (theoretical, applied, survey, experimental)?
2. Context: What other papers is it related to? What theoretical bases were used?
3. Correctness: Do the assumptions appear valid?
4. Contributions: What are the paper's main contributions (3-5 bullet points)?
5. Clarity: Is the paper well written and easy to follow?
6. Key Findings: What are the most important results or insights?
7. Relevance: What problems does this solve? Who would find this useful?

Return your analysis as a JSON object with these exact keys:
{{
  "category": "string",
  "related_work": ["string"],
  "assumptions_valid": "boolean (true/false)",
  "main_contributions": ["string"],
  "clarity_rating": "number (1-10)",
  "clarity_notes": "string",
  "key_findings": ["string"],
  "problems_solved": "string",
  "target_audience": "string",
  "read_further": "boolean - should reader invest more time?"
}}""",

        2: f"""{metadata_context}

SECOND PASS ANALYSIS (Detailed Reading - 1 hour)
Read the paper with care but skip proofs and implementation details. Focus on:

1. Figures and Diagrams: Identify 1-3 most important figures. Why are they crucial?
2. Methodology: What approach/methods does the paper use? How do they work at a high level?
3. Key Equations: Which equations are most important? What do they represent?
4. Experimental Setup: What datasets, benchmarks, or experiments were used?
5. Results: What were the main experimental results and comparisons?
6. Important Tables: Which tables contain the most critical evaluation data?
7. Unread References: List 3-5 references you should read to understand this paper better
8. Grasp: Do you now understand the paper's content and flow?

Return your analysis as a JSON object with these exact keys:
{{
  "critical_figures": [
    {{
      "reference": "string (e.g., Figure 1)",
      "description": "string",
      "why_important": "string"
    }}
  ],
  "methodology": {{
    "approach": "string",
    "how_it_works": "string",
    "novelty": "string"
  }},
  "key_equations": [
    {{
      "equation": "string or latex",
      "meaning": "string",
      "why_important": "string"
    }}
  ],
  "experiments": {{
    "datasets": ["string"],
    "benchmarks": ["string"],
    "baseline_comparisons": ["string"]
  }},
  "main_results": ["string"],
  "important_tables": [
    {{
      "reference": "string",
      "content_summary": "string"
    }}
  ],
  "references_to_read": ["string"],
  "content_understood": "boolean"
}}""",

        3: f"""{metadata_context}

THIRD PASS ANALYSIS (Deep Understanding - 1-5 hours)
Virtually re-implement the paper. Think critically and challenge every assumption. Focus on:

1. Virtual Re-implementation:
   - What would you need to implement this from scratch?
   - What are the key algorithmic steps?
   - What data structures and computational resources are needed?

2. Strong Points: What are the paper's greatest strengths?

3. Weak Points and Limitations:
   - What assumptions might be problematic?
   - What corner cases or scenarios weren't addressed?
   - What are the limitations mentioned (and not mentioned)?

4. Reproducibility:
   - Is there enough detail to reproduce the work?
   - What information is missing?
   - Are datasets and code available?

5. Innovation Assessment:
   - What is truly novel vs. incremental improvements?
   - How significant is the contribution to the field?

6. Future Work:
   - What are promising directions for extension?
   - What questions remain unanswered?

7. Presentation Quality:
   - How could the paper be improved?
   - Are there any errors or unclear sections?

Return your analysis as a JSON object with these exact keys:
{{
  "reimplementation_requirements": {{
    "key_algorithms": ["string"],
    "data_structures": ["string"],
    "computational_resources": "string",
    "estimated_complexity": "string"
  }},
  "strong_points": ["string"],
  "weak_points": ["string"],
  "limitations": {{
    "mentioned": ["string"],
    "not_mentioned": ["string"]
  }},
  "reproducibility": {{
    "reproducible": "boolean",
    "missing_information": ["string"],
    "code_available": "boolean",
    "data_available": "boolean"
  }},
  "innovation_assessment": {{
    "truly_novel": ["string"],
    "incremental": ["string"],
    "significance": "string (Low/Medium/High/Groundbreaking)"
  }},
  "future_work": ["string"],
  "presentation_improvements": ["string"],
  "overall_quality": "number (1-10)",
  "recommendation": "string (Reject/Weak Accept/Accept/Strong Accept)"
}}"""
    }

    try:
        logger.info(f"Starting pass {pass_number} analysis")

        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com",
                "X-Title": "Arxow - Research Paper Analyzer",
            },
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert research paper reviewer. Analyze papers using the three-pass reading method. Always return valid JSON matching the requested schema exactly."
                },
                {
                    "role": "user",
                    "content": f"{prompts[pass_number]}\n\n=== PAPER CONTENT ===\n{text[:50000]}"  # Limit to avoid token limits
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent analysis
        )

        response_content = completion.choices[0].message.content
        if response_content is None:
            logger.error("No response received from LLM")
            return {"error": "No response received from LLM"}

        cleaned_content = clean_json_response(response_content)

        try:
            parsed_json = json.loads(cleaned_content)
            logger.info(f"Pass {pass_number} analysis completed successfully")
            return parsed_json
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            return {
                "error": "Failed to parse JSON response",
                "details": str(e),
                "raw_content": cleaned_content[:1000]  # Limit raw content length
            }

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return {
            "error": "Analysis failed",
            "details": str(e)
        }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Arxow API",
        "version": "1.0.0",
        "models_loaded": model_lst is not None
    }

@app.post("/upload/paper")
async def upload_paper(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and process a PDF paper
    - Extracts text, figures, tables using Marker-PDF
    - Returns document ID for subsequent analysis
    """
    if model_lst is None:
        raise HTTPException(status_code=500, detail="Marker models not loaded. Check server logs.")

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    logger.info(f"Processing upload: {file.filename}")

    try:
        # Create a temporary file to save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()

            # Convert PDF to markdown using marker
            full_text, images_dict, out_meta = convert_single_pdf(tmp_file.name, model_lst)

        # Clean up temporary file
        os.unlink(tmp_file.name)

        # Process images
        processed_images = process_images(images_dict)
        logger.info(f"Extracted {len(processed_images)} images from PDF")

        # Generate document ID
        doc_id = base64.urlsafe_b64encode(os.urandom(16)).decode('ascii')

        # Store processed document
        document_store.add_document(
            doc_id,
            ProcessedDocument(
                markdown_text=full_text,
                images=processed_images,
                metadata=out_meta
            )
        )

        logger.info(f"Document processed successfully. ID: {doc_id}")

        return {
            "document_id": doc_id,
            "metadata": out_meta,
            "message": "Document processed and stored successfully",
            "filename": file.filename
        }

    except Exception as e:
        logger.error(f"Failed to process paper: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process paper: {str(e)}")

@app.post("/analyze/paper/{doc_id}")
async def analyze_paper(doc_id: str, pass_number: int) -> Dict[str, Any]:
    """
    Analyze a processed paper using the three-pass reading method
    - pass_number: 1 (quick scan), 2 (detailed reading), or 3 (deep analysis)
    - Returns cached results if available
    """
    if pass_number not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="pass_number must be 1, 2, or 3")

    logger.info(f"Analysis request - Document: {doc_id}, Pass: {pass_number}")

    try:
        # Cleanup old documents first
        document_store.cleanup_old_documents()

        # Retrieve stored document
        document = document_store.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if analysis for this pass already exists
        if pass_number in document.analyses:
            return {
                "analysis": document.analyses[pass_number],
                "metadata": document.metadata,
                "images": document.images,
                "cached": True
            }

        # Perform new analysis
        analysis_result = analyze_with_llm(
            document.markdown_text,
            pass_number,
            document.metadata,
            document.images
        )

        # Store the analysis result
        document.analyses[pass_number] = analysis_result

        return {
            "analysis": analysis_result,
            "metadata": document.metadata,
            "images": document.images,
            "cached": False
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/deep-research/{doc_id}")
async def deep_research(doc_id: str, question: Dict[str, str]) -> Dict[str, Any]:
    """
    Deep research Q&A endpoint
    Ask specific questions about the paper and get detailed answers
    """
    logger.info(f"Deep research request - Document: {doc_id}, Question: {question.get('question', '')}")

    try:
        # Retrieve stored document
        document = document_store.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        user_question = question.get("question", "").strip()
        if not user_question:
            raise HTTPException(status_code=400, detail="Question is required")

        # Use LLM to answer the question based on the paper
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com",
                "X-Title": "Arxow - Deep Research",
            },
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert research assistant. Answer questions about academic papers based on their content. Provide detailed, accurate, and well-structured answers. If the paper doesn't contain information to answer the question, say so clearly."
                },
                {
                    "role": "user",
                    "content": f"""Based on this research paper, please answer the following question:

Question: {user_question}

Paper content:
{document.markdown_text[:30000]}

Provide a comprehensive answer based on the paper's content."""
                }
            ],
            temperature=0.3,
        )

        answer = completion.choices[0].message.content
        if answer is None:
            raise HTTPException(status_code=500, detail="No response from LLM")

        logger.info(f"Deep research completed successfully for doc {doc_id}")

        return {
            "question": user_question,
            "answer": answer,
            "document_id": doc_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deep research failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deep research failed: {str(e)}")

@app.post("/extract/citations/{doc_id}")
async def extract_citations(doc_id: str) -> Dict[str, Any]:
    """
    Extract citations and references from the paper
    """
    logger.info(f"Citation extraction request - Document: {doc_id}")

    try:
        # Retrieve stored document
        document = document_store.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if citations were already extracted
        if hasattr(document, 'citations') and document.citations:
            return {
                "citations": document.citations,
                "cached": True
            }

        # Use LLM to extract citations
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com",
                "X-Title": "Arxow - Citation Extraction",
            },
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting citations from academic papers. Extract all citations and return them in a structured JSON format."
                },
                {
                    "role": "user",
                    "content": f"""Extract all citations from this research paper. Return a JSON object with the following structure:

{{
  "references": [
    {{
      "number": "citation number or key",
      "title": "paper title",
      "authors": ["author1", "author2"],
      "year": "publication year",
      "venue": "conference or journal name",
      "relevance": "brief description of why this paper is cited"
    }}
  ],
  "key_references": ["list of most important reference numbers"],
  "total_citations": number
}}

Paper content:
{document.markdown_text[:30000]}"""
                }
            ],
            temperature=0.2,
        )

        response_content = completion.choices[0].message.content
        if response_content is None:
            raise HTTPException(status_code=500, detail="No response from LLM")

        cleaned_content = clean_json_response(response_content)

        try:
            citations = json.loads(cleaned_content)
            # Store citations in document
            document.citations = citations

            logger.info(f"Extracted {citations.get('total_citations', 0)} citations")

            return {
                "citations": citations,
                "cached": False
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse citations JSON: {str(e)}")
            return {
                "error": "Failed to parse citations",
                "details": str(e),
                "raw_content": cleaned_content[:500]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Citation extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Citation extraction failed: {str(e)}")

def extract_arxiv_id(url: str) -> Optional[str]:
    """
    Extract arXiv ID from various arXiv URL formats
    Supports:
    - https://arxiv.org/abs/2301.12345
    - https://arxiv.org/pdf/2301.12345.pdf
    - https://arxiv.org/abs/2301.12345v1
    - arxiv.org/abs/2301.12345
    """
    patterns = [
        r'arxiv\.org/abs/(\d+\.\d+)',
        r'arxiv\.org/pdf/(\d+\.\d+)',
        r'(\d{4}\.\d{4,5})',  # Just the ID
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

def download_arxiv_pdf(arxiv_id: str) -> bytes:
    """
    Download PDF from arXiv given an arXiv ID
    """
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    logger.info(f"Downloading PDF from {pdf_url}")

    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to download PDF from arXiv: {str(e)}")

@app.post("/upload/from-url")
async def upload_from_url(url_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Upload and process a paper from a URL (arXiv, etc.)
    - Automatically detects arXiv URLs
    - Downloads the PDF
    - Processes it like a regular upload
    """
    if model_lst is None:
        raise HTTPException(status_code=500, detail="Marker models not loaded. Check server logs.")

    url = url_data.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    logger.info(f"Processing URL: {url}")

    # Extract arXiv ID
    arxiv_id = extract_arxiv_id(url)
    if not arxiv_id:
        raise HTTPException(status_code=400, detail="Invalid or unsupported URL. Currently only arXiv URLs are supported.")

    try:
        # Download PDF from arXiv
        pdf_content = download_arxiv_pdf(arxiv_id)

        # Create a temporary file to save the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file.flush()

            # Convert PDF to markdown using marker
            full_text, images_dict, out_meta = convert_single_pdf(tmp_file.name, model_lst)

        # Clean up temporary file
        os.unlink(tmp_file.name)

        # Process images
        processed_images = process_images(images_dict)
        logger.info(f"Extracted {len(processed_images)} images from PDF")

        # Generate document ID
        doc_id = base64.urlsafe_b64encode(os.urandom(16)).decode('ascii')

        # Store processed document
        document_store.add_document(
            doc_id,
            ProcessedDocument(
                markdown_text=full_text,
                images=processed_images,
                metadata=out_meta
            )
        )

        logger.info(f"Document processed successfully from URL. ID: {doc_id}")

        return {
            "document_id": doc_id,
            "metadata": out_meta,
            "message": "Document processed and stored successfully",
            "filename": f"arxiv_{arxiv_id}.pdf",
            "arxiv_id": arxiv_id,
            "source_url": url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process paper from URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process paper: {str(e)}")
