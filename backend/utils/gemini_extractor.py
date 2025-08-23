"""
Gemini Extractor Module for SoF Event Extractor
Handles event extraction using Google's Gemini AI
"""

import google.generativeai as genai
import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiEmbeddingExtractor:
    """Gemini-based maritime event extraction utility"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.gemini_available = False
        
        if not self.api_key or self.api_key == "":
            logger.warning("Google API key not properly configured")
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.gemini_available = True
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.model = None
    
    async def extract_events_with_gemini(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract maritime events from text using Gemini
        
        Args:
            text: Document text content
            
        Returns:
            List[Dict]: List of extracted events
        """
        if not self.model or not self.gemini_available:
            logger.warning("Gemini model not available, returning sample events")
            return self._get_sample_events()
        
        try:
            # Create prompt for maritime event extraction
            prompt = self._create_extraction_prompt(text)
            
            response = self.model.generate_content(prompt)
            
            # Parse the response
            events = self._parse_gemini_response(response.text)
            
            logger.info(f"Gemini extracted {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}")
            return self._get_sample_events()
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create extraction prompt for Gemini"""
        return f"""
        You are an expert maritime analyst. Analyze the following maritime document and extract key events.

        Please return ONLY a valid JSON array of events with this exact format:

        [
          {{
            "event": "Brief event name",
            "description": "Detailed description of what happened",
            "start": "Start time if available, otherwise 'Not Available'",
            "end": "End time if available, otherwise 'Not Available'", 
            "location": "Location if available, otherwise 'Not Available'",
            "severity": "High, Medium, or Low"
          }}
        ]

        Focus on:
        - Maritime incidents (collisions, grounding, machinery failures)
        - Operational events (arrival, departure, berthing, loading)
        - Weather conditions that affected operations
        - Any safety or security events
        - Navigation events
        - Cargo operations

        Document text:
        {text[:4000]}

        Return ONLY the JSON array, no additional text or explanation.
        """
    
    def _parse_gemini_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse Gemini response and extract events"""
        try:
            # Clean the response to extract JSON
            content = content.strip()
            
            # Find JSON array in response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                events = json.loads(json_text)
                
                # Validate and clean events
                cleaned_events = []
                for event in events:
                    if isinstance(event, dict) and 'event' in event:
                        cleaned_event = {
                            'event': str(event.get('event', 'Unknown Event'))[:100],
                            'description': str(event.get('description', 'No description available'))[:500],
                            'start': str(event.get('start', 'Not Available'))[:50],
                            'end': str(event.get('end', 'Not Available'))[:50],
                            'location': str(event.get('location', 'Not Available'))[:100],
                            'severity': str(event.get('severity', 'Medium'))[:20]
                        }
                        cleaned_events.append(cleaned_event)
                
                return cleaned_events if cleaned_events else self._get_sample_events()
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            logger.debug(f"Raw response: {content}")
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            logger.debug(f"Raw response: {content}")
        
        return self._get_sample_events()
    
    def _get_sample_events(self) -> List[Dict[str, Any]]:
        """Return sample events when Gemini is not available"""
        return [
            {
                "event": "Gemini Service Unavailable",
                "description": "Google Gemini AI service is not properly configured or unavailable. Please check your API key configuration.",
                "start": "Not Available",
                "end": "Not Available",
                "location": "Not Available",
                "severity": "Warning"
            }
        ]
