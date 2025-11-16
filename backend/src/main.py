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
