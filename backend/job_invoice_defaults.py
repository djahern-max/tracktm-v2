"""
Job-Specific Invoice Defaults
Stores default invoice information per job number to auto-populate the invoice form
"""

JOB_INVOICE_DEFAULTS = {
    "2507": {
        "job_name": "PNSY DD #2 Stairwells T&M",
        "contract_number": "Contract #2083-S-018",
        "ship_to_location": "Portsmouth Naval Shipyard, Kittery Maine",
        "bill_to_name": "Cianbro Corporation",
        "bill_to_address1": "60 Cassidy Drive",
        "bill_to_address2": "Portland, ME 04102",
        "notes": "Subcontract 312550016 - T&M Work on Fuel Building Fireproofing",
    },
    "2317": {
        "job_name": "Project 2317",
        "contract_number": "",
        "ship_to_location": "Newport, RI",
        "bill_to_name": "Reagan Marine Construction LLC",
        "bill_to_address1": "221 Third St, 5th Floor Suite 513",
        "bill_to_address2": "Newport, RI 02840",
        "notes": "",
    },
}


def get_job_defaults(job_number):
    """Get default invoice settings for a job number"""
    return JOB_INVOICE_DEFAULTS.get(
        str(job_number),
        {
            "job_name": f"Job {job_number}",
            "contract_number": "",
            "ship_to_location": "",
            "bill_to_name": "",
            "bill_to_address1": "",
            "bill_to_address2": "",
            "notes": "",
        },
    )


def add_job_defaults(job_number, defaults):
    """Add or update defaults for a job"""
    JOB_INVOICE_DEFAULTS[str(job_number)] = defaults


# For API integration
def get_all_job_defaults():
    """Return all job defaults"""
    return JOB_INVOICE_DEFAULTS
