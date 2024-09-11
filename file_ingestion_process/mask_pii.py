import pandas as pd
import json

# Example function to mask 'diagnosedWithTb'
def mask_pii(json_str):
    data = json.loads(json_str)  # Parse JSON string to Python dict
    if 'surname' in data:
        data['surname'] = '******'  # Masking value
    if 'first_name' in data:
        data['first_name'] = '******'  # Masking value
    if 'middle_name' in data:
        data['middle_name'] = '******'  # Masking value
    if 'phone_number' in data:
        data['phone_number'] = '******'  # Masking value
    
    return json.dumps(data)  # Convert back to JSON string


# Example DataFrame
df = pd.DataFrame({
    'risk_assessment': [{'type': 'jsonb', 'value': '{"diagnosedWithTb": true, "age": 30}'},
                        {'type': 'jsonb', 'value': '{"diagnosedWithTb": false, "age": 25}'}]
        })

# Extract 'value', apply the mask function, and update the DataFrame
df['extra'] = df['extra'].apply(lambda x: {'type': x['type'], 'value': mask_pii(x['value'])})

# print(df)

# check if successful
df['extra'].apply(lambda x: x['value'])