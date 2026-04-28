"""
Programmatic clients for image generation via API
Wraps the /generate-with-image endpoint
Integrates form agents for structured data extraction (ITF, NAR, DSC, etc.)
"""
import re
import json
import aiohttp
import asyncio
import logging
import ssl
from pathlib import Path
from config import Config
from typing import Optional, Dict, Any, Tuple, Type
from agents.itf_agent import ITFAgent
from agents.nar_agent import NARAgent

logger = logging.getLogger(__name__)

# Form type agent mapping
FORM_TYPE_AGENTS = {
    "ITF": ITFAgent,
    "NAR": NARAgent,
    # "DSC": DSCAgent,  # Add when available
}


def extract_page_number(image_path: Path) -> Optional[int]:
    """
    Extract page number from image filename.

    Supports patterns like:
    - ITF_40000071_page_1.png -> 1
    - ITF_40000071_p1.png -> 1
    - ITF_40000071_1.png -> 1

    Args:
        image_path: Path to image file

    Returns:
        int: Page number if found, None otherwise
    """
    filename = image_path.stem.lower()

    # Try "page_N" pattern
    match = re.search(r'page[_-]?(\d+)', filename)
    if match:
        return int(match.group(1))

    # Try "_pN" pattern
    match = re.search(r'_p(\d+)$', filename)
    if match:
        return int(match.group(1))

    # Try trailing number pattern
    match = re.search(r'_(\d+)$', filename)
    if match:
        return int(match.group(1))

    return None


def load_prompt_from_file(
        form_type: str,
        page_number: Optional[int] = None,
        use_fallback: bool = True
) -> str:
    """
    Load prompt from file based on form type and page number.

    Directory structure:
    prompts/
    ├── ITF_1.txt          # ITF page 1
    ├── ITF_2.txt          # ITF page 2
    ├── NAR_1.txt          # NAR page 1
    ├── DSC_1.txt          # DSC page 1
    └── DEFAULT.txt        # Fallback prompt

    Args:
        form_type: Form type identifier (e.g., 'ITF', 'NAR', 'DSC')
        page_number: Page number (optional)
        use_fallback: Use DEFAULT.txt if specific prompt not found (default: True)

    Returns:
        str: Prompt text loaded from file

    Raises:
        FileNotFoundError: If prompt file not found and fallback disabled
        ValueError: If form_type is invalid
    """
    form_type_upper = form_type.upper().strip()

    if not form_type_upper:
        raise ValueError("form_type cannot be empty")

    # Build filename using config format
    if page_number is not None:
        prompt_filename = Config.PROMPT_NAMING_FORMAT.format(
            form_type=form_type_upper,
            page_number=page_number
        )
    else:
        prompt_filename = Config.PROMPT_NAMING_FORMAT.format(
            form_type=form_type_upper,
            page_number=""
        ).replace('__', '_').rstrip('_') + '.txt'

    prompt_path = Config.PROMPTS_DIR / prompt_filename

    logger.debug(f"🔍 Looking for prompt: {prompt_path}")

    # Try specific prompt first
    if prompt_path.exists():
        try:
            content = prompt_path.read_text(encoding='utf-8').strip()
            logger.info(f"📄 Loaded prompt from: {prompt_filename}")
            logger.debug(f"   Prompt length: {len(content)} chars")
            return content
        except Exception as e:
            logger.error(f"❌ Error reading prompt file: {e}")
            if not use_fallback:
                raise
    else:
        logger.debug(f"⚠️  Prompt file not found: {prompt_path}")

    # Try fallback prompt
    if use_fallback and Config.DEFAULT_PROMPT_FALLBACK:
        fallback_path = Config.PROMPTS_DIR / Config.DEFAULT_PROMPT_FILE

        logger.debug(f"🔄 Trying fallback prompt: {fallback_path}")

        if fallback_path.exists():
            try:
                content = fallback_path.read_text(encoding='utf-8').strip()
                logger.warning(f"⚠️  Using fallback prompt from: {Config.DEFAULT_PROMPT_FILE}")
                logger.debug(f"   Prompt length: {len(content)} chars")
                return content
            except Exception as e:
                logger.error(f"❌ Error reading fallback prompt: {e}")
                raise

    # No prompt found
    error_msg = (
        f"Prompt not found for {form_type_upper}"
        f"{f' page {page_number}' if page_number else ''} "
        f"at {prompt_path.absolute()}"
    )
    if use_fallback and Config.DEFAULT_PROMPT_FALLBACK:
        error_msg += f", and fallback {Config.DEFAULT_PROMPT_FILE} not found"

    raise FileNotFoundError(error_msg)


def list_available_prompts() -> Dict[str, list]:
    """
    List all available prompts in the prompts directory.

    Returns:
        dict: Form type -> list of available prompt files

    Example:
        prompts = list_available_prompts()
        for form_type, files in prompts.items():
            print(f"{form_type}: {files}")
    """
    if not Config.PROMPTS_DIR.exists():
        return {}

    prompts_by_type = {}

    for prompt_file in sorted(Config.PROMPTS_DIR.glob("*.txt")):
        filename = prompt_file.name

        # Skip default fallback
        if filename == Config.DEFAULT_PROMPT_FILE:
            prompts_by_type.setdefault('DEFAULT', []).append(filename)
            continue

        # Parse form type from filename
        match = re.match(r'([A-Z]+)_?.*\.txt', filename)
        if match:
            form_type = match.group(1)
            prompts_by_type.setdefault(form_type, []).append(filename)

    return prompts_by_type


def strip_markdown_code_blocks(text: str) -> str:
    """
    Strip markdown code blocks (```json ... ```) from text.
    Returns the raw content, optionally parsed if it's valid JSON.
    """
    if not isinstance(text, str):
        return text

    # Pattern to match ```[language]\n...\n```
    pattern = r'```(?:json|python|javascript|yaml)?\n(.*?)\n```'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        # Extract content from code block
        content = match.group(1)
        logger.debug(f"🔍 Stripped markdown code block, content length: {len(content)}")
        return content

    # If no code block found, return as-is
    return text


def get_agent_for_form_type(form_type: str):
    """
    Get the appropriate agent for the given form type.

    Args:
        form_type: Form type identifier (e.g., 'ITF', 'NAR', 'DSC')

    Returns:
        Agent class (not instantiated)

    Raises:
        ValueError: If form type is not supported
    """
    form_type_upper = form_type.upper().strip()

    if form_type_upper not in FORM_TYPE_AGENTS:
        supported = ", ".join(FORM_TYPE_AGENTS.keys())
        raise ValueError(
            f"Unsupported form type: '{form_type}'. "
            f"Supported types: {supported}"
        )

    return FORM_TYPE_AGENTS[form_type_upper]


async def _process_with_agent(
        response_text: str,
        image_path: Path,
        form_type: str = "ITF"
) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """
    Process LLM response through form agent for structured extraction.

    Args:
        response_text: Raw LLM response text
        image_path: Path to the original image file
        form_type: Form type identifier (e.g., 'ITF', 'NAR', 'DSC')

    Returns:
        Tuple of (raw_json, cleaned_json, case_summary)
        - raw_json: Direct LLM response parsed as JSON
        - cleaned_json: Cleaned/extracted sections from agent
        - case_summary: Human-readable case summary

    Raises:
        ValueError: If form type is not supported
    """
    try:
        form_type_upper = form_type.upper()
        logger.debug(f"🔄 Processing response through {form_type_upper} agent...")

        # Step 1: Parse raw response as JSON
        try:
            raw_json = json.loads(response_text)
            logger.debug(f"✅ Raw response parsed as JSON")
        except json.JSONDecodeError:
            logger.warning(f"⚠️  Raw response is not valid JSON, storing as text")
            raw_json = {"response": response_text}

        # Step 2: Get appropriate agent
        try:
            agent_class = get_agent_for_form_type(form_type)
        except ValueError as e:
            logger.warning(f"⚠️  {str(e)}")
            return (raw_json, {}, f"Agent not available for form type: {form_type}")

        # Step 3: Create temporary markdown file for agent
        temp_md_file = Path(f"/tmp/{form_type_upper.lower()}_extract_{image_path.stem}.md")

        # Format response as markdown for agent
        if isinstance(raw_json, dict):
            md_content = f"\n"
            md_content += json.dumps(raw_json, indent=2)
            md_content += "\n"
        else:
            md_content = f"\n{response_text}\n"

        temp_md_file.write_text(md_content, encoding='utf-8')
        logger.debug(f"📝 Created temporary markdown file: {temp_md_file}")

        # Step 4: Process with agent
        agent = agent_class()

        # Call appropriate method based on agent type
        if hasattr(agent, 'process_itf_file'):
            # ITF agent uses process_itf_file
            result = await agent.process_itf_file(str(temp_md_file))
        elif hasattr(agent, 'process_nar_file'):
            # NAR agent uses process_nar_file
            result = await agent.process_nar_file(str(temp_md_file))
        elif hasattr(agent, 'process_dsc_file'):
            # DSC agent uses process_dsc_file
            result = await agent.process_dsc_file(str(temp_md_file))
        elif hasattr(agent, 'process_file'):
            # Generic process_file method
            result = await agent.process_file(str(temp_md_file))
        else:
            raise AttributeError(f"Agent does not have a process method")

        # Step 5: Clean up temporary file
        try:
            temp_md_file.unlink()
            logger.debug(f"🗑️  Cleaned up temporary file")
        except Exception as e:
            logger.warning(f"⚠️  Could not delete temporary file: {e}")

        # Step 6: Extract cleaned data and summary
        if result.get("status") == "success":
            # Try to get sections, data, or any cleaned output
            cleaned_json = result.get("sections") or result.get("data") or result.get("cleaned_data") or {}
            case_summary = result.get("summary") or result.get("report") or ""

            logger.info(f"✅ {form_type_upper} processing successful")
            logger.info(f"   Data extracted: {len(cleaned_json)} items")
            logger.info(f"   Summary length: {len(case_summary)} chars")

            return (raw_json, cleaned_json, case_summary)
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.warning(f"⚠️  Agent returned error: {error_msg}")
            return (raw_json, {}, f"{form_type_upper} processing failed: {error_msg}")

    except Exception as e:
        logger.error(f"❌ Error processing with {form_type_upper} agent: {e}", exc_info=True)
        # Fallback: return raw JSON with empty cleaned data
        try:
            raw_json = json.loads(response_text)
        except:
            raw_json = {"response": response_text}

        return (raw_json, {}, f"Error during {form_type_upper} processing: {str(e)}")


async def generate_with_image_async(
        image_path: str,
        prompt: Optional[str] = None,
        api_url: Optional[str] = None,
        output_file: Optional[str] = None,
        as_markdown: bool = True,
        timeout: int = 300,
        process_with_agent: bool = True,
        form_type: str = "ITF",
        page_number: Optional[int] = None,
        use_file_prompt: bool = True,
) -> Dict[str, Any]:
    """
    Send image and prompt to the /generate-with-image endpoint asynchronously.
    Automatically loads prompt from directory if not provided.
    Optionally processes response through form agent for structured extraction.

    Args:
        image_path: Path to the image file
        prompt: Text prompt to send with the image
                If None and use_file_prompt=True, loads from prompts directory
        api_url: Base URL of the API (default: https://localhost:8443)
        output_file: Optional file path to save the JSON response
                     If ends with .md, saves response as markdown
                     If ends with .json, saves as JSON (default)
        as_markdown: If True and output_file provided, auto-detect format from extension
                     and save response text as .md if no extension specified
        timeout: Request timeout in seconds (default: 300)
        process_with_agent: If True, process response through form agent (default: True)
        form_type: Form type identifier (default: 'ITF')
                   Supported: 'ITF', 'NAR', 'DSC', etc.
        page_number: Page number for prompt file lookup
                     If None, auto-detect from image filename
        use_file_prompt: If True and prompt is None, load from prompts directory (default: True)

    Returns:
        dict: The JSON response from the API with optional agent processing

        If process_with_agent=True, response includes:
        {
            "response": "...",
            "raw_json": {...},           # Direct LLM response
            "cleaned_json": {...},       # Extracted sections/data
            "case_summary": "...",       # Human-readable summary
            "form_type": "ITF",
            "agent_processed": True,
            "metrics": {...}
        }

    Raises:
        FileNotFoundError: If image file or prompt file doesn't exist
        aiohttp.ClientError: If API request fails
        ValueError: If API returns an error or form type is unsupported

    Example:
        # Auto-load prompt from prompts/ITF_1.txt based on filename
        result = await generate_with_image_async(
            image_path="./ITF_40000071_page_1.png",
            output_file="response.md",
            process_with_agent=True,
            form_type="ITF"
        )

        # Use custom prompt instead of file
        result = await generate_with_image_async(
            image_path="./itf_form.png",
            prompt="Extract ITF form data...",
            form_type="ITF",
            use_file_prompt=False
        )

        # Load specific prompt file for page 2
        result = await generate_with_image_async(
            image_path="./itf_form.png",
            form_type="ITF",
            page_number=2
        )
    """

    # Use config values if not provided
    if api_url is None:
        api_url = f"https://{Config.API_HOST}:{Config.API_PORT}"

    if timeout is None:
        timeout = Config.REQUEST_TIMEOUT

    # Resolve image path
    image_path = Path(image_path).resolve()

    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    file_size_mb = image_path.stat().st_size / (1024 * 1024)
    form_type_upper = form_type.upper()

    # Load prompt from file if not provided
    if prompt is None and use_file_prompt:
        # Auto-detect page number if not provided
        if page_number is None:
            page_number = extract_page_number(image_path)
            if page_number:
                logger.debug(f"🔍 Auto-detected page number: {page_number}")

        # Load prompt from file
        try:
            prompt = load_prompt_from_file(
                form_type=form_type,
                page_number=page_number,
                use_fallback=True
            )
        except FileNotFoundError as e:
            logger.error(f"❌ {e}")
            raise
    elif prompt is None:
        raise ValueError("prompt must be provided or use_file_prompt must be True")

    logger.info(f"📸 Processing image: {image_path.name} ({file_size_mb:.2f} MB)")
    logger.info(f"💬 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    logger.info(f"📋 Form Type: {form_type_upper}")
    logger.info(f"🔗 API URL: {api_url}/generate-with-image")
    logger.info(f"🤖 Agent Processing: {'✅ ON' if process_with_agent else '❌ OFF'}")

    # Open file OUTSIDE of form data to keep it open during request
    file_handle = None
    try:
        file_handle = open(image_path, 'rb')

        # Create form data with opened file handle
        data = aiohttp.FormData()
        data.add_field(
            'image',
            file_handle,
            filename=image_path.name,
            content_type='image/png'
        )
        data.add_field('prompt', prompt)

        # Create SSL context that ignores self-signed certificate warnings
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Create connector with SSL context
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout_obj = aiohttp.ClientTimeout(total=timeout)

        # Make request
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                logger.debug(f"📤 Sending POST request...")
                async with session.post(
                        f"{api_url}/generate-with-image",
                        data=data,
                        timeout=timeout_obj
                ) as response:

                    logger.debug(f"📥 Received status: {response.status}")

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ API error {response.status}: {error_text}")
                        raise ValueError(f"API error {response.status}: {error_text}")

                    result = await response.json()
                    response_text = result.get('response', '')

                    # ✅ Strip markdown code blocks
                    response_text = strip_markdown_code_blocks(response_text)

                    # Keep a trace on the processing time taken
                    json_path = Path(Config.LOG_LLM_TRACE + "/" + image_path.stem + ".json")
                    gen_metadata = {k: v for k, v in result.items() if k != "response"}
                    gen_metadata['file'] = image_path.name
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(gen_metadata, f, indent=2)
                    logger.info(f"📋 JSON metadata saved to: {json_path.absolute()}")

                    # Process through agent if requested
                    if process_with_agent:
                        logger.info(f"🤖 Processing response through {form_type_upper} agent...")
                        raw_json, cleaned_json, case_summary = await _process_with_agent(
                            response_text,
                            image_path,
                            form_type=form_type
                        )

                        # Add agent processing results to response
                        result['raw_json'] = raw_json
                        result['cleaned_json'] = cleaned_json
                        result['case_summary'] = case_summary
                        result['form_type'] = form_type_upper
                        result['agent_processed'] = True

                        logger.info(f"✅ Agent processing complete")
                    else:
                        # Parse response as JSON if possible
                        try:
                            result['raw_json'] = json.loads(response_text)
                        except:
                            result['raw_json'] = {"response": response_text}

                        result['cleaned_json'] = {}
                        result['case_summary'] = ""
                        result['form_type'] = form_type_upper
                        result['agent_processed'] = False

                    # Save to file if specified
                    if output_file:
                        output_path = Path(output_file)
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        if as_markdown:
                            # No extension and as_markdown=True, save as markdown
                            md_path = output_path.with_suffix('.md')

                            # Write header with form type
                            md_content = f"# {form_type_upper} Form Response\n\n"

                            # Write raw response
                            md_content += "## Raw API Response\n\n```json\n"
                            md_content += json.dumps(result.get('raw_json', {}), indent=2)
                            md_content += "\n```\n\n"

                            # Write case summary if available
                            if result.get('case_summary'):
                                md_content += "## Case Summary\n\n"
                                md_content += result['case_summary']
                                md_content += "\n\n"

                            # Write cleaned data if available
                            if result.get('cleaned_json'):
                                md_content += "## Extracted Data\n\n```json\n"
                                md_content += json.dumps(result['cleaned_json'], indent=2)
                                md_content += "\n```\n"

                            with open(md_path, 'w', encoding='utf-8') as f:
                                f.write(md_content)
                            logger.info(f"📝 Markdown response saved to: {md_path.absolute()}")

                        # Save as JSON
                        json_path = output_path.with_suffix('.json')

                        gen_metadata = {k: v for k, v in result.items() if k not in ["response"]}
                        gen_metadata['file'] = image_path.name
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(gen_metadata, f, indent=2, ensure_ascii=False)
                        logger.info(f"📋 JSON metadata saved to: {json_path.absolute()}")

                    # Print summary
                    metrics = result.get('metrics', {})

                    logger.info(f"\n📊 Response Summary:")
                    logger.info(f"   Model: {result.get('model')}")
                    logger.info(f"   Form Type: {result.get('form_type')}")
                    logger.info(f"   Response Length: {len(response_text)} chars")
                    logger.info(f"   Agent Processed: {'✅ Yes' if result.get('agent_processed') else '❌ No'}")

                    if metrics:
                        logger.info(f"   Total Duration: {metrics.get('total_duration')}s")
                        logger.info(f"   Eval Count: {metrics.get('eval_count')}")

                    if result.get('case_summary'):
                        summary_preview = result['case_summary'][:300]
                        logger.info(f"\n📋 Summary Preview:\n{summary_preview}...\n")
                    else:
                        response_preview = response_text[:200]
                        logger.info(f"\n📝 Response Preview:\n{response_preview}...\n")

                    return result

            except aiohttp.ClientError as e:
                logger.error(f"❌ Request failed: {e}")
                raise

    finally:
        # Ensure file is closed after request completes
        if file_handle and not file_handle.closed:
            file_handle.close()
            logger.debug(f"🔒 Closed file: {image_path.name}")


def list_supported_form_types() -> Dict[str, str]:
    """
    List all supported form types and their agent implementations.

    Returns:
        dict: Form type -> Agent class mapping

    Example:
        forms = list_supported_form_types()
        for form_type, agent_class in forms.items():
            print(f"{form_type}: {agent_class.__name__}")
    """
    return {
        form_type: agent_class.__name__
        for form_type, agent_class in FORM_TYPE_AGENTS.items()
    }
