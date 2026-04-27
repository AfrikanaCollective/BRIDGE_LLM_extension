"""
NAR Page 1 Schema - Neonatal Admission Record (Part 1)
"""

from agents.config import FieldType, SectionType, ClinicalCategory

NAR_PAGE_1_SCHEMA = {
    # Add NAR page 1 fields here
    "Clinical assessment": {
        "field_name": "Clinical assessment",
        "type": FieldType.MULTILINE,
        "required": True,
        "section": SectionType.MOTHER_DETAILS,  # Use appropriate section
        "clinical_category": ClinicalCategory.HIGH,
        "is_clinical_concept": True,
        "description": "Clinical assessment findings"
    },
}
