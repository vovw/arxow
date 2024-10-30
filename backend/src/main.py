from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from marker.convert import convert_single_pdf
from marker.models import load_all_models
import tempfile
import os
from pydantic import BaseModel
from typing import Dict, Optional, Union, Any, List
import json
from openai import OpenAI
from os import getenv
import base64
from PIL import Image
import io
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("OPENROUTER_API_KEY"),
)

# Load models once at startup
model_lst = load_all_models()

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
    # Add metadata context to the prompts
    metadata_context = f"""
    Paper metadata:
    - Number of pages: {metadata.get('pages', 'unknown')}
    - Number of tables: {metadata.get('block_stats', {}).get('table', 0)}
    - Number of code blocks: {metadata.get('block_stats', {}).get('code', 0)}
    - Number of equations: {metadata.get('block_stats', {}).get('equations', {}).get('equations', 0)}
    """

    # Include image information in the context
    image_context = f"The paper contains {len(images)} figures/images."

    prompts = {
        1: f"{metadata_context}\n{image_context}\nAnalyze this research paper for a first pass reading...",  # Rest of prompt 1
        2: f"{metadata_context}\n{image_context}\nPerform a second pass analysis...",  # Rest of prompt 2
        3: f"{metadata_context}\n{image_context}\nPerform a deep third pass analysis..."  # Rest of prompt 3
    }

    try:
        print(f"Starting analysis for pass {pass_number}")

        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "your-site-url",
                "X-Title": "Research Paper Analyzer",
            },
            model="google/gemini-flash-1.5",
            messages=[
                {
                    "role": "user",
                    "content": f"{prompts[pass_number]}\n\nPaper content: {text}"
                }
            ]
        )

        response_content = completion.choices[0].message.content
        if response_content is None:
            return {"error": "No response received from LLM"}

        cleaned_content = clean_json_response(response_content)

        try:
            parsed_json = json.loads(cleaned_content)
            return parsed_json
        except json.JSONDecodeError as e:
            return {
                "error": "Failed to parse JSON response",
                "details": str(e),
                "raw_content": cleaned_content
            }

    except Exception as e:
        return {
            "error": "Analysis failed",
            "details": str(e)
        }

@app.post("/upload/paper")
async def upload_paper(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Initial endpoint to process and store the PDF"""
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

        # Generate document ID (you might want to use a more sophisticated method)
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

        return {
            "document_id": doc_id,
            "metadata": out_meta,
            "message": "Document processed and stored successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process paper: {str(e)}")

@app.post("/analyze/paper/{doc_id}")
async def analyze_paper(doc_id: str, pass_number: int) -> Dict[str, Any]:
    """Endpoint to analyze stored paper for specific pass"""
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
