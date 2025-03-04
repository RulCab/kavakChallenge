# Tech Challenge - AI Debate Bot

## Overview
This project implements an AI-powered debate bot using **FastAPI**, **Google Gemini API**, and **Firebase Firestore**. The bot is designed to engage in persuasive debates while maintaining a strong stance on a given topic.

## Getting Started

First, clone this repository:

```sh
git clone https://github.com/RulCab/kavakChallenge.git
cd kavakChallenge
```

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

## Environment Variables Setup
To run this service, you need to create a `.env` file in the root directory with the following environment variables:

```sh
GEMINI_API_KEY=your_gemini_api_key
FIREBASE_CREDENTIALS=/app/your_firebase_credentials.json
NGROK_AUTH_TOKEN=your_ngrok_token
```

Here's how you can obtain them:

- **GEMINI_API_KEY**:  
  1. Visit [Google AI Studio](https://aistudio.google.com/) and sign in with your Google account.  
  2. Create a new project and enable the **Gemini API**.  
  3. Generate an API key and copy it into your `.env` file.

- **FIREBASE_CREDENTIALS**:  
  1. Go to [Firebase Console](https://console.firebase.google.com/) and create a new project.  
  2. Navigate to **Project Settings > Service Accounts**.  
  3. Click **Generate new private key**, and save the `.json` file in the root directory of your project.  
  4. Ensure your `.env` file references it as `/app/your_firebase_credentials.json`.  
  5. Update `docker-compose.yml` to mount the file inside the container:
     ```yaml
     volumes:
       - ./your_firebase_credentials.json:/app/your_firebase_credentials.json
     ```

- **NGROK_AUTH_TOKEN**:  
  1. Sign up at [Ngrok](https://ngrok.com/) and log in.  
  2. Go to your dashboard and copy your authentication token.  
  3. Add it to your `.env` file.

Once the `.env` file is set up, you can proceed with running the service using Docker:

```sh
make run
```

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
      - FIREBASE_CREDENTIALS=/app/your_firebase_credentials.json
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./your_firebase_credentials.json:/app/your_firebase_credentials.json
```

## Example Usage

Here is a screenshot of a conversation with the bot in action:

![AI Debate Bot en acción](ai-bot-in-action.png)

You can also test the bot using the following command:

```sh
curl -X POST "http://localhost:8000/chat" -H "Content-Type: application/json" -d '{"conversation_id": "conv_1234", "message": "Is expensive perfume worth it?"}'
```

## Conclusion
This project successfully meets all the requirements of the tech challenge by implementing a **fast, persuasive, and structured AI debate bot** with **automated deployment and testing**. It supports multiple argument styles and topics while maintaining a logical flow of conversation stored in Firebase Firestore.





