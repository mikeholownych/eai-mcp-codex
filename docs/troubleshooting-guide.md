# Troubleshooting Guide

This guide provides solutions to common problems that you may encounter when using the MCP Microservices project.

## Agents Not Responding

If agents are not responding, it may be due to a variety of issues, including:

*   **Network connectivity issues**: Ensure that the agents can connect to the message broker.
*   **Message broker issues**: Ensure that the message broker is running and that there are no issues with the message queues.
*   **Agent issues**: Ensure that the agents are running and that there are no errors in the agent logs.

## Consensus Never Reached

If consensus is never reached, it may be due to a variety of issues, including:

*   **Insufficient number of agents**: Ensure that there are enough agents to reach a quorum.
*   **Conflicting proposals**: If there are conflicting proposals, it may be difficult to reach a consensus. Try to simplify the proposals or to find a compromise.
*   **Network connectivity issues**: Ensure that the agents can communicate with each other.

## High Memory Usage

If you are experiencing high memory usage, it may be due to a variety of issues, including:

*   **Too many agents**: Try reducing the number of agents.
*   **Large messages**: Try reducing the size of the messages that are being sent between agents.
*   **Memory leaks**: Check the agent logs for any memory leak warnings.
