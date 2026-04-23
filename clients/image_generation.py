"""
Programmatic clients for image generation via API
Wraps the /generate-with-image endpoint
"""
import re
import json
import aiohttp
import asyncio
import logging
import ssl
from pathlib import Path
from config import Config
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


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

async def generate_with_image_async(
        image_path: str,
        prompt: str,
        api_url: Optional[str] = None,
        output_file: Optional[str] = None,
        as_markdown: bool = True,
        timeout: int = 300
) -> Dict[str, Any]:
    """
    Send image and prompt to the /generate-with-image endpoint asynchronously

    Args:
        image_path: Path to the image file
        prompt: Text prompt to send with the image
        api_url: Base URL of the API (default: https://localhost:8443)
        output_file: Optional file path to save the JSON response
                     If ends with .md, saves response as markdown
                     If ends with .json, saves as JSON (default)
        as_markdown: If True and output_file provided, auto-detect format from extension
                     and save response text as .md if no extension specified
        timeout: Request timeout in seconds (default: 300)

    Returns:
        dict: The JSON response from the API

    Raises:
        FileNotFoundError: If image file doesn't exist
        aiohttp.ClientError: If API request fails
        ValueError: If API returns an error

    Example:
        result = await generate_with_image_async(
            image_path="./image.png",
            prompt="What is in this image?",
            output_file="response.md"
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
    logger.info(f"📸 Processing image: {image_path.name} ({file_size_mb:.2f} MB)")
    logger.info(f"💬 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    logger.info(f"🔗 API URL: {api_url}/generate-with-image")

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

                    # ✅ FIX: Strip markdown code blocks
                    response_text = strip_markdown_code_blocks(response_text)

                    # Save to file if specified
                    if output_file:
                        output_path = Path(output_file)
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        if as_markdown:
                            # No extension and as_markdown=True, save as markdown
                            md_path = output_path.with_suffix('.md')
                            with open(md_path, 'w', encoding='utf-8') as f:
                                f.write(response_text)
                            logger.info(f"📝 Markdown response saved to: {md_path.absolute()}")

                    # No extension and as_markdown=False, save as JSON
                    json_path = output_path.with_suffix('.json')

                    gen_metadata = {k: v for k, v in result.items() if k != "response"}
                    gen_metadata['file'] = image_path.name
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(gen_metadata, f, indent=2)
                    logger.info(f"📋 JSON metadata saved to: {json_path.absolute()}")

                    # Print summary
                    metrics = result.get('metrics', {})

                    logger.info(f"\n📊 Response Summary:")
                    logger.info(f"   Model: {result.get('model')}")
                    logger.info(f"   Response Length: {len(response_text)} chars")

                    if metrics:
                        logger.info(f"   Total Duration: {metrics.get('total_duration')}s")
                        logger.info(f"   Eval Count: {metrics.get('eval_count')}")

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


def generate_with_image(
        image_path: str,
        prompt: str,
        api_url: Optional[str] = None,
        output_file: Optional[str] = None,
        as_markdown: bool = True,
        timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Synchronous wrapper for generate_with_image_async

    Use this when you're not already in an async context.

    Args:
        image_path: Path to the image file
        prompt: Text prompt to send with the image
        api_url: Base URL of the API (default: https://localhost:8443)
        output_file: Optional file path to save the response
                     .md extension → saves as markdown
                     .json extension → saves as JSON
                     no extension + as_markdown=True → saves as .md
                     no extension + as_markdown=False → saves as .json
        as_markdown: Default format when no extension specified (default: True)
        timeout: Request timeout in seconds (default: 300)

    Returns:
        dict: The JSON response from the API

    Example:
        # Save as markdown
        result = generate_with_image(
            image_path="./image.png",
            prompt="What is in this image?",
            output_file="response.md"
        )

        # Save as JSON
        result = generate_with_image(
            image_path="./image.png",
            prompt="What is in this image?",
            output_file="response.json"
        )

        # Auto-detect based on as_markdown flag
        result = generate_with_image(
            image_path="./image.png",
            prompt="What is in this image?",
            output_file="response",
            as_markdown=True  # → saves as response.md
        )
    """
    try:
        loop = asyncio.get_running_loop()
        # If we're already in an async context, this will fail
        # and we'll create a new loop
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(generate_with_image_async(
            image_path=image_path,
            prompt=prompt,
            api_url=api_url,
            output_file=output_file,
            as_markdown=as_markdown,
            timeout=timeout
        ))
    else:
        # Already in async context, create task instead
        raise RuntimeError(
            "Cannot use generate_with_image() from async context. "
            "Use generate_with_image_async() instead."
        )


async def batch_generate_with_images(
        images: list[Dict[str, str]],
        api_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_concurrent: Optional[int] = None,
        as_markdown: bool = True
) -> Dict[str, list]:
    """
    Process multiple images concurrently with rate limiting

    Args:
        images: List of dicts with keys:
                - path: image file path (required)
                - prompt: text prompt (required)
                - output_file: optional output file (auto-detects .md or .json)
                - as_markdown: optional override for this image
        api_url: Base URL of the API
        timeout: Request timeout in seconds
        max_concurrent: Maximum concurrent requests (default: 3)
        as_markdown: Default format for images without explicit output_file (default: True)

    Returns:
        dict: Contains 'successful' and 'failed' lists

    Example:
        images = [
            {
                "path": "image1.png",
                "prompt": "What is this?",
                "output_file": "response1.md"  # Saves as markdown
            },
            {
                "path": "image2.png",
                "prompt": "Describe this",
                "output_file": "response2.json"  # Saves as JSON
            },
            {
                "path": "image3.png",
                "prompt": "Analyze this",
                "output_file": "response3",
                "as_markdown": True  # Auto-saves as response3.md
            }
        ]
        results = await batch_generate_with_images(images, max_concurrent=2)
        print(f"✅ {len(results['successful'])} successful")
        print(f"❌ {len(results['failed'])} failed")
    """

    # Use config values if not provided
    if api_url is None:
        api_url = f"https://{Config.API_HOST}:{Config.API_PORT}"

    if timeout is None:
        timeout = Config.REQUEST_TIMEOUT

    if max_concurrent is None:
        max_concurrent = Config.MAX_CONCURRENT_REQUESTS

    logger.info(f"🚀 Starting batch processing of {len(images)} image(s)")
    logger.info(f"   Max concurrent: {max_concurrent}")
    logger.info(f"   Timeout: {timeout}s")
    logger.info(f"   Default format: {'Markdown' if as_markdown else 'JSON'}")
    logger.info(f"   API URL: {api_url}")

    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_generate(index: int, img_data: Dict[str, str]):
        """Process single image with semaphore limit"""
        async with semaphore:
            img_path = Path(img_data["path"]).name
            try:
                logger.info(f"⏳ [{index + 1}/{len(images)}] Processing: {img_path}")

                result = await generate_with_image_async(
                    image_path=img_data["path"],
                    prompt=img_data["prompt"],
                    api_url=api_url,
                    output_file=img_data.get("output_file"),
                    as_markdown=img_data.get("as_markdown", as_markdown),
                    timeout=timeout
                )

                logger.info(f"✅ [{index + 1}/{len(images)}] Complete: {img_path}")
                return result

            except Exception as e:
                logger.error(f"❌ [{index + 1}/{len(images)}] Failed: {img_path} - {e}")
                raise

    # Create tasks with index for logging
    tasks = [bounded_generate(idx, img) for idx, img in enumerate(images)]

    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Separate successful and failed results
    successful = []
    failed = []

    for img_data, result in zip(images, results):
        if isinstance(result, Exception):
            failed.append({
                "path": img_data["path"],
                "error": str(result)
            })
        else:
            successful.append(result)

    logger.info(f"\n📈 Batch Processing Complete:")
    logger.info(f"   ✅ Successful: {len(successful)}")
    logger.info(f"   ❌ Failed: {len(failed)}\n")

    return {"successful": successful, "failed": failed}
