from datetime import timedelta
from feast import (
    Entity,
    FeatureService,
    FeatureView,
    Field,
    FileSource,
)
from feast.types import Float32, Int64, String

# Define the customer entity
customer = Entity(
    name="customer",
    join_keys=["customer_id"],
)

# Define data sources
customer_interactions_source = FileSource(
    name="customer_interactions_source",
    path="data/customer_interactions.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created",
)

customer_profile_source = FileSource(
    name="customer_profile_source",
    path="data/customer_profiles.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created",
)

# Define feature views
customer_interactions_fv = FeatureView(
    name="customer_interactions",
    entities=[customer],
    ttl=timedelta(days=90),
    schema=[
        Field(name="session_duration", dtype=Int64),
        Field(name="pages_viewed", dtype=Int64),
        Field(name="purchase_amount", dtype=Float32),
        Field(name="is_weekend", dtype=Int64),
        Field(name="device_type", dtype=String),
        Field(name="browser", dtype=String),
        Field(name="interaction_type", dtype=String),
    ],
    source=customer_interactions_source,
    online=True,
)

customer_profile_fv = FeatureView(
    name="customer_profile",
    entities=[customer],
    ttl=timedelta(days=90),
    schema=[
        Field(name="age", dtype=Int64),
        Field(name="subscription_type", dtype=String),
        Field(name="country", dtype=String),
        Field(name="customer_segment", dtype=String),
        Field(name="email_subscribed", dtype=Int64),
        Field(name="lifetime_value", dtype=Float32),
    ],
    source=customer_profile_source,
    online=True,
)

# Define feature services for different use cases
recommendation_fs = FeatureService(
    name="recommendation_features",
    features=[
        customer_interactions_fv[["session_duration", "pages_viewed", "purchase_amount", "interaction_type"]],
        customer_profile_fv[["age", "subscription_type", "customer_segment", "lifetime_value"]],
    ],
)

personalization_fs = FeatureService(
    name="personalization_features",
    features=[
        customer_interactions_fv[["device_type", "browser", "is_weekend"]],
        customer_profile_fv[["country", "email_subscribed", "customer_segment"]],
    ],
)
