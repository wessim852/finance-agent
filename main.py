import os
from dotenv import load_dotenv
import yfinance as yf
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from crewai_tools import SerperDevTool

# 1. Imports & Setup
# Load environment variables (GOOGLE_API_KEY, SERPER_API_KEY)
load_dotenv()

# Configure LLM: Gemini 2.5 Flash
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    verbose=True,
    temperature=0.5,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# 2. Custom Tools Definition

@tool("yfinance_tool")
def yfinance_tool(ticker: str):
    """
    Fetch fundamental financial data for a given stock ticker using Yahoo Finance.
    Includes current price, forward P/E, and 52-week high/low.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            return f"No financial data found for {ticker}. Ensure the ticker is correct."

        # Extracting key metrics with fallbacks
        data = {
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice"),
            "forward_pe": info.get("forwardPE") or info.get("trailingPE"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "market_cap": info.get("marketCap"),
            "revenue_growth": info.get("revenueGrowth"),
            "ebitda": info.get("ebitda"),
            "profit_margins": info.get("profitMargins"),
            "debt_to_equity": info.get("debtToEquity")
        }
        
        # Clean up None values
        data = {k: v for k, v in data.items() if v is not None}
        
        if not data:
            return f"Could not extract meaningful financial data for {ticker}."

        return f"Financial Data for {ticker}: {data}"
    except Exception as e:
        return f"Error fetching data for {ticker}: {e}"

# Placeholder/SerperDevTool for Sentiment Scraper
# Assuming SERPER_API_KEY is in .env for SerperDevTool to work
search_tool = SerperDevTool()

# 3. Agent Instantiation

# Agent 1: The Ears (Sentiment Scraper)
sentiment_scraper = Agent(
    role='Social Sentiment Analyst',
    goal='Search for breaking financial news and social chatter regarding {ticker} to gauge public sentiment.',
    backstory="""Known as 'The Ears', you are an expert at sniffing out market-moving sentiment 
    before it hits the mainstream. You scan social media, Reddit (r/WallStreetBets), 
    and financial news to identify if public sentiment is Positive, Negative, Panic, or Hype. 
    You excel at distinguishing between genuine interest and artificial 'pumping'.""",
    tools=[search_tool],
    llm=llm,
    verbose=True
)

# Agent 2: The Brain (Fundamentals Analyst)
fundamentals_analyst = Agent(
    role='Senior Financial Data Analyst',
    goal='Pull live market data, P/E ratios, and performance metrics for {ticker} to verify if the hype is backed by reality.',
    backstory="""You are 'The Brain'. You don't care about tweets or hype; you care about the numbers. 
    You analyze balance sheets, P/E ratios, and revenue growth. Your job is to verify if the 
    current price movement of a stock is justified by its financial health or if it's purely speculative.""",
    tools=[yfinance_tool],
    llm=llm,
    verbose=True
)

# Agent 3: The Tactician (Trading Strategist)
trading_strategist = Agent(
    role='Quantitative Trading Strategist',
    goal='Analyze sentiment (hype) and fundamentals to formulate a short-term trading hypothesis for {ticker}.',
    backstory="""As 'The Tactician', you bridge the gap between sentiment and reality. 
    You take the 'chatter' from the Scraper and the 'facts' from the Analyst to build a high-probability 
    trading thesis. You decide if we should play the momentum or wait for a mean reversion.""",
    llm=llm,
    verbose=True
)

# Agent 4: The Brakes (Risk Manager)
risk_manager = Agent(
    role='Chief Risk Officer',
    goal='Review the trading hypothesis, calculate position sizing, set stop-losses, and output a final Go/No-Go report.',
    backstory="""You are 'The Brakes'. Your mission is to protect the firm's capital. 
    You evaluate the downside of every trade. You assume a $10,000 paper portfolio and must 
    calculate precise position sizing and risk-to-reward ratios. You provide the final 
    structured JSON verdict: Go or No-Go.""",
    llm=llm,
    verbose=True
)

# 4. Task Definition

sentiment_task = Task(
    description="""Search for the latest social media chatter, Reddit posts, and news articles for {ticker}. 
    Identify the prevailing sentiment (Bullish/Bearish) and any specific catalysts mentioned. 
    Summarize the 'Hype Level' and identify if there is any 'Fear Of Missing Out' (FOMO) present.""",
    expected_output="A detailed summary of the current social sentiment and news sentiment for the ticker.",
    agent=sentiment_scraper
)

fundamentals_task = Task(
    description="""Fetch the current financial metrics for {ticker} using the yfinance tool. 
    Specifically look for Current Price, Forward P/E, 52-Week High/Low, and Market Cap. 
    Compare these metrics to historical averages if possible to see if the stock is overvalued or undervalued.""",
    expected_output="A technical report on the stock's financial health and valuation metrics.",
    agent=fundamentals_analyst,
    context=[sentiment_task]
)

strategist_task = Task(
    description="""Review the sentiment analysis and the financial fundamentals for {ticker}. 
    Formulate a short-term trading strategy (1-5 days). Explain the 'Why' behind the trade. 
    Is it a momentum play based on hype, or a value play based on fundamentals? 
    Define the entry price range.""",
    expected_output="A detailed trading hypothesis including entry price, target price, and the rationale.",
    agent=trading_strategist,
    context=[sentiment_task, fundamentals_task]
)

risk_task = Task(
    description="""Analyze the trading strategist's hypothesis for {ticker}. 
    Assume a starting portfolio of $10,000. Calculate the position size (how many shares), 
    the stop-loss price, and the take-profit level. 
    Identify the key risks that could invalidate the trade. 
    Finally, provide a structured 'Go/No-Go' recommendation in JSON format.""",
    expected_output="""A final risk assessment report including:
    - Verdict: (Go/No-Go)
    - Position Size: (USD and Shares)
    - Stop-Loss: (Price)
    - Take-Profit: (Price)
    - Risk/Reward Ratio: (e.g., 1:3)
    - Reasoning: (Summary)""",
    agent=risk_manager,
    context=[strategist_task]
)

# 5. Crew Execution

def run_trading_simulator(ticker):
    # Assemble the Crew
    trading_crew = Crew(
        agents=[sentiment_scraper, fundamentals_analyst, trading_strategist, risk_manager],
        tasks=[sentiment_task, fundamentals_task, strategist_task, risk_task],
        process=Process.sequential,
        verbose=True
    )

    # Execute the workflow
    print(f"\n--- Starting Multi-Agent Sentiment Arbitrage Simulator for: {ticker} ---\n")
    result = trading_crew.kickoff(inputs={'ticker': ticker})
    return result

if __name__ == "__main__":
    target_ticker = input("Enter the stock ticker you want to analyze (e.g., TSLA, NVDA, GME): ").upper()
    if target_ticker:
        final_report = run_trading_simulator(target_ticker)
        print("\n\n########################")
        print("## FINAL RISK REPORT ##")
        print("########################\n")
        print(final_report)
    else:
        print("Invalid ticker provided.")
