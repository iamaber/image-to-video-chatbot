# Pydantic AI agent for prompt enhancement using O3 Mini
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
import json
from config import settings
import logging

logger = logging.getLogger(__name__)


class EnhancedPromptResponse(BaseModel):
    # Response from prompt enhancement
    original_prompt: str
    enhanced_prompt: str
    visual_details: str
    cinematography_suggestions: str
    estimated_complexity: str
    recommended_duration: int


# Initialize the O3 Mini agent for prompt enhancement
prompt_enhancement_agent = Agent(
    model=f"openai:{settings.LLM_MODEL}",
    system_prompt="""You are an expert cinematographer and AI video generation specialist. 
Your task is to enhance user prompts for video generation to be more detailed and visually descriptive.

When enhancing prompts:
1. Add specific visual details (colors, lighting, composition)
2. Include cinematography suggestions (camera movement, angles, transitions)
3. Specify the mood and atmosphere
4. Estimate complexity level (simple/medium/complex)
5. Recommend optimal video duration

Return ONLY a valid JSON response with these exact fields:
{
    "original_prompt": "the original prompt",
    "enhanced_prompt": "the enhanced, detailed prompt",
    "visual_details": "specific visual elements and colors",
    "cinematography_suggestions": "camera movements and techniques",
    "estimated_complexity": "simple|medium|complex",
    "recommended_duration": <number between 3 and 30>
}

Do not include any text outside the JSON.""",
    retries=1,
)


async def enhance_prompt(user_prompt: str) -> EnhancedPromptResponse:
    # Enhance user prompt using O3 Mini model
    # Args: user_prompt (Raw user input for video generation)
    # Returns: EnhancedPromptResponse with enhanced details
    try:
        logger.info(f"Enhancing prompt: {user_prompt[:100]}...")
        
        # Run the agent to enhance the prompt
        result = await prompt_enhancement_agent.run(
            f"Enhance this video generation prompt: {user_prompt}",
            result_type=str
        )
        
        # Parse the JSON response
        response_text = result.data
        logger.debug(f"Raw response: {response_text}")
        
        # Extract JSON from response (in case there's extra text)
        try:
            enhanced_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                enhanced_data = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON response: {response_text}")
        
        # Validate and create response
        enhanced_response = EnhancedPromptResponse(**enhanced_data)
        
        logger.info(f"Prompt enhanced successfully. Estimated complexity: {enhanced_response.estimated_complexity}")
        
        return enhanced_response
        
    except Exception as e:
        logger.error(f"Error enhancing prompt: {str(e)}")
        # Fallback: return the original prompt as-is
        return EnhancedPromptResponse(
            original_prompt=user_prompt,
            enhanced_prompt=user_prompt,
            visual_details="User-provided description",
            cinematography_suggestions="Standard cinematography",
            estimated_complexity="medium",
            recommended_duration=5
        )
