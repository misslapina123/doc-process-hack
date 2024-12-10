import re
import json
import os
from pydantic import BaseModel
from openai import AzureOpenAI

def model_termsandconditions(terms_and_conditions):
   
    terms_and_conditions_structured, contact_info = clean_json_data(terms_and_conditions)

    finaljsonstr = create_structured_json(terms_and_conditions_structured)
    
    result_json = formatted_data_cleaning(finaljsonstr, contact_info)

    document = {
        'id': result_json.get('id'),
        'content': result_json
    }
    return document

def clean_json_data(json_data):
    """
    Extract relevant text content from the JSON, join it into a plain text string,
    and extract specific fields like Customer Service, Email, and Address.
    """
    content = []

    # Extract text from pages and lines
    pages = json_data.get("pages", [])
    for page in pages:
        for line in page.get("lines", []):
            content.append(line.get("text", "").strip())

    # Join all text content into a single string with spaces between components
    plain_text_content = " ".join(content)

    # Extract Customer Service, Email, and Address using regex
    contact_info = {
        "Customer Service": re.search(r"Customer Service:\s+([\+\d\(\)\-\s]+)", plain_text_content),
        "Email": re.search(r"Email:\s+([\w\.\@]+)", plain_text_content),
        "Address": re.search(r"Address:\s+(.+)", plain_text_content),
    }

    # Clean up the extracted values
    contact_info = {key: (match.group(1).strip() if match else None) for key, match in contact_info.items()}

    return plain_text_content, contact_info

def formatted_data_cleaning(json_string, contact_info):
    """
    Replaces the first 'id' in the JSON string with the 'customer_id' and returns the JSON with only the parsed information.

    Args:
        json_string (str): The original JSON string.

    Returns:
        dict: The modified JSON object with 'id' replaced by 'customer_id' and only the parsed information included.
    """
    # Load the JSON string into a Python dictionary
    data = json.loads(json_string)

    # Extract the parsed information
    parsed_info = data["choices"][0]["message"]["parsed"]

    # Replace the first id with the customer_id
    data["id"] = parsed_info["bank"]

    # Create a new dictionary with only the parsed information
    result = {
        "id": data["id"],
        **contact_info,
        **parsed_info
    }

    return result

def create_structured_json(terms_and_conditions_structured):
    client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-08-01-preview"
    )
    class TermsAndConditions(BaseModel):
        bank: str
        introduction: str
        loan_amount_and_purpose: str
        interest_rates: str
        loan_tenure: str
        monthly_repayments: str
        late_payments: str
        loan_security: str
        loan_processing_fees: str
        default_and_foreclosure: str
        early_repayment_and_penalties: str
        changes_to_terms: str
        insurance_requirements: str
        loan_cancellation: str
        dispute_resolution: str
        governing_law: str 
    completion = client.beta.chat.completions.parse(
        model="gpt-4o", # replace with the model deployment name of your gpt-4o 2024-08-06 deployment
        messages=[
        {"role": "system", "content": "Extract the information about this loan agreement contract."},
        {"role": "user", "content": terms_and_conditions_structured},
        ],
        response_format=TermsAndConditions,
    )
    finaljsonstr = completion.model_dump_json(indent=2)
    return finaljsonstr
