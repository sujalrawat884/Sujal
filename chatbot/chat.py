from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv
from .prompt import create_system_message

# Load environment variables
load_dotenv()

# Dictionary to store chat histories
# Key: user_id-subject-unit, Value: list of messages
chat_histories = {}

def get_chatbot_response(subject, unit, question, user_id=None):
    """Generate a response using Google Gemini based on subject, unit and question"""
    
    # Create a unique key for this conversation
    if user_id:
        conversation_key = f"{user_id}-{subject}-{unit}"
    else:
        conversation_key = f"anonymous-{subject}-{unit}"
    
    # Initialize chat history if it doesn't exist
    if conversation_key not in chat_histories:
        system_message = create_system_message(subject, unit)
        chat_histories[conversation_key] = [system_message]
    
    # Add user message to history
    chat_histories[conversation_key].append(HumanMessage(content=question))
    
    # Initialize the language model
    llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', temperature=0.7)
    
    try:
        # Get response from the model
        response = llm.invoke(chat_histories[conversation_key])
        
        # Add AI response to history
        chat_histories[conversation_key].append(AIMessage(content=response.content))
        
        return response.content
    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(error_message)
        return f"I'm sorry, I encountered an error while generating a response. Please try again later. Technical details: {error_message}"