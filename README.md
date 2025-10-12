MindEase AI – A Mental Health Companion

MindEase AI is a Streamlit-based mental health journaling and emotional companion application powered by the Gemini API. It provides supportive conversations, emotion analysis, journaling insights, and emotional trend visualization.

Features
- AI Chat Companion with emotion detection
- Journaling with automatic sentiment analysis and summaries
- Emotional trend visualization using charts and data insights
- Local data storage for journal entries
- Crisis keyword detection and immediate redirection message

Tech Stack
- Python
- Streamlit
- Gemini API (via google-genai)
- Python dotenv for secure API key management
- Pandas for data analysis

Setup Instructions
1. Clone the repository
   git clone https://github.com/Samyuktha-Rama/MindEaseAI.git
   cd MindEaseAI

2. (optional)Create a `.env` file and add your Gemini API key:
   GEMINI_API_KEY=your_api_key_here

3. Install dependencies
   pip install -r requirements.txt

4. Run the application
   streamlit run app.py

Folder Structure
MindEaseAI/
│
├── app.py                  # Main Streamlit application file
├── .env                    # Contains the GEMINI_API_KEY (excluded from Git)
├── requirements.txt         # Python dependencies
├── .gitignore               # Files and folders to exclude from version control
├── README.md                # Project documentation
└── mind_ease_data.json      # Journal data (auto-created, excluded from Git)

Deployment (Optional - Streamlit Cloud)
1. Log in to https://share.streamlit.io
2. Click New App
3. Select your GitHub repository and choose app.py as the main file
4. Under Advanced Settings, add an environment variable:
   Key: GEMINI_API_KEY
   Value: your API key
5. Click Deploy

Security Notes
- The `.env` file must never be uploaded to GitHub.
- The `mind_ease_data.json` file stores personal journaling data locally; it is excluded from GitHub for privacy.
- This application is not a replacement for professional mental health services. In case of a crisis, users are advised to seek immediate professional help.
