import gradio as gr
import asyncio
import os
import time
import datetime
import static_ffmpeg
static_ffmpeg.add_paths()
from groq import AsyncGroq
import edge_tts

# We will initialize the AsyncGroq client dynamically inside the functions

INTERVIEWER_SYSTEM_PROMPT = """You are a strict Senior PM Interviewer conducting a Product Sense interview.
This is a real-time conversational roleplay. Act like a real human interviewer.
- Ask ONE question at a time and WAIT for the candidate to respond. 
- Do NOT give them the answers or monologue. Ask probing questions based on their previous response.
- Guide them through the Product Sense framework (Motivation, Segmentation, Problem Identification, Solution) step-by-step.
- If they jump straight to brainstorming features without clarifying the goal or target user, verbally push back.
- Keep your responses extremely short, concise, and conversational (1-3 sentences max).
- Do NOT output any formatting, markdown, or emojis. Only plain text that will be read aloud by TTS."""

async def start_interview(api_key):
    if not api_key:
        return "Error: Please provide a Groq API Key.", [], [[None, "Error: Missing API Key"]], None
        
    client = AsyncGroq(api_key=api_key)
    
    try:
        # Dynamically generate a fresh, interesting PM case study question
        prompt = "Generate a single, complex Product Management 'Product Sense' interview question. It should be about designing a new feature, app, or physical product for a specific demographic or company (e.g. Meta, Spotify, etc). Output ONLY the question text, nothing else."
        chat_completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.9
        )
        question = chat_completion.choices[0].message.content.strip().replace('"', '')
    except Exception as e:
        question = f"Design a smart refrigerator for a busy family of five. (Error fetching dynamic question: {e})"
        
    transcript_state = [("model", f"Welcome. Today's question is: {question}. How would you approach this?")]
    chatbot_ui = [[None, f"Welcome. Today's question is: {question}. How would you approach this?"]]
    
    # Generate initial audio via edge-tts
    initial_audio_path = "output_initial.mp3"
    communicate = edge_tts.Communicate(f"Welcome. Today's question is: {question}. How would you approach this?", "en-US-ChristopherNeural")
    await communicate.save(initial_audio_path)
    
    # Clear the download outputs on new interview
    return question, transcript_state, chatbot_ui, initial_audio_path, gr.update(value=None)

async def process_audio(audio_path, transcript_state, chatbot_ui, api_key):
    if not api_key:
        chatbot_ui.append([None, "Error: Please provide a Groq API Key."])
        return None, transcript_state, chatbot_ui, gr.update()
    if not audio_path:
        return None, transcript_state, chatbot_ui, gr.update()

    client = AsyncGroq(api_key=api_key)
    try:
        # 1. Transcribe audio via Groq Whisper
        with open(audio_path, "rb") as file:
            transcription = await client.audio.transcriptions.create(
                file=(audio_path, file.read()),
                model="whisper-large-v3",
            )
        user_text = transcription.text
        
        transcript_state.append(("user", user_text))
        chatbot_ui.append([user_text, None])
        
        # 2. Get LLM response via Groq Llama 3
        messages = [{"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT}]
        for role, text in transcript_state:
            messages.append({"role": "assistant" if role == "model" else "user", "content": text})
            
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=256
        )
        
        ai_response = chat_completion.choices[0].message.content
        transcript_state.append(("model", ai_response))
        chatbot_ui[-1][1] = ai_response
        
        # 3. Generate Audio response via edge-tts
        output_audio_path = "output_turn.mp3"
        communicate = edge_tts.Communicate(ai_response, "en-US-ChristopherNeural")
        await communicate.save(output_audio_path)
        
        return output_audio_path, transcript_state, chatbot_ui, gr.update(value=None)
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        chatbot_ui.append([None, f"Error: {str(e)}"])
        return None, transcript_state, chatbot_ui, gr.update(value=None)

async def end_interview(transcript_state, api_key):
    if not api_key:
        return "Error: Please provide a Groq API Key.", None
        
    client = AsyncGroq(api_key=api_key)
    try:
        # Read the summarized guide to save tokens
        with open("Product_Sense_Guide_Summary.md", "r") as f:
            guide_content = f.read()
            
        transcript_text = "\n".join([f"{role}: {text}" for role, text in transcript_state])
        
        # Create history directory
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        history_dir = os.path.join("history", timestamp)
        os.makedirs(history_dir, exist_ok=True)
        
        transcript_path = os.path.join(history_dir, "transcript.txt")
        scorecard_path = os.path.join(history_dir, "scorecard.md")
        
        # Save transcript
        with open(transcript_path, "w") as f:
            f.write("=== YOUR INTERVIEW TRANSCRIPT ===\n\n")
            f.write(transcript_text)
        
        prompt = f"""You are an expert Product Management Interview Reviewer.
        
Here is the Product Sense Guide Summary outlining the core philosophy:
{guide_content}

Here is the transcript of the interview that just concluded:
{transcript_text}

Generate a final, comprehensive text-based markdown scorecard evaluating the candidate based on the Product Sense Guide.
Evaluate across: Motivation, Segmentation, Problem identification, Solution development.
Provide constructive feedback and a final score (Hire / No Hire / Lean Hire).
"""
        messages = [{"role": "user", "content": prompt}]
        chat_completion = await client.chat.completions.create(
            messages=messages,
            # 8b instant handles large contexts and ensures we never hit the 6000 TPM limit of 70b
            model="llama-3.1-8b-instant",
            temperature=0.7
        )
        
        scorecard_content = chat_completion.choices[0].message.content
        
        # Save scorecard
        with open(scorecard_path, "w") as f:
            f.write(scorecard_content)
            
        # Return scorecard text, and the files for download
        return scorecard_content, [transcript_path, scorecard_path]
    except Exception as e:
        return f"Error generating scorecard: {str(e)}", None

# Sleek Professional UI Theme
custom_theme = gr.themes.Monochrome(
    primary_hue="slate",
    secondary_hue="gray",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
)

# Gradio App Layout
with gr.Blocks(title="AI Mock PM Interviewer", theme=custom_theme) as demo:
    gr.Markdown("# 🎙️ AI Mock PM Interviewer\n*A sleek, real-time voice conversational agent to practice Product Sense interviews.*")
    
    with gr.Accordion("⚙️ Settings & Configuration", open=True):
        api_key_input = gr.Textbox(label="Groq API Key", type="password", placeholder="Enter your Groq API key here to start...")
    
    with gr.Row():
        start_btn = gr.Button("▶️ Start New Interview", variant="primary")
        end_btn = gr.Button("🛑 End Interview & Grade", variant="stop")
        
    question_display = gr.Textbox(label="Current Interview Scenario", interactive=False)
    
    transcript_state = gr.State([])
    
    with gr.Row():
        with gr.Column(scale=1):
            audio_output = gr.Audio(autoplay=True, label="Interviewer Voice", interactive=False)
            audio_input = gr.Audio(source="microphone", type="filepath", label="Your Microphone")
            
        with gr.Column(scale=2):
            chatbot_display = gr.Chatbot(label="Live Transcript", height=400)
    
    with gr.Accordion("📊 Final Scorecard & Downloads", open=True):
        scorecard_display = gr.Markdown("*Scorecard will generate here after the interview ends.*")
        download_files = gr.File(label="Download Interview Records", interactive=False)
    
    # Event wiring
    start_btn.click(
        fn=start_interview,
        inputs=[api_key_input],
        outputs=[question_display, transcript_state, chatbot_display, audio_output, download_files]
    )
    
    audio_input.stop_recording(
        fn=process_audio,
        inputs=[audio_input, transcript_state, chatbot_display, api_key_input],
        outputs=[audio_output, transcript_state, chatbot_display, audio_input]
    )
    
    end_btn.click(
        fn=end_interview,
        inputs=[transcript_state, api_key_input],
        outputs=[scorecard_display, download_files]
    )

if __name__ == "__main__":
    demo.launch()
