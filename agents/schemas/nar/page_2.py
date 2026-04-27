"""
NAR Page 2 Schema - Neonatal Admission Record (Part 2)
"""

from agents.config import FieldType, SectionType, ClinicalCategory

NAR_PAGE_2_SCHEMA = {
    # Add NAR page 2 fields here
    "Follow-up plan": {
        "field_name": "Follow-up plan",
        "type": FieldType.MULTILINE,
        "required": False,
        "section": SectionType.MOTHER_DETAILS,
        "clinical_category": ClinicalCategory.MODERATE,
        "is_clinical_concept": False,
        "description": "Recommended follow-up plan"
    },
}
