# Custom Agents

This guide provides instructions for creating custom agents for the MCP Microservices project.

## Base Agent

All agents must inherit from the `BaseAgent` class. The `BaseAgent` class provides the basic functionality for all agents, including:

*   **Connecting to the message broker**
*   **Publishing and subscribing to messages**
*   **Handling messages**

## Creating a Custom Agent

To create a custom agent, you will need to create a new class that inherits from the `BaseAgent` class. You will also need to implement the `handle_message` method. The `handle_message` method is called whenever the agent receives a message.

### Example

```python
from src.agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def handle_message(self, message):
        # Handle the message here
        pass
```
