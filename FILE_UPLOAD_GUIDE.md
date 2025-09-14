# File Upload Feature Guide

This guide explains how to use the new file upload feature in the Agentic AI Carbon Ranker application.

## Overview

The file upload feature allows users to upload their own vendor data files directly through the web interface, which are then processed by the same agentic system that handles the predefined data.

## Features

### ✅ **Supported File Formats**
- **CSV** (.csv) - Comma-separated values
- **JSON** (.json) - JavaScript Object Notation
- **Excel** (.xlsx, .xls) - Microsoft Excel files

### ✅ **File Validation**
- Maximum file size: 10MB
- Required columns validation
- File format validation
- Data type validation

### ✅ **Processing Options**
- Automatic processing after upload
- Overwrite existing data option
- Real-time progress tracking
- Detailed success/error reporting

## How to Use

### 1. **Access the Upload Feature**
- Click the "📁 Upload Data" button in the top-right corner of the dashboard
- The upload modal will open

### 2. **Download Sample Template** (Optional)
- Click "📥 Download Sample Template" to get a sample CSV file
- Use this as a reference for the expected data format

### 3. **Select Your File**
- Click "Upload a file" or drag and drop your file
- The system will auto-detect the file format
- File information will be displayed

### 4. **Configure Options**
- **Data Format**: Select CSV, JSON, or Excel (auto-detected)
- **Auto Process**: Automatically process data after upload (recommended)
- **Overwrite Existing**: Replace existing data for the same companies

### 5. **Upload and Process**
- Click "Upload & Process"
- Watch the progress bar
- View results and any warnings

## Data Format Requirements

### **Required Columns**
Your data file must contain these columns:

| Column | Description | Example |
|--------|-------------|---------|
| `company` | Company name | "GreenCompute-Inc" |
| `month` | Month in YYYY-MM format | "2024-01" |
| `region` | Geographic region | "US-CA" |

### **Optional Columns**
These columns are optional but recommended for better analysis:

| Column | Description | Example |
|--------|-------------|---------|
| `gpu_hours` | GPU hours used | 1200 |
| `energy` | Energy consumption (kWh) | 480 |
| `tokens` | Number of tokens processed | 1500000 |
| `api_calls` | Number of API calls | 25000 |
| `pue` | Power Usage Effectiveness | 1.2 |
| `utilization` | GPU utilization percentage | 85 |

### **Sample Data Format**

#### CSV Format:
```csv
company,month,region,gpu_hours,energy,tokens,api_calls,pue,utilization
GreenCompute-Inc,2024-01,US-CA,1200,480,1500000,25000,1.2,85
CloudAI-Pro,2024-01,EU-DE,2000,800,2800000,45000,1.3,78
```

#### JSON Format:
```json
[
  {
    "company": "GreenCompute-Inc",
    "month": "2024-01",
    "region": "US-CA",
    "gpu_hours": 1200,
    "energy": 480,
    "tokens": 1500000,
    "api_calls": 25000,
    "pue": 1.2,
    "utilization": 85
  }
]
```

## Processing Flow

### 1. **File Validation**
- File size check (≤10MB)
- File format validation
- Required columns check
- Data type validation

### 2. **Data Ingestion**
- Parse file based on format
- Validate each row
- Check for existing records
- Store in `raw_ingest` table

### 3. **Agentic Processing** (if auto-process enabled)
- **Planner**: Detect data quality issues
- **Executor**: Normalize and calculate metrics
- **Critic**: Validate results and retry if needed
- Generate rankings and rollups

### 4. **Results Display**
- Records processed count
- Companies added count
- Processing time
- Warnings and errors

## Error Handling

### **Common Errors**

| Error | Cause | Solution |
|-------|-------|----------|
| "File size exceeds 10MB limit" | File too large | Reduce file size or split into multiple files |
| "Unsupported file type" | Wrong file format | Use CSV, JSON, or Excel format |
| "Missing required columns" | Missing company, month, or region | Add required columns to your file |
| "Error parsing file" | Invalid file structure | Check file format and encoding |

### **Warnings**
- Duplicate records (when overwrite is disabled)
- Missing optional data
- Data quality issues
- Processing failures

## API Endpoint

The upload functionality is available via REST API:

```bash
POST /api/upload
Content-Type: multipart/form-data

Parameters:
- file: The data file to upload
- format: Data format (csv, json, excel)
- auto_process: Whether to auto-process (true/false)
- overwrite_existing: Whether to overwrite existing data (true/false)
```

### **Example API Usage**

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@vendor_data.csv" \
  -F "format=csv" \
  -F "auto_process=true" \
  -F "overwrite_existing=false"
```

## Best Practices

### **Data Preparation**
1. **Use consistent formats**: Stick to one data format across all files
2. **Validate data quality**: Check for missing values and outliers
3. **Use standard regions**: Use consistent region codes (e.g., "US-CA", "EU-DE")
4. **Include metadata**: Add as much optional data as possible for better analysis

### **File Organization**
1. **One file per upload**: Upload one file at a time for better error tracking
2. **Reasonable file sizes**: Keep files under 10MB for faster processing
3. **Clear naming**: Use descriptive filenames (e.g., "vendor_data_2024_01.csv")

### **Processing Strategy**
1. **Enable auto-processing**: Let the system process data automatically
2. **Review warnings**: Check warnings for data quality issues
3. **Verify results**: Check the leaderboard after upload to ensure data is correct

## Troubleshooting

### **Upload Fails**
1. Check file format and size
2. Verify required columns are present
3. Check browser console for errors
4. Try uploading a smaller file first

### **Processing Errors**
1. Check the processing status modal
2. Review warnings in upload results
3. Verify data quality in your source file
4. Try uploading with overwrite enabled

### **Data Not Appearing**
1. Check if auto-processing was enabled
2. Verify the data was processed successfully
3. Check for duplicate records
4. Refresh the dashboard

## Security Considerations

- Files are processed in memory and not stored permanently
- File size limits prevent resource exhaustion
- Input validation prevents malicious data injection
- All processing is done server-side for security

## Performance Notes

- Large files may take longer to process
- Auto-processing adds time but provides immediate results
- The system can handle multiple concurrent uploads
- Processing time scales with data complexity

## Future Enhancements

- **Batch upload**: Upload multiple files at once
- **Data preview**: Preview data before processing
- **Advanced validation**: More sophisticated data validation rules
- **Progress tracking**: Real-time processing progress
- **Data mapping**: Custom column mapping for different formats
