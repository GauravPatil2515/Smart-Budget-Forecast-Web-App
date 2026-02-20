# Smart Budget Forecast Web App

AI-powered expense prediction, savings trends & financial risk analysis.

## Demo

[Live Demo](https://smart-budget-forecast.onrender.com)

## Deploy on Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Settings:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (optional, see below)
6. Click Deploy

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | No | Groq API key for AI forecasting |
| `OPENROUTER_API_KEY` | No | OpenRouter API key |
| `HUGGINGFACE_API_KEY` | No | HuggingFace Inference API key |

If no API key is set, the app uses built-in deterministic forecasting.

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:8000

## Usage

Enter budget data like:

```
income: 5000, rent: 1500, food: 600, transport: 200, entertainment: 300
```

Click **Analyze Budget** to get expense breakdown, 6-month forecast, risk analysis, and tips.
