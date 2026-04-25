"""Test script for prompt management functionality."""

import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from clients.image_generation import (
    load_prompt_from_file,
    extract_page_number,
    list_available_prompts,
)


def test_page_number_extraction():
    """Test page number extraction from filenames."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Page Number Extraction")
    logger.info("=" * 80)

    test_cases = [
        ("ITF_40000071_page_1.png", 1),
        ("ITF_40000072_page_2.png", 2),
        ("NAR_40000071_p1.png", 1),
        ("DSC_40000071_p3.png", 3),
        ("FORM_123_1.png", 1),
        ("no_page_number.png", None),
    ]

    for filename, expected in test_cases:
        path = Path(filename)
        result = extract_page_number(path)
        status = "✅" if result == expected else "❌"
        logger.info(f"{status} {filename} -> {result} (expected: {expected})")


def test_prompt_loading():
    """Test prompt file loading."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Prompt File Loading")
    logger.info("=" * 80)

    # Test loading ITF page 1 prompt
    logger.info("\n• Loading ITF page 1 prompt:")
    try:
        prompt = load_prompt_from_file("ITF", page_number=1, use_fallback=False)
        logger.info(f"  ✅ Loaded {len(prompt)} chars")
        logger.info(f"  Preview: {prompt[:100]}...")
    except FileNotFoundError as e:
        logger.warning(f"  ⚠️  {e}")

    # Test loading with fallback
    logger.info("\n• Loading with fallback:")
    try:
        prompt = load_prompt_from_file("NONEXISTENT", use_fallback=True)
        logger.info(f"  ✅ Fallback loaded {len(prompt)} chars")
    except FileNotFoundError as e:
        logger.error(f"  ❌ {e}")

    # Test form type validation
    logger.info("\n• Testing form type validation:")
    try:
        prompt = load_prompt_from_file("", use_fallback=False)
        logger.error(f"  ❌ Empty form_type was accepted (unexpected)")
    except ValueError as e:
        logger.info(f"  ✅ Empty form_type rejected: {e}")


def test_list_prompts():
    """Test listing available prompts."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: List Available Prompts")
    logger.info("=" * 80)

    prompts = list_available_prompts()

    if not prompts:
        logger.warning("\n⚠️  No prompts found in prompts directory")
        logger.info("   Create prompt files like: ITF_1.txt, NAR_1.txt, DEFAULT.txt")
        return

    logger.info("\n📁 Available prompts:")
    for form_type, files in sorted(prompts.items()):
        logger.info(f"\n   {form_type}:")
        for file in files:
            logger.info(f"      • {file}")


if __name__ == "__main__":
    logger.info("\n" + "#" * 80)
    logger.info("# PROMPT MANAGEMENT TESTS")
    logger.info("#" * 80)

    test_page_number_extraction()
    test_prompt_loading()
    test_list_prompts()

    logger.info("\n" + "#" * 80)
    logger.info("# END OF TESTS")
    logger.info("#" * 80)
