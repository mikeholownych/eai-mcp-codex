# A2A Communication Guide

This guide provides a comprehensive overview of the Agent-to-Agent (A2A) communication system in the MCP Microservices project.

## Core Concepts

The A2A communication system is designed to facilitate seamless and efficient collaboration between autonomous AI agents. It is built on a publish-subscribe model, with a central message broker that routes messages between agents.

### Message Broker

The message broker is the heart of the A2A communication system. It is responsible for:

*   **Message Routing**: The message broker routes messages to the appropriate agents based on the message topic.
*   **Message Delivery**: The message broker ensures that messages are delivered to the intended recipients.
*   **Message Queuing**: The message broker queues messages for agents that are offline or busy.

### Agents

Agents are the primary actors in the A2A communication system. They can be specialized for specific tasks, such as planning, development, or security. Agents communicate with each other by publishing and subscribing to messages on the message broker.

## Collaboration Protocols

The A2A communication system supports a variety of collaboration protocols, including:

*   **Request-Response**: One agent sends a request to another agent and waits for a response.
*   **Publish-Subscribe**: One agent publishes a message to a topic, and any interested agents can subscribe to that topic to receive the message.
*   **Broadcast**: One agent sends a message to all other agents.

## Consensus Engine

The consensus engine is a key component of the A2A communication system. It allows agents to reach agreement on important decisions, such as architectural choices or implementation plans. The consensus engine is based on a voting mechanism, where each agent can cast a vote on a proposal. A proposal is accepted if it receives a sufficient number of votes.

## Agent Factory

The agent factory is responsible for creating and managing agents. It can be used to dynamically create new agents as needed, and to scale the number of agents up or down based on the workload.

## Monitoring

The WebSocket gateway exposes Prometheus metrics for active connections and A2A
message throughput. Counters track messages sent and received per service so
that dashboards can display real-time communication rates.
