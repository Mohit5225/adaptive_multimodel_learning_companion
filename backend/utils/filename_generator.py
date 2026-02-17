"""
Intelligent filename generator for video content.
Extracts meaningful concepts from prompts and creates human-readable, unique filenames.
"""
import re
from datetime import datetime, timezone


# Common stop words to filter out
STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been',
    'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'can', 'me', 'my', 'you', 'your', 'he', 'she',
    'it', 'its', 'we', 'our', 'they', 'their', 'what', 'which', 'who', 'where',
    'when', 'why', 'how', 'this', 'that', 'these', 'those', 'i', 'if', 'about',
    'through', 'during', 'because', 'up', 'down', 'out', 'off', 'over', 'under',
    'just', 'so', 'show', 'me', 'the', 'visualize', 'animation', 'video'
}

# Priority keywords - concepts we want to preserve if they exist
PRIORITY_KEYWORDS = {
    'gravity', 'quantum', 'relativity', 'photosynthesis', 'mitochondria', 'dna',
    'molecule', 'atom', 'electron', 'force', 'energy', 'wave', 'particle',
    'motion', 'velocity', 'acceleration', 'friction', 'momentum', 'vector',
    'triangle', 'pythagorean', 'circle', 'quadratic', 'equation', 'derivative',
    'integral', 'function', 'limit', 'sequence', 'series', 'algebra', 'geometry',
    'trigonometry', 'cosine', 'sine', 'tangent', 'angle', 'radius', 'diameter',
    'evolution', 'cell', 'organism', 'ecosystem', 'organism', 'biology', 'physics',
    'chemistry', 'thermodynamics', 'entropy', 'acid', 'base', 'reaction', 'compound'
}


def extract_keywords(prompt: str, max_keywords: int = 3) -> list:
    """
    Extract meaningful keywords from a prompt.
    Smart extraction that prioritizes domain-specific terms.
    
    Args:
        prompt: User's original prompt/question
        max_keywords: Maximum number of keywords to extract
    
    Returns:
        List of extracted keywords (sorted by relevance)
    """
    # Convert to lowercase and remove special characters but keep hyphens
    cleaned = re.sub(r'[^\w\s\-]', '', prompt.lower())
    
    # Split into words
    words = cleaned.split()
    
    # First pass: look for priority keywords (domain-specific)
    priority_matches = [w for w in words if w in PRIORITY_KEYWORDS]
    
    if priority_matches:
        return priority_matches[:max_keywords]
    
    # Second pass: filter out stop words and very short words
    meaningful_words = [
        w for w in words 
        if w not in STOP_WORDS and len(w) > 2 and w.isalpha()
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_words = []
    for w in meaningful_words:
        if w not in seen:
            unique_words.append(w)
            seen.add(w)
    
    # Return top N keywords
    return unique_words[:max_keywords]


def sanitize_slug(text: str) -> str:
    """
    Convert text to URL-safe slug.
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # Remove any non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Strip leading/trailing hyphens
    slug = slug.strip('-')
    
    # Limit to reasonable length
    return slug[:40]


def generate_video_filename(prompt: str, chat_id: str = None, message_id: str = None) -> str:
    """
    Generate a human-readable, unique video filename based on prompt content.
    
    Format: {topic-slug}-{timestamp}-{short_id}.mp4
    Example: gravity-visualization-20260208-143025-a7f2.mp4
    
    Args:
        prompt: User's original prompt
        chat_id: Chat ID (optional, used for short ID)
        message_id: Message ID (optional, used for short ID)
    
    Returns:
        Unique filename string
    """
    # Extract meaningful keywords
    keywords = extract_keywords(prompt)
    
    if not keywords:
        # Fallback if no meaningful keywords found
        keywords = ['content']
    
    # Create slug from keywords
    topic_slug = '-'.join(keywords)
    topic_slug = sanitize_slug(topic_slug)
    
    # Generate timestamp (timezone-aware)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    
    # Generate short unique ID from message or chat ID
    if message_id:
        short_id = str(message_id)[-4:].lower()
    elif chat_id:
        short_id = str(chat_id)[-4:].lower()
    else:
        # Fallback: use random hex
        import secrets
        short_id = secrets.token_hex(2)
    
    # Combine into filename
    filename = f"vid-{topic_slug}-{timestamp}-{short_id}.mp4"
    
    return filename


def get_video_metadata(filename: str) -> dict:
    """
    Parse a generated filename to extract metadata.
    
    Returns:
        dict with 'topic', 'timestamp', 'id'
    """
    # Pattern: vid-{topic-slug}-{timestamp}-{short_id}.mp4
    pattern = r'^vid-(.+)-(\d{8}-\d{6})-([a-f0-9\w]+)\.mp4$'
    match = re.match(pattern, filename)
    
    if not match:
        return {"filename": filename, "parseable": False}
    
    topic_slug, timestamp_str, short_id = match.groups()
    
    return {
        "filename": filename,
        "parseable": True,
        "topic": topic_slug.replace('-', ' ').title(),
        "topic_slug": topic_slug,
        "timestamp": timestamp_str,
        "short_id": short_id,
    }


# Test examples (can be removed in production)
if __name__ == "__main__":
    test_prompts = [
        "Show me how gravity works",
        "Visualize the pythagorean theorem with animation",
        "Explain quantum mechanics",
        "Draw a circle and show the radius",
        "Create an animation for photosynthesis process",
    ]
    
    for prompt in test_prompts:
        filename = generate_video_filename(prompt)
        metadata = get_video_metadata(filename)
        print(f"Prompt: {prompt}")
        print(f"  → Filename: {filename}")
        print(f"  → Topic: {metadata.get('topic', 'N/A')}")
        print()
