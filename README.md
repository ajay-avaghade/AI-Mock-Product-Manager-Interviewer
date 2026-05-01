Live public link: https://huggingface.co/spaces/ajay-avaghade/AI-Mock-Product-Manager-Interviewer

# AI-Mock-Product-Manager-Interviewer
A sleek, real-time voice conversational web application designed to help Product Managers practice "Product Sense" interviews.  Built with **Gradio**, **Groq (Llama 3 &amp; Whisper)**, and **Edge-TTS**, this application provides a highly responsive, zero-cost (via Groq's free tier), back-and-forth mock interview experience.

## ✨ Features

- **Real-Time Voice Conversation:** Speak into your microphone and receive instant audio responses from the AI interviewer.
- **Dynamic Case Studies:** Every interview is unique! The app uses an LLM agent to dynamically generate complex, modern PM questions.
- **Strict Interview Persona:** The AI is instructed to ask probing questions, push back on assumptions, and guide you through the Product Sense framework (Motivation, Segmentation, Problem Identification, Solution Development).
- **Automated Scorecard:** Once the interview ends, the LLM evaluates your entire transcript against a summarized Product Sense rubric and provides structured feedback.
- **History Tracking & Downloads:** Instantly download your full transcript and markdown scorecard for your own records and track progress over time.

## 🛠️ Architecture

- **UI:** Gradio (with Monochrome Theme)
- **STT (Speech-to-Text):** Groq `whisper-large-v3`
- **LLM:** Groq `llama-3.3-70b-versatile` (Conversation) & `llama-3.1-8b-instant` (Case Study Generation & Scorecard Evaluation)
- **TTS (Text-to-Speech):** `edge-tts` (Voice: `en-US-ChristopherNeural`)
- **Audio Processing:** `static-ffmpeg` (for browser `.webm` encoding)

## 🚀 Setup & Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/Mock-Interviewer.git
   cd Mock-Interviewer
   ```
2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```
3. **Get a Groq API Key:**
   Get a free API key from the [Groq Console](https://console.groq.com/keys).
4. **Run the App:**

   ```bash
   python3 app.py
   ```

   Open `http://127.0.0.1:7860` in your browser. Paste your Groq API key into the Settings box and start practicing!

## 📝 Folder Structure

- `app.py`: Core application logic.
- `Product_Sense_Guide_Summary.md`: The rubric the AI uses to grade you.
- `history/`: Automatically created directory where your past transcripts and scorecards are saved.
