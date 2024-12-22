# Feature Store Demo

This project demonstrates a feature store implementation using Feast, showcasing how to manage and serve features for machine learning applications. The demo includes both batch and online feature serving capabilities.

## Project Structure

```
feature_store_demo/
├── data/                      # Data storage directory
│   ├── customer_interactions.parquet
│   ├── customer_profiles.parquet
│   ├── registry.db           # Feast registry
│   └── online_store.db       # SQLite online store
├── feature_repo/             # Feature definitions
│   ├── __init__.py
│   └── feature_store.py      # Feature views and services
├── demo.py                   # Demo script
├── feature_store.yaml        # Feast configuration
├── environment.yml          # Conda environment specification
└── README.md                # This file
```

## Feature Sets

### 1. Customer Interactions Features
Real-time customer behavior and interaction data:
- `session_duration` (Int64): Duration of user sessions in seconds
- `pages_viewed` (Int64): Number of pages viewed in a session
- `purchase_amount` (Float32): Amount spent in the session
- `is_weekend` (Int64): Binary flag indicating weekend activity
- `device_type` (String): Device used (mobile, desktop, tablet)
- `browser` (String): Browser used (chrome, firefox, safari)
- `interaction_type` (String): Type of interaction (view, cart, purchase)

### 2. Customer Profile Features
Static customer attributes and aggregated metrics:
- `age` (Int64): Customer's age
- `subscription_type` (String): Subscription level (free, basic, premium)
- `country` (String): Customer's country
- `customer_segment` (String): Customer segment (new, regular, vip)
- `email_subscribed` (Int64): Email subscription status
- `lifetime_value` (Float32): Customer's lifetime value

## Feature Services

### 1. Recommendation Features
Optimized for product recommendations:
```python
recommendation_fs = FeatureService(
    name="recommendation_features",
    features=[
        customer_interactions_fv[["session_duration", "pages_viewed", "purchase_amount", "interaction_type"]],
        customer_profile_fv[["age", "subscription_type", "customer_segment", "lifetime_value"]],
    ],
)
```

### 2. Personalization Features
Designed for UI/UX personalization:
```python
personalization_fs = FeatureService(
    name="personalization_features",
    features=[
        customer_interactions_fv[["device_type", "browser", "is_weekend"]],
        customer_profile_fv[["country", "email_subscribed", "customer_segment"]],
    ],
)
```

## Setup Instructions

1. Create and activate the conda environment:
```bash
conda env create -f environment.yml
conda activate feature-store-demo
```

2. Generate sample data:
```bash
python data/generate_data.py
```

3. Initialize the feature store:
```bash
feast apply
```

4. Run the demo:
```bash
python demo.py
```

## Demo Walkthrough

The demo script (`demo.py`) demonstrates:

1. Data Generation:
   - Creates synthetic customer interaction data
   - Generates customer profile information
   - Saves data in parquet format

2. Feature Store Operations:
   - Materializes features to the online store
   - Retrieves historical features for batch processing
   - Demonstrates real-time feature serving

3. Feature Retrieval Examples:
   ```python
   # Batch feature retrieval
   features = store.get_historical_features(
       entity_df=entity_df,
       features=[
           "customer_interactions:session_duration",
           "customer_profile:customer_segment",
       ],
   )

   # Online feature retrieval
   online_features = store.get_online_features(
       features=[
           "customer_interactions:session_duration",
           "customer_profile:customer_segment",
       ],
       entity_rows=[{"customer_id": 1}],
   )
   ```

## Data Freshness

- Customer Interactions: Features have a TTL of 90 days
- Customer Profiles: Features have a TTL of 90 days
- Online Store: Updated through feature materialization
- Offline Store: Uses parquet files with event timestamps

## Dependencies

- feast==0.42.0
- pandas>=2.0.1
- numpy>=1.24.4
- scikit-learn>=1.3.2
- python-dotenv>=1.0.0

## Best Practices

1. Feature Definition:
   - Use meaningful feature names
   - Include proper data types
   - Set appropriate TTL values

2. Data Management:
   - Maintain timestamp fields (event_timestamp, created)
   - Use appropriate file formats (parquet)
   - Regular feature materialization

3. Feature Services:
   - Group related features
   - Create purpose-specific services
   - Document feature usage

## Contributing

Feel free to contribute by:
1. Opening issues for bugs or feature requests
2. Submitting pull requests with improvements
3. Adding new feature services or views
