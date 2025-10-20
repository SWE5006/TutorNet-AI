# TutorNet-AI

AI Agent for TutorNet

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Start the application**

   ```bash
   # Development
   uvicorn main:app --reload

   # Production
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
