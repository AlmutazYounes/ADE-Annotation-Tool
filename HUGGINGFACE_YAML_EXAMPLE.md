# Hugging Face YAML Metadata Example

This file shows an example of the YAML metadata that will be automatically generated and embedded in the README.md file when uploading datasets to Hugging Face Hub.

## Example YAML Metadata

```yaml
---
annotations_creators:
- expert-generated
language_creators:
- found
language:
- en
license: mit
multilinguality:
- monolingual
size_categories:
- n<1K  # Automatically determined based on dataset size
source_datasets:
- original
task_categories:
- token-classification
- text-classification
task_ids:
- named-entity-recognition
paperswithcode_id: null
pretty_name: Medical Annotations Dataset  # Auto-generated from dataset name
tags:
- medical
- pharmacovigilance
- adverse-drug-events
- drug-entities
- biomedical-nlp
- annotation-tool
dataset_info:
  features:
  - name: id
    dtype: int64
  - name: text
    dtype: string
  - name: drugs
    sequence: string
  - name: adverse_events
    sequence: string
  - name: is_validated
    dtype: bool
  - name: created_at
    dtype: string
  - name: updated_at
    dtype: string
  config_name: default
  data_files:
  - split: train
    path: data.jsonl
  default: true
  description: Medical text annotation dataset with 150 examples for adverse drug event detection
  download_size: null
  dataset_size: 150
configs:
- config_name: default
  data_files:
  - split: train
    path: data.jsonl
  default: true
  description: Default configuration
---
```

## Size Categories

The system automatically determines the appropriate size category:

- `n<1K`: Less than 1,000 examples
- `1K<n<10K`: 1,000 to 9,999 examples  
- `10K<n<100K`: 10,000 to 99,999 examples
- `100K<n<1M`: 100,000 to 999,999 examples
- `1M<n<10M`: 1,000,000 to 9,999,999 examples

## Features

✅ **Automatic YAML Generation**: No manual configuration needed
✅ **Proper HF Compliance**: Follows Hugging Face dataset card standards
✅ **Medical Domain Tags**: Includes relevant medical and NLP tags
✅ **Schema Definition**: Complete feature schema for the dataset
✅ **Citation Block**: Auto-generated citation information

## Files Uploaded

1. **data.jsonl** - The actual annotation data
2. **dataset_info.json** - Metadata about the dataset
3. **README.md** - Documentation with embedded YAML metadata
4. **YAML metadata** - Embedded in README for proper dataset card formatting

This ensures your dataset will be properly recognized and categorized on Hugging Face Hub!
