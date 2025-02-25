# DeepSeek R1 Chat Application

A Python-based AI chat application that connects to DeepSeek R1, supports continuous conversations, and can store chat history.

## Features

- Connect to DeepSeek R1 AI model
- Modern UI with customtkinter
- Continuous conversation support
- Save and load conversation history
- API key management

## Installation

1. Clone this repository or download the source code.

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on the `.env.example` template:

```bash
cp .env.example .env
```

4. Edit the `.env` file and add your DeepSeek API key.

## Getting a DeepSeek API Key

To use this application, you need a DeepSeek API key:

1. Visit [DeepSeek Platform](https://platform.deepseek.com/)
2. Create an account or log in
3. Navigate to the API section
4. Generate a new API key
5. Copy the API key and add it to your `.env` file

## Running the Application

Run the application with:

```bash
python main.py
```

## Usage

### API Key Management

- The application will attempt to load your API key from the `.env` file
- You can also enter or update your API key directly in the application
- Click "Save Key" to update the API key being used

### Chat Interface

- Type your message in the input box at the bottom
- Press Enter or click "Send" to send your message
- The AI will respond automatically
- Use Shift+Enter to add a new line without sending

### Conversation Management

- Click "New Chat" to start a fresh conversation
- Click "Save Chat" to save the current conversation
- Click "Load Chat" to load a previously saved conversation

## Troubleshooting

If you encounter issues:

- Ensure your API key is correct
- Check your internet connection
- Verify that the DeepSeek API is available
- Make sure all dependencies are installed correctly

## License

This project is open source and available under the MIT License.