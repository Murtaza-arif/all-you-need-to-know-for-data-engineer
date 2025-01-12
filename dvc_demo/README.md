# Data Version Control (DVC) Demo Project

This project demonstrates the usage of DVC (Data Version Control) in a machine learning workflow. It includes a simple classification task to showcase data and model versioning.

## Project Structure

```
dvc_demo/
├── data/           # Data directory (versioned by DVC)
│   └── dataset.csv
├── models/         # Model directory (versioned by DVC)
│   └── model.joblib
├── src/           # Source code
│   ├── generate_data.py
│   └── train.py
├── .dvc/          # DVC configuration
├── dvc.yaml       # DVC pipeline definition
├── dvc.lock       # Pipeline state file
├── params.yaml    # Model and data parameters
├── metrics.json   # Model metrics tracked by DVC
├── .gitignore     # Git ignore file
└── requirements.txt
```

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## DVC Pipeline

The project uses DVC pipelines to manage the machine learning workflow. The pipeline is defined in `dvc.yaml` and consists of two stages:

1. `generate_data`: Creates a synthetic classification dataset
2. `train`: Trains a Random Forest classifier and outputs performance metrics

The current pipeline structure:
```
+---------------+  
| generate_data |  
+---------------+  
        *          
        *          
        *          
    +-------+      
    | train |      
    +-------+      
```

To run the entire pipeline:
```bash
dvc repro
```

## Parameters and Experiments

The project uses `params.yaml` to manage all parameters for data generation and model training. We've experimented with different model configurations:

1. Baseline Model:
   - n_estimators: 100
   - max_depth: None (unlimited)
   - Results: Train accuracy = 100%, Test accuracy = 90%

2. Limited Depth Model:
   - n_estimators: 200
   - max_depth: 5
   - Results: Train accuracy = 100%, Test accuracy = 90%

3. More Complex Model:
   - n_estimators: 300
   - max_depth: 10
   - Results: Train accuracy = 100%, Test accuracy = 90%

All experiments showed similar performance, suggesting that our simpler models might be sufficient for this dataset.

## Current Metrics

The latest model performance metrics:
```
Path          test_accuracy    train_accuracy
metrics.json  0.9              1.0
```

The consistent 100% training accuracy across all experiments suggests that our models might be overfitting, despite the good test accuracy.

## Metrics Tracking

The training stage outputs metrics to `metrics.json`, which is tracked by DVC. View the current metrics with:
```bash
dvc metrics show
```

Compare metrics between versions:
```bash
dvc metrics diff
```

## Common DVC Commands

- Initialize DVC:
```bash
dvc init
```

- Run the pipeline:
```bash
dvc repro
```

- Show pipeline structure:
```bash
dvc dag
```

- Track changes and commit:
```bash
git add dvc.yaml dvc.lock metrics.json params.yaml
git commit -m "Update pipeline"
```

- Push/Pull data:
```bash
dvc push  # Push data to remote storage
dvc pull  # Pull data from remote storage
```

## Data Pipeline

1. `generate_data.py`: Creates a synthetic classification dataset using scikit-learn with configurable parameters
2. `train.py`: Trains a Random Forest classifier with configurable hyperparameters and outputs metrics

## Model Performance

The model's performance metrics (accuracy) are tracked in `metrics.json` and can be viewed using DVC metrics commands. Current performance:
- Training Accuracy: 100%
- Test Accuracy: 90%

This indicates that our model is performing well but might be slightly overfitting to the training data. We've tried different model complexities, but the performance remains stable, suggesting that the problem might be relatively simple and that a simpler model could be sufficient.

## Version Control

- Git is used for code version control
- DVC is used for data and model version control
- Pipeline stages and dependencies are tracked in `dvc.yaml`
- Parameters are managed in `params.yaml`
- Metrics are tracked separately for easy comparison between versions

## License

This project is open source and available under the MIT License.
