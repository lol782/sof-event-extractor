"""
GPT Extractor Module for SoF Event Extractor
Handles event extraction using OpenAI's GPT API
"""

import openai
import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import re
from datetime import datetime

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class GPTExtractor:
    """GPT-based maritime event extraction utility"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key or self.api_key == "sk-demo-key-for-testing":
            logger.warning("OpenAI API key not properly configured")
            self.client = None
        else:
            try:
                openai.api_key = self.api_key
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    async def extract_events(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract maritime events from text using GPT
        
        Args:
            text: Document text content
            
        Returns:
            List[Dict]: List of extracted events
        """
        if not self.client:
            logger.warning("OpenAI client not available, returning sample events")
            return self._get_sample_events()
        
        try:
            # Create prompt for maritime event extraction
            prompt = self._create_extraction_prompt(text)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert maritime analyst specializing in extracting events from Statement of Facts documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            # Parse the response
            content = response.choices[0].message.content
            events = self._parse_gpt_response(content)
            
            logger.info(f"GPT extracted {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"GPT extraction failed: {e}")
            return self._get_sample_events()
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create extraction prompt for GPT"""
        return f"""
        Analyze the following maritime document and extract key events. Return a JSON array of events with the following format:

        [
          {{
            "event": "Brief event name",
            "description": "Detailed description",
            "start": "Start time (if available)",
            "end": "End time (if available)", 
            "location": "Location (if available)",
            "severity": "High/Medium/Low"
          }}
        ]

        Focus on maritime incidents, operational events, weather conditions, and significant occurrences.

        Document text:
        {text[:3000]}...
        
        Return only the JSON array, no other text.
        """
    
    def _parse_gpt_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse GPT response and extract events"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                events = json.loads(json_text)
                
                # Validate and clean events
                cleaned_events = []
                for event in events:
                    if isinstance(event, dict) and 'event' in event:
                        cleaned_event = {
                            'event': event.get('event', 'Unknown Event'),
                            'description': event.get('description', 'No description available'),
                            'start': event.get('start', 'Not Available'),
                            'end': event.get('end', 'Not Available'),
                            'location': event.get('location', 'Not Available'),
                            'severity': event.get('severity', 'Medium')
                        }
                        cleaned_events.append(cleaned_event)
                
                return cleaned_events if cleaned_events else self._get_sample_events()
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT JSON response: {e}")
        except Exception as e:
            logger.error(f"Error parsing GPT response: {e}")
        
        return self._get_sample_events()
    
    def _get_sample_events(self) -> List[Dict[str, Any]]:
        """Return sample events when GPT is not available"""
        return [
            {
                "event": "GPT Service Unavailable",
                "description": "OpenAI GPT service is not properly configured or unavailable. Please check your API key configuration.",
                "start": "Not Available",
                "end": "Not Available",
                "location": "Not Available",
                "severity": "Warning"
            }
        ]
