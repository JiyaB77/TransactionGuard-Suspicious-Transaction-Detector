# TransactionGuard — Rule-Based Suspicious Transaction Detector

A beginner-friendly fintech dashboard written in Python, Streamlit, and Pandas.

**This is an educational rules demonstration, not a fraud prediction model.** A flagged transaction is not proof of fraud.

## Features
- Analyze a built-in synthetic transaction dataset or upload a CSV.
- Flag large transactions over a configurable threshold.
- Flag rapid transaction activity within configurable time windows per account.
- Assign a transparent rule-based score (0, 50, 100).
- Visualize flagged counts and risk-level distribution.
- Download analyzed and flagged records.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Input CSV format

Required column headings (exact names):

`transaction_id,timestamp,account_id,amount,merchant`

For example:

```csv
transaction_id,timestamp,account_id,amount,merchant
TX001,2026-10-01 09:00:00,A101,250,Cafe
TX002,2026-10-01 09:02:00,A101,750,Store
```

Use fake/demo data only when sharing screenshots or making the repository public. Avoid exposing real people's financial transaction details.

## How detection works
- **High amount:** amount >= selected threshold, adds 50 points.
- **Rapid activity:** a group of at least N transactions for the same account occurring within a rolling time window, adds 50 points to every transaction in the detected group.
- **Risk labels:** 0 = Low, 50 = Review, 100 = High.

The scores are illustrative, not statistically calibrated probabilities.

## Next improvements
- Add unit tests, transaction date filtering, and separate configuration file.
- Train and evaluate a model on a labeled public dataset (clearly separate from rules-based predictions).
