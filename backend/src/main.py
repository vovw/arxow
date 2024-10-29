from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import io
from pydantic import BaseModel
from typing import Dict, Optional, Union, Any
import json
from openai import OpenAI
from os import getenv

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

class PaperAnalysis(BaseModel):
    first_pass: Optional[Dict[str, Any]] = {}
    second_pass: Optional[Dict[str, Any]] = {}
    third_pass: Optional[Dict[str, Any]] = {}

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

def analyze_with_llm(text: str, pass_number: int) -> Dict[str, Any]:
    prompts = {
        1: """Analyze this research paper for a first pass reading. Focus on:
            1. Title, abstract, and introduction analysis
            2. Section and sub-section headings
            3. Conclusions
            4. References overview

            Then answer the five C's:
            1. Category: What type of paper is this?
            2. Context: Which other papers is it related to?
            3. Correctness: Do the assumptions appear valid?
            4. Contributions: What are the paper's main contributions?
            5. Clarity: Is the paper well written?

            Format your response as a structured JSON object with the following format:
            {
                "overview": {
                    "title_analysis": "...",
                    "abstract_analysis": "...",
                    "introduction_analysis": "..."
                },
                "structure": {
                    "sections": [...],
                    "subsections": [...]
                },
                "conclusions": "...",
                "references": "...",
                "five_cs": {
                    "category": "...",
                    "context": "...",
                    "correctness": "...",
                    "contributions": "...",
                    "clarity": "..."
                }
            }""",

        2: """Perform a second pass analysis of this research paper. Focus on:
            1. Detailed analysis of figures, diagrams, and illustrations
            2. Evaluation of graphs and statistical significance
            3. Main thrust of the paper with supporting evidence
            4. Key technical concepts and terminology
            5. Relevant references for further reading

            Format your response as a structured JSON object with the following format:
            {
                "visual_analysis": {
                    "figures": [...],
                    "diagrams": [...],
                    "graphs": [...]
                },
                "statistical_analysis": "...",
                "main_thrust": {
                    "key_arguments": [...],
                    "supporting_evidence": [...]
                },
                "technical_concepts": [...],
                "key_references": [...]
            }""",

        3: """Perform a deep third pass analysis of this research paper. Focus on:
            1. Virtual re-implementation of the paper
            2. Identification and analysis of assumptions
            3. Critical evaluation of methodologies
            4. Comparison with potential alternative approaches
            5. Strong and weak points
            6. Potential future work directions

            Format your response as a structured JSON object with the following format:
            {
                "implementation": {
                    "key_steps": [...],
                    "challenges": [...]
                },
                "assumptions": {
                    "explicit": [...],
                    "implicit": [...]
                },
                "methodology_evaluation": "...",
                "alternative_approaches": [...],
                "evaluation": {
                    "strengths": [...],
                    "weaknesses": [...]
                },
                "future_work": [...]
            }"""
    }

    try:
        print(f"Starting analysis for pass {pass_number}")  # Debug log

        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "your-site-url",
                "X-Title": "Research Paper Analyzer",
            },
            model="google/gemini-flash-1.5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{prompts[pass_number]}\n\nPaper content: {text}"
                        }
                    ]
                }
            ]
        )

        response_content = completion.choices[0].message.content
        print(f"Raw response received: {response_content[:200]}...")  # Debug log

        # Clean up the response content
        cleaned_content = clean_json_response(response_content)
        print(f"Cleaned content: {cleaned_content[:200]}...")  # Debug log

        try:
            parsed_json = json.loads(cleaned_content)
            print("Successfully parsed JSON response")  # Debug log
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")  # Debug log
            # Return a structured error response
            return {
                "error": "Failed to parse JSON response",
                "details": str(e),
                "raw_content": cleaned_content
            }

    except Exception as e:
        print(f"Analysis error: {str(e)}")  # Debug log
        return {
            "error": "Analysis failed",
            "details": str(e)
        }

@app.post("/analyze/paper")
async def analyze_paper(file: UploadFile = File(...), pass_number: int = 1) -> Dict[str, Any]:
    try:
        print(f"Processing paper for pass {pass_number}")  # Debug log

        # Read PDF content
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

        # Extract text from PDF
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        print(f"Extracted {len(text)} characters from PDF")  # Debug log

        # Get analysis based on pass number
        analysis_result = analyze_with_llm(text, pass_number)

        print("Analysis completed successfully")  # Debug log
        return {"analysis": analysis_result}

    except Exception as e:
        print(f"Error processing paper: {str(e)}")  # Debug log
        return {
            "error": f"Failed to process paper: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
