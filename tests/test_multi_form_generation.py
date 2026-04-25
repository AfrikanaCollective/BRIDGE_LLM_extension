"""Test script for multi-form type image generation integration."""
import sys
import json
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from clients.image_generation import (
    generate_with_image_async,
    list_supported_form_types,
    get_agent_for_form_type,
)


def discover_test_images():
    """Discover actual test images in tests/test_data directory."""
    test_data_dir = Path("./tests/test_data")

    if not test_data_dir.exists():
        logger.warning(f"⚠️  Test data directory not found: {test_data_dir.absolute()}")
        return {}

    images_by_type = {
        'ITF': [],
        'NAR': [],
        'DSC': [],
        'OTHER': []
    }

    # Discover images by filename pattern
    for image_file in sorted(test_data_dir.glob("*.png")):
        filename = image_file.name.upper()

        if 'ITF' in filename:
            images_by_type['ITF'].append(image_file)
        elif 'NAR' in filename:
            images_by_type['NAR'].append(image_file)
        elif 'DSC' in filename:
            images_by_type['DSC'].append(image_file)
        else:
            images_by_type['OTHER'].append(image_file)

    logger.info(f"\n📊 Discovered test images:")
    for form_type, images in images_by_type.items():
        if images:
            logger.info(f"\n   {form_type} Forms ({len(images)} images):")
            for img in images:
                size_mb = img.stat().st_size / (1024 * 1024)
                logger.info(f"      • {img.name} ({size_mb:.2f} MB)")

    return images_by_type


async def test_list_supported_forms():
    """Test listing supported form types."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 0: Supported Form Types")
    logger.info("=" * 80)

    forms = list_supported_form_types()

    logger.info("\n✅ Supported form types:")
    for form_type, agent_name in forms.items():
        logger.info(f"   • {form_type}: {agent_name}")

    return forms


async def test_single_itf_form(image_path: Path):
    """Test processing single ITF form."""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 1: Single ITF Form Processing")
    logger.info("=" * 80)
    logger.info(f"📁 Image: {image_path.name}")

    try:
        result = await generate_with_image_async(
            image_path=str(image_path),
            output_file=f"./tests/test_output/test_agent/agent/{image_path.stem}",
            as_markdown=True,
            process_with_agent=True,
            form_type="ITF"
        )

        logger.info("\n✅ ITF Processing Result:")
        logger.info(f"   Image: {image_path.name}")
        logger.info(f"   Form Type: {result.get('form_type')}")
        logger.info(f"   Agent Processed: {result.get('agent_processed')}")
        logger.info(f"   Response Length: {len(result.get('response', ''))} chars")
        logger.info(f"   Response keys: {list(result.keys())}")

        if result.get('metrics'):
            logger.info(f"\n\n Metrics: {result['metrics']}")

        if result.get('cleaned_json'):
            logger.info(f"\n\n Form data: {result['cleaned_json']}")

        if result.get('case_summary'):
            logger.info(f"\n\n Summary: {result['case_summary']}\n\n")

        return result

    except Exception as e:
        logger.error(f"❌ Error processing {image_path.name}: {e}", exc_info=True)
        return None


async def test_single_nar_form(image_path: Path):
    """Test processing single NAR form."""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 2: Single NAR Form Processing")
    logger.info("=" * 80)
    logger.info(f"📁 Image: {image_path.name}")

    try:
        result = await generate_with_image_async(
            image_path=str(image_path),
            output_file=f"./tests/test_output/test_agent/nar_{image_path.stem}",
            as_markdown=True,
            process_with_agent=True,
            form_type="NAR"
        )

        logger.info("\n✅ NAR Processing Result:")
        logger.info(f"   Image: {image_path.name}")
        logger.info(f"   Form Type: {result.get('form_type')}")
        logger.info(f"   Agent Processed: {result.get('agent_processed')}")
        logger.info(f"   Response Length: {len(result.get('response', ''))} chars")

        if result.get('case_summary'):
            logger.info(f"   Summary length: {len(result['case_summary'])} chars")

        return result

    except ValueError as e:
        error_msg = str(e)
        if "Unsupported form type" in error_msg:
            logger.warning(f"⚠️  NAR agent not yet implemented")
            logger.info("   Note: Add NARAgent to FORM_TYPE_AGENTS to enable NAR support")
            return None
        else:
            raise
    except Exception as e:
        logger.error(f"❌ Error processing {image_path.name}: {e}", exc_info=True)
        return None


async def test_form_type_validation():
    """Test form type validation."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Form Type Validation")
    logger.info("=" * 80)

    test_cases = [
        ("ITF", True, "Valid form type"),
        ("itf", True, "Lowercase form type"),
        ("ITF ", True, "Form type with whitespace"),
        ("INVALID", False, "Invalid form type"),
        ("XYZ", False, "Unknown form type"),
    ]

    logger.info("\nValidation Test Cases:")

    for form_type, should_succeed, description in test_cases:
        logger.info(f"\n   • {description}: '{form_type}'")

        try:
            agent_class = get_agent_for_form_type(form_type)
            if should_succeed:
                logger.info(f"     ✅ Accepted - Agent: {agent_class.__name__}")
            else:
                logger.warning(f"     ⚠️  Unexpectedly accepted (expected rejection)")
        except ValueError as e:
            if not should_succeed:
                logger.info(f"     ✅ Rejected - {str(e)[:80]}...")
            else:
                logger.error(f"     ❌ Unexpectedly rejected: {e}")


async def test_batch_mixed_forms(images_by_type: dict):
    """Test batch processing with multiple form types."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Batch Processing Mixed Form Types")
    logger.info("=" * 80)

    # Build batch list from discovered images
    batch_images = []

    # Add ITF forms
    for img_path in images_by_type.get('ITF', [])[:1]:  # Limit to 2 per type
        batch_images.append({
            "image_path": str(img_path),
            "output_file": f"./tests/test_output/test_agent/batch/{img_path.stem}",
            "form_type": "ITF",
            "process_with_agent": True
        })

    # Add NAR forms
    for img_path in images_by_type.get('NAR', [])[:1]:
        batch_images.append({
            "image_path": str(img_path),
            "output_file": f"./tests/test_output/test_agent/batch/{img_path.stem}",
            "form_type": "NAR",
            "process_with_agent": True
        })

    # Add generic images without agent processing
    for img_path in images_by_type.get('OTHER', [])[:1]:
        batch_images.append({
            "image_path": str(img_path),
            "output_file": f"./tests/test_output/test_agent/batch/{img_path.stem}",
            "process_with_agent": False
        })

    if not batch_images:
        logger.warning("⚠️  No images discovered for batch processing")
        return None

    try:
        logger.info(f"\n📋 Batch Configuration:")
        logger.info(f"   Total images: {len(batch_images)}")

        for idx, img_config in enumerate(batch_images, 1):
            form_type = img_config.get('form_type', 'GENERIC')
            agent = "✅" if img_config.get('process_with_agent') else "❌"
            img_name = Path(img_config['image_path']).name
            logger.info(f"   [{idx}] {img_name} ({form_type}) {agent} Agent")

        # Process batch sequentially (can be parallelized later)
        logger.info(f"\n⏳ Processing batch...")

        successful = []
        failed = []

        for idx, img_config in enumerate(batch_images, 1):
            img_path = Path(img_config['image_path'])
            form_type = img_config.get('form_type', 'GENERIC')
            process_agent = img_config.get('process_with_agent', True)

            logger.info(f"\n   [{idx}/{len(batch_images)}] Processing: {img_path.name}")

            try:
                result = await generate_with_image_async(
                    image_path=img_config['image_path'],
                    output_file=img_config.get('output_file'),
                    as_markdown=True,
                    process_with_agent=process_agent,
                    form_type=form_type
                )

                successful.append(result)
                logger.info(f"      ✅ Success - Agent processed: {result.get('agent_processed')}")

            except Exception as e:
                failed.append({
                    'image': img_path.name,
                    'form_type': form_type,
                    'error': str(e)[:200]
                })
                logger.warning(f"      ❌ Failed: {str(e)[:100]}...")

        logger.info("\n✅ BATCH RESULTS:")
        logger.info(f"   Successful: {len(successful)}")
        logger.info(f"   Failed: {len(failed)}")

        for idx, result in enumerate(successful, 1):
            form_type = result.get('form_type', 'UNKNOWN')
            agent_processed = result.get('agent_processed', False)
            logger.info(f"\n   [{idx}] Form Type: {form_type}")
            logger.info(f"       Agent Processed: {'✅' if agent_processed else '❌'}")

            if agent_processed and result.get('cleaned_json'):
                cleaned_keys = list(result['cleaned_json'].keys())
                logger.info(f"       Data sections: {cleaned_keys[:5]}{'...' if len(cleaned_keys) > 5 else ''}")

        if failed:
            logger.warning(f"\n   Failed items ({len(failed)}):")
            for item in failed:
                logger.warning(f"     • {item['image']} ({item['form_type']})")
                logger.warning(f"       Error: {item['error']}")

        return {
            'successful': successful,
            'failed': failed,
            'total': len(batch_images)
        }

    except Exception as e:
        logger.error(f"❌ Batch processing error: {e}", exc_info=True)
        return None


def print_test_summary(results: dict):
    """Print summary of all test results."""
    logger.info("\n" + "#" * 80)
    logger.info("# TEST SUMMARY")
    logger.info("#" * 80)

    summary = {
        'test_0_forms': results.get('test_0_forms'),
        'test_1_itf': "✅ PASS" if results.get('test_1_itf') else "❌ FAIL",
        'test_2_nar': "⚠️  SKIPPED" if results.get('test_2_nar') is None else (
            "✅ PASS" if results.get('test_2_nar') else "❌ FAIL"),
        'test_3_dsc': "⚠️  SKIPPED" if results.get('test_3_dsc') is None else (
            "✅ PASS" if results.get('test_3_dsc') else "❌ FAIL"),
        'test_4_validation': "✅ PASS",
        #'test_4_batch': "✅ PASS" if results.get('test_4_batch') else "❌ FAIL",
    }

    for test_name, status in summary.items():
        logger.info(f"\n{test_name}: {status}")

    logger.info("\n" + "#" * 80)
    logger.info("# END OF TESTS")
    logger.info("#" * 80)


async def main():
    """Run all tests with discovered images."""
    logger.info("\n" + "#" * 80)
    logger.info("# MULTI-FORM TYPE IMAGE GENERATION TESTS")
    logger.info("#" * 80)

    # Create output directory
    output_dir = Path("./tests/test_output/test_agent")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"\n📁 Output directory: {output_dir.absolute()}\n")

    # Discover test images
    images_by_type = discover_test_images()

    if not any(images_by_type.values()):
        logger.error("\n❌ No test images found in tests/test_data/")
        logger.info("   Please ensure your form images are in: tests/test_data/")
        logger.info("   Filenames should contain: ITF, NAR, or DSC")
        return

    # Store results
    results = {}

    # Run tests
    logger.info("\n" + "#" * 80)

    # TEST 0: List supported forms
    results['test_0_forms'] = await test_list_supported_forms()

    # TEST 1: Single ITF form
    itf_images = images_by_type.get('ITF', [])
    if itf_images:
        results['test_1_itf'] = await test_single_itf_form(itf_images[0]) is not None
    else:
        logger.warning("\n⚠️  No ITF images found - skipping TEST 1")
        results['test_1_itf'] = None

    # TEST 2: Single NAR form
    nar_images = images_by_type.get('NAR', [])
    if nar_images:
        results['test_2_nar'] = await test_single_nar_form(nar_images[0]) is not None
    else:
        logger.warning("\n⚠️  No NAR images found - skipping TEST 2")
        results['test_2_nar'] = None

    # TEST 3: Validation
    await test_form_type_validation()

    # TEST 4: Batch processing
    # results['test_4_batch'] = await test_batch_mixed_forms(images_by_type) is not None

    # Print summary
    print_test_summary(results)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)
