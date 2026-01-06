#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"
export USE_MOCK_OCR=false
export USE_MOCK_STORAGE=false

python main.py