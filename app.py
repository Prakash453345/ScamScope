from flask import Flask, request, jsonify, render_template
import traceback
import re
from dotenv import load_dotenv
load_dotenv()

from risk_engine import analyze_message

app = Flask(__name__)

def parse_risk_score(result_text: str) -> int:
    match = re.search(r'(\d{1,3})\s*/\s*100', result_text)
    if match:
        return min(int(match.group(1)), 100)
    return -1

def get_risk_level(score: int):
    if score <= 20: return "Safe", "safe"
    elif score <= 40: return "Low Risk", "low"
    elif score <= 60: return "Moderate Risk", "moderate"
    elif score <= 80: return "High Risk", "high"
    else: return "Critical Risk", "critical"

def parse_sections(result_text: str):
    sections = {"indicators": "", "explanation": "", "safety": ""}
    lines = result_text.split("\n")
    current_section = None
    for line in lines:
        line_lower = line.strip().lower()
        if "risk indicator" in line_lower or "primary risk" in line_lower:
            current_section = "indicators"
            continue
        elif "explanation" in line_lower and current_section != "safety":
            current_section = "explanation"
            continue
        elif "safety advice" in line_lower or "safety recommendation" in line_lower:
            current_section = "safety"
            continue
        elif "risk score" in line_lower:
            continue
        if current_section and line.strip():
            sections[current_section] += line + "\n"
    return sections

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    user_text = data.get('text', '')
    
    if not user_text.strip():
        return jsonify({"error": "No text provided"}), 400
        
    try:
        result = analyze_message(user_text)
        score = parse_risk_score(result)
        sections = parse_sections(result)
        
        if score < 0: score = 50
        level_label, level_class = get_risk_level(score)
        
        return jsonify({
            "score": score,
            "level_label": level_label,
            "level_class": level_class,
            "indicators": sections["indicators"],
            "explanation": sections["explanation"],
            "safety": sections["safety"]
        })
    except Exception as e:
        error_msg = str(e)
        if any(kw in error_msg.lower() for kw in ["resource_exhausted", "quota", "429", "rate limit"]):
            return jsonify({"error": "API rate limit reached. Please wait and retry."}), 429
        return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
