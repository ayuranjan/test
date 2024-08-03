import csv
import os
import pandas as pd
from openai import OpenAI
from sklearn.metrics import mean_absolute_error
import base64
import re


filtered_csv_path = 'filtered_dishes.csv'
results_csv_path = 'gpt_responses.csv'
image_path = '../imagery/realsense_overhead/'

client = OpenAI(api_key="your_api_key")

MODEL = "gpt-4o"

def get_image_path(dish_id):
    return os.path.join(image_path, str(dish_id), 'rgb.png')

filtered_df = pd.read_csv(filtered_csv_path)

filtered_df['image_path'] = filtered_df['dish_id'].apply(get_image_path)

filtered_df.to_csv(filtered_csv_path, index=False)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_gpt4_response(image_path):
    base64_image = encode_image(image_path)
    prompt = """
Please provide only the total nutritional information of the entire dish in the following image in this exact format:
total_calories: <value>
total_mass: <value>
total_fat: <value>
total_carb: <value>
total_protein: <value>

Only provide these five values. Do not include any additional information or comments.
Image:
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that responds in a structured format."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }}
            ]}
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content

def clean_response(response):
    lines = response.split('\n')
    cleaned_lines = [line for line in lines if line.startswith(('total_calories', 'total_mass', 'total_fat', 'total_carb', 'total_protein'))]
    return '\n'.join(cleaned_lines)

def extract_numeric_value(value_str):
    numeric_part = re.findall(r"[-+]?\d*\.\d+|\d+", value_str)
    if numeric_part:
        return float(numeric_part[0])
    else:
        return 0

gpt_responses = []
accuracies = []

for index, row in filtered_df.iterrows():
    try:
        response = get_gpt4_response(row['image_path'])
        cleaned_response = clean_response(response)
        gpt_responses.append(cleaned_response)
        print(cleaned_response)
        # Parse the cleaned GPT-4 response to extract the values
        parts = cleaned_response.split('\n')
        response_values = [
            extract_numeric_value(parts[0].split(':')[1].strip()),  # total_calories
            extract_numeric_value(parts[1].split(':')[1].strip()),  # total_mass
            extract_numeric_value(parts[2].split(':')[1].strip()),  # total_fat
            extract_numeric_value(parts[3].split(':')[1].strip()),  # total_carb
            extract_numeric_value(parts[4].split(':')[1].strip())   # total_protein
        ]
        
        # Calculate accuracy for each field
        actual_values = [
            float(row['total_calories']),
            float(row['total_mass']),
            float(row['total_fat']),
            float(row['total_carb']),
            float(row['total_protein'])
        ]
        
        accuracy = 1 - mean_absolute_error(actual_values, response_values) / pd.Series(actual_values).mean()
        accuracies.append(accuracy)
        print("accuracy:",accuracy)
        
    except Exception as e:
        print(f"Error with image {row['image_path']}: {e}")
        gpt_responses.append("Error")
        accuracies.append(None)

intermediate_results = pd.DataFrame({
    'dish_id': filtered_df['dish_id'],
    'gpt_response': gpt_responses,
    'accuracy': accuracies
})
intermediate_results.to_csv('intermediate_results.csv', index=False)

if len(gpt_responses) != len(filtered_df):
    raise ValueError("Length of GPT responses does not match the length of the DataFrame")

filtered_df['gpt_response'] = gpt_responses
filtered_df['accuracy'] = accuracies

filtered_df.to_csv(results_csv_path, index=False)

successful_accuracies = [acc for acc in accuracies if acc is not None]
mean_accuracy = sum(successful_accuracies) / len(successful_accuracies)

print(f'Mean Accuracy: {mean_accuracy * 100:.2f}%')