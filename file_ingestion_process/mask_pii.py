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
    'extra': [{'type': 'jsonb', 'value': '{"age": 30, "first_name":"Uche"}'},
                        {'type': 'jsonb', 'value': '{"age": 25, "first_name":"Joseph"}'}]
})

# Extract 'value', apply the mask function, and update the DataFrame
df['extra'] = df['extra'].apply(lambda x: {'type': x['type'], 'value': mask_pii(x['value'])})

# print(df)

# check if successful
print(df['extra'].apply(lambda x: x['value']))

# print(df[['extra']])