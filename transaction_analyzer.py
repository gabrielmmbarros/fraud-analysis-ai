import openai
from dotenv import load_dotenv
import os
import json

# This function loads environment variables from .env file into the application's environment,
# allowing for secure management of sensitive data
load_dotenv()

# Configure the OpenAI API with Azure credentials from environment variables
openai.api_type = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_type = os.getenv("AZURE_OPENAI_API_TYPE")

model = "gpt-4o"

# Function to load file contents
def load_file(file_name):
    try:
        with open(file_name, "r") as file:
            data = file.read()
            return data
    except IOError as e:
        print(f"Error: {e}")


# Function to save analysis results to a file
def save_result(file_name, content):
    try:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(content)
    except IOError as e:
        print(f"Error saving file: {e}")

# Function that analyzes financial transactions and identifies if each one is "Possible Fraud" or should be "Approved"
def analyze_transaction(transaction_list):
    print("1. Running transaction analysis")
    
    system_prompt = """
    Analyze the following financial transactions and identify if each one is a "Possible Fraud" or should be "Approved". 
    Add a "Status" attribute with one of these values: "Possible Fraud" or "Approved".

    Each new transaction should be inserted inside the JSON list.

    # Possible fraud indicators
    - Transactions with very discrepant values
    - Transactions that occur in very distant locations (city - state)
    
        Use the response format below to compose your answer.
        
    # Output Format 
    {
        "transactions": [
            {
            "Id": "id",
            "type": "credit or debit",
            "merchant": "merchant name",
            "time": "transaction time",
            "amount": "$XX.XX",
            "product_name": "product name",
            "location": "city - state (Country)"
            "status": ""
            },
        ]
    } 
    """

    message_list = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Consider the CSV below, where each line is a different transaction: {transaction_list}. Your response must follow the #Output Format (just a json without other comments)"
            }
    ]
    
    # Make API call to analyze transactions
    response = openai.chat.completions.create(
        messages = message_list,
        model = model,
        temperature = 0.1
    )

    content = response.choices[0].message.content
    
    # Clean up the response for proper JSON parsing
    content = content.replace("```json", "").replace("```", "")
    content = content.replace("`", '"')
    content = content.strip()
    print("\nOriginal content:", content)

    json_result = json.loads(content)
    return json_result

# Function that generates an explanatory result of the possible fraud reasons
def generate_report(transaction):
    print("2. Generating report for transaction: ", transaction["Id"])
    system_prompt = f"""
    For the following transaction, provide an assessment only if its status is "Possible Fraud".
    Include in the assessment a justification for why you identified it as fraud.
    Transaction: {transaction}

    ## Response Format
    "Id": "id",
    "type": "credit or debit",
    "merchant": "merchant name",
    "time": "transaction time",
    "amount": "$XX.XX",
    "product_name": "product name",
    "location": "city - state (Country)"
    "status": "",
    "assessment" : "Write Not Applicable if status is Approved"
    """

    message_list = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # Make API call to generate fraud report
    response = openai.chat.completions.create(
        messages = message_list,
        model = model,
    )

    content = response.choices[0].message.content
    print("Report generation completed")
    return content

# Function that generates an actionable recommendation for each analysis
def generate_actionable_recommendation(report):
    print("3. Generating recommendations")
        
    system_prompt = f"""
    For the following transaction, provide an appropriate recommendation based on the status and details of the transaction: {report}

    The recommendations can be "Notify Customer", "Engage Anti-Fraud Team", or "Perform Manual Verification".
    They should be written in a technical format.

    Also include a classification of the type of fraud, if applicable. 
    """

    message_list = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    response = openai.chat.completions.create(
        messages = message_list,
        model = model,
    )

    content = response.choices[0].message.content
    print("Finished generating recommendation")
    return content


# Load transaction data from CSV file
data = load_file("database/transactions.csv")
transactions = analyze_transaction(data)

# Process each transaction and generate reports for suspicious ones
for t in transactions["transactions"]: 
    if t["status"] == "Possible Fraud": 
        report = generate_report(t)
        act_recommendation = generate_actionable_recommendation(report)

        transaction_id = t["Id"]
        transaction_product = t["product_name"] 
        transaction_status = t["status"]
        
        # creating actionable recommendation file
        save_result(f"results/transaction-{transaction_id}-{transaction_product}-{transaction_status}.txt", act_recommendation)