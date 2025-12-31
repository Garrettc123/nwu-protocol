"""Verification logic for Agent-Alpha."""

import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .config import config

logger = logging.getLogger(__name__)


class Verifier:
    """AI-powered verification engine."""
    
    def __init__(self):
        """Initialize the verifier with OpenAI."""
        if not config.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured. Using mock verification.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                api_key=config.OPENAI_API_KEY,
                model="gpt-4",
                temperature=0.3
            )
    
    async def verify_code(self, code_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify code quality and originality.
        
        Args:
            code_content: The code to verify
            metadata: Additional metadata about the submission
            
        Returns:
            Verification results with scores and reasoning
        """
        if not self.llm:
            return self._mock_verification("code")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert code reviewer for the NWU Protocol. 
            Analyze the provided code and score it on the following criteria (0-100 each):
            1. Quality: Syntax, best practices, code structure
            2. Originality: Uniqueness, not plagiarized
            3. Security: Vulnerability assessment
            4. Documentation: Comments, clarity
            
            Provide scores and detailed reasoning."""),
            ("human", "Analyze this code:\n\n{code}\n\nMetadata: {metadata}")
        ])
        
        try:
            response = await self.llm.ainvoke(
                prompt.format_messages(code=code_content, metadata=str(metadata))
            )
            return self._parse_response(response.content, "code")
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return self._mock_verification("code")
    
    async def verify_dataset(self, dataset_info: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify dataset quality and validity.
        
        Args:
            dataset_info: Information about the dataset
            metadata: Additional metadata
            
        Returns:
            Verification results
        """
        if not self.llm:
            return self._mock_verification("dataset")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data quality expert for the NWU Protocol.
            Analyze the dataset and score it on:
            1. Quality: Data integrity, completeness
            2. Originality: Uniqueness of the dataset
            3. Utility: Potential value for AI/ML
            4. Documentation: Metadata, description quality
            
            Provide scores and reasoning."""),
            ("human", "Analyze this dataset:\n\n{info}\n\nMetadata: {metadata}")
        ])
        
        try:
            response = await self.llm.ainvoke(
                prompt.format_messages(info=dataset_info, metadata=str(metadata))
            )
            return self._parse_response(response.content, "dataset")
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return self._mock_verification("dataset")
    
    async def verify_document(self, document_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify document quality and originality.
        
        Args:
            document_content: The document text
            metadata: Additional metadata
            
        Returns:
            Verification results
        """
        if not self.llm:
            return self._mock_verification("document")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a document quality assessor for the NWU Protocol.
            Analyze the document and score it on:
            1. Quality: Content quality, coherence
            2. Originality: Uniqueness, not plagiarized
            3. Accuracy: Factual correctness
            4. Completeness: Thoroughness of coverage
            
            Provide scores and reasoning."""),
            ("human", "Analyze this document:\n\n{content}\n\nMetadata: {metadata}")
        ])
        
        try:
            response = await self.llm.ainvoke(
                prompt.format_messages(content=document_content[:5000], metadata=str(metadata))
            )
            return self._parse_response(response.content, "document")
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return self._mock_verification("document")
    
    def _parse_response(self, response: str, file_type: str) -> Dict[str, Any]:
        """Parse LLM response into structured scores."""
        import re
        
        lines = response.split('\n')
        
        scores = {
            'quality_score': 75.0,
            'originality_score': 70.0,
            'security_score': 65.0 if file_type == "code" else None,
            'documentation_score': 60.0
        }
        
        # Try to extract scores from response using regex
        for line in lines:
            # Match patterns like "Quality: 85" or "Quality Score: 85.5"
            if 'quality' in line.lower():
                match = re.search(r'(\d+(?:\.\d+)?)', line)
                if match:
                    scores['quality_score'] = float(match.group(1))
            elif 'originality' in line.lower():
                match = re.search(r'(\d+(?:\.\d+)?)', line)
                if match:
                    scores['originality_score'] = float(match.group(1))
            elif 'security' in line.lower() and file_type == "code":
                match = re.search(r'(\d+(?:\.\d+)?)', line)
                if match:
                    scores['security_score'] = float(match.group(1))
            elif 'documentation' in line.lower():
                match = re.search(r'(\d+(?:\.\d+)?)', line)
                if match:
                    scores['documentation_score'] = float(match.group(1))
        
        # Calculate overall vote score
        vote_score = sum(s for s in scores.values() if s is not None) / len([s for s in scores.values() if s is not None])
        
        return {
            'vote_score': round(vote_score, 2),
            'quality_score': scores['quality_score'],
            'originality_score': scores['originality_score'],
            'security_score': scores['security_score'],
            'documentation_score': scores['documentation_score'],
            'reasoning': response[:500],  # Truncate for storage
            'details': {
                'file_type': file_type,
                'full_analysis': response
            }
        }
    
    def _mock_verification(self, file_type: str) -> Dict[str, Any]:
        """Provide mock verification results when OpenAI is not configured."""
        import random
        
        base_score = random.randint(65, 85)
        
        return {
            'vote_score': float(base_score),
            'quality_score': float(base_score + random.randint(-5, 5)),
            'originality_score': float(base_score + random.randint(-10, 10)),
            'security_score': float(base_score + random.randint(-5, 5)) if file_type == "code" else None,
            'documentation_score': float(base_score + random.randint(-10, 5)),
            'reasoning': f"Mock verification for {file_type}. OpenAI API key not configured.",
            'details': {
                'file_type': file_type,
                'mock': True
            }
        }


# Global verifier instance
verifier = Verifier()
