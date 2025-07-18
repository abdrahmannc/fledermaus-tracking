# Fledermaus Tracking API Documentation

## Overview

The Fledermaus Tracking API provides robust video analysis for bat detection and tracking. The system is designed with comprehensive error handling to prevent division by zero errors and handle edge cases gracefully.

## Features

### Division by Zero Protection
- **Safe FPS Handling**: Automatically uses fallback FPS (30.0) when video FPS is 0, negative, or invalid
- **Robust Contour Processing**: Handles zero-area contours and invalid moments gracefully
- **Mathematical Safety**: All calculations use safe division to prevent crashes
- **Video Validation**: Comprehensive checks for video integrity before processing

### Error Handling
- **Graceful Degradation**: System continues processing even when encountering errors
- **Comprehensive Logging**: Detailed error messages for debugging
- **Fallback Mechanisms**: Default values for missing or invalid data
- **User-Friendly Messages**: Clear error reporting to frontend

## API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{
  "message": "Fledermaus Tracking API",
  "status": "healthy",
  "version": "1.0.0"
}
```

### `GET /health`
Detailed health check with system status.

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "api": true,
    "config": true,
    "upload_dir": true,
    "detector": true
  },
  "timestamp": 1234567890
}
```

### `POST /analyze`
Analyze video for bat detection.

**Parameters:**
- `file`: Video file (multipart/form-data)
- `start_time`: Start time in seconds (optional, default: 0)
- `end_time`: End time in seconds (optional, default: full video)
- `upload_sensitivity`: Detection sensitivity (optional, default: 1.0)

**Response:**
```json
{
  "success": true,
  "message": "Analysis completed successfully",
  "data": {
    "totalFrames": 1000,
    "batDetected": true,
    "detectionCount": 42,
    "startPoint": {"x": 10.5, "y": 20.3},
    "endPoint": {"x": 80.2, "y": 90.1},
    "analysisTime": "01:23",
    "fps": 30.0,
    "videoDuration": 33.33,
    "positions": [
      {
        "frame": 1,
        "x": 10.5,
        "y": 20.3,
        "width": 15.0,
        "height": 30.0,
        "timestamp": "00:00:01"
      }
    ],
    "movementsPerFrame": [
      {"frame": 1, "count": 1}
    ]
  },
  "errors": null
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error description",
  "errors": ["Detailed error messages"]
}
```

## Configuration

### Environment Variables
- `FLEDERMAUS_HOST`: Server host (default: "0.0.0.0")
- `FLEDERMAUS_PORT`: Server port (default: 8000)
- `FLEDERMAUS_DEBUG`: Debug mode (default: False)
- `FLEDERMAUS_LOG_LEVEL`: Logging level (default: "INFO")
- `FLEDERMAUS_DEFAULT_FPS`: Default FPS fallback (default: 30.0)
- `FLEDERMAUS_MAX_FILE_SIZE`: Maximum upload size (default: 100MB)

### Video Processing Parameters
- **Default FPS**: 30.0 (used when video FPS is invalid)
- **Min/Max FPS**: 1.0 - 120.0
- **Min/Max Contour Area**: 50.0 - 10,000.0 pixels
- **Background Subtraction Threshold**: 16.0
- **Max Processing Errors**: 10 (before stopping)

## Division by Zero Protection Details

### 1. FPS Handling
```python
# Automatically handles:
- fps = 0 → uses default_fps (30.0)
- fps < 0 → uses default_fps (30.0)  
- fps > max_fps → uses default_fps (30.0)
- invalid fps → uses default_fps (30.0)
```

### 2. Contour Moments
```python
# Safely handles:
- m00 = 0 → returns center (0, 0)
- m00 < 1e-10 → returns center (0, 0)
- missing moments → returns center (0, 0)
```

### 3. Safe Mathematical Operations
```python
# All divisions use safe_divide():
- denominator = 0 → returns default value
- denominator < min_threshold → returns default value
- mathematical errors → returns default value with logging
```

## Usage Example

### Starting the Server
```bash
python main.py
```

### Analyzing a Video
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@video.mp4" \
  -F "start_time=0" \
  -F "end_time=30" \
  -F "upload_sensitivity=1.0"
```

### With Python Requests
```python
import requests

with open('video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/analyze',
        files={'file': f},
        data={
            'start_time': 0,
            'end_time': 30,
            'upload_sensitivity': 1.0
        }
    )
    
result = response.json()
print(f"Detected {result['data']['detectionCount']} bats")
```

## Testing

The repository includes comprehensive tests for division by zero protection:

- `test_division_protection.py`: Basic safe math function tests
- `test_comprehensive_protection.py`: Complete pipeline testing

Run tests:
```bash
python test_division_protection.py
python test_comprehensive_protection.py
```

## Supported Video Formats

- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)

## Error Recovery

The system includes multiple layers of error recovery:

1. **Input Validation**: File type, size, and format validation
2. **Video Property Validation**: FPS, dimensions, frame count
3. **Processing Error Handling**: Continue processing despite frame errors
4. **Mathematical Safety**: Safe division and range validation
5. **Graceful Degradation**: Meaningful defaults when data is missing

## Logging

Comprehensive logging includes:
- Video processing status
- Division by zero warnings
- Error recovery actions
- Performance metrics
- Debug information

Logs are written to both console and file (configurable).