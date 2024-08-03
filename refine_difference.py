import pandas as pd
from sklearn.metrics import mean_absolute_error
import os

filtered_csv_path = 'gpt_responses.csv'
results_csv_path = 'differences_results.csv'

filtered_df = pd.read_csv(filtered_csv_path)

if 'gpt_response' not in filtered_df.columns:
    raise KeyError("'gpt_response' column not found in the DataFrame.")

filtered_df = filtered_df[~filtered_df['gpt_response'].str.contains('Error', na=False)]
filtered_df = filtered_df.dropna(subset=['gpt_response'])

def extract_numeric_value(value_str):
    import re
    numeric_part = re.findall(r"[-+]?\d*\.\d+|\d+", value_str)
    if numeric_part:
        return float(numeric_part[0])
    else:
        return 0

calories_actual = []
calories_pred = []
mass_actual = []
mass_pred = []
fat_actual = []
fat_pred = []
carb_actual = []
carb_pred = []
protein_actual = []
protein_pred = []

calories_diff = []
mass_diff = []
fat_diff = []
carb_diff = []
protein_diff = []

for index, row in filtered_df.iterrows():
    try:
        response = row['gpt_response']
        parts = response.split('\n')
        
        response_values = {
            'total_calories': extract_numeric_value(parts[0].split(':')[1].strip()),
            'total_mass': extract_numeric_value(parts[1].split(':')[1].strip()),
            'total_fat': extract_numeric_value(parts[2].split(':')[1].strip()),
            'total_carb': extract_numeric_value(parts[3].split(':')[1].strip()),
            'total_protein': extract_numeric_value(parts[4].split(':')[1].strip())
        }

        actual_values = {
            'total_calories': float(row['total_calories']),
            'total_mass': float(row['total_mass']),
            'total_fat': float(row['total_fat']),
            'total_carb': float(row['total_carb']),
            'total_protein': float(row['total_protein'])
        }


        calories_actual.append(actual_values['total_calories'])
        calories_pred.append(response_values['total_calories'])
        
        mass_actual.append(actual_values['total_mass'])
        mass_pred.append(response_values['total_mass'])
        
        fat_actual.append(actual_values['total_fat'])
        fat_pred.append(response_values['total_fat'])
        
        carb_actual.append(actual_values['total_carb'])
        carb_pred.append(response_values['total_carb'])
        
        protein_actual.append(actual_values['total_protein'])
        protein_pred.append(response_values['total_protein'])

        calories_diff.append(actual_values['total_calories'] - response_values['total_calories'])
        mass_diff.append(actual_values['total_mass'] - response_values['total_mass'])
        fat_diff.append(actual_values['total_fat'] - response_values['total_fat'])
        carb_diff.append(actual_values['total_carb'] - response_values['total_carb'])
        protein_diff.append(actual_values['total_protein'] - response_values['total_protein'])

    except Exception as e:
        print(f"Error processing row {index}: {e}")

results_df = pd.DataFrame({
    'dish_id': filtered_df['dish_id'],
    'calories_actual': calories_actual,
    'calories_pred': calories_pred,
    'mass_actual': mass_actual,
    'mass_pred': mass_pred,
    'fat_actual': fat_actual,
    'fat_pred': fat_pred,
    'carb_actual': carb_actual,
    'carb_pred': carb_pred,
    'protein_actual': protein_actual,
    'protein_pred': protein_pred,
    'calories_diff': calories_diff,
    'mass_diff': mass_diff,
    'fat_diff': fat_diff,
    'carb_diff': carb_diff,
    'protein_diff': protein_diff
})

mean_calories_diff = results_df['calories_diff'].mean()
mean_mass_diff = results_df['mass_diff'].mean()
mean_fat_diff = results_df['fat_diff'].mean()
mean_carb_diff = results_df['carb_diff'].mean()
mean_protein_diff = results_df['protein_diff'].mean()

print(f'Mean Calories Difference: {mean_calories_diff:.2f}')
print(f'Mean Mass Difference: {mean_mass_diff:.2f}')
print(f'Mean Fat Difference: {mean_fat_diff:.2f}')
print(f'Mean Carbs Difference: {mean_carb_diff:.2f}')
print(f'Mean Protein Difference: {mean_protein_diff:.2f}')

results_df.to_csv(results_csv_path, index=False)

print(f"Results saved to {results_csv_path}")
