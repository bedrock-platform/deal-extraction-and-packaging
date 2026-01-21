"""
LLM Inference Pipeline

Core enrichment logic for Stage 1 semantic deal enrichment.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..common.schema import UnifiedPreEnrichmentSchema, EnrichedDeal, Taxonomy, Safety, Audience, Commercial
from .llm_client import GeminiClient
from .taxonomy_validator import TaxonomyValidator
from .publisher_intelligence import PublisherIntelligence
from .temporal_signals import TemporalSignalExtractor

logger = logging.getLogger(__name__)

# Global instances (initialized lazily)
_taxonomy_validator: Optional[TaxonomyValidator] = None
_publisher_intelligence: Optional[PublisherIntelligence] = None
_temporal_extractor: Optional[TemporalSignalExtractor] = None


def get_taxonomy_validator() -> TaxonomyValidator:
    """Get or create TaxonomyValidator instance."""
    global _taxonomy_validator
    if _taxonomy_validator is None:
        _taxonomy_validator = TaxonomyValidator()
    return _taxonomy_validator


def get_publisher_intelligence() -> PublisherIntelligence:
    """Get or create PublisherIntelligence instance."""
    global _publisher_intelligence
    if _publisher_intelligence is None:
        _publisher_intelligence = PublisherIntelligence()
    return _publisher_intelligence


def get_temporal_extractor() -> TemporalSignalExtractor:
    """Get or create TemporalSignalExtractor instance."""
    global _temporal_extractor
    if _temporal_extractor is None:
        _temporal_extractor = TemporalSignalExtractor()
    return _temporal_extractor


def load_prompt_template(template_name: str) -> str:
    """
    Load prompt template from config directory.
    
    Args:
        template_name: Name of template file (e.g., "taxonomy_prompt.txt")
        
    Returns:
        Template content as string
    """
    template_path = Path(__file__).parent.parent.parent / "config" / "enrichment" / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def format_deal_for_prompt(deal: UnifiedPreEnrichmentSchema) -> Dict[str, str]:
    """
    Format deal data for LLM prompt substitution with Phase 2 enhancements.
    
    Args:
        deal: UnifiedPreEnrichmentSchema instance
        
    Returns:
        Dictionary of formatted values for prompt substitution
    """
    # Format publishers
    publishers_str = ", ".join(deal.publishers) if deal.publishers else "Unknown"
    
    # Format volume metrics
    volume_metrics_str = "N/A"
    if deal.volume_metrics:
        parts = []
        if deal.volume_metrics.bid_requests:
            parts.append(f"Bid Requests: {deal.volume_metrics.bid_requests:,}")
        if deal.volume_metrics.impressions:
            parts.append(f"Impressions: {deal.volume_metrics.impressions:,}")
        if deal.volume_metrics.uniques:
            parts.append(f"Uniques: {deal.volume_metrics.uniques:,}")
        if deal.volume_metrics.bid_requests_ratio:
            parts.append(f"Bid Requests Ratio: {deal.volume_metrics.bid_requests_ratio:,.2f}")
        volume_metrics_str = ", ".join(parts) if parts else "N/A"
    
    # Format taxonomy (if already enriched)
    taxonomy_str = "N/A"
    # This will be populated if we're doing stepwise inference
    
    # Phase 2: Publisher Intelligence
    publisher_intel = get_publisher_intelligence()
    publisher_context = publisher_intel.format_publisher_context_for_prompt(deal.publishers)
    
    # Phase 2: Temporal Signals
    temporal_extractor = get_temporal_extractor()
    temporal_signals = temporal_extractor.extract_temporal_signals(
        deal.deal_name,
        deal.start_time,
        deal.end_time,
        deal.description
    )
    temporal_context = temporal_extractor.format_temporal_context_for_prompt(temporal_signals)
    
    return {
        "deal_name": deal.deal_name,
        "ssp_name": deal.ssp_name,
        "format": deal.format.value if hasattr(deal.format, 'value') else str(deal.format),
        "publishers": publishers_str,
        "description": deal.description or "N/A",
        "inventory_type": str(deal.inventory_type) if deal.inventory_type else "N/A",
        "floor_price": f"{deal.floor_price:.2f}",
        "volume_metrics": volume_metrics_str,
        "taxonomy": taxonomy_str,
        "publisher_context": publisher_context,
        "temporal_context": temporal_context,
    }


def infer_taxonomy(deal: UnifiedPreEnrichmentSchema, llm_client: GeminiClient) -> Optional[Taxonomy]:
    """
    Infer IAB Content Taxonomy using LLM.
    
    Args:
        deal: UnifiedPreEnrichmentSchema instance
        llm_client: GeminiClient instance
        
    Returns:
        Taxonomy object or None if inference fails
    """
    try:
        template = load_prompt_template("taxonomy_prompt.txt")
        prompt_data = format_deal_for_prompt(deal)
        prompt = template.format(**prompt_data)
        
        response = llm_client.generate_json(prompt)
        
        return Taxonomy(
            tier1=response.get("tier1"),
            tier2=response.get("tier2"),
            tier3=response.get("tier3"),
        )
    except Exception as e:
        logger.error(f"Taxonomy inference failed for deal {deal.deal_id}: {e}")
        return None


def infer_safety(deal: UnifiedPreEnrichmentSchema, llm_client: GeminiClient) -> Optional[Safety]:
    """
    Infer brand safety (GARM rating) using LLM.
    
    Args:
        deal: UnifiedPreEnrichmentSchema instance
        llm_client: GeminiClient instance
        
    Returns:
        Safety object or None if inference fails
    """
    try:
        template = load_prompt_template("safety_prompt.txt")
        prompt_data = format_deal_for_prompt(deal)
        prompt = template.format(**prompt_data)
        
        response = llm_client.generate_json(prompt)
        
        return Safety(
            garm_risk_rating=response.get("garm_risk_rating"),
            family_safe=response.get("family_safe"),
            safe_for_verticals=response.get("safe_for_verticals", []),
        )
    except Exception as e:
        logger.error(f"Safety inference failed for deal {deal.deal_id}: {e}")
        return None


def infer_audience(
    deal: UnifiedPreEnrichmentSchema,
    llm_client: GeminiClient,
    taxonomy: Optional[Taxonomy] = None
) -> Optional[Audience]:
    """
    Infer audience profile using LLM.
    
    Args:
        deal: UnifiedPreEnrichmentSchema instance
        llm_client: GeminiClient instance
        taxonomy: Optional Taxonomy (if already inferred, helps with audience inference)
        
    Returns:
        Audience object or None if inference fails
    """
    try:
        template = load_prompt_template("audience_prompt.txt")
        prompt_data = format_deal_for_prompt(deal)
        
        # Add taxonomy to prompt if available
        if taxonomy:
            taxonomy_str = f"{taxonomy.tier1} > {taxonomy.tier2}"
            if taxonomy.tier3:
                taxonomy_str += f" > {taxonomy.tier3}"
            prompt_data["taxonomy"] = taxonomy_str
        
        prompt = template.format(**prompt_data)
        
        response = llm_client.generate_json(prompt)
        
        return Audience(
            inferred_audience=response.get("inferred_audience", []),
            demographic_hint=response.get("demographic_hint"),
            audience_provenance="Inferred",
        )
    except Exception as e:
        logger.error(f"Audience inference failed for deal {deal.deal_id}: {e}")
        return None


def infer_commercial(deal: UnifiedPreEnrichmentSchema, llm_client: GeminiClient) -> Optional[Commercial]:
    """
    Infer commercial profile (quality/volume tiers) using LLM.
    
    Args:
        deal: UnifiedPreEnrichmentSchema instance
        llm_client: GeminiClient instance
        
    Returns:
        Commercial object or None if inference fails
    """
    try:
        template = load_prompt_template("commercial_prompt.txt")
        prompt_data = format_deal_for_prompt(deal)
        prompt = template.format(**prompt_data)
        
        response = llm_client.generate_json(prompt)
        
        return Commercial(
            quality_tier=response.get("quality_tier"),
            volume_tier=response.get("volume_tier"),
            floor_price=response.get("floor_price", deal.floor_price),
        )
    except Exception as e:
        logger.error(f"Commercial inference failed for deal {deal.deal_id}: {e}")
        return None


def _extract_concepts_fallback(
    deal: UnifiedPreEnrichmentSchema,
    taxonomy: Optional[Taxonomy],
    commercial: Optional[Commercial]
) -> List[str]:
    """
    Fallback concept extraction from deal metadata when LLM doesn't provide concepts.
    
    Args:
        deal: Deal schema
        taxonomy: Taxonomy object (if available)
        commercial: Commercial object (if available)
        
    Returns:
        List of concept strings
    """
    concepts = []
    
    # Format-based concepts
    format_map = {
        "video": "Video",
        "display": "Display",
        "native": "Native",
        "audio": "Audio"
    }
    if deal.format:
        format_concept = format_map.get(deal.format.value if hasattr(deal.format, 'value') else str(deal.format).lower())
        if format_concept:
            concepts.append(format_concept)
    
    # Inventory type concepts
    if deal.inventory_type:
        inv_type = str(deal.inventory_type).lower()
        if 'ctv' in inv_type or 'connected tv' in inv_type:
            concepts.append("CTV")
        if 'mobile' in inv_type:
            concepts.append("Mobile")
        if 'desktop' in inv_type:
            concepts.append("Desktop")
    
    # Quality tier concepts
    if commercial and commercial.quality_tier:
        if commercial.quality_tier.lower() == "premium":
            concepts.append("Premium")
        elif commercial.quality_tier.lower() == "ron":
            concepts.append("RON")
    
    # Taxonomy-based concepts (use tier2/tier3 as concepts)
    if taxonomy:
        if taxonomy.tier2:
            # Only add if it's a meaningful concept (not too generic)
            tier2 = taxonomy.tier2.strip()
            if tier2 and len(tier2) < 30:  # Avoid very long taxonomy names
                concepts.append(tier2)
    
    # Deal name keyword extraction (simple)
    deal_name_lower = deal.deal_name.lower()
    keyword_map = {
        "premium": "Premium",
        "curated": "Curated",
        "brand-safe": "Brand-Safe",
        "verified": "Verified",
        "political": "Political",
        "us": "US Market",
        "international": "International"
    }
    for keyword, concept in keyword_map.items():
        if keyword in deal_name_lower and concept not in concepts:
            concepts.append(concept)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_concepts = []
    for c in concepts:
        c_lower = c.lower()
        if c_lower not in seen:
            seen.add(c_lower)
            unique_concepts.append(c)
    
    return unique_concepts[:8]  # Limit to 8 concepts


def enrich_deal_unified(
    deal: UnifiedPreEnrichmentSchema,
    llm_client: GeminiClient,
    volume_context: Optional[str] = None
) -> EnrichedDeal:
    """
    Enrich a single deal with ALL semantic metadata using a SINGLE LLM call.
    
    OPTIMIZED: Combines all 4 enrichment types (taxonomy, safety, audience, commercial)
    into one API call instead of 4 separate calls. This provides ~4x speedup.
    
    Args:
        deal: UnifiedPreEnrichmentSchema instance (pre-enrichment deal)
        llm_client: GeminiClient instance
        volume_context: Optional volume context string (for future Phase 2 enhancement)
        
    Returns:
        EnrichedDeal instance with all semantic metadata
    """
    logger.info(f"Enriching deal (unified): {deal.deal_id} - {deal.deal_name}")
    
    # Build unified prompt
    prompt_data = format_deal_for_prompt(deal)
    
    unified_prompt = f"""You are an expert in programmatic advertising deal analysis and semantic enrichment.

Your task is to comprehensively analyze a deal and provide all semantic metadata in a single response:
1. IAB Content Taxonomy classification (Tier 1, Tier 2, Tier 3)
2. Brand safety assessment (GARM risk rating, family-safe status)
3. Audience profile inference (segments, demographics)
4. Commercial profile assessment (quality tier, volume tier)
5. Semantic concepts extraction (key keywords and themes)

## Deal Information

Deal Name: {prompt_data['deal_name']}
SSP: {prompt_data['ssp_name']}
Format: {prompt_data['format']}
Publishers: {prompt_data['publishers']}
Description: {prompt_data['description']}
Inventory Type: {prompt_data['inventory_type']}
Floor Price: ${prompt_data['floor_price']}
Volume Metrics: {prompt_data['volume_metrics']}

## Enhanced Context (Phase 2)

{prompt_data['publisher_context'] if prompt_data.get('publisher_context') else ''}
{prompt_data['temporal_context'] if prompt_data.get('temporal_context') else ''}

## Instructions

### 1. IAB Content Taxonomy Classification
- Analyze the deal name, publishers, description, and format to infer the content category
- Classify into IAB Content Taxonomy 2.2:
  - Tier 1: High-level category (e.g., "Automotive", "Arts & Entertainment", "News & Information")
  - Tier 2: Subcategory (e.g., "Auto Parts & Accessories", "Television", "News")
  - Tier 3: Specific topic (e.g., "Auto Repair", "Streaming", "Breaking News")
- Be specific but accurate. If you cannot determine a specific Tier 3, use a broader Tier 2 category
- For CTV/video deals, consider the publisher brand (e.g., "Paramount+" → Entertainment/Television/Streaming)

### 2. Brand Safety Assessment (GARM)
- Assess brand safety based on:
  - Publisher reputation (recognized brands = safer)
  - Inventory type (CTV typically safer than open web)
  - Floor price (higher floor often indicates premium inventory)
  - Deal name and description (premium keywords = safer)
- Determine family-safe status:
  - **CRITICAL RULE**: Default to True for mainstream news publishers (Yahoo, CNN, BBC, Reuters, New York Post, etc.) even if covering politics
  - **True**: Suitable for all audiences, including children
    - Mainstream news coverage (including politics, current events) from reputable publishers
    - General entertainment, lifestyle, and educational content
    - Established publishers (Yahoo, CNN, BBC, Reuters, New York Post, etc.) covering news/politics should ALWAYS be True
    - Only extremist, violent, or explicit content disqualifies family-safe status
    - **Examples of True**: Yahoo ROS, CNN News, BBC News, New York Post Network - these are mainstream publishers and should be True even with "Politics" taxonomy
  - **False**: May contain adult content, mature themes, or extremist/controversial content
    - Explicit adult content, graphic violence, hate speech
    - Extremist political content (NOT mainstream news coverage)
    - User-generated content platforms with unmoderated controversial content
  - **IMPORTANT**: Do NOT mark as False simply because taxonomy includes "Politics". Mainstream news publishers covering political topics should be True unless there's evidence of extremist, violent, or explicit content.
  - **Publisher Recognition**: If publisher is Yahoo, CNN, BBC, Reuters, New York Post, or similar mainstream news brand, family_safe MUST be True regardless of taxonomy.
- Assign GARM risk rating:
  - **Floor**: Highest brand safety (premium, verified publishers, family-safe)
  - **Low**: Low risk (reputable publishers, standard content, mainstream news)
  - **Medium**: Moderate risk (some user-generated content, less verified)
  - **High**: High risk (unverified, potentially unsafe content)
- List safe-for verticals (e.g., ["Automotive", "Finance", "Retail"]) based on risk rating

### 3. Audience Profile Inference
- Analyze the deal to infer audience segments:
  - Publisher brand signals (e.g., "Paramount+" → Entertainment enthusiasts)
  - Content taxonomy (e.g., "Automotive" → Auto intenders)
  - Format (e.g., CTV → Household decision-makers)
  - Deal name keywords (e.g., "Premium" → High-income)
- Generate 2-5 audience segments that best describe the target audience
- Provide demographic hints (age range, income level, interests) if inferable
- Be specific but realistic based on available signals

### 4. Commercial Profile Assessment
- Assess quality tier based on:
  - Publisher reputation (recognized brands = Premium)
  - Floor price (higher floor often indicates premium)
  - Inventory type (CTV typically Premium)
  - Deal name keywords ("Premium", "Curated" = Premium)
- Quality tier options: **Premium**, **Mid-tier**, **RON**
- Assess volume tier based on:
  - Volume metrics if provided (bid_requests, impressions)
  - Publisher size (major networks = High volume)
  - Inventory type (CTV = High volume typically)
- Volume tier options: **High**, **Medium**, **Low**
- If volume metrics are not available, infer from publisher reputation and inventory type

### 5. Semantic Concepts Extraction
- Extract 3-8 key semantic concepts/keywords that best describe this deal
- Focus on:
  - **Format/Inventory Type**: CTV, Video, Display, Mobile, Desktop, Native, Audio
  - **Quality Indicators**: Premium, Brand-Safe, Verified, Curated, RON
  - **Geographic**: US, International, Regional markets
  - **Content Themes**: News, Sports, Entertainment, Shopping, etc.
  - **Audience Signals**: Political, Family-Safe, Gaming, etc.
  - **Technical**: Programmatic, Direct, Reseller, etc.
- Be concise: single words or short phrases (2-3 words max)
- Examples: ["CTV", "Premium", "US Market", "News", "Brand-Safe"], ["Video", "Mobile", "Gaming", "Gen Z"]
- Do NOT include generic terms like "Advertising" or "Deal"
- Prioritize distinctive characteristics that differentiate this deal

## Output Format

Respond with JSON containing all enrichment fields:

{{
  "taxonomy": {{
    "tier1": "Category name",
    "tier2": "Subcategory name",
    "tier3": "Topic name (or null if not specific enough)"
  }},
  "safety": {{
    "garm_risk_rating": "Floor|Low|Medium|High",
    "family_safe": true|false,
    "safe_for_verticals": ["Vertical1", "Vertical2", ...]
  }},
  "audience": {{
    "inferred_audience": ["Segment1", "Segment2", "Segment3"],
    "demographic_hint": "Age range, Income level, Interests (or null if not inferable)"
  }},
  "commercial": {{
    "quality_tier": "Premium|Mid-tier|RON",
    "volume_tier": "High|Medium|Low",
    "floor_price": {prompt_data['floor_price']}
  }},
  "concepts": ["Concept1", "Concept2", "Concept3", ...]
}}"""
    
    try:
        # Single LLM call for all enrichment
        response = llm_client.generate_json(unified_prompt)
        
        # Parse response
        taxonomy_data = response.get("taxonomy", {})
        safety_data = response.get("safety", {})
        audience_data = response.get("audience", {})
        commercial_data = response.get("commercial", {})
        concepts_data = response.get("concepts", [])
        
        # Phase 2: Validate and correct taxonomy
        taxonomy_raw = Taxonomy(
            tier1=taxonomy_data.get("tier1"),
            tier2=taxonomy_data.get("tier2"),
            tier3=taxonomy_data.get("tier3"),
        ) if taxonomy_data else None
        
        # Validate taxonomy using TaxonomyValidator
        if taxonomy_raw:
            validator = get_taxonomy_validator()
            corrected_tier1, corrected_tier2, corrected_tier3, corrections = validator.validate_and_correct(
                taxonomy_raw.tier1,
                taxonomy_raw.tier2,
                taxonomy_raw.tier3
            )
            
            if any(corrections.values()):
                logger.info(f"Taxonomy corrections for {deal.deal_id}: {corrections}")
            
            taxonomy = Taxonomy(
                tier1=corrected_tier1,
                tier2=corrected_tier2,
                tier3=corrected_tier3,
            )
        else:
            taxonomy = None
        
        safety = Safety(
            garm_risk_rating=safety_data.get("garm_risk_rating"),
            family_safe=safety_data.get("family_safe"),
            safe_for_verticals=safety_data.get("safe_for_verticals", []),
        ) if safety_data else None
        
        audience = Audience(
            inferred_audience=audience_data.get("inferred_audience", []),
            demographic_hint=audience_data.get("demographic_hint"),
            audience_provenance="Inferred",
        ) if audience_data else None
        
        commercial = Commercial(
            quality_tier=commercial_data.get("quality_tier"),
            volume_tier=commercial_data.get("volume_tier"),
            floor_price=commercial_data.get("floor_price", deal.floor_price),
        ) if commercial_data else None
        
        # Extract concepts from LLM response, with fallback extraction
        concepts = []
        if concepts_data and isinstance(concepts_data, list):
            concepts = [str(c).strip() for c in concepts_data if c and str(c).strip()]
        
        # Fallback: Extract concepts from deal metadata if LLM didn't provide them
        if not concepts:
            concepts = _extract_concepts_fallback(deal, taxonomy, commercial)
        
    except Exception as e:
        logger.error(f"Unified enrichment failed for deal {deal.deal_id}: {e}")
        # Fallback to individual calls if unified fails
        logger.warning("Falling back to individual enrichment calls...")
        taxonomy = infer_taxonomy(deal, llm_client)
        safety = infer_safety(deal, llm_client)
        audience = infer_audience(deal, llm_client, taxonomy=taxonomy)
        commercial = infer_commercial(deal, llm_client)
    
    # Build enriched deal
    enriched = EnrichedDeal(
        # Copy all fields from UnifiedPreEnrichmentSchema
        deal_id=deal.deal_id,
        deal_name=deal.deal_name,
        source=deal.source,
        ssp_name=deal.ssp_name,
        format=deal.format,
        publishers=deal.publishers,
        floor_price=deal.floor_price,
        raw_deal_data=deal.raw_deal_data,
        inventory_type=deal.inventory_type,
        start_time=deal.start_time,
        end_time=deal.end_time,
        description=deal.description,
        volume_metrics=deal.volume_metrics,
        inventory_scale=deal.inventory_scale,
        inventory_scale_type=deal.inventory_scale_type,
        
        # Add enrichment fields
        taxonomy=taxonomy,
        concepts=concepts,
        safety=safety,
        audience=audience,
        commercial=commercial,
        
        # Metadata
        schema_version="1.0",
        enrichment_timestamp=datetime.now().isoformat(),
    )
    
    logger.info(f"Successfully enriched deal: {deal.deal_id}")
    return enriched


def enrich_deal(
    deal: UnifiedPreEnrichmentSchema,
    llm_client: GeminiClient,
    volume_context: Optional[str] = None
) -> EnrichedDeal:
    """
    Enrich a single deal with semantic metadata using LLM inference.
    
    OPTIMIZED: Uses unified enrichment (1 API call instead of 4) for ~4x speedup.
    
    This is the main entry point for Stage 1 enrichment.
    
    Process:
    1. Infer IAB Content Taxonomy (Tier 1 → Tier 2 → Tier 3)
    2. Infer brand safety (GARM risk rating, family-safe flag)
    3. Infer audience profile (segments, demographics)
    4. Infer commercial profile (quality tier, volume tier)
    
    Args:
        deal: UnifiedPreEnrichmentSchema instance (pre-enrichment deal)
        llm_client: GeminiClient instance
        volume_context: Optional volume context string (for future Phase 2 enhancement)
        
    Returns:
        EnrichedDeal instance with all semantic metadata
    """
    # Use unified enrichment (1 API call instead of 4)
    return enrich_deal_unified(deal, llm_client, volume_context)
