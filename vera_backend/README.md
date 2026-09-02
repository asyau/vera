# Vira Backend

The backend API for Vira, an AI-powered assistant platform for teams.

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On Unix or MacOS:
     ```
     source venv/bin/activate
     ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```
   cp .env.example .env
   ```

5. Edit the `.env` file to add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Running the API

Start the FastAPI server:
```
uvicorn app.main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).

## API Documentation

Once the server is running, you can access:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Project Structure

```
app/
├── __init__.py
├── main.py
├── routes/
│   ├── __init__.py
│   ├── conversation.py
│   └── openai_service.py
└── services/
    ├── __init__.py
    └── openai_service.py
```
