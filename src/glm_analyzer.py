import json
import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from .config import AppConfig


class GLMAnalyzer:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.api_key = os.environ.get("GLM_API_KEY", "")
        self.api_url = os.environ.get("GLM_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
        self.model = os.environ.get("GLM_MODEL", "GLM-5.1")
        self.temperature = 0.3
        self.max_tokens = 1024

    def analyze_stock(self, symbol: str, indicators: dict, session: str, current_time: str) -> Dict[str, Any]:
        prompt = self._build_prompt(symbol, indicators, session, current_time)
        response = self._call_glm(prompt)
        return self._parse_response(response, symbol)

    def _build_prompt(self, symbol: str, indicators: dict, session: str, current_time: str) -> str:
        rsi = indicators.get("rsi", 50)
        macd_bullish = indicators.get("macd_bullish", False)
        volume_ratio = indicators.get("volume_ratio", 1.0)
        trend = indicators.get("trend", "unknown")
        price = indicators.get("price", 0)
        ema_fast = indicators.get("ema_fast", 0)
        ema_slow = indicators.get("ema_slow", 0)
        bb_position = indicators.get("bb_position", "unknown")

        session_desc = "PAGI (morning session 09:00-12:00)" if session == "morning" else "SIANG/ sore (afternoon session 13:00-16:00)"

        system_prompt = """Anda adalah analis saham intraday profesional untuk pasar Indonesia (IDX).
Berdasarkan data teknikal yang diberikan, tentukan:
1. Action: BUY / SELL / HOLD
2. Jam action yang disarankan (format HH:MM WIB, harus dalam 30 menit dari sekarang)
3. Entry price (dalam Rupiah)
4. Stop Loss (dalam Rupiah, maksimal 3% dari entry)
5. Take Profit (dalam Rupiah, minimal 1.5% dari entry)
6. Confidence level (0-100)
7. Alasan singkat dalam Bahasa Indonesia

Rule:
- Jika session PAGI dan kondisi oversold/uptrend: tendensi BUY
- Jika session SIANG dan sudah profit/overbought: tendensi SELL
- Jika tidak yakin: HOLD
- SL harus realistis, TP harus achievable

Response HANYA dalam JSON format:
{
    "action": "BUY/SELL/HOLD",
    "symbol": "BBCA",
    "time": "09:30",
    "entry": 9200,
    "sl": 9026,
    "tp": 9348,
    "confidence": 85,
    "reason": "RSI oversold + MACD bullish cross"
}"""

        user_prompt = f"""Data Teknikal {symbol}:
- Current Price: Rp {price:,.0f}
- RSI(14): {rsi}
- MACD: {'Bullish' if macd_bullish else 'Bearish'}
- Volume Ratio: {volume_ratio:.1f}x average
- EMA9: Rp {ema_fast:,.0f}, EMA21: Rp {ema_slow:,.0f}
- Bollinger Position: {bb_position}
- Trend: {trend}

Waktu sekarang: {current_time} WIB
Session: {session_desc}

Tentukan action untuk intraday trading hari ini."""

        return {"system": system_prompt, "user": user_prompt}

    def _call_glm(self, prompt: dict) -> str:
        if not self.api_key:
            return self._fallback_response(prompt["user"])

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"GLM API error: {response.status_code} - {response.text}")
                return self._fallback_response(prompt["user"])

        except Exception as e:
            print(f"GLM API exception: {e}")
            return self._fallback_response(prompt["user"])

    def _fallback_response(self, user_prompt: str) -> str:
        import re

        rsi_match = re.search(r"RSI\(14\):\s*(\d+\.?\d*)", user_prompt)
        rsi = float(rsi_match.group(1)) if rsi_match else 50

        macd_match = re.search(r"MACD:\s*(Bullish|Bearish)", user_prompt)
        macd_bullish = macd_match.group(1) == "Bullish" if macd_match else False

        price_match = re.search(r"Current Price:\s*Rp\s*([\d,]+)", user_prompt)
        price = float(price_match.group(1).replace(",", "")) if price_match else 1000

        session_match = re.search(r"Session:\s*(PAGI|SIANG)", user_prompt)
        session = "morning" if session_match and "PAGI" in session_match.group(1) else "afternoon"

        if session == "morning":
            if rsi < 40 and macd_bullish:
                action = "BUY"
                sl = price * 0.98
                tp = price * 1.02
                confidence = 75
                reason = "RSI oversold + MACD bullish, potensi rebound"
            else:
                action = "HOLD"
                sl = price * 0.98
                tp = price * 1.02
                confidence = 50
                reason = "Menunggu konfirmasi entry"
        else:
            if rsi > 60 or not macd_bullish:
                action = "SELL"
                sl = price * 1.02
                tp = price * 0.98
                confidence = 70
                reason = "RSI overbought / MACD bearish, ambil profit"
            else:
                action = "HOLD"
                sl = price * 0.98
                tp = price * 1.02
                confidence = 50
                reason = "Posisi masih aman, tahan"

        now = datetime.now()
        minute = (now.minute // 15 + 1) * 15
        hour = now.hour
        if minute >= 60:
            hour += 1
            minute = 0
        action_time = f"{hour:02d}:{minute:02d}"

        symbol_match = re.search(r"Data Teknikal\s+(\w+)", user_prompt)
        symbol = symbol_match.group(1) if symbol_match else "????"

        return json.dumps({
            "action": action,
            "symbol": symbol,
            "time": action_time,
            "entry": round(price),
            "sl": round(sl),
            "tp": round(tp),
            "confidence": confidence,
            "reason": reason
        })

    def _parse_response(self, response: str, symbol: str) -> Dict[str, Any]:
        try:
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]

            data = json.loads(text)

            return {
                "action": data.get("action", "HOLD").upper(),
                "symbol": data.get("symbol", symbol),
                "time": data.get("time", "09:30"),
                "entry": float(data.get("entry", 0)),
                "sl": float(data.get("sl", 0)),
                "tp": float(data.get("tp", 0)),
                "confidence": int(data.get("confidence", 50)),
                "reason": data.get("reason", "AI analysis")
            }

        except Exception as e:
            print(f"GLM parse error: {e}")
            return {
                "action": "HOLD",
                "symbol": symbol,
                "time": "09:30",
                "entry": 0,
                "sl": 0,
                "tp": 0,
                "confidence": 0,
                "reason": "Parse error, unable to analyze"
            }

    def generate_market_summary(self, signals: list, watchlist_data: dict) -> str:
        system_prompt = """Anda adalah analis pasar saham Indonesia.
Buat ringkasan singkat (3-5 kalimat) dalam Bahasa Indonesia tentang kondisi pasar hari ini berdasarkan data yang diberikan.
Fokus pada: tren utama, saham yang menonjol, dan outlook singkat."""

        signals_text = ""
        for s in signals[:5]:
            signals_text += f"- {s.get('symbol', '???')}: {s.get('action', 'HOLD')} (confidence: {s.get('confidence', 0)}%)\n"

        user_prompt = f"""Data pasar hari ini:
{signals_text}

Buat ringkasan pasar."""

        if not self.api_key:
            return f"Ringkasan pasar hari ini: {len(signals)} sinyal terdeteksi. " + signals_text[:200]

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 300
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]

            return f"Ringkasan pasar: {len(signals)} sinyal terdeteksi hari ini."

        except Exception as e:
            return f"Ringkasan pasar: {len(signals)} sinyal terdeteksi hari ini."
