import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Generate a random classification dataset
X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, 
                         n_redundant=5, random_state=42)

# Convert to DataFrame
data = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
data['target'] = y

# Save the dataset
data.to_csv('data/dataset.csv', index=False)
print("Dataset generated and saved to data/dataset.csv")
