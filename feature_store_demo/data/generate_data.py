import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

def generate_customer_data(n_customers=1000):
    # Generate customer IDs
    customer_ids = range(1, n_customers + 1)
    
    # Generate timestamps for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    data = []
    for customer_id in customer_ids:
        # Generate multiple interactions per customer
        n_interactions = np.random.randint(1, 10)
        for _ in range(n_interactions):
            timestamp = start_date + timedelta(
                days=np.random.randint(0, 30),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            
            interaction = {
                'customer_id': customer_id,
                'event_timestamp': timestamp,
                'session_duration': np.random.randint(1, 120),  # minutes
                'pages_viewed': np.random.randint(1, 20),
                'purchase_amount': np.random.choice([0] * 7 + [round(np.random.uniform(10, 200), 2)] * 3),
                'is_weekend': int(timestamp.weekday() >= 5),
                'device_type': np.random.choice(['mobile', 'desktop', 'tablet']),
                'browser': np.random.choice(['chrome', 'firefox', 'safari', 'edge']),
                'interaction_type': np.random.choice(['view', 'click', 'purchase', 'cart_add'])
            }
            data.append(interaction)
    
    # Convert to DataFrame and sort by timestamp
    df = pd.DataFrame(data)
    df = df.sort_values('event_timestamp')
    return df

def generate_customer_profile(n_customers=1000):
    customer_ids = range(1, n_customers + 1)
    
    profiles = []
    for customer_id in customer_ids:
        profile = {
            'customer_id': customer_id,
            'age': np.random.randint(18, 70),
            'subscription_type': np.random.choice(['basic', 'premium', 'pro']),
            'country': np.random.choice(['US', 'UK', 'CA', 'AU', 'DE']),
            'signup_date': datetime.now() - timedelta(days=np.random.randint(1, 365)),
            'customer_segment': np.random.choice(['new', 'regular', 'vip']),
            'email_subscribed': np.random.choice([True, False]),
            'lifetime_value': round(np.random.uniform(0, 1000), 2)
        }
        profiles.append(profile)
    
    return pd.DataFrame(profiles)

if __name__ == "__main__":
    # Generate datasets
    interactions_df = generate_customer_data()
    profiles_df = generate_customer_profile()
    
    # Save datasets in parquet format
    interactions_df.to_parquet("data/customer_interactions.parquet", index=False)
    profiles_df.to_parquet("data/customer_profiles.parquet", index=False)
    
    print(f"Generated {len(interactions_df)} interaction records")
    print(f"Generated {len(profiles_df)} customer profiles")
