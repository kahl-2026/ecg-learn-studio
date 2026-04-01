# IPC Protocol Specification

This directory contains the JSON schema for communication between the Rust TUI frontend and Python ML backend.

## Protocol Version: 1.0

### Communication Model
- **Transport**: JSON over stdin/stdout
- **Pattern**: Request/Response with async progress updates
- **Encoding**: UTF-8, newline-delimited JSON

### Request Format
```json
{
  "id": "unique-request-id",
  "version": "1.0",
  "method": "method_name",
  "params": { /* method-specific parameters */ }
}
```

### Response Format
```json
{
  "id": "matching-request-id",
  "version": "1.0",
  "success": true,
  "result": { /* method-specific result */ }
}
```

### Error Response
```json
{
  "id": "matching-request-id",
  "version": "1.0",
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { /* additional error context */ }
  }
}
```

### Progress Updates
For long-running operations (like training), the backend can send progress updates:
```json
{
  "type": "progress",
  "data": {
    "percentage": 45.5,
    "message": "Epoch 5/10",
    "eta_seconds": 120,
    "metrics": {
      "train_loss": 0.234,
      "val_accuracy": 0.856
    }
  }
}
```

## Available Methods

### System Methods
- `ping`: Health check and version info
- `get_backend_info`: Backend capabilities and status

### Data Methods
- `load_data`: Load or generate ECG dataset
- `get_datasets`: List available datasets
- `preprocess`: Apply preprocessing to signals
- `extract_features`: Extract features from ECG data

### ML Methods
- `train_model`: Train a classification model
- `get_model_info`: Get model metadata and performance
- `predict`: Run inference on ECG data
- `explain`: Get prediction explanation

### Education Methods
- `get_lessons`: List available lessons
- `get_lesson_content`: Retrieve lesson text and examples
- `get_glossary`: Get glossary entries
- `get_quiz_questions`: Get quiz questions by category
- `submit_quiz_answer`: Check answer and get feedback
- `get_quiz_progress`: Get user's quiz statistics

## Error Codes
- `INVALID_REQUEST`: Malformed JSON or missing required fields
- `UNSUPPORTED_VERSION`: Protocol version mismatch
- `UNKNOWN_METHOD`: Method not implemented
- `INVALID_PARAMS`: Invalid or missing parameters
- `DATA_NOT_FOUND`: Requested data/model not available
- `PROCESSING_ERROR`: Error during computation
- `INTERNAL_ERROR`: Unexpected backend error

## Versioning
The protocol uses semantic versioning. Breaking changes require a new major version.
Clients and servers must check version compatibility on first connection.
