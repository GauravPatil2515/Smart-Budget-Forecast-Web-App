import os, json, re, httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Req(BaseModel):
    data: str

def parse_budget(text):
    pairs = re.findall(r'(\w[\w\s]*?)\s*[:=]\s*\$?([\d,.]+)', text, re.IGNORECASE)
    items = {}
    for k, v in pairs:
        try:
            items[k.strip().lower()] = float(v.replace(',', ''))
        except:
            pass
    return items

def local_forecast(text):
    items = parse_budget(text)
    if not items:
        return "Please enter budget data like: income: 5000, rent: 1500, food: 600, transport: 200, entertainment: 300"
    income_keys = {"income", "salary", "earnings", "pay", "wage", "revenue"}
    income = sum(v for k, v in items.items() if k in income_keys)
    expenses = {k: v for k, v in items.items() if k not in income_keys}
    total_exp = sum(expenses.values())
    if income == 0:
        income = total_exp * 1.2
    savings = income - total_exp
    rate = (savings / income * 100) if income > 0 else 0
    lines = ["--- SMART BUDGET FORECAST ---", f"\nMonthly Income: ${income:,.2f}", f"Total Expenses: ${total_exp:,.2f}", f"Monthly Savings: ${savings:,.2f}", f"Savings Rate: {rate:.1f}%"]
    lines.append("\n-- Expense Breakdown --")
    for k, v in sorted(expenses.items(), key=lambda x: -x[1]):
        pct = (v / total_exp * 100) if total_exp > 0 else 0
        lines.append(f"  {k.title()}: ${v:,.2f} ({pct:.1f}%)")
    lines.append("\n-- 6-Month Forecast --")
    growth = 1.03
    for m in range(1, 7):
        proj_exp = total_exp * (growth ** m)
        proj_sav = income - proj_exp
        lines.append(f"  Month {m}: Expenses ${proj_exp:,.2f} | Savings ${proj_sav:,.2f}")
    lines.append("\n-- Annual Projection --")
    annual_savings = sum(income - total_exp * (growth ** m) for m in range(1, 13))
    lines.append(f"  Projected Annual Savings: ${annual_savings:,.2f}")
    lines.append("\n-- Financial Risk Analysis --")
    risks = []
    if rate < 10:
        risks.append("LOW SAVINGS RATE: Below recommended 20%. Consider cutting discretionary spending.")
    if rate < 0:
        risks.append("DEFICIT SPENDING: You are spending more than you earn. Immediate action needed.")
    top = max(expenses.items(), key=lambda x: x[1]) if expenses else None
    if top and total_exp > 0 and (top[1] / total_exp) > 0.4:
        risks.append(f"CONCENTRATION RISK: {top[0].title()} is {top[1]/total_exp*100:.0f}% of budget. Diversify expenses.")
    if total_exp * (growth ** 6) > income:
        risks.append("TREND WARNING: At 3% monthly growth, expenses will exceed income within 6 months.")
    emergency = savings * 6
    lines.append(f"\n-- Emergency Fund Target: ${max(0,total_exp*3):,.2f} (3 months) --")
    if not risks:
        risks.append("No major risks detected. Budget appears healthy.")
    for r in risks:
        lines.append(f"  * {r}")
    lines.append(f"\n-- Tips --")
    if savings > 0:
        lines.append(f"  Invest ${savings*0.5:,.2f}/month (50% of savings) for long-term growth.")
        lines.append(f"  Keep ${savings*0.3:,.2f}/month (30%) as emergency fund.")
    else:
        lines.append("  Reduce top expense category by 15% to regain positive savings.")
    return "\n".join(lines)

async def ai_forecast(text):
    prompt = f"You are a financial advisor AI. Analyze this budget data and provide: 1) Expense breakdown 2) 6-month forecast with projected expenses and savings 3) Financial risk analysis 4) Actionable tips. Be specific with numbers.\n\nBudget data: {text}"
    for provider, key_name, url, payload_fn in [
        ("groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions",
         lambda k: ({"Authorization": f"Bearer {k}", "Content-Type": "application/json"}, {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024, "temperature": 0.7})),
        ("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions",
         lambda k: ({"Authorization": f"Bearer {k}", "Content-Type": "application/json"}, {"model": "meta-llama/llama-3.3-70b-instruct", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024})),
        ("huggingface", "HUGGINGFACE_API_KEY", "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3/v1/chat/completions",
         lambda k: ({"Authorization": f"Bearer {k}", "Content-Type": "application/json"}, {"model": "mistralai/Mistral-7B-Instruct-v0.3", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024})),
    ]:
        key = os.environ.get(key_name)
        if not key:
            continue
        try:
            headers, body = payload_fn(key)
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(url, headers=headers, json=body)
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
        except:
            continue
    return None

@app.post("/solve")
async def solve(req: Req):
    text = (req.data or "").strip()
    if not text:
        return JSONResponse({"output": "Please enter your budget data.\n\nExample: income: 5000, rent: 1500, food: 600, transport: 200, entertainment: 300"})
    try:
        result = await ai_forecast(text)
        if result:
            return JSONResponse({"output": result})
    except:
        pass
    return JSONResponse({"output": local_forecast(text)})

@app.get("/")
async def index():
    with open("index.html") as f:
        return HTMLResponse(f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
