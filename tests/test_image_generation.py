import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from clients.image_generation import (
    generate_with_image,
    generate_with_image_async,
    batch_generate_with_images,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project directories
BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "images"
OUTPUT_DIR = BASE_DIR / "test_output"
PROMPT_FILE = BASE_DIR / "default_prompt.txt"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)


@dataclass
class TestResult:
    """Single test result"""
    test_name: str
    status: str  # "PASSED" or "FAILED"
    duration: float  # seconds
    details: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class TestResults:
    """Track all test results"""

    def __init__(self):
        self.results: List[TestResult] = []

    def add_result(self, test_name: str, status: str, details: Dict[str, Any], duration: float = 0.0):
        """Add a test result"""
        result = TestResult(test_name, status, duration, details)
        self.results.append(result)
        logger.info(f"✓ {test_name}: {status}")

    def print_summary(self) -> bool:
        """Print test summary and export to JSON"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.results if r.status == "PASSED")
        failed = sum(1 for r in self.results if r.status == "FAILED")
        total = len(self.results)

        for result in self.results:
            status_emoji = "✅" if result.status == "PASSED" else "❌"
            print(f"{status_emoji} {result.test_name}: {result.status} ({result.duration:.2f}s)")
            if result.details:
                for key, value in result.details.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"   {key}: {value[:100]}...")
                    else:
                        print(f"   {key}: {value}")

        print("\n" + "=" * 70)
        print(f"Results: {passed} PASSED, {failed} FAILED out of {total} tests")
        print("=" * 70)

        # Export to JSON
        output_file = OUTPUT_DIR / "test_results.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "summary": {"passed": passed, "failed": failed, "total": total},
                    "results": [asdict(r) for r in self.results],
                    "timestamp": datetime.now().isoformat()
                },
                f,
                indent=2
            )
        logger.info(f"📄 Results exported to {output_file}")

        return failed == 0


def load_prompt() -> str:
    """Load prompt from external text file"""
    if not PROMPT_FILE.exists():
        logger.error(f"Prompt file not found: {PROMPT_FILE}")
        raise FileNotFoundError(f"Please create {PROMPT_FILE} with your prompt text")

    with open(PROMPT_FILE, "r") as f:
        prompt = f.read().strip()

    if not prompt:
        raise ValueError("Prompt file is empty")

    logger.info(f"✓ Loaded prompt from {PROMPT_FILE}")
    logger.info(f"  Prompt: {prompt[:100]}...")
    return prompt


def get_test_images() -> List[Path]:
    """Get all PNG images from images directory"""
    if not IMAGES_DIR.exists():
        logger.error(f"Images directory not found: {IMAGES_DIR}")
        raise FileNotFoundError(f"Please create {IMAGES_DIR} and add PNG images")

    images = sorted(IMAGES_DIR.glob("*.png"))

    if not images:
        raise FileNotFoundError(f"No PNG images found in {IMAGES_DIR}")

    logger.info(f"✓ Found {len(images)} image(s) in {IMAGES_DIR}")
    for img in images:
        logger.info(f"  - {img.name}")

    return images


def verify_image_exists(image_path: Path) -> bool:
    """Verify image file exists"""
    if not image_path.exists():
        logger.error(f"Image file not found: {image_path}")
        return False
    return True


async def test_sync(image_path: Path, prompt: str, test_num: int) -> Optional[str]:
    """Test synchronous generation"""
    logger.info(f"\n🔸 Test {test_num}: Synchronous Generation ({image_path.name})")

    try:
        output_file = OUTPUT_DIR / "sync" / f"{image_path.stem}.json"

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: generate_with_image(
                image_path=str(image_path),
                prompt=prompt,
                output_file=str(output_file),
                as_markdown=True
            )
        )

        logger.info(f"✓ Sync generation completed for {image_path.name}")
        logger.info(f"  Output saved to: {output_file}")
        return result

    except Exception as e:
        logger.error(f"Sync generation failed: {e}")
        raise


async def test_async(image_path: Path, prompt: str, test_num: int) -> Optional[str]:
    """Test asynchronous generation"""
    logger.info(f"\n🔸 Test {test_num}: Asynchronous Generation ({image_path.name})")

    try:
        output_file = OUTPUT_DIR / "async" / f"{image_path.stem}.json"

        result = await generate_with_image_async(
            image_path=str(image_path),
            prompt=prompt,
            output_file=str(output_file),
            as_markdown=True
        )

        logger.info(f"✓ Async generation completed for {image_path.name}")
        logger.info(f"  Output saved to: {output_file}")
        return result

    except Exception as e:
        logger.error(f"Async generation failed: {e}")
        raise


async def test_batch(images: List[Path], prompt: str) -> Optional[Dict[str, list]]:
    """Test batch generation"""
    logger.info(f"\n🔸 Test: Batch Generation ({len(images)} images)")

    try:
        # Build the images list with required structure
        batch_images = [
            {
                "path": str(img),
                "prompt": prompt,
                "output_file": str(OUTPUT_DIR / "batch" / f"{img.stem}.json"),
                "as_markdown": True
            }
            for img in images
        ]

        result = await batch_generate_with_images(
            images=batch_images,
            max_concurrent=2
        )

        logger.info(f"✓ Batch generation completed")
        logger.info(f"  Successful: {len(result['successful'])}")
        logger.info(f"  Failed: {len(result['failed'])}")

        return result

    except Exception as e:
        logger.error(f"Batch generation failed: {e}")
        raise


async def run_all_tests() -> bool:
    """Run all tests sequentially"""
    results = TestResults()

    print("\n" + "=" * 70)
    print("IMAGE GENERATION CLIENT TEST SUITE")
    print("=" * 70)

    try:
        # Load prompt and images
        prompt = load_prompt()
        images = get_test_images()

        print(f"\n📁 Output directory: {OUTPUT_DIR}")
        print(f"📷 Test images: {len(images)}")
        print(f"📝 Prompt length: {len(prompt)} characters\n")

    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Setup failed: {e}")
        results.add_result("Setup", "FAILED", {"error": str(e)})
        return results.print_summary()

    test_counter = 1

    # Test 1-N: Sync generation for each image
    for image_path in images:
        if not verify_image_exists(image_path):
            results.add_result(
                f"Test {test_counter}: Sync Generation ({image_path.name})",
                "FAILED",
                {"error": f"Image not found: {image_path}"},
                0.0
            )
            test_counter += 1
            continue

        try:
            start_time = datetime.now()
            result = await test_sync(image_path, prompt, test_counter)
            duration = (datetime.now() - start_time).total_seconds()

            if result:
                results.add_result(
                    f"Test {test_counter}: Sync Generation ({image_path.name})",
                    "PASSED",
                    {"result": str(result)[:500]},
                    duration
                )
            else:
                results.add_result(
                    f"Test {test_counter}: Sync Generation ({image_path.name})",
                    "FAILED",
                    {"error": "No result returned"},
                    duration
                )

        except Exception as e:
            logger.error(f"Test {test_counter} exception: {e}")
            results.add_result(
                f"Test {test_counter}: Sync Generation ({image_path.name})",
                "FAILED",
                {"error": str(e)},
                0.0
            )

        test_counter += 1
        await asyncio.sleep(2)

    # Test N+1-2N: Async generation for each image
    for image_path in images:
        if not verify_image_exists(image_path):
            results.add_result(
                f"Test {test_counter}: Async Generation ({image_path.name})",
                "FAILED",
                {"error": f"Image not found: {image_path}"},
                0.0
            )
            test_counter += 1
            continue

        try:
            start_time = datetime.now()
            result = await test_async(image_path, prompt, test_counter)
            duration = (datetime.now() - start_time).total_seconds()

            if result:
                results.add_result(
                    f"Test {test_counter}: Async Generation ({image_path.name})",
                    "PASSED",
                    {"result": str(result)[:500]},
                    duration
                )
            else:
                results.add_result(
                    f"Test {test_counter}: Async Generation ({image_path.name})",
                    "FAILED",
                    {"error": "No result returned"},
                    duration
                )

        except Exception as e:
            logger.error(f"Test {test_counter} exception: {e}")
            results.add_result(
                f"Test {test_counter}: Async Generation ({image_path.name})",
                "FAILED",
                {"error": str(e)},
                0.0
            )

        test_counter += 1
        await asyncio.sleep(2)

    # Final test: Batch generation
    try:
        start_time = datetime.now()
        result = await test_batch(images, prompt)
        duration = (datetime.now() - start_time).total_seconds()

        if result:
            successful_count = len(result.get('successful', []))
            failed_count = len(result.get('failed', []))

            results.add_result(
                f"Test {test_counter}: Batch Generation",
                "PASSED",
                {
                    "successful": successful_count,
                    "failed": failed_count,
                    "details": f"{successful_count} successful, {failed_count} failed"
                },
                duration
            )
        else:
            results.add_result(
                f"Test {test_counter}: Batch Generation",
                "FAILED",
                {"error": "No result returned"},
                duration
            )

    except Exception as e:
        logger.error(f"Test {test_counter} exception: {e}")
        results.add_result(
            f"Test {test_counter}: Batch Generation",
            "FAILED",
            {"error": str(e)},
            0.0
        )

    # Print summary
    return results.print_summary()


async def main():
    """Main entry point"""
    try:
        success = await run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test suite interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception("Full traceback:")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
