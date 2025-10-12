import streamlit as st
from google import genai
from google.genai import types
import datetime
import pandas as pd
from collections import Counter
import json
import os

# --- Configuration & Setup ---
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        st.error("GEMINI_API_KEY not found in Streamlit secrets or environment variables. Please check your setup.")
        st.stop()
        
    client = genai.Client(api_key=API_KEY)

except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")
    st.stop()

# --- Constants & File Path ---
AI_NAME = "MindEase AI"
AI_TAGLINE = "A mental health companion"
MODEL = "gemini-2.5-flash"
CRISIS_KEYWORDS = ["suicide", "kill myself", "end my life", "self-harm", "harm myself"]

# --- AI Persona Mapping ---
PERSONA_MAPPING = {
    "Gently Supportive": (
        "You are a compassionate, non-judgemental companion focused on validation and empathy. "
        "Your tone is gentle, warm, and comforting. Focus on making the user feel heard and safe."
    ),
    "Action-Oriented Coach": (
        "You are a positive and motivating coach. After showing empathy, offer a small, "
        "practical step, question, or short exercise the user can do next. Your tone is energetic and forward-looking."
    ),
    "Philosophical Guide": (
        "You are a reflective guide. After acknowledging the user's feelings, offer a broader, "
        "thought-provoking perspective or a philosophical idea to help the user reframe their thoughts. Your tone is calm and reflective."
    )
}

# --- System Instruction Generator & Chat Initializer ---
def initialize_chat_session(persona="Gently Supportive"): 
    """Initializes or re-initializes the Gemini chat session with a new system instruction."""
    
    dynamic_instruction = (
        f"You are {AI_NAME}, a mental health companion. "
        f"{PERSONA_MAPPING.get(persona, PERSONA_MAPPING['Gently Supportive'])} "
        "You are NOT a substitute for a licensed therapist. "
        "Before responding, analyze the user's emotion (e.g., Sadness, Anxiety, Joy, Anger, Neutral) based on their last message and provide a brief, supportive insight before your main response. "
        "If the user expresses immediate suicidal ideation or intent to harm themselves, DO NOT engage in a conversation. "
        "Instead, immediately output a short, urgent statement about your inability to provide crisis help and redirect them to a professional resource (e.g., 'Please contact a crisis hotline immediately. Call or text 988. You are not alone.')."
    )

    config = types.GenerateContentConfig(system_instruction=dynamic_instruction)
    
    st.session_state.chat = client.chats.create(model=MODEL, config=config)
    
    if not st.session_state.get('messages'):
        st.session_state.messages = []

# --- Function to manage the chat object across reruns ---
def manage_chat_session_state():
    """Ensures the chat object is present and properly initialized."""
    if "chat" not in st.session_state:
        # Initial setup
        initialize_chat_session(st.session_state.ai_persona)

# --- Session State Initialization ---
st.set_page_config(
    page_title=AI_NAME, 
    page_icon="🧠", 
    layout="wide"
)

# AI default persona
st.session_state.ai_persona = "Gently Supportive" 
manage_chat_session_state() # <--- CALL THE MANAGER HERE
    
if "journal_entries" not in st.session_state:
    st.session_state.journal_entries = {}
    
if "journal_entry_key" not in st.session_state:
    st.session_state.journal_entry_key = datetime.date.today().isoformat() + "_entry"

# --- Inject Custom CSS for Professional Styling ---
st.markdown(
    """
    <style>
    /* 1. Sidebar Title and Tagline Customization (Unchanged) */
    .main-title {
        font-size: 2.2em;
        font-weight: 800;
        margin-bottom: 0px; 
        color: #1E90FF;
    }

    .sub-tagline {
        display: block;
        font-style: italic;
        font-size: 0.95em;
        font-family: 'Georgia', serif; 
        margin-top: -5px; 
        margin-bottom: 15px;
        color: #696969;
    }

    /* 2. Important Note (st.info in sidebar) Styling (Unchanged) */
    .stAlert {
        border-radius: 8px;
        line-height: 1.5;
        font-size: 0.9em;
        text-align: left;
    }
    
    /* 3. Horizontal Tabs Styling (BLUE BACKGROUND ADDED) */
    
    /* Target the container that holds the tab list and set its background color */
    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] {
        background-color: #E0F7FF; /* Light Blue Background for the tab bar */
        border-radius: 8px 8px 0 0; 
        padding-top: 5px; /* Add slight padding above the tabs */
    }

    /* Style for the individual tab buttons */
    button[data-baseweb="tab"] {
        font-size: 1.8rem; 
        font-weight: 700; 
        font-family: 'Arial', sans-serif; 
        padding: 12px 25px; 
        border-radius: 8px 8px 0 0; 
        transition: all 0.2s ease-in-out;
        text-transform: uppercase; 
        background-color: #B3E5FC; /* Slightly darker blue for unselected tabs */
        color: #1E90FF; /* Keep text color as deep blue */
    }
    
    /* Style for the active (selected) tab */
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #1E90FF; 
        border-bottom: 4px solid #1E90FF !important;
        background-color: #FFFFFF; /* Set active tab background to white */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Subtle shadow on active tab */
    }
    
    /* 4. Heading Adjustments (Inner Heading Sizes remain slightly reduced for balance) */
    /* st.title (h1 in markdown) */
    .stApp h1 { 
        font-size: 2.0rem; 
    }
    /* st.header (h2 in markdown) */
    .stApp h2 { 
        font-size: 1.7rem; 
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    /* st.subheader (h3 in markdown) */
    .stApp h3 {
        font-size: 1.4rem; 
        font-weight: 600;
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
    }
    
    /* Ensure markdown headers in the sidebar are also left-aligned cleanly (Unchanged) */
    .stSidebar .stSubheader {
        margin-top: 10px;
        margin-bottom: 5px;
    }
    
    </style>
    """,
    unsafe_allow_html=True,
)
# --- End Custom Tabs CSS ---

# --- Helper Functions ---

def check_crisis(text):
    """Checks if the user's text contains crisis keywords."""
    return any(keyword in text.lower() for keyword in CRISIS_KEYWORDS)

def analyze_journal_entry(text):
    """Uses Gemini to get a summary and overall sentiment for a journal entry."""
    
    analysis_prompt = (
        f"Analyze the following journal entry and provide a summary (max 3 sentences) "
        f"and an overall emotional sentiment (e.g., 'Calm', 'Stressed', 'Reflective', 'Motivated', 'Hopeful'). "
        f"Format your response STRICTLY as a JSON object with keys 'summary' and 'sentiment'. "
        f"Entry to analyze: '{text}'"
    )

    try:
        response = client.models.generate_content(
            model=MODEL, 
            contents=analysis_prompt
        )
        
        json_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        analysis = json.loads(json_text)
        
        return analysis.get('summary', 'No summary available.'), analysis.get('sentiment', 'Unknown')

    except Exception as e:
        return "Could not generate summary.", "Analysis Error"


def get_ai_response_and_emotion(prompt):
    """Gets AI response and extracts the detected emotion."""
    
    emotion_prompt = (
        f"Analyze the following user message for a single dominant emotion "
        f"(e.g., Sadness, Anxiety, Joy, Anger, Neutral): '{prompt}'. "
        f"Then, respond as a compassionate AI companion, following your system instructions. "
        f"Format your output strictly as: [Emotion: <Emotion>] <Your Supportive Response>"
    )

    try:
        # Use the chat object currently in session state
        response = st.session_state.chat.send_message(emotion_prompt)
        full_text = response.text.strip()

        if full_text.startswith("[Emotion:"):
            parts = full_text.split("] ", 1)
            emotion = parts[0].replace("[Emotion: ", "").replace("]", "")
            ai_response = parts[1] if len(parts) > 1 else "I hear you."
        else:
            emotion = "Neutral/Unknown"
            ai_response = full_text

        return ai_response, emotion

    except Exception as e:
        error_message = f"--- GEMINI API CALL FAILED ---\nSpecific Error: {e}"
        # Print the error for debugging but return a user-friendly message
        print(error_message) 
        return "I'm sorry, I'm having trouble connecting to the AI right now. Please check your API key and logs.", "Error"

# --- UI Components ---

def render_sidebar():
    """Renders the sidebar with fixed information and custom styling."""
    with st.sidebar:
        # Title and Tagline rendered using custom CSS classes for precise control
        st.markdown(f'<div class="main-title">{AI_NAME}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sub-tagline">{AI_TAGLINE}</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Important Note: st.subheader ensures good visual separation, and st.info
        # component looks clean with the new CSS rule applied to .stAlert.
        st.subheader("Important Note")
        st.info(
            "MindEase AI is a companion, **not a substitute** for a licensed therapist or a crisis hotline. "
            "For emergencies, please seek professional help immediately."
        )

def render_journal_tab():
    """Renders the Journaling interface, with AI analysis and session-based storage."""
    # Using st.header (which maps to h2) for the main title of the tab content
    st.header("Journaling 📝") 
    st.markdown("Use this space to reflect on your thoughts and feelings. Each save creates a new timestamped entry, which is then analyzed by the AI for sentiment and summary.")

    today = datetime.date.today().isoformat()
    
    # Text area for new entry
    new_entry = st.text_area(
        "Start a New Entry:", 
        value="", 
        height=300, 
        key=st.session_state.journal_entry_key 
    )

    if st.button("Save Entry", use_container_width=True, key="save_entry_btn"):
        if new_entry.strip():
            
            # 1. Create unique timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 2. Perform AI Analysis on the new entry
            with st.spinner("Analyzing journal entry for insights..."):
                summary, sentiment = analyze_journal_entry(new_entry.strip())
            
            entry_data = {
                "timestamp": timestamp,
                "content": new_entry.strip(),
                "summary": summary, 
                "sentiment": sentiment 
            }
            
            # 3. Append the new entry to the list for today's date
            if today not in st.session_state.journal_entries:
                st.session_state.journal_entries[today] = []
                
            st.session_state.journal_entries[today].append(entry_data)
            
            # 4. Reset text area and notify
            # Ensure the key is unique for the next text area instance
            st.session_state.journal_entry_key = datetime.datetime.now().isoformat() + "_entry"
            st.success(f"Entry saved and analyzed! Sentiment: **{sentiment}**")
        else:
            st.warning("Journal entry cannot be empty.")
        
        st.rerun() 

    st.divider()
    st.subheader("Journaling History")

    if not st.session_state.journal_entries:
        st.info("You haven't saved any journal entries yet. They will appear here.")
    else:
        # The keys (dates) are stored in 'YYYY-MM-DD' format
        dates = sorted(st.session_state.journal_entries.keys(), reverse=True)
        
        for selected_date in dates:
            entries_for_day = st.session_state.journal_entries[selected_date]
            
            # Convert the stored 'YYYY-MM-DD' key to 'DD-MM-YYYY' for display
            try:
                # Parse the ISO date string and format it to DD-MM-YYYY
                display_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            except ValueError:
                display_date = selected_date # Fallback if format is unexpected
            
            all_entries_text = f"--- Journal Entries for {display_date} ---\n\n"
            
            with st.expander(f"📅 **{display_date}** ({len(entries_for_day)} entries)"):
                
                for entry in entries_for_day[::-1]:
                    time_str = entry['timestamp'].split(' ')[1][:-3] 
                    
                    st.markdown(f"**🕒 {time_str}** | Sentiment: **{entry.get('sentiment', 'N/A')}**")
                    st.markdown(f"_Summary: {entry.get('summary', 'No summary available.')}_")
                    st.text(entry['content'])
                    st.markdown("---") 
                    
                    # Also update the downloadable text file content to use the new display format
                    all_entries_text += f"Date: {display_date}\n"
                    all_entries_text += f"Entry Time: {entry['timestamp'].split(' ')[1]}\n"
                    all_entries_text += f"Sentiment: {entry.get('sentiment', 'N/A')}\n"
                    all_entries_text += f"Summary: {entry.get('summary', 'N/A')}\n"
                    all_entries_text += f"Content: {entry['content']}\n"
                    all_entries_text += "--------------------------------------\n"
                    
                st.download_button(
                    label=f"Download All Entries for {display_date}",
                    data=all_entries_text,
                    # Keep the filename using the ISO format for better file sorting
                    file_name=f"mind_ease_journal_all_{selected_date}.txt", 
                    mime="text/plain",
                    use_container_width=True,
                    key=f"download_btn_all_{selected_date}"
                )

def render_insights_tab():
    """Renders the Emotional Insights interface, combining chat and journal data."""
    st.header("Advanced Emotional Tracking & Insights 📈")
    st.markdown("Visualizing your emotional journey from both your conversations and your reflections.")
    
    # --- 1. Chat Emotion Analysis ---
    emotions = [msg['emotion'] for msg in st.session_state.messages 
                if msg['role'] == 'assistant' and msg.get('emotion') not in ['Neutral/Unknown', 'Error', 'Crisis']]

    if not emotions and not st.session_state.journal_entries:
        st.info("Start chatting and journaling to generate emotional data.")
        return

    st.subheader("💬 Reflective Space Emotion Frequency Breakdown") 
    if not emotions:
        st.info("No chat emotional data yet.")
    else:
        emotion_counts = Counter(emotions)
        df_emotions = pd.DataFrame(emotion_counts.items(), columns=['Emotion', 'Count'])
        df_emotions = df_emotions.sort_values(by='Count', ascending=False).reset_index(drop=True)

        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(df_emotions, hide_index=True, use_container_width=True)
            
        with col2:
            st.bar_chart(df_emotions.set_index('Emotion'))
            
        most_frequent_chat_emotion = df_emotions.iloc[0]['Emotion'] if not df_emotions.empty else "None"
    
    # --- 2. Journal Sentiment Analysis ---
    st.markdown("---")
    st.subheader("📝 Journaling Sentiment Insights")

    journal_sentiments = []
    for day_entries in st.session_state.journal_entries.values():
        for entry in day_entries:
            sentiment = entry.get('sentiment')
            if sentiment and sentiment not in ['Analysis Error', 'Unknown']:
                journal_sentiments.append(sentiment)

    if not journal_sentiments:
        st.info("Save journal entries to see a sentiment breakdown here.")
        most_frequent_journal_sentiment = "None"
    else:
        sentiment_counts = Counter(journal_sentiments)
        df_sentiments = pd.DataFrame(sentiment_counts.items(), columns=['Sentiment', 'Count'])
        df_sentiments = df_sentiments.sort_values(by='Count', ascending=False).reset_index(drop=True)

        col_j1, col_j2 = st.columns([1, 2])
        
        with col_j1:
            st.dataframe(df_sentiments, hide_index=True, use_container_width=True)
            
        with col_j2:
            st.bar_chart(df_sentiments.set_index('Sentiment'))
            
        most_frequent_journal_sentiment = df_sentiments.iloc[0]['Sentiment'] if not df_sentiments.empty else "None"
    
    # --- 3. Final Synthesis ---
    st.divider()
    
    st.subheader("Key Synthesis") 
    
    st.metric(label="Most Frequent Chat Emotion", value=most_frequent_chat_emotion if 'most_frequent_chat_emotion' in locals() else "None")
    st.metric(label="Most Frequent Journal Mood", value=most_frequent_journal_sentiment)

    if 'most_frequent_chat_emotion' in locals() and most_frequent_chat_emotion != "None" or most_frequent_journal_sentiment != "None":
        
        chat_emotion_text = most_frequent_chat_emotion if 'most_frequent_chat_emotion' in locals() and most_frequent_chat_emotion != "None" else "not yet recorded"
        journal_sentiment_text = most_frequent_journal_sentiment if most_frequent_journal_sentiment != "None" else "not yet recorded"
        
        st.info(
            f"**Overall Wellness Insight:** Your primary conversational emotion is **{chat_emotion_text}** "
            f"and your most frequent journal sentiment is **{journal_sentiment_text}**. "
            f"Use the journaling feature to explore the **root causes** of challenging feelings (e.g., Sadness, Anxiety) "
            f"or to detail the **sources of joy** when you're feeling good."
        )
    else:
        st.info("**Overall Wellness Insight:** Keep chatting and journaling to build a comprehensive emotional profile.")

def render_chat_tab():
    """Renders the Reflective Space interface."""
    st.title("Reflective Space💬") 
    st.markdown(f"I am here to listen and hold space for you.") 
    st.divider()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "emotion" in message and message["emotion"] != "Error":
                st.caption(f"**Detected Emotion:** {message['emotion']}")
            elif message["role"] == "assistant" and message.get("emotion") == "Error":
                st.caption(f"**Status:** AI Connection Failed (Check your API Key)")


    # Chat input
    prompt = st.chat_input("Share what's on your mind...") 
    
    if prompt:
        # Add user message to history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 1. CRISIS REDIRECTION PROTOCOL
        if check_crisis(prompt):
            crisis_response = (
                "🚨 **CRISIS ALERT: IMMEDIATE ACTION REQUIRED** 🚨\n\n"
                "I am **MindEase AI**, a companion, not a crisis resource. "
                "Your safety is paramount. Please, reach out for professional help **right now**.\n\n"
                "Call or Text **988** (Suicide & Crisis Lifeline)\n"
                "**Stay safe. You are not alone.**"
            )
            with st.chat_message("assistant"):
                st.markdown(crisis_response)
            st.session_state.messages.append({"role": "assistant", "content": crisis_response, "emotion": "Crisis"})
            # The session will rerun, hitting the manage_chat_session_state() at the top
            st.rerun() 
            return 

        # 2. ADVANCED EMOTIONAL TRACKING & RESPONSE
        try:
            with st.spinner("MindEase AI is thinking..."):
                ai_response, emotion = get_ai_response_and_emotion(prompt) 
        
            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(ai_response)
                if emotion != "Error":
                    st.caption(f"**Detected Emotion:** {emotion}")
                else:
                    st.caption(f"**Status:** AI Connection Failed (Check your API Key)")
        
            st.session_state.messages.append({"role": "assistant", "content": ai_response, "emotion": emotion})

        except Exception as e:
            # Catch API-level failures explicitly
            error_response = "I'm sorry, an unexpected error occurred during the conversation. I will reset our chat."
            st.session_state.messages.append({"role": "assistant", "content": error_response, "emotion": "Error"})
            st.error(f"Chat Error: {e}") # Show the actual error for debugging

        # --- Delete the used chat object ---
        # This forces manage_chat_session_state() (run on the next rerun) 
        # to create a fresh, ready-to-use chat object for the next user input.
        if 'chat' in st.session_state:
            del st.session_state.chat

        st.rerun() 

# --- Main Application Logic (Using Horizontal Tabs) ---
render_sidebar()

tab1, tab2, tab3 = st.tabs(["💬 REFLECTIVE SPACE", "📝 JOURNALING", "📈 EMOTIONAL INSIGHTS"])

with tab1:
    render_chat_tab()
    
with tab2:
    render_journal_tab()
    
with tab3:
    render_insights_tab()
