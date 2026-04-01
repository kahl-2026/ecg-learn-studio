# ECG Learn Studio - ML Guide

## Machine Learning Overview

This guide explains the machine learning components of ECG Learn Studio, designed for educational purposes.

## Classification Task

**Goal**: Classify ECG signals into 5 arrhythmia types

### Classes

1. **Normal Sinus Rhythm**
   - Regular heartbeat, 60-100 bpm
   - Clear P waves, QRS, T waves
   - Consistent RR intervals

2. **Atrial Fibrillation (AFib)**
   - Irregular rhythm
   - No clear P waves (fibrillatory waves instead)
   - Variable RR intervals

3. **Bradycardia**
   - Heart rate < 60 bpm
   - Otherwise normal morphology
   - Regular rhythm

4. **Tachycardia**
   - Heart rate > 100 bpm
   - May be supraventricular or ventricular origin
   - Regular or irregular

5. **Premature Ventricular Contractions (PVCs)**
   - Extra beats from ventricles
   - Wide QRS complexes (>0.12s)
   - Compensatory pause after

## Datasets

### Synthetic ECG Generator

**Purpose**: Generate reproducible, labeled training data

**Algorithm**:
```python
# Simplified pseudocode
def generate_ecg(arrhythmia_type, duration, hr):
    signal = zeros(duration * sampling_rate)
    
    for beat in beats:
        if arrhythmia_type == "normal":
            add_pqrst_complex(signal, beat_position)
        elif arrhythmia_type == "afib":
            add_irregular_qrst(signal, beat_position)
            add_fibrillation_waves(signal)
        elif arrhythmia_type == "pvc":
            if is_pvc_beat:
                add_wide_qrs(signal, beat_position)
            else:
                add_pqrst_complex(signal, beat_position)
    
    return signal + noise
```

**Parameters**:
- Sampling rate: 360 Hz (MIT-BIH standard)
- Duration: 10 seconds default
- Noise level: 0.05 (5% of signal amplitude)

**Advantages**:
- Perfect labels (no annotation errors)
- Controllable difficulty
- Unlimited data
- No licensing issues

**Limitations**:
- Simplified physiology
- May not capture all real-world variations

### Public Datasets

#### MIT-BIH Arrhythmia Database

- **Size**: 48 half-hour recordings
- **Subjects**: 47 patients
- **Sampling**: 360 Hz
- **Annotations**: Beat-by-beat labels
- **Classes**: 17 beat types
- **License**: Open Database License

#### PTB-XL Database

- **Size**: 21,837 recordings
- **Duration**: 10 seconds each
- **Sampling**: 100 Hz or 500 Hz
- **Leads**: 12-lead ECG
- **Annotations**: Diagnostic statements
- **License**: Creative Commons Attribution 4.0

## Preprocessing Pipeline

### 1. Filtering

**Bandpass Filter (0.5-40 Hz)**:
```python
# Remove baseline wander and high-frequency noise
filtered_signal = bandpass_filter(raw_signal, lowcut=0.5, highcut=40.0)
```

**Why these frequencies?**
- 0.5 Hz: Removes baseline wander from breathing
- 40 Hz: Preserves QRS while removing muscle noise
- QRS complex: 5-15 Hz (preserved)

**Optional Notch Filter (60 Hz)**:
- Removes powerline interference
- US standard is 60 Hz (Europe: 50 Hz)

### 2. Normalization

**Z-score Normalization**:
```
normalized = (signal - mean) / std
```

**Purpose**:
- Makes signals comparable across different amplitudes
- Centers data around 0
- Helps neural networks converge faster

### 3. Segmentation

**Beat-based Segmentation**:
1. Detect R-peaks using Pan-Tompkins algorithm
2. Extract window around each peak (-0.2s to +0.4s)
3. Results in ~60-100 beats per 10-second signal

**Fixed-window Segmentation**:
1. Split signal into 10-second windows
2. Optional overlap for data augmentation
3. Better for rhythm classification

### 4. Feature Extraction

**Time-Domain Features**:
- Mean, standard deviation
- Skewness, kurtosis
- Signal energy
- Zero crossing rate

**Frequency-Domain Features**:
- Dominant frequency
- Power spectral density
- Spectral entropy
- VLF, LF, HF band powers

**Morphological Features**:
- QRS duration
- R-peak amplitude
- QRS area
- Wave amplitudes

**Heart Rate Variability (HRV)**:
- Mean RR interval
- RMSSD (root mean square of successive differences)
- pNN50 (percentage of intervals differing by >50ms)

## Models

### Baseline: Logistic Regression

**Type**: Linear classifier

**Input**: Feature vector (~30 features)

**Architecture**:
```
Features (30) → Logistic → Softmax → Predictions (5)
```

**Hyperparameters**:
- C (regularization): 1.0
- Solver: lbfgs
- Max iterations: 1000

**Advantages**:
- Fast training (<10 seconds)
- Interpretable (feature weights)
- Low risk of overfitting
- Probabilistic outputs

**Limitations**:
- Assumes linear separability
- Requires manual feature engineering
- May underfit complex patterns

**When to use**:
- Quick baseline
- Feature importance analysis
- Interpretability required

### Baseline: Random Forest

**Type**: Ensemble of decision trees

**Input**: Feature vector (~30 features)

**Architecture**:
```
Features → 100 Decision Trees → Majority Vote → Predictions
```

**Hyperparameters**:
- n_estimators: 100
- max_depth: 10
- min_samples_split: 5

**Advantages**:
- Non-linear decision boundaries
- Feature importance (Gini/entropy)
- Robust to outliers
- Less prone to overfitting than single trees

**Limitations**:
- Requires feature engineering
- Can be slow for inference (100 trees)
- Less interpretable than logistic regression

**When to use**:
- Better accuracy than logistic regression
- Feature importance analysis
- Robust predictions

### Neural: 1D CNN

**Type**: Convolutional Neural Network

**Input**: Raw ECG signal (3600 samples)

**Architecture**:
```
Input (1 x 3600)
    ↓
Conv1D (32 filters, kernel=5) + ReLU + BatchNorm + MaxPool + Dropout(0.2)
    ↓
Conv1D (64 filters, kernel=5) + ReLU + BatchNorm + MaxPool + Dropout(0.2)
    ↓
Conv1D (128 filters, kernel=5) + ReLU + BatchNorm + MaxPool + Dropout(0.3)
    ↓
Conv1D (256 filters, kernel=5) + ReLU + BatchNorm + MaxPool + Dropout(0.3)
    ↓
Flatten
    ↓
Dense (128) + ReLU + Dropout(0.5)
    ↓
Dense (5) → Softmax → Predictions
```

**Hyperparameters**:
- Learning rate: 0.001
- Batch size: 32
- Epochs: 50
- Optimizer: Adam
- Loss: Cross-entropy

**Advantages**:
- Learns features automatically (no manual extraction)
- Captures temporal patterns
- State-of-the-art performance
- End-to-end training

**Limitations**:
- Requires more data (1000+ samples)
- Longer training time (minutes)
- Less interpretable (blackbox)
- Risk of overfitting

**When to use**:
- Best accuracy needed
- Sufficient training data
- Computational resources available

## Training Process

### Data Splitting

**Strategy**: Stratified split
- Train: 60%
- Validation: 20%
- Test: 20%

**Why stratified?**
- Preserves class distribution in each split
- Critical for imbalanced datasets

### Class Imbalance

**Problem**: Some arrhythmias are rarer than others

**Solutions**:

1. **Class Weights**:
   ```python
   weight_i = n_samples / (n_classes * n_samples_i)
   ```
   - Penalize misclassifying minority classes more

2. **Oversampling**:
   - SMOTE (Synthetic Minority Over-sampling Technique)
   - Generate synthetic examples of minority classes

3. **Evaluation Metrics**:
   - Use macro-averaged metrics (average across classes)
   - Don't rely solely on accuracy

### Training Loop (CNN)

```python
for epoch in range(num_epochs):
    # Training phase
    model.train()
    for batch in train_loader:
        optimizer.zero_grad()
        outputs = model(batch.data)
        loss = criterion(outputs, batch.labels)
        loss.backward()
        optimizer.step()
    
    # Validation phase
    model.eval()
    with torch.no_grad():
        for batch in val_loader:
            outputs = model(batch.data)
            # Compute metrics
    
    # Learning rate scheduling
    scheduler.step(val_loss)
```

### Early Stopping

Stop training if validation loss doesn't improve for N epochs:
- Prevents overfitting
- Saves computation time
- Default patience: 10 epochs

## Evaluation Metrics

### Accuracy

**Definition**: Proportion of correct predictions

```
Accuracy = (TP + TN) / (TP + TN + FP + FN)
```

**Example**: 85% accuracy means 85 out of 100 predictions are correct

**Limitations**:
- Misleading with imbalanced data
- Doesn't distinguish between error types

### Precision

**Definition**: Proportion of positive predictions that are correct

```
Precision = TP / (TP + FP)
```

**Example**: 90% precision means 9 out of 10 "AFib" predictions are truly AFib

**Use case**: When false positives are costly

### Recall (Sensitivity)

**Definition**: Proportion of actual positives that were found

```
Recall = TP / (TP + FN)
```

**Example**: 80% recall means model finds 8 out of 10 actual AFib cases

**Use case**: When false negatives are costly (e.g., missing disease)

### F1 Score

**Definition**: Harmonic mean of precision and recall

```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Why harmonic mean?**
- Penalizes extreme imbalances
- F1 is low if either precision or recall is low

**Example**: Balances false positives and false negatives

### ROC-AUC

**Definition**: Area Under Receiver Operating Characteristic curve

**Interpretation**:
- 0.5: Random guessing
- 0.7-0.8: Acceptable
- 0.8-0.9: Excellent
- 0.9-1.0: Outstanding

**Use case**: Overall model quality, threshold-independent

### Confusion Matrix

```
                Predicted
              N   A   B   T   P
Actual    N  45   2   1   1   1
          A   1  42   3   2   2
          B   2   1  44   1   2
          T   1   3   1  43   2
          P   1   2   2   1  44
```

**Insights**:
- Diagonal: Correct predictions
- Off-diagonal: Confusion between classes
- Each row sums to true class count

## Explainability

### Feature Importance (Baseline Models)

**Logistic Regression**:
- Absolute coefficient values
- High |weight| = important feature

**Random Forest**:
- Gini importance
- How much each feature reduces impurity

**Example**:
```
Top 5 Features:
1. Heart rate (0.15)
2. RR interval std (0.12)
3. QRS duration (0.10)
4. Dominant frequency (0.08)
5. Spectral entropy (0.07)
```

### Saliency Maps (CNN)

**Method**: Gradient-based attribution
1. Compute gradient of output w.r.t. input
2. High gradient = important region
3. Visualize as heatmap overlay

**Use case**: "Which part of the signal influenced the prediction?"

### Plain-English Explanations

**Template**:
```
The model predicts [CLASS] with [CONFIDENCE]% confidence.

[CLASS_DESCRIPTION]

This prediction was based on:
- [KEY_FEATURE_1]
- [KEY_FEATURE_2]
- [KEY_FEATURE_3]

Confidence interpretation: [LOW/MEDIUM/HIGH] confidence
```

## Hyperparameter Tuning

### Grid Search

**Method**: Try all combinations

**Example**:
```python
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [2, 5, 10]
}
# Total: 3 x 3 x 3 = 27 combinations
```

**Pros**: Exhaustive
**Cons**: Computationally expensive

### Random Search

**Method**: Sample random combinations

**Pros**: Faster than grid search
**Cons**: May miss optimal combination

### Bayesian Optimization

**Method**: Use previous results to guide search

**Pros**: Most efficient
**Cons**: Complex to implement

## Best Practices

1. **Always use a validation set**: Don't tune on test set
2. **Cross-validation**: K-fold CV for robust evaluation
3. **Stratify splits**: Preserve class distribution
4. **Handle class imbalance**: Use class weights or SMOTE
5. **Monitor overfitting**: Track train vs validation metrics
6. **Use appropriate metrics**: Not just accuracy
7. **Save checkpoints**: Don't lose trained models
8. **Document experiments**: Track hyperparameters and results
9. **Visualize predictions**: Check where model fails
10. **Plain-language explanations**: Make results accessible

## Common Pitfalls

1. **Data leakage**: Test data in training
2. **Overfitting**: Model memorizes training data
3. **Underfitting**: Model too simple for task
4. **Ignoring class imbalance**: High accuracy, poor performance on minorities
5. **Not normalizing**: Different scales cause issues
6. **Using wrong metrics**: Accuracy with imbalanced data
7. **Overly complex models**: Start simple, add complexity as needed

## Further Reading

- **ECG Analysis**: "Introduction to ECG Interpretation" (Hampton)
- **ML for Time Series**: "Deep Learning for Time Series Forecasting" (Brownlee)
- **CNNs for ECG**: "ECG Heartbeat Classification Using Deep Transfer Learning" (Rajpurkar et al.)
- **Imbalanced Learning**: "Learning from Imbalanced Data" (He & Garcia)

## Conclusion

This guide covers the core ML concepts in ECG Learn Studio. Remember: this is an educational platform. Focus on understanding concepts, not achieving state-of-the-art performance.

**Happy Learning!** 🎓
