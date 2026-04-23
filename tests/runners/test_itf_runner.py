"""ITF form test runner - processes directory of .md files and generates reports."""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.itf_agent import ITFAgent
from agents.itf_tools import ITFTools

# Setup logging - use project root for logs
log_dir = project_root / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "itf_test_run.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ITFTestRunner:
    """Test runner for ITF forms."""

    def __init__(self, input_dir: str, output_dir: str = None):
        """
        Initialize test runner.

        Args:
            input_dir: Directory containing .md files
            output_dir: Directory for output reports (default: ./test_reports/itf)
        """
        self.input_dir = Path(input_dir).resolve()

        # Determine output directory with fallback logic
        if output_dir:
            self.output_dir = Path(output_dir).resolve()
        else:
            # Try parent directory first, fall back to project root
            parent_test_reports = self.input_dir.parent / "itf_reports"
            project_test_reports = project_root / "test_reports" / "itf"

            # Use parent if it's writable, otherwise use project root
            if self._is_writable(self.input_dir.parent):
                self.output_dir = parent_test_reports
            else:
                self.output_dir = project_test_reports

        # Initialize validation state
        self.validation_passed = False
        self.validation_errors = []
        self.itf_files = []

        # Create output directory
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Output directory ready: {self.output_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to create output directory: {e}")
            raise

        # Initialize agent
        self.agent = ITFAgent()

        logger.info(f"🚀 ITF Test Runner initialized")

    @staticmethod
    def _is_writable(path: Path) -> bool:
        """Check if directory is writable."""
        try:
            # Try to create a test file
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except (OSError, PermissionError):
            return False

    def validate_input_directory(self) -> bool:
        """
        Validate input directory:
        1. Directory exists
        2. Directory contains files
        3. Files match pattern: *ITF*.md

        Returns:
            True if validation passed
        """
        logger.info(f"\n{'=' * 80}")
        logger.info(f"📁 DIRECTORY VALIDATION")
        logger.info(f"{'=' * 80}")

        self.validation_errors = []

        # Step 1: Check directory exists
        logger.info(f"\n✓ Checking directory exists: {self.input_dir}")
        if not self.input_dir.exists():
            error = f"Directory does not exist: {self.input_dir}"
            logger.error(f"❌ {error}")
            self.validation_errors.append(error)
            return False

        if not self.input_dir.is_dir():
            error = f"Path is not a directory: {self.input_dir}"
            logger.error(f"❌ {error}")
            self.validation_errors.append(error)
            return False

        logger.info(f"✅ Directory exists and is accessible")

        # Step 2: Check directory has files
        logger.info(f"\n✓ Checking directory contains files")
        all_files = list(self.input_dir.glob("*"))

        if not all_files:
            error = f"Directory is empty: {self.input_dir}"
            logger.error(f"❌ {error}")
            self.validation_errors.append(error)
            return False

        logger.info(f"✅ Found {len(all_files)} total files")

        # Step 3: Filter for .md files
        logger.info(f"\n✓ Filtering for .md files")
        md_files = [f for f in all_files if f.suffix.lower() == ".md"]

        if not md_files:
            error = f"No .md files found in: {self.input_dir}"
            logger.error(f"❌ {error}")
            self.validation_errors.append(error)
            logger.info(f"   Found files: {[f.name for f in all_files[:10]]}")
            return False

        logger.info(f"✅ Found {len(md_files)} markdown files")
        for f in md_files[:5]:
            logger.info(f"   • {f.name}")
        if len(md_files) > 5:
            logger.info(f"   ... and {len(md_files) - 5} more")

        # Step 4: Filter for ITF files
        logger.info(f"\n✓ Filtering for ITF files (containing 'ITF' in name)")
        itf_files = [f for f in md_files if "ITF" in f.name.upper()]

        if not itf_files:
            error = f"No files matching '*ITF*.md' pattern found in: {self.input_dir}"
            logger.error(f"❌ {error}")
            logger.info(f"   Markdown files found: {[f.name for f in md_files]}")
            self.validation_errors.append(error)
            return False

        logger.info(f"✅ Found {len(itf_files)} ITF markdown files")
        for f in itf_files:
            file_size = f.stat().st_size
            logger.info(f"   • {f.name} ({file_size:,} bytes)")

        self.itf_files = sorted(itf_files)

        # Final validation summary
        logger.info(f"\n{'=' * 80}")
        logger.info(f"✅ VALIDATION PASSED")
        logger.info(f"{'=' * 80}")
        logger.info(f"Input Dir:     {self.input_dir}")
        logger.info(f"Output Dir:    {self.output_dir}")
        logger.info(f"ITF Files:     {len(self.itf_files)}")
        logger.info(f"{'=' * 80}\n")

        self.validation_passed = True
        return True

    async def process_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Process single ITF file.

        Returns:
            Processing result dictionary
        """
        logger.info(f"\n{'=' * 80}")
        logger.info(f"📋 Processing: {file_path.name}")
        logger.info(f"{'=' * 80}")

        try:
            result = await self.agent.process_itf_file(str(file_path))

            if result.get("status") == "success":
                logger.info(f"✅ SUCCESS: {file_path.name}")
                self._log_result_summary(result)
            else:
                logger.error(f"❌ FAILED: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"❌ Exception processing {file_path.name}: {e}", exc_info=True)
            return {
                "file": str(file_path),
                "form_type": "ITF",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _log_result_summary(self, result: Dict[str, Any]):
        """Log summary of processing result."""
        if result.get("status") != "success":
            return

        metadata = result.get("metadata", {})
        risk_assessment = result.get("risk_assessment", {})
        validation = result.get("validation", {})

        logger.info(f"  📊 Metadata:")
        logger.info(f"     Sections:         {metadata.get('sections_parsed')}")
        logger.info(f"     Fields:           {metadata.get('fields_extracted')}")
        logger.info(f"     Clinical Concepts: {metadata.get('clinical_concept_fields')}")
        logger.info(f"     Risk Flags:       {metadata.get('total_risk_flags')}")

        logger.info(f"  ✔ Validation:")
        status = "✅ PASS" if validation.get('required_fields_valid') else "❌ FAIL"
        logger.info(f"     Required Fields: {status}")
        if validation.get("missing_fields"):
            logger.info(f"     Missing: {validation['missing_fields']}")
        if validation.get("validation_errors"):
            logger.info(f"     Errors: {len(validation['validation_errors'])}")

        logger.info(f"  🚩 Risk Flags:")
        for severity in ["critical", "high", "moderate"]:
            count = len(risk_assessment.get(severity, []))
            if count > 0:
                symbol = "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡"
                logger.info(f"     {symbol} {severity.upper()}: {count}")

    async def run_all(self) -> Dict[str, Any]:
        """
        Process all validated ITF markdown files.

        Returns:
            Summary of all processing results
        """
        # Validate directory first
        if not self.validate_input_directory():
            logger.error(f"\n❌ Directory validation failed!")
            logger.error(f"Errors:")
            for error in self.validation_errors:
                logger.error(f"  • {error}")

            return {
                "status": "validation_failed",
                "timestamp": datetime.now().isoformat(),
                "validation_errors": self.validation_errors,
                "results": []
            }

        logger.info(f"\n{'#' * 80}")
        logger.info(f"# ITF BATCH PROCESSING - START")
        logger.info(f"{'#' * 80}\n")

        start_time = datetime.now()

        # Process files
        results = []
        for idx, file_path in enumerate(self.itf_files, 1):
            logger.info(f"[{idx}/{len(self.itf_files)}] Processing file...")
            result = await self.process_file(file_path)
            results.append(result)

            # Small delay between files
            if idx < len(self.itf_files):
                await asyncio.sleep(0.1)

        # Compile summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        successful_results = [r for r in results if r.get("status") == "success"]
        failed_results = [r for r in results if r.get("status") == "error"]

        # Aggregate statistics
        total_sections = sum(
            r.get("metadata", {}).get("sections_parsed", 0)
            for r in successful_results
        )
        total_fields = sum(
            r.get("metadata", {}).get("fields_extracted", 0)
            for r in successful_results
        )
        total_clinical_concepts = sum(
            r.get("metadata", {}).get("clinical_concept_fields", 0)
            for r in successful_results
        )
        total_risk_flags = sum(
            r.get("metadata", {}).get("total_risk_flags", 0)
            for r in successful_results
        )

        # Aggregate risk flags by severity
        aggregated_risk = {
            "critical": [],
            "high": [],
            "moderate": [],
            "observation": []
        }

        for result in successful_results:
            for severity in ["critical", "high", "moderate", "observation"]:
                flags = result.get("risk_assessment", {}).get(severity, [])
                aggregated_risk[severity].extend(flags)

        summary = {
            "status": "complete",
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "input_directory": str(self.input_dir),
            "output_directory": str(self.output_dir),
            "files": {
                "total": len(results),
                "successful": len(successful_results),
                "failed": len(failed_results)
            },
            "aggregated_statistics": {
                "total_sections": total_sections,
                "total_fields": total_fields,
                "total_clinical_concepts": total_clinical_concepts,
                "total_risk_flags": total_risk_flags,
                "risk_flags_by_severity": {
                    "critical": len(aggregated_risk["critical"]),
                    "high": len(aggregated_risk["high"]),
                    "moderate": len(aggregated_risk["moderate"]),
                    "observation": len(aggregated_risk["observation"])
                }
            },
            "results": results
        }

        # Log summary
        logger.info(f"\n{'#' * 80}")
        logger.info(f"# BATCH PROCESSING SUMMARY")
        logger.info(f"{'#' * 80}")
        logger.info(f"Total Files:        {len(results)}")
        logger.info(f"Successful:         {len(successful_results)} ✅")
        logger.info(f"Failed:             {len(failed_results)} ❌")
        logger.info(f"Duration:           {duration:.2f}s")
        logger.info(f"\nAggregated Statistics:")
        logger.info(f"  Sections Parsed:  {total_sections}")
        logger.info(f"  Fields Extracted: {total_fields}")
        logger.info(f"  Clinical Concepts: {total_clinical_concepts}")
        logger.info(f"  Total Risk Flags: {total_risk_flags}")
        logger.info(f"    🔴 CRITICAL:    {len(aggregated_risk['critical'])}")
        logger.info(f"    🟠 HIGH:        {len(aggregated_risk['high'])}")
        logger.info(f"    🟡 MODERATE:    {len(aggregated_risk['moderate'])}")
        logger.info(f"    ⚪ OBSERVATION: {len(aggregated_risk['observation'])}")
        logger.info(f"{'#' * 80}\n")

        return summary

    def export_summary_json(self, summary: Dict[str, Any]):
        """Export batch summary as JSON."""
        output_file = self.output_dir / "batch_summary.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            logger.info(f"📄 Batch summary exported: {output_file}")
            logger.info(f"   Size: {output_file.stat().st_size:,} bytes")

        except Exception as e:
            logger.error(f"Error exporting summary: {e}")

    def export_individual_reports(self, summary: Dict[str, Any]):
        """Export individual reports for each file."""
        successful = [r for r in summary.get("results", []) if r.get("status") == "success"]

        logger.info(f"\n📊 Exporting {len(successful)} individual reports...")

        for idx, result in enumerate(successful, 1):
            try:
                # Extract filename from path
                file_path = Path(result.get("file", ""))
                base_name = file_path.stem

                # JSON report
                json_output = self.output_dir / f"{base_name}_report.json"
                self.agent.export_json_report(result, str(json_output))

                json_individual_output = self.output_dir / f"{base_name}.json"
                self.agent.export_individual_json(result, str(json_individual_output))

                # Text report
                text_output = self.output_dir / f"{base_name}_report.txt"
                self.agent.export_text_report(result, str(text_output))

                logger.info(f"  [{idx}/{len(successful)}] ✅ {base_name}")

            except Exception as e:
                logger.error(f"  [{idx}/{len(successful)}] ❌ Error exporting {base_name}: {e}")

    def print_file_summary_table(self, summary: Dict[str, Any]):
        """Print summary table for all files."""
        successful = [r for r in summary.get("results", []) if r.get("status") == "success"]

        if not successful:
            logger.info("No successful files to display")
            return

        logger.info(f"\n{'=' * 120}")
        logger.info(f"{'File':<40} {'Sections':<10} {'Fields':<10} {'Concepts':<10} {'🔴':<5} {'🟠':<5} {'🟡':<5}")
        logger.info(f"{'=' * 120}")

        for result in successful:
            file_name = Path(result.get("file", "")).name
            metadata = result.get("metadata", {})
            risk = result.get("risk_assessment", {})

            logger.info(
                f"{file_name:<40} "
                f"{metadata.get('sections_parsed', 0):<10} "
                f"{metadata.get('fields_extracted', 0):<10} "
                f"{metadata.get('clinical_concept_fields', 0):<10} "
                f"{len(risk.get('critical', [])):<5} "
                f"{len(risk.get('high', [])):<5} "
                f"{len(risk.get('moderate', [])):<5}"
            )

        logger.info(f"{'=' * 120}\n")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="ITF Form Test Runner - Process directory of ITF markdown files",
        epilog="Example: python -m tests.runners.test_itf_runner /tests/test_output/async"
    )

    parser.add_argument(
        "input_dir",
        type=str,
        help="Directory containing ITF markdown files (*ITF*.md)"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output directory for reports (default: input_dir/../itf_reports or ./test_reports/itf)"
    )

    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Skip JSON report generation"
    )

    parser.add_argument(
        "--no-text",
        action="store_true",
        help="Skip text report generation"
    )

    parser.add_argument(
        "--no-table",
        action="store_true",
        help="Skip summary table output"
    )

    args = parser.parse_args()

    # Create runner
    runner = ITFTestRunner(args.input_dir, args.output)

    # Process all files
    summary = await runner.run_all()

    # Check if validation failed
    if summary.get("status") == "validation_failed":
        logger.error(f"\n❌ Test run aborted due to validation failures")
        return 1

    # Export reports
    if not args.no_json:
        runner.export_summary_json(summary)
        runner.export_individual_reports(summary)

    if not args.no_table:
        runner.print_file_summary_table(summary)

    logger.info(f"\n{'=' * 80}")
    logger.info(f"✅ Test run complete!")
    logger.info(f"{'=' * 80}")
    logger.info(f"📁 Reports saved to: {runner.output_dir}")
    logger.info(f"📋 Log file: {log_file}")
    logger.info(f"{'=' * 80}\n")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
