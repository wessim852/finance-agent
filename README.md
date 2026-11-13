# CrewAI Trading Advisor

A multi-agent stock research assistant that combines market sentiment with financial fundamentals to produce a short-term trading hypothesis and a final **Go / No-Go** risk assessment.

Built with **CrewAI**, **Google Gemini 2.5 Flash**, **Yahoo Finance via yfinance**, and **Serper web search**.

## Table of Contents

- [Overview](#overview)
- [Agent Workflow](#agent-workflow)
- [Financial Data](#financial-data)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Output](#output)
- [Project Structure](#project-structure)
- [Limitations](#limitations)

## Overview

Enter a stock ticker to run a sequential research workflow that:

1. Searches for recent news and social sentiment.
2. Retrieves financial metrics to assess the stock's valuation and financial health.
3. Develops a trading hypothesis for a **1–5 day** horizon.
4. Reviews the hypothesis against an assumed **$10,000 paper portfolio** and proposes position sizing, stop-loss, and take-profit levels.

The application prints the final report in the terminal. It does not connect to a brokerage or place orders.

## Agent Workflow

| Agent | Role | Tools / Context |
| --- | --- | --- |
| **The Ears** | Searches for news, market chatter, catalysts, hype, and FOMO. | `SerperDevTool` |
| **The Brain** | Evaluates financial health and valuation. | Custom `yfinance_tool`; sentiment report |
| **The Tactician** | Combines sentiment and fundamentals into a trading thesis with entry and target prices. | Sentiment and fundamentals reports |
| **The Brakes** | Assesses risk and proposes a Go / No-Go verdict, position size, and exit levels. | Trading hypothesis |

CrewAI runs these tasks using `Process.sequential`, with each task receiving the context configured in `main.py`. All four agents use Gemini 2.5 Flash.

## Financial Data

The custom `yfinance_tool` requests the following metrics when available:

| Metric | Source field / fallback |
| --- | --- |
| Current price | `currentPrice`, then `regularMarketPrice`, then `navPrice` |
| P/E ratio | `forwardPE`, falling back to `trailingPE` |
| 52-week range | `fiftyTwoWeekLow`, `fiftyTwoWeekHigh` |
| Market capitalization | `marketCap` |
| Revenue growth | `revenueGrowth` |
| EBITDA | `ebitda` |
| Profit margins | `profitMargins` |
| Debt-to-equity ratio | `debtToEquity` |

Missing values are omitted. The tool returns a text message if data is unavailable or retrieval fails.

### Installation

Clone the repository and open its directory, then create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```dotenv
GOOGLE_API_KEY=your_google_api_key
SERPER_API_KEY=your_serper_api_key
```

`python-dotenv` loads these variables when the application starts. Keep real credentials out of commits and shared terminal logs.

## Usage

Run the application from the project root:

```bash
python main.py
```

Enter a ticker when prompted:

```text
Enter the stock ticker you want to analyze (e.g., TSLA, NVDA, GME): NVDA
```

The application converts the input to uppercase, runs the crew with verbose logging, and prints the result beneath `FINAL RISK REPORT`.

You can also call the workflow from Python:

```python
from main import run_trading_simulator

report = run_trading_simulator("NVDA")
print(report)
```

Importing `main` initializes the model, tools, and agents, so configure the environment first.

## Output

The risk manager is prompted to produce a report containing:

- **Verdict:** Go or No-Go.
- **Position size:** USD allocation and number of shares.
- **Stop-loss:** Proposed exit price to limit losses.
- **Take-profit:** Proposed target price.
- **Risk/reward ratio:** Expected downside relative to upside.
- **Reasoning:** Supporting rationale and risks that could invalidate the trade.

## Limitations

- **Research prototype:** The workflow generates analysis; it does not simulate portfolio performance, strategies, or execute trades.
- **Search-based sentiment:** Social sentiment comes from web search results, with no dedicated Reddit or social media API integration.
- **Data availability:** Financial fields may be missing or delayed. The tool does not fetch historical price series or historical valuation averages.
- **Model-generated risk calculations:** Position sizing and exit levels are proposed by the model, without deterministic calculation or validation in code.
- **Reproducibility:** Dependencies are unpinned, and external data and model responses can change between runs.
- **External services:** Runs depend on API availability, credentials, and usage limits, and may incur provider charges.

This project is intended for educational research
