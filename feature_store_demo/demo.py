from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from feast import FeatureStore

def generate_sample_data():
    """Generate sample data for demonstration"""
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate customer interactions data
    n_interactions = 1000
    customer_ids = np.random.randint(1, 6, n_interactions)
    
    # Generate timestamps for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    timestamps = pd.date_range(start=start_date, end=end_date, periods=n_interactions)
    
    interactions_df = pd.DataFrame({
        "event_timestamp": timestamps,
        "created": timestamps,  # Additional timestamp field
        "customer_id": customer_ids,
        "session_duration": np.random.randint(1, 3600, n_interactions),
        "pages_viewed": np.random.randint(1, 50, n_interactions),
        "purchase_amount": np.random.uniform(0, 1000, n_interactions),
        "is_weekend": np.random.randint(0, 2, n_interactions),
        "device_type": np.random.choice(["mobile", "desktop", "tablet"], n_interactions),
        "browser": np.random.choice(["chrome", "firefox", "safari"], n_interactions),
        "interaction_type": np.random.choice(["view", "cart", "purchase"], n_interactions),
    })
    
    # Generate customer profile data
    n_customers = 5
    profile_timestamps = [datetime.now()] * n_customers
    
    profile_df = pd.DataFrame({
        "event_timestamp": profile_timestamps,
        "created": profile_timestamps,  # Additional timestamp field
        "customer_id": range(1, n_customers + 1),
        "age": np.random.randint(18, 80, n_customers),
        "subscription_type": np.random.choice(["free", "basic", "premium"], n_customers),
        "country": np.random.choice(["US", "UK", "CA"], n_customers),
        "customer_segment": np.random.choice(["new", "regular", "vip"], n_customers),
        "email_subscribed": np.random.randint(0, 2, n_customers),
        "lifetime_value": np.random.uniform(0, 5000, n_customers),
    })
    
    # Convert timestamps to pandas datetime
    interactions_df['event_timestamp'] = pd.to_datetime(interactions_df['event_timestamp'])
    interactions_df['created'] = pd.to_datetime(interactions_df['created'])
    profile_df['event_timestamp'] = pd.to_datetime(profile_df['event_timestamp'])
    profile_df['created'] = pd.to_datetime(profile_df['created'])
    
    # Save the dataframes
    interactions_df.to_parquet("data/customer_interactions.parquet")
    profile_df.to_parquet("data/customer_profiles.parquet")
    
    return interactions_df, profile_df

def main():
    # Initialize the feature store
    store = FeatureStore(repo_path=".")
    
    print("\n=== Demonstration of Feature Store Usage ===\n")
    
    # 1. Generate and save sample data
    print("1. Generating sample data...")
    interactions_df, profile_df = generate_sample_data()
    print("Sample data generated and saved to parquet files.")
    
    # 2. Materialize features to online store
    print("\n2. Materializing features to online store...")
    store.materialize_incremental(end_date=datetime.now())
    print("Features materialized successfully.")
    
    # 3. Generate sample entity dataframe for feature retrieval
    entity_df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5],
            "event_timestamp": [datetime.now() for _ in range(5)]
        }
    )
    
    print("\n3. Fetching historical features for recommendation system:")
    recommendation_features = store.get_historical_features(
        entity_df=entity_df,
        features=[
            "customer_interactions:session_duration",
            "customer_interactions:purchase_amount",
            "customer_profile:customer_segment",
            "customer_profile:lifetime_value",
        ],
    ).to_df()
    print("\nRecommendation Features Sample:")
    print(recommendation_features.head())
    
    # 4. Online feature retrieval
    print("\n4. Online Feature Retrieval Example:")
python demo.py    online_features = store.get_online_features(
        features=[
            "customer_interactions:session_duration",
            "customer_interactions:purchase_amount",
            "customer_profile:customer_segment",
        ],
        entity_rows=[{"customer_id": 1}],
    ).to_dict()
    print("\nOnline Features for Customer 1:")
    print(online_features)

if __name__ == "__main__":
    main()
