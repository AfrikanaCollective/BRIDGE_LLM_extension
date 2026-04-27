"""Test schema loading functionality."""

import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from agents.config import (
    get_form_schema,
    list_available_schemas,
    validate_schema,
)


def test_schema_loading():
    """Test loading all available schemas."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Schema Loading")
    logger.info("=" * 80)

    # List available schemas
    available = list_available_schemas()
    logger.info("\n📋 Available Schemas:")
    for form_type, pages in available.items():
        logger.info(f"   {form_type}: pages {pages}")

    # Load each schema and validate
    for form_type, pages in available.items():
        for page_number in pages:
            logger.info(f"\n   Loading {form_type} page {page_number}...")

            try:
                schema = get_form_schema(form_type, page_number)

                # Validate schema
                validate_schema(schema)

                field_count = len(schema)
                logger.info(f"   ✅ Loaded successfully ({field_count} fields)")

                # Show sample field
                first_field = next(iter(schema.items()))
                logger.debug(f"      Sample: {first_field[0]}")

            except Exception as e:
                logger.error(f"   ❌ Failed to load: {e}")

    logger.info("\n" + "=" * 80)


def test_schema_validation():
    """Test schema validation."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Schema Validation")
    logger.info("=" * 80)

    # Try loading ITF page 1
    try:
        schema = get_form_schema('ITF', 1)
        validate_schema(schema)
        logger.info("\n✅ ITF Page 1 schema is valid")
        logger.info(f"   Total fields: {len(schema)}")

        # Count fields by section
        from agents.config import SectionType
        sections = {}
        for field_name, field_def in schema.items():
            section = field_def.get('section')
            sections[section] = sections.get(section, 0) + 1

        logger.info("\n   Fields by section:")
        for section, count in sorted(sections.items(), key=lambda x: str(x[0])):
            logger.info(f"      {section.value}: {count} fields")

    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")

    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    test_schema_loading()
    test_schema_validation()
