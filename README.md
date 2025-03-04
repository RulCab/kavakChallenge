# Tech Challenge - AI Debate Bot

## Overview
This project implements an AI-powered debate bot using **FastAPI**, **Google Gemini API**, and **Firebase Firestore**. The bot is designed to engage in persuasive debates while maintaining a strong stance on a given topic.

## Features
- **Maintains a consistent argument**: The bot never changes its position, regardless of user input.
- **Persuasive responses**: Uses different argumentation styles (historical, scientific, emotional, sarcastic) to convince the user.
- **Conversation persistence**: Previous messages are stored in Firebase Firestore to maintain a logical flow.
- **Handles long discussions**: The bot supports conversations exceeding ten messages, up to a maximum of 9 interactions (can be adjusted).
- **Response time optimization**: Ensures responses are generated within **30 seconds**.
- **Multiple debate topics**: The bot debates on various **perfumery-related topics**, including fragrance pricing, seasonal suitability, and niche vs. designer scents.
- **Different argument styles**: The bot can argue using **historical, scientific, emotional, or sarcastic** tones.

## Technologies Used
- **FastAPI**: Backend framework for handling API requests.
- **Google Gemini API**: Generates AI-based debate responses.
- **Firebase Firestore**: Stores conversation history.
- **Ngrok**: Exposes the local API to a public URL.
- **Python-dotenv**: Manages environment variables securely.
- **Docker**: Containerizes the application for deployment.
- **Makefile**: Automates service management tasks.

## Code Structure
A `Makefile` is provided to simplify the installation, execution, and testing of the service.

### Makefile Commands
- `make` - Shows a list of all available commands.
- `make install` - Installs all dependencies required to run the service.
- `make test` - Runs the test suite.
- `make run` - Starts the service and all related dependencies (e.g., Firebase) inside **Docker**.
- `make down` - Stops all running services.
- `make clean` - Removes all Docker containers and related services.

## Environment Variables
To run the service, you need to set the following environment variables in a `.env` file:

```sh
GEMINI_API_KEY=your_gemini_api_key
FIREBASE_CREDENTIALS=/app/api-bot-af0af-firebase-adminsdk-fbsvc-a6b2971832.json
NGROK_AUTH_TOKEN=your_ngrok_token
```

Additionally, **move your Firebase credentials JSON file** to the root directory of the project and ensure it is referenced correctly in both the `.env` file and `docker-compose.yml`.

## API Endpoint
### `POST /chat`
Handles user messages and generates AI responses.

#### Request Body:
```json
{
  "conversation_id": "optional_conversation_id",
  "message": "User's input message"
}
```
- `conversation_id` (optional): Allows the API to track ongoing debates.
- `message`: The user's message to the bot.

#### Response:
```json
{
  "conversation_id": "unique_id_for_the_conversation",
  "messages": [
    {"role": "user", "message": "User's input"},
    {"role": "bot", "message": "AI-generated response"}
  ]
}
```

## Deployment
### Running with Docker
1. Build and start the service:
   ```sh
   make run
   ```
2. Stop running services:
   ```sh
   make down
   ```
3. Remove all containers:
   ```sh
   make clean
   ```

### Running Locally (Without Docker)
1. Install dependencies:
   ```sh
   make install
   ```
2. Start the FastAPI server:
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
3. Start ngrok:
   ```sh
   ngrok http 8000
   ```
4. Use the generated ngrok URL to interact with the bot.

## Testing
Run the test suite using:
```sh
make test
```
This will validate:
- **Consistency of arguments**
- **Response persuasiveness**
- **Correct tracking of conversation history**

## Modifications in `docker-compose.yml`
For the bot to work correctly, update your `docker-compose.yml` to include the Firebase credentials JSON file as a volume:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    container_name: ai-debate-bot
    environment:
      - FIREBASE_CREDENTIALS=/app/api-bot-af0af-firebase-adminsdk-fbsvc-a6b2971832.json
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./api-bot-af0af-firebase-adminsdk-fbsvc-a6b2971832.json:/app/api-bot-af0af-firebase-adminsdk-fbsvc-a6b2971832.json
```

## Conclusion
This project successfully meets all the requirements of the tech challenge by implementing a **fast, persuasive, and structured AI debate bot** with **automated deployment and testing**. It supports multiple argument styles and topics while maintaining a logical flow of conversation stored in Firebase Firestore.



