# LLM Judge System Setup Guide

This guide will help you set up the LLM-based verification system using Google's free Gemini API with Gemma 3.

## 🎯 Overview

The LLM Judge system provides automated evaluation of your agent extraction results as an alternative to manual human validation. It uses Google's free Gemini API with Gemma 3 models to evaluate the accuracy of extracted fields against the original HTML content.

### Key Features
- **Automated Evaluation**: No manual validation required
- **Free API Access**: Uses Google's free Gemini API tier
- **No Local Setup**: No need to install or run local models
- **Smart Batch Evaluation**: Evaluates agents intelligently (up to 3x fewer API calls)
  - Identical responses: 1 API call instead of 3
  - Grouped responses: Groups identical answers to minimize calls
- **Dynamic Field Descriptions**: Loads field definitions from `configs/single_project_config.json`
- **Confidence Scoring**: Each evaluation comes with a confidence score
- **Comparative Analysis**: Compare LLM vs human validation results
- **Detailed Reporting**: Comprehensive scoring reports with explanations

## 📋 Prerequisites

- Python 3.8+
- Internet connection
- Google account for API access

## 🚀 Step 1: Get Your Free Gemini API Key

1. **Visit Google AI Studio**: Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

2. **Sign in**: Use your Google account to sign in

3. **Create API Key**: 
   - Click "Create API Key"
   - Choose "Create API key in new project" or use existing project
   - Copy the generated API key

4. **Set Environment Variable**:

### Windows (PowerShell)
```powershell
# Set for current session
$env:GEMINI_API_KEY="your_api_key_here"

# Set permanently
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your_api_key_here", "User")
```

### Windows (Command Prompt)
```cmd
set GEMINI_API_KEY=your_api_key_here
```

### macOS/Linux
```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export GEMINI_API_KEY="your_api_key_here"

# Or set for current session
export GEMINI_API_KEY="your_api_key_here"
```

### Alternative: Create .env file
Create a `.env` file in the crawler_agent directory:
```
GEMINI_API_KEY=your_api_key_here
```

## 🐍 Step 2: Install Python Dependencies

```bash
cd crawler_agent

# Install LLM-specific dependencies
pip install -r requirements_llm.txt

# Or install manually
pip install google-generativeai beautifulsoup4 lxml
```

## ✅ Step 3: Test the Setup

```bash
# Test the API connection
python -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemma-2-2b-it')
response = model.generate_content('Hello')
print('✅ API working:', response.text[:50])
"
```

If this works, you'll see a response from the model.

## 🎮 Step 4: Run LLM Evaluation

### Run LLM Judge on All Projects
```bash
python llm_judge.py
```

This will:
1. Connect to Google's Gemini API
2. Check all projects with agent results
3. Skip projects already evaluated by LLM
4. Evaluate each field using the Gemma model
5. Save results to `results/llm_validation/`

### Generate LLM-Based Scoring Report
```bash
# Run LLM scoring calculator
python calculate_scores_llm.py

# Or use the main calculator with LLM flag
python calculate_scores.py --llm
```

This creates `results/scoring_report_llm.json` with LLM-based evaluations.

## 📊 Expected Output

### Directory Structure After LLM Evaluation
```
results/
├── basic/              # Agent results
├── function/
├── expert/
├── validation/         # Human validation results
├── llm_validation/     # LLM validation results
│   ├── dongi_llm_validation.json
│   ├── halalfund_llm_validation.json
│   └── ...
├── scoring_report.json     # Human-based scoring
└── scoring_report_llm.json # LLM-based scoring
```

### Sample LLM Validation Result
```json
{
  "project_name": "dongi",
  "evaluation_date": "2025-01-20T10:30:00",
  "llm_model": "gemma-2-2b-it",
  "basic_agent": {
    "correct": 6,
    "incorrect": 1,
    "average_confidence": 0.85
  },
  "field_evaluations": {
    "name": {
      "basic_value": "تامین سرمایه در گردش جهت خرید و فروش بذر ذرت",
      "evaluations": {
        "basic_correct": true,
        "basic_explanation": "Extracted project name matches HTML title",
        "basic_confidence": 0.95
      }
    }
  }
}
```

## ⚙️ Configuration Options

### Model Selection
Edit `llm_judge.py` to change the model:
```python
# Use different Gemma model
judge = GemmaLLMJudge(model_name="gemma-2-9b-it")  # Larger, more accurate
judge = GemmaLLMJudge(model_name="gemma-2-27b-it") # Largest, highest quality
```

**Available Models:**
- `gemma-2-2b-it` - 2B parameters, fastest (default)
- `gemma-2-9b-it` - 9B parameters, balanced
- `gemma-2-27b-it` - 27B parameters, highest quality

### Field Descriptions Configuration

The LLM judge automatically loads field descriptions from `configs/single_project_config.json`. This ensures the evaluation prompts match your exact field definitions.

**Config File Structure:**
```json
{
  "fields": {
    "name": {
      "type": "string",
      "description": "The title or name of the project",
      "required": true
    },
    "profit": {
      "type": "number", 
      "description": "A number between 0 and 100 representing the profit percentage",
      "required": true
    }
  }
}
```

**Focused Prompt Generation:**
- Only the specific field being evaluated is included in prompts
- Type information helps LLM understand expected data format
- Required/optional status influences evaluation strictness
- Reduces token usage and improves focus
- No need to manually update prompts when field definitions change

### Evaluation Parameters
Adjust generation parameters in `llm_judge.py`:
```python
generation_config = genai.GenerationConfig(
    max_output_tokens=1000,  # Max tokens to generate
    temperature=0.1,         # Lower = more consistent
    top_p=0.9,              # Nucleus sampling
    top_k=40                # Top-k sampling
)
```

## 🔍 Troubleshooting

### API Key Issues
```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Test API key manually
python -c "
import google.generativeai as genai
import os
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    print('✅ API key is valid')
except Exception as e:
    print('❌ API key error:', e)
"
```

### Rate Limiting
If you encounter rate limits:
- The system automatically waits 60 seconds on quota errors
- Consider using smaller models (`gemma-2-2b-it`)
- Process fewer projects at once

### Network Issues
```bash
# Test internet connection
ping google.com

# Test API endpoint
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemma-2-2b-it:generateContent?key=$GEMINI_API_KEY"
```

### Python Import Errors
```bash
# Reinstall dependencies
pip uninstall google-generativeai beautifulsoup4 lxml
pip install -r requirements_llm.txt
```

### LLM Response Parsing Issues
The system handles malformed LLM responses gracefully, but if you see many parsing errors:
1. Check your internet connection
2. Verify API key is correct
3. Try a different model (e.g., `gemma-2-9b-it`)

## 📈 Performance Tips

### Speed Optimization
- Use `gemma-2-2b-it` for fastest evaluation
- Process projects in smaller batches
- Use stable internet connection

### Quality Optimization
- Use `gemma-2-9b-it` or `gemma-2-27b-it` for better accuracy
- Lower temperature (0.1) for more consistent results
- Increase `max_output_tokens` for detailed explanations

### API Limits
- **Free Tier**: 15 requests per minute, 1 million tokens per minute
- **Rate Limiting**: System automatically handles rate limits
- **Usage Monitoring**: Check usage at [Google AI Studio](https://aistudio.google.com)

## 🔄 Workflow Integration

### Complete Evaluation Workflow
```bash
# 1. Set up API key (one time)
export GEMINI_API_KEY="your_api_key_here"

# 2. Run your agents (if not already done)
python process_single_agent.py

# 3. Run LLM evaluation
python llm_judge.py

# 4. Generate LLM scoring report
python calculate_scores.py --llm

# 5. Compare with human validation (if available)
# The comparison is automatically included in the LLM report
```

### Continuous Evaluation
For new projects:
```bash
# LLM judge will automatically skip already evaluated projects
python llm_judge.py

# Update scoring report
python calculate_scores.py --llm
```

## 📚 Understanding Results

### Accuracy Scores
- **Human Validation**: Based on manual field-by-field review
- **LLM Validation**: Based on automated LLM judgment via Google Gemini API
- **Confidence**: LLM's certainty in its evaluation (0.0-1.0)

### Result Comparison
The system automatically compares LLM vs human validation when both are available, showing:
- Accuracy differences per agent
- Agreement on best performing agent
- Overall correlation between methods

## 💰 Cost Considerations

### Free Tier Limits
- **15 requests per minute**
- **1 million tokens per minute** 
- **1,500 requests per day**

### Estimations for Your Project
- **Per Field Evaluation**: ~1 request, ~800 tokens (batch evaluation of 3 agents)
- **Per Project**: ~7 requests (7 fields), ~5,600 tokens
- **10 Projects**: ~70 requests, ~56,000 tokens
- **Daily Capacity**: Can evaluate ~200+ projects per day within free limits
- **Efficiency**: Up to 3x fewer API calls with smart optimizations:
  - All identical: 1 call instead of 3 (common when agents agree)
  - 2 identical + 1 different: 1 call instead of 3 (common scenario)  
  - All different: 1 call instead of 3 (still optimized with grouped evaluation)

### Monitoring Usage
- Check usage at [Google AI Studio](https://aistudio.google.com)
- The system includes automatic rate limiting
- Consider upgrading to paid tier for heavy usage

## 🎯 Next Steps

1. **Get your free API key** from Google AI Studio
2. **Set the environment variable** with your API key
3. **Run the LLM evaluation** on your existing projects
4. **Compare results** with human validation
5. **Analyze patterns** in LLM vs human disagreements
6. **Integrate LLM evaluation** into your regular workflow

## 💡 Tips for Best Results

1. **Stable Internet**: Ensure reliable internet connection for API calls
2. **API Key Security**: Keep your API key secure and don't commit it to version control
3. **Batch Processing**: The system handles rate limiting automatically
4. **Field Clarity**: Clear field names help the LLM understand what to evaluate
5. **Monitor Usage**: Keep track of your API usage to stay within limits

## 🆚 Why Google Gemini API vs Local Setup?

### Advantages of API Approach:
- ✅ **No Installation**: No need to download large models or install Ollama
- ✅ **No Hardware Requirements**: Works on any machine with internet
- ✅ **Always Updated**: Access to latest Gemma models
- ✅ **Free Tier**: Generous free usage limits
- ✅ **Reliable**: Google's infrastructure ensures high availability

### Considerations:
- 🌐 **Internet Required**: Need stable internet connection
- 📊 **Usage Limits**: Free tier has daily/minute limits
- 🔐 **API Key Management**: Need to secure your API key

---

For issues or questions, check the troubleshooting section above or review the error messages for specific guidance.
