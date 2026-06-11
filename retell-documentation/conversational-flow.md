> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Conversation Flow Overview

> Build structured Retell voice agents with conversation flow — nodes for dialogue, tools, transfers, code, and transitions for precise call control.

## What is a Conversation Flow Agent?

Conversation flow agents allow you to create multiple nodes to handle different scenarios in conversations. This approach provides more fine-grained control over the conversation flow compared to Single/Multi Prompt agents, enabling you to handle more complex scenarios with predictable outcomes.

### Key Benefits

* **Structured conversations**: Define exact paths and transitions
* **Predictable behavior**: Each node has specific logic and outcomes
* **Complex scenario handling**: Support for conditional branching and state management
* **Fine-tuning capabilities**: Improve performance with node-specific examples

<Frame>
  <img src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/cf/overview.jpeg?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=640760021e9ae1f52da8b17b17a41ac0" alt="Conversation flow diagram showing nodes connected by edges with transition conditions" width="2450" height="1122" data-path="images/cf/overview.jpeg" />
</Frame>

## Components

* **Global Settings**: Configuration that applies to the entire conversation, including:
  * Global prompt and personality
  * Default voice and language settings
  * Agent-wide parameters and behaviors

* **Node**: The basic unit of conversation flow. Multiple node types are available:
  * Conversation nodes for dialogue without tool calling
  * Subagent nodes for dialogue with tool calling
  * Function nodes for deterministic API and tool execution
  * Logic nodes for branching
  * End nodes for call termination

* **Edge**: Connections between nodes that define transition logic:
  * Condition-based transitions
  * Default fallback paths
  * Dynamic routing based on conversation context

* **Tools / Functions**: Reusable capabilities that can be attached to subagent nodes or invoked from function nodes. Conversation nodes do not use tools / functions:
  * Custom API integrations
  * Built-in utilities (calendar, SMS, transfers)
  * External service connections

## How it Works

Every node defines a small set of logic, and the transition condition is used to determine which node to transition to. Once the condition is met when checked, the agent will transition to the next node. There are also finetune examples on nodes that can help you further improve the performance. It might take longer to set up, as you want to cover all the scenarios, but after that it's much easier to maintain and the performance is more stable and predictable.

## Quickstart

Head to the Dashboard, create a new conversation flow agent and select a pre-built template to get started. You can view all options available to the agent within the Dashboard, with details of the options and any latency implications listed there. You can also view the estimated latency and cost of the agent. Modify the template to your needs, all changes are auto-saved.

## Pricing

Since the choice of model can be overridden within individual nodes, the pricing for each call is calculated based on:

* Time spent in each node (seconds)
* Model price per second for that specific node
* Total aggregated across all nodes visited during the call

This allows you to optimize costs by using different models for different parts of the conversation (e.g., cheaper models for simple routing, premium models for complex interactions).

---

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Node Overview

> Nodes are the building blocks of Retell conversation flow agents — learn node types, how edges connect them, and how transition conditions move calls forward.

## What are Nodes?

Nodes are the fundamental building blocks of your conversation flow. Each node represents a specific step or action in your agent's conversation, with its own logic, behavior, and purpose.

### Key Concepts

* **Node Type**: Determines the node's functionality (conversation, subagent, function call, logic, etc.)
* **Edges**: Connections between nodes that define the conversation flow
* **Transition Conditions**: Rules that determine when and where to move next
* **Fine-tuning**: Each node can be optimized independently for better performance

### Why Use Nodes?

By breaking complex workflows into individual nodes:

* **Precise Control**: Define exact behavior for each conversation scenario
* **Better Performance**: Fine-tune specific parts without affecting others
* **Easier Debugging**: Isolate and fix issues in specific conversation paths
* **Reusability**: Connect nodes in different ways for various flows

## Node Types Available

### Conversation Nodes

* [**Conversation Node**](/build/conversation-flow/conversation-node): Handle dialogue and user interactions without tool calling
* [**Subagent Node**](/build/conversation-flow/subagent-node): Handle dialogue and user interactions with tool calling
* [**Extract DV Node**](/build/conversation-flow/extract-dv-node): Extract and store dynamic variables from conversations

### Action Nodes

* [**Function Node**](/build/conversation-flow/function-node): Execute custom functions and API calls
* [**Code Node**](/build/conversation-flow/code-node): Execute JavaScript code directly without an external server
* [**SMS Node**](/build/conversation-flow/sms-node): Send SMS messages during the call
* [**MCP Node**](/build/conversation-flow/mcp-node): Integrate with Model Context Protocol tools

### Call Control Nodes

* [**Call Transfer Node**](/build/conversation-flow/call-transfer-node): Transfer calls to other phone numbers
* [**Transfer Agent Node**](/build/conversation-flow/transfer-agent-node): Transfer to another Retell agent
* [**Press Digit Node**](/build/conversation-flow/press-digit-node): Send DTMF tones (press digits)
* [**End Node**](/build/conversation-flow/end-node): Terminate the call gracefully

### Logic Nodes

* [**Logic Split Node**](/build/conversation-flow/logic-split-node): Create conditional branches based on variables

## Add a Node

<Steps>
  <Step title="Select node type">
    Click from the left sidebar to select the node type you want to add. Click on it, and it will be added to the canvas.

    <Frame>
      <img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/add-node.png?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=9f943a03432352f72166c04f780e19ba" alt="Left sidebar showing available node types to add to the conversation flow" width="298" height="722" data-path="images/cf/add-node.png" />
    </Frame>
  </Step>

  <Step title="Configure the node">
    Configure the node by clicking on the node, check the setting on the right, and fill in node instructions inside the node. Check out respective node guide for more details.

    <Frame>
      <img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/configure-node.jpeg?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=217edcea975d2e0578e385ba4fb5df50" alt="Node configuration panel on the right showing settings and instructions" width="736" height="567" data-path="images/cf/configure-node.jpeg" />
    </Frame>
  </Step>

  <Step title="Add transition conditions as needed">
    Add edges by clicking on bottom part of the node, and add your transition conditions. Check out next step for more details on how to add transition conditions.
  </Step>

  <Step title="Connect node">
    Click and hold the circle to start a line that connects the node to other node, and other node to this node.

    <Frame>
      <img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/connect-node.jpeg?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=25e5c0f3b617d167734bf18f28c0397a" alt="Connecting nodes by dragging from the circle connector to create edges" width="986" height="724" data-path="images/cf/connect-node.jpeg" />
    </Frame>
  </Step>
</Steps>

## Organize Nodes

Sometimes after adding a great amount of nodes, the canvas can get cluttered. You can use the `Organize` button to automatically organize the nodes.

<Frame>
  <img src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/cf/organize-node.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=1c5a3a922cae124f11a5f374c1746f2d" alt="Organize button that automatically arranges nodes for better visibility" width="1112" height="438" data-path="images/cf/organize-node.png" />
</Frame>

## FAQ

<AccordionGroup>
  <Accordion title="When should I break down a node?">
    Consider breaking down a node when:

    * The node handles multiple complex logic paths
    * The LLM struggles with consistency (hallucinations or incorrect responses)
    * You need different settings (model, temperature) for different parts
    * The conversation flow becomes hard to follow or debug

    Breaking complex nodes into smaller, focused nodes often improves reliability.
  </Accordion>

  <Accordion title="How to zoom in and out the canvas?">
    Depending on whether you are using mouse or touchpad, you can use the scroll wheel or pinch to zoom.
  </Accordion>

  <Accordion title="Is there a limit on the number of nodes?">
    No, you can add as many nodes as you want.
  </Accordion>
</AccordionGroup>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Conversation Node

> Use Retell conversation nodes for multi-turn dialogue without tool calls — the default building block for capturing info and guiding callers through a flow.

Conversation node is the most commonly used node type in conversation flow. It's used to have a conversation with the user without tool calling during the conversation.

If you want the agent to talk to the user and call tools during the same node, use a [Subagent Node](/build/conversation-flow/subagent-node).

Please note that the agent can have a multi-turn conversation inside a single node, so you don't necessarily need to create a new conversation node for every sentence the agent needs to say. It's recommended to split node when there's logic split, or the instruction got too long.

<img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/conversation-node.jpeg?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=2a67c7583585883d1bec9fdcef6b3243" width="800" height="504" data-path="images/cf/conversation-node.jpeg" />

## Write Instruction

Inside the node, you get to pick how you want to write the specific instruction for the agent to follow:

* **Prompt**: Write a prompt for the agent to dynamically generate what to say.
* **Static Sentence**: Agent will say a fixed sentence first, and if later still inside this node, it will generate content dynamically based on the static sentence set.

## When Can Transition Happen

* when user is done speaking
* when `Skip Response` is enabled and agent finishes speaking

## Node Settings

* **Skip Response**: when enabled, the transition will only have one edge that you can connect, and when agent is done talking, it will transition to the next node via that specific edge. This is useful when you want the agent to say things like disclaimers, where you don't need a response to move on to another node.
* **Knowledge Base**: configure node-level knowledge bases to combine topic-specific knowledge with the agent-level knowledge base. Read more at [Knowledge Base](/build/knowledge-base).
* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)
* **Block Interruptions**: when enabled, the agent will not be interrupted by user when speaking.
* **LLM**: choose a different model for this particular node. Will be used for response generation.
* **Fine-tuning Examples**: Can finetune conversation response, and transition. Read more at [Finetune Examples](/build/conversation-flow/finetune-examples)

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Subagent Node

> Subagent nodes let a Retell conversation flow combine dialogue with on-the-fly tool calls — the LLM decides whether and when to use each attached tool.

Subagent node is used to have a conversation with the user while allowing the agent to call tools / functions during the conversation. Use it when the agent should decide whether and when to use a tool / function based on the conversation context.

If you only need dialogue without tool calling, use a [Conversation Node](/build/conversation-flow/conversation-node).

## How It Works

When a subagent node has tools / functions attached, the LLM receives both the node instruction and the list of available tools / functions. During the conversation, the LLM determines when a tool / function should be called based on context, extracts the required parameters, and invokes it while maintaining the dialogue with the user.

* Multiple tools / functions can be added to a single subagent node
* The agent can continue talking while a tool / function executes
* Tool / function results are available to the LLM for generating follow-up responses

## Write Instruction

Subagent nodes only support `Prompt` instructions. Unlike a conversation node, `Static Sentence` is not supported.

Write the instruction to define the task, what information the agent should gather, and when it should use the available tools / functions.

For example:

```text theme={null}
Help the user check their order status. If the user provides an order number,
use the available order lookup tool to retrieve the latest status.
```

## Subagent Node vs Function Node

Subagent nodes and [function nodes](/build/conversation-flow/function-node) serve different purposes:

|                    | Function Node                                                  | Subagent Node                                                                           |
| ------------------ | -------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Execution**      | Deterministic — executes on node entry                         | LLM-driven — called when the LLM decides it's appropriate                               |
| **Tools per node** | One                                                            | Multiple                                                                                |
| **Conversation**   | Not intended for dialogue                                      | Full dialogue with tools available                                                      |
| **Best for**       | Always-execute actions (e.g. always look up an order on entry) | Context-dependent actions during dialogue (e.g. look up an order only if the user asks) |

**Use function nodes** when you want guaranteed execution every time the flow reaches that step.

**Use subagent nodes** when the agent should decide whether and when to call a tool / function based on what the user says.

## Add Tools / Functions

<Steps>
  <Step title="Select a subagent node">
    Click on a subagent node to open its settings panel on the right side.
  </Step>

  <Step title="Add a tool / function">
    In the settings panel, find the **Tools** section and click **+ Add**.

    Select the tool / function type from the dropdown menu.
  </Step>

  <Step title="Configure the tool / function">
    Configure the tool / function based on its type. See the **Available Tool / Function Types** table below for configuration details for each type.
  </Step>

  <Step title="Update the node instruction">
    Update the node prompt to guide the LLM on when to use the tool / function.
  </Step>
</Steps>

## Available Tool / Function Types

| Tool Type                   | Description                                             | Configuration Guide                                               |
| --------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------- |
| Custom Function             | Make HTTP requests to your external APIs                | [Custom Function](/build/conversation-flow/custom-function)       |
| Code Tool                   | Run JavaScript code directly without an external server | [Code Tool](/build/single-multi-prompt/code-tool)                 |
| Check Calendar Availability | Query available time slots via Cal.com                  | [Check Availability](/build/check-availability)                   |
| Book Appointment            | Book calendar events via Cal.com                        | [Book Calendar](/build/book-calendar)                             |
| End Call                    | Terminate the call                                      | [End Call](/build/single-multi-prompt/end-call)                   |
| Transfer Call               | Transfer to a phone number                              | [Transfer Call](/build/single-multi-prompt/transfer-call)         |
| Transfer Agent              | Transfer to another Retell agent                        | [Transfer Agent](/build/single-multi-prompt/transfer-agent)       |
| Press Digit                 | Send DTMF tones                                         | [Press Digit](/build/single-multi-prompt/press-digit)             |
| Send SMS                    | Send a text message                                     | [Send SMS](/build/single-multi-prompt/send-sms)                   |
| Extract Dynamic Variable    | Extract variables from the conversation                 | [Extract Dynamic Variable](/build/single-multi-prompt/extract-dv) |
| MCP Tool                    | Call tools on your MCP server                           | [MCP Node](/build/conversation-flow/mcp-node)                     |

## Execution Speech Settings

Each tool / function has settings that control what the agent says while it is running and after it completes.

### Speak During Execution

When enabled, the agent says a message while the tool / function is executing, for example `One moment, let me check that for you.` This is recommended when the tool / function takes over 1 second, including network latency, so the agent remains responsive.

You can configure how the message is generated:

* **Prompt**: The LLM dynamically generates what to say based on a description you provide.
* **Static Sentence**: The agent speaks the exact text you provide.

### Speak After Execution

When enabled, the agent calls the LLM after the tool / function returns a result so it can speak about the outcome to the user. Turn this off if you want to run it silently.

<Note>
  * **Speak During Execution** is available on: Custom Function, Code Tool, End Call, Transfer Call, Transfer Agent, and MCP Tool.
  * **Speak After Execution** is available on: Custom Function, Code Tool, and MCP Tool.
</Note>

## When Can Transition Happen

* when user is done speaking
* when `Skip Response` is enabled and agent finishes speaking

Tool / function execution happens within the subagent node, so the node can stay active across multiple turns and tool / function calls before it transitions.

## Node Settings

* **Tools**: attach the tools / functions this subagent can use during the conversation.
* **Skip Response**: when enabled, the transition will only have one edge that you can connect, and when agent is done talking, it will transition to the next node via that specific edge.
* **Knowledge Base**: configure node-level knowledge bases to combine topic-specific knowledge with the agent-level knowledge base. Read more at [Knowledge Base](/build/knowledge-base).
* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)
* **Block Interruptions**: when enabled, the agent will not be interrupted by user when speaking.
* **LLM**: choose a different model for this particular node. Will be used for response generation, tool / function selection, and tool / function argument generation.
* **Fine-tuning Examples**: Can finetune conversation response, and transition. Read more at [Finetune Examples](/build/conversation-flow/finetune-examples)

## Best Practices

* **Be explicit in your node instruction.** Tell the agent when each tool / function should be used.
* **Use function nodes for guaranteed execution.** If a tool / function must always run at a certain point in the flow, use a function node instead.
* **Avoid adding too many tools / functions to one subagent node.** If you have many tools / functions, consider splitting them across multiple subagent nodes.

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Subagent Node

> Subagent nodes let a Retell conversation flow combine dialogue with on-the-fly tool calls — the LLM decides whether and when to use each attached tool.

Subagent node is used to have a conversation with the user while allowing the agent to call tools / functions during the conversation. Use it when the agent should decide whether and when to use a tool / function based on the conversation context.

If you only need dialogue without tool calling, use a [Conversation Node](/build/conversation-flow/conversation-node).

## How It Works

When a subagent node has tools / functions attached, the LLM receives both the node instruction and the list of available tools / functions. During the conversation, the LLM determines when a tool / function should be called based on context, extracts the required parameters, and invokes it while maintaining the dialogue with the user.

* Multiple tools / functions can be added to a single subagent node
* The agent can continue talking while a tool / function executes
* Tool / function results are available to the LLM for generating follow-up responses

## Write Instruction

Subagent nodes only support `Prompt` instructions. Unlike a conversation node, `Static Sentence` is not supported.

Write the instruction to define the task, what information the agent should gather, and when it should use the available tools / functions.

For example:

```text theme={null}
Help the user check their order status. If the user provides an order number,
use the available order lookup tool to retrieve the latest status.
```

## Subagent Node vs Function Node

Subagent nodes and [function nodes](/build/conversation-flow/function-node) serve different purposes:

|                    | Function Node                                                  | Subagent Node                                                                           |
| ------------------ | -------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Execution**      | Deterministic — executes on node entry                         | LLM-driven — called when the LLM decides it's appropriate                               |
| **Tools per node** | One                                                            | Multiple                                                                                |
| **Conversation**   | Not intended for dialogue                                      | Full dialogue with tools available                                                      |
| **Best for**       | Always-execute actions (e.g. always look up an order on entry) | Context-dependent actions during dialogue (e.g. look up an order only if the user asks) |

**Use function nodes** when you want guaranteed execution every time the flow reaches that step.

**Use subagent nodes** when the agent should decide whether and when to call a tool / function based on what the user says.

## Add Tools / Functions

<Steps>
  <Step title="Select a subagent node">
    Click on a subagent node to open its settings panel on the right side.
  </Step>

  <Step title="Add a tool / function">
    In the settings panel, find the **Tools** section and click **+ Add**.

    Select the tool / function type from the dropdown menu.
  </Step>

  <Step title="Configure the tool / function">
    Configure the tool / function based on its type. See the **Available Tool / Function Types** table below for configuration details for each type.
  </Step>

  <Step title="Update the node instruction">
    Update the node prompt to guide the LLM on when to use the tool / function.
  </Step>
</Steps>

## Available Tool / Function Types

| Tool Type                   | Description                                             | Configuration Guide                                               |
| --------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------- |
| Custom Function             | Make HTTP requests to your external APIs                | [Custom Function](/build/conversation-flow/custom-function)       |
| Code Tool                   | Run JavaScript code directly without an external server | [Code Tool](/build/single-multi-prompt/code-tool)                 |
| Check Calendar Availability | Query available time slots via Cal.com                  | [Check Availability](/build/check-availability)                   |
| Book Appointment            | Book calendar events via Cal.com                        | [Book Calendar](/build/book-calendar)                             |
| End Call                    | Terminate the call                                      | [End Call](/build/single-multi-prompt/end-call)                   |
| Transfer Call               | Transfer to a phone number                              | [Transfer Call](/build/single-multi-prompt/transfer-call)         |
| Transfer Agent              | Transfer to another Retell agent                        | [Transfer Agent](/build/single-multi-prompt/transfer-agent)       |
| Press Digit                 | Send DTMF tones                                         | [Press Digit](/build/single-multi-prompt/press-digit)             |
| Send SMS                    | Send a text message                                     | [Send SMS](/build/single-multi-prompt/send-sms)                   |
| Extract Dynamic Variable    | Extract variables from the conversation                 | [Extract Dynamic Variable](/build/single-multi-prompt/extract-dv) |
| MCP Tool                    | Call tools on your MCP server                           | [MCP Node](/build/conversation-flow/mcp-node)                     |

## Execution Speech Settings

Each tool / function has settings that control what the agent says while it is running and after it completes.

### Speak During Execution

When enabled, the agent says a message while the tool / function is executing, for example `One moment, let me check that for you.` This is recommended when the tool / function takes over 1 second, including network latency, so the agent remains responsive.

You can configure how the message is generated:

* **Prompt**: The LLM dynamically generates what to say based on a description you provide.
* **Static Sentence**: The agent speaks the exact text you provide.

### Speak After Execution

When enabled, the agent calls the LLM after the tool / function returns a result so it can speak about the outcome to the user. Turn this off if you want to run it silently.

<Note>
  * **Speak During Execution** is available on: Custom Function, Code Tool, End Call, Transfer Call, Transfer Agent, and MCP Tool.
  * **Speak After Execution** is available on: Custom Function, Code Tool, and MCP Tool.
</Note>

## When Can Transition Happen

* when user is done speaking
* when `Skip Response` is enabled and agent finishes speaking

Tool / function execution happens within the subagent node, so the node can stay active across multiple turns and tool / function calls before it transitions.

## Node Settings

* **Tools**: attach the tools / functions this subagent can use during the conversation.
* **Skip Response**: when enabled, the transition will only have one edge that you can connect, and when agent is done talking, it will transition to the next node via that specific edge.
* **Knowledge Base**: configure node-level knowledge bases to combine topic-specific knowledge with the agent-level knowledge base. Read more at [Knowledge Base](/build/knowledge-base).
* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)
* **Block Interruptions**: when enabled, the agent will not be interrupted by user when speaking.
* **LLM**: choose a different model for this particular node. Will be used for response generation, tool / function selection, and tool / function argument generation.
* **Fine-tuning Examples**: Can finetune conversation response, and transition. Read more at [Finetune Examples](/build/conversation-flow/finetune-examples)

## Best Practices

* **Be explicit in your node instruction.** Tell the agent when each tool / function should be used.
* **Use function nodes for guaranteed execution.** If a tool / function must always run at a certain point in the flow, use a function node instead.
* **Avoid adding too many tools / functions to one subagent node.** If you have many tools / functions, consider splitting them across multiple subagent nodes.

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Function Node Overview

> Call any prebuilt or custom function from a Retell conversation flow function node — agent enters the node, fires the function, then transitions on the result.

Function node is used to call a function, whether it's a pre-built function or a custom function. It's not intended for having a conversation with the user, but agent can still talk while in this node if needed.

The function that associates with this node will be called when entering this node.

<img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/function-node.jpeg?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=0363ae6dc939a92f0d5715d9eaf136af" width="744" height="580" data-path="images/cf/function-node.jpeg" />

## Add a Function

Here you need to add the function first, and then select it inside the node. This way if you delete the node, you don't need to re-create the function again.

<img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/add-function.jpeg?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=df6c4968c14799e166c19b3cb0c679fb" width="587" height="254" data-path="images/cf/add-function.jpeg" />

For specific instructions on different types of functions:

* [Custom Function](/build/conversation-flow/custom-function)
* Pre-built Functions:
  * [Check Calendar Availability](/build/check-availability)
  * [Book Calendar](/build/book-calendar)

## When Can Transition Happen

* if `wait for result` is turned off
  * if `speak during execution` is turned on, the agent will transition once done talking
  * if `speak during execution` is turned off, the agent will transition immediately after function gets invoked, which is right upon entering the node
  * if the user interrupts the agent, the transition can also happen once user is done speaking
* if `wait for result` is turned on
  * if `speak during execution` is turned on, the agent will transition once function result is ready and agent is done talking
  * if `speak during execution` is turned off, the agent will transition once function result is ready
  * if the user interrupts the agent, the transition can also happen once function result is ready and user is done speaking

Given that the function node takes function result into consideration for transition timing, you can write your transition condition to be based on the function result.

## Node Settings

* **Speak During Execution**: when enabled, a text input box will show up where you can write instructions for the agent to follow to generate an utterance like `Let me check that for you.` to say while the function is being executed. You can choose between `Prompt` and `Static Sentence`.
* **Wait for Result**: when enabled, the agent will wait for the function to finish executing before attempting to transition to any other node. This guarantees that when you reach the next node, the result is already ready to be used.
* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)
* **Block Interruptions**: when enabled, the agent will not be interrupted by user when speaking.
* **LLM**: choose a different model for this particular node. Will be used for function argument generation, and potentially speak during execution message generation.
* **Fine-tuning Examples**: Can finetune transition. Read more at [Finetune Examples](/build/conversation-flow/finetune-examples)

## How to Tell User the Result

Since the function node is not intended for having a conversation with the user, you will need to attach a conversation node to the function node to tell the user the result. You can create different conversation nodes for different function results, so that it can engage user in different ways when function result varies.


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Custom function in conversation flow

> Add a custom function to a Retell conversation flow to call your external API mid-call — configure method, URL, headers, parameters, and response extraction.

Custom functions allow you to extend your agent's capabilities by integrating external APIs, providing additional knowledge, or implementing custom logic.

## Steps to create a custom function

When a custom function is called, Retell sends a request (POST, GET, PUT, PATCH, DELETE) to your specified URL with the function name and parameters.
You can include headers and query parameters in the request, and extract data from the response.

<Steps>
  <Step title="Configure function details">
    Add a name and description for the custom function. The name should be unique and separated with underscore.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/custom-function.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=4fea08589e8c8a30fb2cb20f813b02b6" alt="Custom function configuration showing name and description fields" data-path="images/custom-function/custom-function.png" />
    </Frame>

    For example:

    * Name: `get_user_details`
    * Description: `Get user details based on name and age`
  </Step>

  <Step title="Select HTTP Method">
    Choose the HTTP method that Retell will use to send the request to your endpoint. Available methods include:

    <ul>
      <li><strong>GET</strong></li>
      <li><strong>POST</strong></li>
      <li><strong>PATCH</strong></li>
      <li><strong>PUT</strong></li>
      <li><strong>DELETE</strong></li>
    </ul>
  </Step>

  <Step title="Add endpoint URL">
    Add the URL where Retell will send the request to execute your custom function. This has to be a valid URL.
  </Step>

  <Step title="Set request headers (optional)">
    You can define custom headers to include with the request Retell sends to your endpoint.
    Header values can be static or include dynamic variables.

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/headers.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=44295c732912fcb1c3f29259e3f59609" alt="Custom request headers configuration with static and dynamic variable values" data-path="images/custom-function/headers.png" />
    </Frame>
  </Step>

  <Step title="Set query parameters (optional)">
    You can define query parameters to include in the request URL that Retell appends to your endpoint.
    There is a switch to change between parameter description or const value. Both description and const value could be dynamic variables.
    Description will be resolved by LLM while const value will be applied directly to the function.

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/YMPW7mFNipo6shGp/images/custom-function/query-params.png?fit=max&auto=format&n=YMPW7mFNipo6shGp&q=85&s=0a0ccd469644d04aa87c086a8dc68bfb" alt="Query parameter configuration with toggle between description and const value" data-path="images/custom-function/query-params.png" />
    </Frame>
  </Step>

  <Step title="Define parameters">
    Define the parameters for the custom function using JSON schema format or JSON form. Only available for POST, PATCH and PUT requests. For guidance, refer to:

    * [OpenAI's Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
    * [Function Calling Tutorial](https://semaphoreci.com/blog/function-calling)

    **Payload: args only**

    When **Payload: args only** is enabled, the JSON body is only the function's arguments: those fields appear at the top level of the request, not nested under `args`. When it is off, the body follows **Request & response spec** below (`name`, `call`, and `args`).

    <Tip>
      Turn this on when your endpoint expects a flat JSON body that matches your parameter object exactly, with no outer wrapper.
    </Tip>

    Example parameter schema:

    ```json theme={null}
    {
      "type": "object",
      "required": [
        "order_id"
      ],
      "properties": {
        "name": {
          "type": "object",
          "description": "",
          "properties": {
            "first_name": {
              "type": "string",
              "description": "User first name"
            },
            "last_name": {
              "type": "string",
              "const": "{{last_name}}"
            }
          }
        },
        "order_id": {
          "type": "number",
          "const": 1234
        }
      }
    }
    ```

    Example JSON form:

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/json-form.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=6762a2122b6476f28a4f5ed79ffc9423" alt="JSON form interface for defining function parameters" data-path="images/custom-function/json-form.png" />
    </Frame>
  </Step>

  <Step title="Set response variables (optional)">
    Extract values from the API response and save them as <strong>dynamic variables</strong> for use later in the conversation.

    For example, you can extract a user’s name from the response and reference it later using <code>\{\{user\_name}}</code>.

    Example response body

    ```javascript theme={null}
    {
      "properties": {
        "user": {
          "name": "John Doe",
          "age": 26
        }
      }
    }
    ```

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/response-variables.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=389a898c0ab3705d3a83acb61a3a4634" alt="Response variable extraction mapping API response fields to dynamic variables" data-path="images/custom-function/response-variables.png" />
    </Frame>
  </Step>
</Steps>

### Troubleshooting

If you failed to save the custom function, it is likely because the parameters are not valid.

One common mistake is not adding `"type": "object",` to the top level of the JSON schema. We recommend clicking one of the examples and updating accordingly.

## Request & response spec

Retell will send the request to your endpoint with the following request spec.

**Request**

* header
  * `X-Retell-Signature`: encrypted request body using your secret key, used to verify the request is from Retell. Read more below.
  * Content-Type: application/json. This indicates the payload is in JSON format.
* body (in JSON format, for POST, PUT and PATCH request)
  * `name`: the name of the custom function.
  * `call`: the call object for you to get more context about the call, it also contains real time transcript up to the time the request is sent. Check out [Get Call API](/api-references/get-call) for more details about the call object.
  * `args`: the arguments for the custom function, as a JSON object.

<Note>
  If **Payload: args only** is enabled for a function, the body is only the argument object (no `name`, `call`, or `args` wrapper). Parse parameters from the top level of the JSON, and run signature verification on that same body string.
</Note>

<Accordion title="Example request body">
  ```json theme={null}
  {
    "name": "analyze_transcript",
    "args": {
      "analysis_type": "sentiment"
    },
    "call": {
      "call_type": "web_call",
      "access_token": "eyJhbGciOiJIUzI1NiJ9.eyJ2aWRlbyI6eyJyb29tSm9p",
      "call_id": "Jabr9TXYYJHfvl6Syypi88rdAHYHmcq6",
      "agent_id": "oBeDLoLOeuAbiuaMFXRtDOLriTJ5tSxD",
      "agent_version": 1,
      "agent_name": "My Agent",
      "call_status": "ongoing",
      "metadata": {
        "internal_customer_id": "cust_12345"
      },
      "retell_llm_dynamic_variables": {
        "customer_name": "John Doe"
      },
      "custom_sip_headers": {
        "X-Custom-Header": "Custom Value"
      },
      "data_storage_setting": "everything",
      "opt_in_signed_url": true,
      "start_timestamp": 1703302407333,
      "transcript": "Agent: Hi John, thanks for calling! How can I help you today?\nUser: Hi, I'd like to check the status of my recent order.\nAgent: Sure, I'd be happy to help with that. Could you provide me your order number?\nUser: Yes, it's 78542.\nAgent: Let me look that up for you.\n",
      "transcript_object": [
        {
          "role": "agent",
          "content": "Hi John, thanks for calling! How can I help you today?",
          "words": [
            { "word": "Hi", "start": 0.5, "end": 0.7 },
            { "word": "John,", "start": 0.8, "end": 1.1 },
            { "word": "thanks", "start": 1.2, "end": 1.5 },
            { "word": "for", "start": 1.5, "end": 1.6 },
            { "word": "calling!", "start": 1.7, "end": 2.1 },
            { "word": "How", "start": 2.2, "end": 2.4 },
            { "word": "can", "start": 2.4, "end": 2.5 },
            { "word": "I", "start": 2.5, "end": 2.6 },
            { "word": "help", "start": 2.6, "end": 2.8 },
            { "word": "you", "start": 2.8, "end": 2.9 },
            { "word": "today?", "start": 2.9, "end": 3.3 }
          ]
        },
        {
          "role": "user",
          "content": "Hi, I'd like to check the status of my recent order.",
          "words": [
            { "word": "Hi,", "start": 4.0, "end": 4.3 },
            { "word": "I'd", "start": 4.4, "end": 4.6 },
            { "word": "like", "start": 4.6, "end": 4.8 },
            { "word": "to", "start": 4.8, "end": 4.9 },
            { "word": "check", "start": 4.9, "end": 5.2 },
            { "word": "the", "start": 5.2, "end": 5.3 },
            { "word": "status", "start": 5.3, "end": 5.7 },
            { "word": "of", "start": 5.7, "end": 5.8 },
            { "word": "my", "start": 5.8, "end": 5.9 },
            { "word": "recent", "start": 5.9, "end": 6.2 },
            { "word": "order.", "start": 6.2, "end": 6.6 }
          ]
        },
        {
          "role": "agent",
          "content": "Sure, I'd be happy to help with that. Could you provide me your order number?",
          "words": [
            { "word": "Sure,", "start": 7.0, "end": 7.4 },
            { "word": "I'd", "start": 7.5, "end": 7.7 },
            { "word": "be", "start": 7.7, "end": 7.8 },
            { "word": "happy", "start": 7.8, "end": 8.1 },
            { "word": "to", "start": 8.1, "end": 8.2 },
            { "word": "help", "start": 8.2, "end": 8.4 },
            { "word": "with", "start": 8.4, "end": 8.6 },
            { "word": "that.", "start": 8.6, "end": 8.9 },
            { "word": "Could", "start": 9.0, "end": 9.2 },
            { "word": "you", "start": 9.2, "end": 9.3 },
            { "word": "provide", "start": 9.3, "end": 9.6 },
            { "word": "me", "start": 9.6, "end": 9.7 },
            { "word": "your", "start": 9.7, "end": 9.9 },
            { "word": "order", "start": 9.9, "end": 10.2 },
            { "word": "number?", "start": 10.2, "end": 10.6 }
          ]
        },
        {
          "role": "user",
          "content": "Yes, it's 78542.",
          "words": [
            { "word": "Yes,", "start": 11.5, "end": 11.8 },
            { "word": "it's", "start": 11.9, "end": 12.1 },
            { "word": "78542.", "start": 12.2, "end": 12.9 }
          ]
        },
        {
          "role": "agent",
          "content": "Let me look that up for you.",
          "words": [
            { "word": "Let", "start": 13.5, "end": 13.7 },
            { "word": "me", "start": 13.7, "end": 13.8 },
            { "word": "look", "start": 13.8, "end": 14.0 },
            { "word": "that", "start": 14.0, "end": 14.2 },
            { "word": "up", "start": 14.2, "end": 14.3 },
            { "word": "for", "start": 14.3, "end": 14.5 },
            { "word": "you.", "start": 14.5, "end": 14.8 }
          ]
        }
      ],
      "transcript_with_tool_calls": [
        {
          "role": "agent",
          "content": "Hi John, thanks for calling! How can I help you today?",
          "words": [
            { "word": "Hi", "start": 0.5, "end": 0.7 },
            { "word": "John,", "start": 0.8, "end": 1.1 }
          ]
        },
        {
          "role": "user",
          "content": "Hi, I'd like to check the status of my recent order.",
          "words": [
            { "word": "Hi,", "start": 4.0, "end": 4.3 }
          ]
        },
        {
          "role": "agent",
          "content": "Sure, I'd be happy to help with that. Could you provide me your order number?",
          "words": [
            { "word": "Sure,", "start": 7.0, "end": 7.4 }
          ]
        },
        {
          "role": "user",
          "content": "Yes, it's 78542.",
          "words": [
            { "word": "Yes,", "start": 11.5, "end": 11.8 }
          ]
        },
        {
          "role": "agent",
          "content": "Let me look that up for you.",
          "words": [
            { "word": "Let", "start": 13.5, "end": 13.7 }
          ]
        },
        {
          "role": "tool_call_invocation",
          "tool_call_id": "tool_call_abc123",
          "name": "analyze_transcript",
          "arguments": "{\"analysis_type\": \"sentiment\"}"
        }
      ],
      "latency": {
        "e2e": {
          "p50": 650,
          "p90": 900,
          "p95": 1100,
          "p99": 1500,
          "max": 1600,
          "min": 400,
          "num": 3,
          "values": [400, 650, 1600]
        }
      }
    }
  }
  ```
</Accordion>

The request will timeout in your specified timeout period, or 2 minutes if not specified. When request fails, it will be retried up to 2 times.

**Response**

Response should have a status code between 200-299 to indicate success of HTTP request.
Response to the request can be in various formats:

* string
* buffer
* JSON object
* blob

All these formats will be converted to string before sending to LLM for further processing.

<Note>
  The function result is capped at 15000 characters to prevent overloading LLM context window.
</Note>

## Verifying Request is from Retell

To verify that the request is coming from Retell, you can check the `X-Retell-Signature` header. The value is an encrypted request body using your secret key.
For `GET` and `DELETE` requests, the request body is empty. You can use empty string in the verify function.

```javascript theme={null}
import { Retell } from "retell-sdk";
import express from "express";

const app = express();
// Use raw body for signature verification, not JSON.stringify(req.body).
app.use(express.raw({ type: "application/json" }));

app.post("/check-weather", async (req, res) => {
  const rawBody = req.body.toString("utf-8");
  if (
    !Retell.verify(
      rawBody,
      process.env.RETELL_API_KEY,
      req.headers["x-retell-signature"],
    )
  ) {
    console.error("Invalid signature");
    return;
  }
  const content = JSON.parse(rawBody);
  if (content.args.city === "New York") {
    return res.json("25f and sunny");
  } else {
    return res.json("20f and cloudy");
  }
});
```

```Python theme={null}
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from retell import Retell

retell = Retell(api_key=os.environ["RETELL_API_KEY"])

@app.post("/check-weather")
async def check-weather(request: Request):
    try:
        raw_body = (await request.body()).decode("utf-8")
        valid_signature = retell.verify(
            raw_body,
            api_key=str(os.environ["RETELL_API_KEY"]),
            signature=str(request.headers.get("X-Retell-Signature")),
        )
        if not valid_signature:
            print("Received Unauthorized")
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})
        post_data = json.loads(raw_body)
        args = post_data["args"]
        if args["city"] == "New York":
            return JSONResponse(status_code=200, content={"result": "25f and sunny"})
        else:
            return JSONResponse(status_code=200, content={"result": "20f and cloudy"})
    except Exception as err:
        print(f"Error in webhook: {err}")
        return JSONResponse(
            status_code=500, content={"message": "Internal Server Error"}
        )
```

<Note>You can also secure your server from public network by only allowlisting Retell IP addresses: `100.20.5.228`</Note>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# End call

> Add the End Call tool to a Retell single or multi-prompt agent and define when the agent should automatically hang up based on conversation conditions.

By default, the agent won't end the call automatically. You'll need to configure when and how the call should be terminated using the end call tool.

<Steps>
  <Step title="Add End Call Tool">
    Click "+ Add" in the tools section and select "End Call" from the dropdown menu.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/end_call.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=53ae902cbe4dbfa4edff788fff3ca94e" alt="Adding end call tool" data-path="images/end_call.png" />
    </Frame>
  </Step>

  <Step title="Configure Termination Conditions">
    Define specific conditions under which the call should be terminated. For example:

    * "If the user says 'thank you', 'goodbye', or 'bye', use the end\_call tool to terminate the conversation."

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/end_call_2.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=6fb7c7e1b1183a8b25eee5cfab6fb885" alt="Configuring end call conditions" data-path="images/end_call_2.png" />
    </Frame>
  </Step>

  <Step title="Update the Prompt">
    Enhance the agent's understanding by incorporating the end call conditions into the prompt. Include specific instructions such as:

    "If the user says 'thank you', 'goodbye', or 'bye', use the end\_call tool to terminate the conversation."

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/end_call_3.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=c9f4683f55f36dae81c83b91bd607ad0" alt="Adding end call instructions to prompt" data-path="images/end_call_3.png" />
    </Frame>
  </Step>
</Steps>

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Integrate any system with custom function

> Add a custom function to a Retell single or multi-prompt agent so it can call your API mid-call — set URL, method, headers, parameters, and response handling.

Custom functions allow you to extend your agent's capabilities by integrating external APIs, providing additional knowledge, or implementing custom logic.

## Steps to create a custom function

You can create custom functions that will be called by the LLM when needed. When called, Retell sends a POST request to your specified URL with the function name and parameters.

<Steps>
  <Step title="Add custom function in dashboard">
    Click "+ Add" in the tools section and select "Custom Function" from the dropdown menu.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/end_call.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=53ae902cbe4dbfa4edff788fff3ca94e" alt="Adding custom function" data-path="images/end_call.png" />
    </Frame>
  </Step>

  <Step title="Configure function details">
    Add a name and description for the custom function. The name should be unique and separated with underscore.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/custom-function.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=4fea08589e8c8a30fb2cb20f813b02b6" alt="Custom function name and description fields" data-path="images/custom-function/custom-function.png" />
    </Frame>

    For example:

    * Name: `get_user_details`
    * Description: `Get user details based on name and age`
  </Step>

  <Step title="Select HTTP Method">
    Choose the HTTP method that Retell will use to send the request to your endpoint. Available methods include:

    <ul>
      <li><strong>GET</strong></li>
      <li><strong>POST</strong></li>
      <li><strong>PATCH</strong></li>
      <li><strong>PUT</strong></li>
      <li><strong>DELETE</strong></li>
    </ul>
  </Step>

  <Step title="Add endpoint URL">
    Add the URL where Retell will send the request to execute your custom function. This has to be a valid URL.
  </Step>

  <Step title="Set request headers (optional)">
    You can define custom headers to include with the request Retell sends to your endpoint.
    Header values can be static or include dynamic variables.

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/headers.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=44295c732912fcb1c3f29259e3f59609" data-path="images/custom-function/headers.png" />
    </Frame>
  </Step>

  <Step title="Set query parameters (optional)">
    You can define query parameters to include in the request URL that Retell appends to your endpoint.
    There is a switch to change between parameter description or const value. Both description and const value could be dynamic variables.
    Description will be resolved by LLM while const value will be applied directly to the function.

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/YMPW7mFNipo6shGp/images/custom-function/query-params.png?fit=max&auto=format&n=YMPW7mFNipo6shGp&q=85&s=0a0ccd469644d04aa87c086a8dc68bfb" data-path="images/custom-function/query-params.png" />
    </Frame>
  </Step>

  <Step title="Define parameters">
    Define the parameters for the custom function using JSON schema format or JSON form. Only available for POST, PATCH and PUT requests. For guidance, refer to:

    * [OpenAI's Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
    * [Function Calling Tutorial](https://semaphoreci.com/blog/function-calling)

    **Payload: args only**

    When **Payload: args only** is enabled, the JSON body is only the function's arguments: those fields appear at the top level of the request, not nested under `args`. When it is off, the body follows **Request & response spec** below (`name`, `call`, and `args`).

    <Tip>
      Turn this on when your endpoint expects a flat JSON body that matches your parameter object exactly, with no outer wrapper.
    </Tip>

    Example parameter schema:

    ```json theme={null}
    {
      "type": "object",
      "required": [
        "order_id"
      ],
      "properties": {
        "name": {
          "type": "object",
          "description": "",
          "properties": {
            "first_name": {
              "type": "string",
              "description": "User first name"
            },
            "last_name": {
              "type": "string",
              "const": "{{last_name}}"
            }
          }
        },
        "order_id": {
          "type": "number",
          "const": 1234
        }
      }
    }
    ```

    Example JSON form:

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/json-form.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=6762a2122b6476f28a4f5ed79ffc9423" data-path="images/custom-function/json-form.png" />
    </Frame>
  </Step>

  <Step title="Set response variables (optional)">
    Extract values from the API response and save them as <strong>dynamic variables</strong> for use later in the conversation.

    For example, you can extract a user’s name from the response and reference it later using <code>\{\{user\_name}}</code>.

    Example response body

    ```javascript theme={null}
    {
      "properties": {
        "user": {
          "name": "John Doe",
          "age": 26
        }
      }
    }
    ```

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/response-variables.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=389a898c0ab3705d3a83acb61a3a4634" data-path="images/custom-function/response-variables.png" />
    </Frame>
  </Step>

  <Step title="Configure speech behavior">
    Set up how the agent should handle speech during and after function execution. These two options are controlling agent's behavior when user is not talking during the function call period. If user interrupts or talks, the agent would respond normally regardless of these settings.
    Note: both **Speak During Execution** and **Speak After Execution** are `Prompt` based. LLM will generate the message based on the config and the conversation.

    * **Speak during execution**: Whether the agent would speak the moment the function is called. Note that currently agent would speak just for one time during the beginning of the function call.
      * Enable for user-facing actions (e.g., getting weather information)
      * Disable for background tasks (e.g., attaching notes to call)

    * **Speak after execution**: Whether the agent would keep talking / do other actions (maybe call another function) after the function call is completed. You can use this to let agent tell user the result of the function call, continue the conversation, execute another task, etc after the function call is completed, without the need to wait for user to say anything to trigger a response.
      * Probably should enable for almost all cases, except for ones that are like press a digit kind of task where you don't expect the agent to keep talking.
  </Step>

  <Step title="Update prompt for function">
    It's best to include in the prompt explicitly when is the best time to invoke the custom function. For example:

    ```
    When user provided the city name, please get the weather for that city by calling the `get_weather` function.
    ```
  </Step>
</Steps>

### Troubleshooting

If you failed to save the custom function, it is likely because the parameters are not valid.

One common mistake is not adding `"type": "object",` to the top level of the JSON schema. We recommend clicking one of the examples and updating accordingly.

## Request & response spec

Retell will send the request to your endpoint with the following request spec.

**Request**

* header
  * `X-Retell-Signature`: encrypted request body using your secret key, used to verify the request is from Retell. Read more below.
  * Content-Type: application/json. This indicates the payload is in JSON format.
* body (in JSON format, for POST, PUT and PATCH request)
  * `name`: the name of the custom function.
  * `call`: the call object for you to get more context about the call, it also contains real time transcript up to the time the request is sent. Check out [Get Call API](/api-references/get-call) for more details about the call object.
  * `args`: the arguments for the custom function, as a JSON object.

<Note>
  If **Payload: args only** is enabled for a function, the body is only the argument object (no `name`, `call`, or `args` wrapper). Parse parameters from the top level of the JSON, and run signature verification on that same body string.
</Note>

The request will timeout in your specified timeout period, or 2 minutes if not specified. When request fails, it will be retried up to 2 times.

**Response**

Response should have a status code between 200-299 to indicate success of HTTP request.
Response to the request can be in various formats:

* string
* buffer
* JSON object
* blob

All these formats will be converted to string before sending to LLM for further processing.

<Note>
  The function result is capped at 15000 characters to prevent overloading LLM context window.
</Note>

## Verifying Request is from Retell

To verify that the request is coming from Retell, you can check the `X-Retell-Signature` header.

The value is an encrypted request body using your secret key.
For `GET` and `DELETE` requests, the request body is empty. You can use empty string in the verify function.

```javascript theme={null}
import { Retell } from "retell-sdk";
import express from "express";

const app = express();
// Use raw body for signature verification, not JSON.stringify(req.body).
app.use(express.raw({ type: "application/json" }));

app.post("/check-weather", async (req, res) => {
  const rawBody = req.body.toString("utf-8");
  if (
    !Retell.verify(
      rawBody,
      process.env.RETELL_API_KEY,
      req.headers["x-retell-signature"],
    )
  ) {
    console.error("Invalid signature");
    return;
  }
  const content = JSON.parse(rawBody);
  if (content.args.city === "New York") {
    return res.json("25f and sunny");
  } else {
    return res.json("20f and cloudy");
  }
});
```

```Python theme={null}
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from retell import Retell

retell = Retell(api_key=os.environ["RETELL_API_KEY"])

@app.post("/check-weather")
async def check-weather(request: Request):
    try:
        raw_body = (await request.body()).decode("utf-8")
        valid_signature = retell.verify(
            raw_body,
            api_key=str(os.environ["RETELL_API_KEY"]),
            signature=str(request.headers.get("X-Retell-Signature")),
        )
        if not valid_signature:
            print("Received Unauthorized")
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})
        post_data = json.loads(raw_body)
        args = post_data["args"]
        if args["city"] == "New York":
            return JSONResponse(status_code=200, content={"result": "25f and sunny"})
        else:
            return JSONResponse(status_code=200, content={"result": "20f and cloudy"})
    except Exception as err:
        print(f"Error in webhook: {err}")
        return JSONResponse(
            status_code=500, content={"message": "Internal Server Error"}
        )
```

<Note>You can also secure your server from public network by only allowlisting Retell IP addresses: `100.20.5.228`</Note>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Code Node

> Run JavaScript inline in a Retell conversation flow with a code node — no external server needed, perfect for formatting, calculations, and quick lookups.

Code node executes JavaScript code when the agent enters it. Unlike [custom functions](/build/conversation-flow/custom-function), code nodes run directly in Retell's sandbox — no external server needed. The node is not intended for having a conversation with the user, but the agent can still talk while code is running if needed.

<Frame>
  <img src="https://mintcdn.com/retellai/9xto-Or-KLZnnbLr/images/cf/code-node.png?fit=max&auto=format&n=9xto-Or-KLZnnbLr&q=85&s=47f4edf2355f4b2f96ca573723392a7f" alt="Code node on the conversation flow canvas" width="150" height="159" data-path="images/cf/code-node.png" />
</Frame>

## Code Node vs Custom Function

|                   | Code Node                                                   | Custom Function                                  |
| ----------------- | ----------------------------------------------------------- | ------------------------------------------------ |
| **Runs**          | JavaScript in Retell's sandbox                              | HTTP request to your server                      |
| **Requires**      | Nothing — runs directly                                     | Your own API endpoint                            |
| **Best for**      | Data transformation, simple API calls, logic & calculations | Complex integrations, accessing internal systems |
| **Max code size** | 5,000 characters                                            | N/A (runs on your server)                        |

<Warning>
  Code Node is designed for lightweight logic like formatting, calculations, and simple read-only lookups. Do not use it to access internal systems, write to production databases, or handle sensitive credentials. Both `dv` and `metadata` values are stored in plaintext with every call record. For integrations that require authentication, secrets management, or write access, use a [Custom Function](/build/conversation-flow/custom-function) hosted on your own backend. See [Security and Architecture Guidance](#security-and-architecture-guidance) for details.
</Warning>

## Write Your Code

<Steps>
  <Step title="Add a Code Node">
    Click the Code node from the left sidebar to add it to the canvas.

    <Frame>
      <img src="https://mintcdn.com/retellai/9xto-Or-KLZnnbLr/images/cf/add-code-node.png?fit=max&auto=format&n=9xto-Or-KLZnnbLr&q=85&s=f3a2d7d9e7db9ff3687f4abf9573737a" alt="Left sidebar showing the Code node option" width="220" height="215" data-path="images/cf/add-code-node.png" />
    </Frame>
  </Step>

  <Step title="Open the code editor">
    Click **Open** on the code node to launch the code editor.
  </Step>

  <Step title="Write JavaScript">
    Write your JavaScript code in the editor. You have access to dynamic variables, call metadata, and the `fetch` function for HTTP requests. See [JavaScript Environment](#javascript-environment) below for details.

    <Frame>
      <img src="https://mintcdn.com/retellai/9xto-Or-KLZnnbLr/images/cf/code-node-modal.png?fit=max&auto=format&n=9xto-Or-KLZnnbLr&q=85&s=d25f6e4527c4e6383cc35cfb57291c75" alt="Code editor with JavaScript code and configuration options" width="1078" height="815" data-path="images/cf/code-node-modal.png" />
    </Frame>

    ```javascript theme={null}
    // Example: look up an order and return the status
    const response = await fetch("https://api.example.com/orders/" + dv.order_id);
    const data = await response.json();
    return { status: data.status, estimated_delivery: data.delivery_date };
    ```
  </Step>

  <Step title="Set response variables (optional)">
    Use **Store Fields as Variables** to extract values from your code's return value and save them as dynamic variables. Specify a variable name and the JSON path to the value.

    For example, if your code returns `{ "status": "shipped", "estimated_delivery": "March 25" }`:

    | Variable Name   | JSON Path            | Extracted Value |
    | --------------- | -------------------- | --------------- |
    | `order_status`  | `status`             | `"shipped"`     |
    | `delivery_date` | `estimated_delivery` | `"March 25"`    |

    These variables can then be referenced as `{{order_status}}` and `{{delivery_date}}` in other nodes.
  </Step>

  <Step title="Test your code">
    Click **Run Code** at the bottom of the editor to test. Use the **Dynamic Variables** dropdown in the editor to set test values for your variables (e.g., give `customer_name` a value of "John Doe") — these values are only used during testing and won't affect your live agent. The output panel will show the result and any `console.log()` output.

    <Frame>
      <img src="https://mintcdn.com/retellai/9xto-Or-KLZnnbLr/images/cf/code-node-test.png?fit=max&auto=format&n=9xto-Or-KLZnnbLr&q=85&s=178cd6a2df2dacc07307b31d22451430" alt="Code editor showing test output after clicking Run Code" width="1078" height="815" data-path="images/cf/code-node-test.png" />
    </Frame>
  </Step>
</Steps>

## JavaScript Environment

Your code runs in a JavaScript sandbox with the following globals available. The code editor provides **autocomplete** — as you type, it will suggest available globals, dynamic variable names, and built-in functions.

### `dv` — Dynamic Variables

Access your agent's dynamic variables as properties on the `dv` object. All values are strings.

```javascript theme={null}
const name = dv.customer_name;       // "John Doe"
const orderId = dv.order_id;         // "78542"
const total = parseFloat(dv.amount); // Convert to number if needed
```

### `metadata` — Call Metadata

Access metadata passed when the call was created via the API. This is the same object you pass in the `metadata` field of the [Create Call](/api-references/create-phone-call) API.

```javascript theme={null}
const customerId = metadata.customer_id;
const priority = metadata.priority_level;
```

<Warning>
  Both `dv` and `metadata` values are stored in plaintext with every call record and are visible in call logs and API responses. Do not use them to pass API keys, database credentials, or other sensitive secrets. See [Security and Architecture Guidance](#security-and-architecture-guidance) for more details.
</Warning>

### `fetch(url)` — HTTP Requests

Make HTTP requests to external APIs. Works like the standard [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API).

```javascript theme={null}
// GET request
const response = await fetch("https://api.example.com/data");
const data = await response.json();

// POST request
const response = await fetch("https://api.example.com/submit", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: dv.customer_name })
});
```

### `console.log()` — Debugging

Log output for debugging. Logs appear in the test output panel when using **Run Code**, and are also available in call logs.

```javascript theme={null}
console.log("Customer:", dv.customer_name);
console.log("API response:", JSON.stringify(data));
```

<Note>
  * Your code can return any value (object, string, number) or return nothing at all.
  * Standard JavaScript built-ins are available: `Math`, `JSON`, `Date`, `Array`, `Object`, `String` methods, etc.
  * External packages (`require`, `import`) are **not** available. Use `fetch()` for external integrations.
  * Code is limited to 5,000 characters.
</Note>

## Examples

### Format data from dynamic variables

```javascript theme={null}
// Combine and format customer info
const fullName = dv.first_name + " " + dv.last_name;
const summary = `Customer ${fullName} (ID: ${dv.customer_id}) requested a callback.`;
return { full_name: fullName, summary: summary };
```

### Fetch data from a public API

```javascript theme={null}
// Look up current weather for the customer's city
const response = await fetch("https://api.weatherapi.com/v1/current.json?q=" + encodeURIComponent(dv.city));
const weather = await response.json();
return {
  location: weather.location.name,
  temperature: weather.current.temp_f + "°F",
  condition: weather.current.condition.text
};
```

### Conditional logic with API call

```javascript theme={null}
// Route based on customer tier
const response = await fetch("https://api.example.com/customers/" + dv.customer_id);
const customer = await response.json();

if (customer.tier === "premium") {
  return { action: "priority_support", wait_time: "0 minutes" };
} else if (customer.tier === "standard") {
  return { action: "standard_queue", wait_time: "5 minutes" };
} else {
  return { action: "general_queue", wait_time: "10 minutes" };
}
```

## Security and Architecture Guidance

Code Node is best for lightweight, low-risk logic that runs entirely within Retell's sandbox. As your integration needs grow, use a [Custom Function](/build/conversation-flow/custom-function) hosted on your own backend where you control the security boundary.

| Use case                                                                             | Recommended             |
| ------------------------------------------------------------------------------------ | ----------------------- |
| Formatting, calculations, string cleanup                                             | Code Node               |
| Simple read-only lookups to low-risk public APIs                                     | Code Node, with caution |
| Accessing internal systems or private APIs                                           | Custom Function         |
| Writing to CRM, EHR, booking, payment, or ticketing systems                          | Custom Function         |
| Workflows requiring secrets, audit logs, retries, idempotency, or policy enforcement | Custom Function         |

<Warning>
  **Do not treat dynamic variables or metadata as a secret vault.** Avoid placing long-lived API keys, database credentials, or other sensitive secrets in dynamic variables or call metadata for use in Code Node. Both `dv` and `metadata` values are stored in plaintext with every call record — anything you pass in will be visible in call logs and API responses. They are not designed for secret management. Prefer short-lived tokens where possible, and use a [Custom Function](/build/conversation-flow/custom-function) for integrations that require sensitive credentials or customer-controlled secret handling.
</Warning>

<Warning>
  **Use `fetch()` with caution.** Enabling outbound HTTP requests from an LLM-invoked tool increases security and operational risk. Treat any use of `fetch()` as an external integration surface. Prefer read-only requests to low-risk, public endpoints. Avoid direct state-changing actions (writes, payments, deletions) unless you fully understand the risks and have appropriate controls in place.
</Warning>

<Note>
  **Keep production logic in your own backend.** For anything involving sensitive credentials, direct writes to production systems, payment actions, regulated data workflows, or business-critical operations that require strict authentication, validation, audit logging, idempotency, or approval controls — use a [Custom Function](/build/conversation-flow/custom-function) hosted on your own backend. Code Node should be reserved for data transformation, calculations, and simple read-only lookups.
</Note>

## Response Variables

Response variables let you extract specific values from your code's return value and store them as dynamic variables for use in other nodes.

Specify each variable as a **name** and a **JSON path** using dot notation:

| Path Syntax     | Example         | Extracts               |
| --------------- | --------------- | ---------------------- |
| Top-level field | `status`        | `result.status`        |
| Nested field    | `data.order.id` | `result.data.order.id` |
| Array element   | `items[0].name` | First item's name      |

If a path doesn't exist in the return value, the variable is skipped (no error).

## When Can Transition Happen

* If **Wait for Result** is turned off:
  * If **Speak During Execution** is on, the agent transitions once done talking
  * If **Speak During Execution** is off, the agent transitions immediately after code starts running
  * If the user interrupts the agent, transition can happen once the user is done speaking
* If **Wait for Result** is turned on:
  * If **Speak During Execution** is on, the agent transitions once code finishes and agent is done talking
  * If **Speak During Execution** is off, the agent transitions once code finishes
  * If the user interrupts the agent, transition can happen once code finishes and user is done speaking

Since the code node considers the code result for transition timing, you can write [transition conditions](/build/conversation-flow/transition-condition) based on the code result or the extracted dynamic variables.

## Node Settings

* **Speak During Execution**: When enabled, the agent says something while the code runs (e.g., "Let me check that for you."). Choose between **Prompt** (LLM generates the message) or **Static Text** (exact text you provide).
* **Wait for Result**: When enabled, the agent waits for the code to finish before transitioning. This guarantees that when you reach the next node, the result and extracted variables are ready.
* **Timeout**: How long the code can run before timing out. Range: 5–60 seconds. Default: 30 seconds.
* **Global Node**: Read more at [Global Node](/build/conversation-flow/global-node).
* **Block Interruptions**: When enabled, the agent will not be interrupted by the user when speaking.
* **LLM**: Choose a different model for this node. Used for speak during execution message generation if set to Prompt.
* **Fine-tuning Examples**: Can finetune transition. Read more at [Finetune Examples](/build/conversation-flow/finetune-examples).

## FAQ

<AccordionGroup>
  <Accordion title="Can I use npm packages or external libraries?">
    No. The code runs in a lightweight JavaScript sandbox without access to `require` or `import`. You can use all standard JavaScript built-ins (`Math`, `JSON`, `Date`, `Array` methods, etc.) and the `fetch()` function for external API calls.
  </Accordion>

  <Accordion title="What happens if my code times out?">
    If your code exceeds the configured timeout (default 30 seconds), it will be stopped and treated as a failed execution. The result will contain a timeout error message. You can adjust the timeout in Node Settings (5–60 seconds).
  </Accordion>

  <Accordion title="What happens if my code throws an error?">
    If your code throws an error or crashes, the execution is marked as failed and the error message is returned as the result. Response variables will not be extracted. You can use `try/catch` in your code to handle errors gracefully.
  </Accordion>

  <Accordion title="Can I use async/await?">
    Yes. The `fetch()` function is async, so you can use `await` to wait for HTTP responses. Top-level `await` is supported.
  </Accordion>

  <Accordion title="Is there a limit on the result size?">
    Yes, the result is capped at 15,000 characters to prevent overloading the LLM context.
  </Accordion>
</AccordionGroup>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Call transfer node in conversation flow

> Use a call transfer node to hand a Retell phone call off to a different number — supports Retell and imported numbers, with optional pre-transfer messages.

<Warning>
  This node only works during phone calls instead of web calls. It's available for Retell numbers and imported numbers.
</Warning>

Call transfer node is used to transfer the call to another number. The agent will not speak when it's in this node. If you want the agent to say things like `Let me transfer you right away` before performing the actual transfer, you can do so by putting a conversation node (with `skip response` turned on) before this node.

<Frame>
  <img src="https://mintcdn.com/retellai/CusS6gidcUzaxvEx/images/cf/transfer-call-node.png?fit=max&auto=format&n=CusS6gidcUzaxvEx&q=85&s=d00f0caa67dcf341e314c56091eba8d7" width="1156" height="1082" data-path="images/cf/transfer-call-node.png" />
</Frame>

## When Can Transition Happen

Transition happens when transfer fails. There's already a pre-populated edge for this, feel free to connect that to a node to handle transfer failure.

## Configure Transfer

<Steps>
  <Step title="Setup Transfer To Target">
    Set transfer number to be either:

    * a number in e.164 format, or a SIP URI in the format of `sip:username@domain` (e.g. `sip:user@retellai.com`).
    * [dynamic variable](/build/dynamic-variables) that gets substituted at runtime
    * (Optional) if your transfer destination is not in e.164 format then you can choose to keep the input as is by choosing raw format. This only applies when you are using custom telephony and does not apply when you are using Retell Telephony. This can be useful when you want to transfer to internal pseudo numbers.

    <Frame>
      <img src="https://mintcdn.com/retellai/CusS6gidcUzaxvEx/images/cf/transfer-call-e164.png?fit=max&auto=format&n=CusS6gidcUzaxvEx&q=85&s=ba54ab3635ca7cd934d213eb68414143" width="1182" height="1098" data-path="images/cf/transfer-call-e164.png" />
    </Frame>

    Set the transfer number extension if needed. Extension must be 0-9, '\*', '#' (E.g. 123#)
  </Step>

  <Step title="Configure Transfer Type">
    Choose between cold transfer, warm transfer, or agentic warm transfer:

    * **Cold transfer**: The call is transferred to a destination number and that's it.
    * **Warm transfer**: After the call is transferred to the destination number, the AI agent can attempt to detect if the other side is human, leave private messages that are not heard by user, do a three-way introduce, etc. This is a direct warm transfer flow (not agentic warm transfer). (more details below).
    * **Agentic warm transfer**: A transfer agent has a two-way conversation with the transfer target and then decides to either bridge the original caller or cancel the transfer.
  </Step>

  <Step title="Configure Transfer Dial Timeout (All Modes)">
    Use this slider to set how long the destination should ring for this transfer.

    * The value you set here applies only to this transfer.
    * If you do not set it, we use your agent-level ring duration setting.
    * This works for cold transfer, warm transfer, and agentic warm transfer.

    <Frame>
      <img src="https://mintcdn.com/retellai/CusS6gidcUzaxvEx/images/cf/transfer-dial-timeout.png?fit=max&auto=format&n=CusS6gidcUzaxvEx&q=85&s=e4777c28ca59cfe802877a72cdef8cd8" width="798" height="166" data-path="images/cf/transfer-dial-timeout.png" />
    </Frame>
  </Step>

  <Step title="Configure Caller ID (Optional)">
    You can configure which caller id shows up to the transfer destination:

    1. **Retell Agent's number**: The transfer destination will see the Retell agent's number

    2. **User's Number**: The transfer destination will see the number of the user. Please note that the telephony provider must support caller id override for this feature to work.
       * For warm transfer, it's using SIP DIAL, and we are setting `from` and `P-Asserted-Identity` headers to the user's number.
       * For cold transfer, it's using SIP REFER, and it's up to the telephony provider to support caller id override for SIP REFER.
       * Retell Twilio numbers support showing user's number on both warm and cold transfer, Retell Telnyx numbers only support this when using SIP REFER via cold transfer.
       * If caller id override is not supported, the transfer would fail.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/_QrxQEoxP5f0zRlL/images/telephony/caller-id-setting.png?fit=max&auto=format&n=_QrxQEoxP5f0zRlL&q=85&s=6f73a184623714e31913189556b39f59" data-path="images/telephony/caller-id-setting.png" />
    </Frame>
  </Step>

  <Step title="Configure Cold Transfer Specific Settings">
    For cold transfer, you can configure the following settings:

    * **Cold transfer modes**: You can choose `SIP INVITE` or `SIP REFER`.
    * **What SIP is**: SIP (Session Initiation Protocol) is the signaling protocol used to set up and route VoIP calls.
    * **SIP INVITE**: This is the default transfer method. It establishes or updates the active call path, then bridges the transfer. You can choose which caller ID to use.
    * **SIP REFER**: This asks an endpoint to start a separate call to a third party for transfer handoff. Use this only if your telephony provider supports SIP REFER. Caller ID behavior depends on provider support and configuration.
    * **Caller ID behavior**: `show transferee as caller` only applies when cold transfer mode is `SIP INVITE`.

    <Frame>
      <img src="https://mintcdn.com/retellai/CusS6gidcUzaxvEx/images/cf/cold-transfer-settings.png?fit=max&auto=format&n=CusS6gidcUzaxvEx&q=85&s=c94a233055d022b53239d625249633d8" width="794" height="1092" data-path="images/cf/cold-transfer-settings.png" />
    </Frame>
  </Step>

  <Step title="Configure Warm Transfer Specific Settings (Non-Agentic)">
    For warm transfer (non-agentic), you can configure the following settings:

    * **On-hold music**: The audio played to the caller while they are on hold. The default is a standard ringtone.
    * **Navigate IVR**: Provide a prompt to help you navigate if the transfer target is an IVR system.
    * **Enable human detection**: When enabled, the agent will check if a human is present after the transfer target answers. The original caller will only be connected once a human is detected.
    * **Auto-greet**: If enabled, the agent will immediately say “Hello” when the transfer target picks up. This encourages a response, increasing the likelihood of detecting a human.
    * **Agent detection timeout**: The maximum amount of time the AI agent will wait to determine whether the transfer target is a human. The caller is connected only if human detection succeeds within this timeframe. Otherwise, the transfer is marked as failed. The default timeout is 30 seconds.
    * **Whisper message (optional)**: A message spoken privately to the transfer target before connecting them to the original caller.
    * **Three-way message (optional)**: A message spoken to both the transfer target and the original caller once the connection is established.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/_QrxQEoxP5f0zRlL/images/telephony/warm-transfer-settings.png?fit=max&auto=format&n=_QrxQEoxP5f0zRlL&q=85&s=d813bc6a8f2fdb7c3dbb1ae8b8078c4b" data-path="images/telephony/warm-transfer-settings.png" />
    </Frame>
  </Step>

  <Step title="Configure Agentic Warm Transfer Specific Settings">
    For agentic warm transfer, you can configure the following settings:

    * **On-hold music**: The audio played to the original caller while the transfer agent is working.
    * **Two-way conversation agent**: Select the transfer agent (and version) that has a two-way conversation with the transfer target and decides whether to bridge or cancel.
    * **Wait time for agent answer**: Set how long to wait for the transfer agent to make a decision.
    * **Three-way ring tone**: While the transfer agent is handling the handoff, the original caller hears the selected ring tone/on-hold audio until the call is bridged or canceled.
    * **Three-way message (optional)**: A message shared with both parties when the call is bridged.

    <Frame>
      <img src="https://mintcdn.com/retellai/CusS6gidcUzaxvEx/images/cf/agentic-warm-transfer-settings.png?fit=max&auto=format&n=CusS6gidcUzaxvEx&q=85&s=368a42d0327ce1785097e8ffbda06e86" width="716" height="1230" data-path="images/cf/agentic-warm-transfer-settings.png" />
    </Frame>
  </Step>

  <Step title="Add Custom SIP Headers (Optional)">
    Add custom SIP headers for outbound calls. Custom SIP headers (usually prefixed with `X-`) let you pass session-specific data, such as user IDs or campaign codes, between VoIP endpoints.
    These headers are forwarded to your SIP provider on SIP INVITE and are useful for custom routing and tagging.

    <Warning>Custom SIP headers are preserved only when transferring the call directly to a SIP endpoint. They may be stripped if you are transferring the call to a PSTN number.</Warning>

    <code>All header names must start with `X-` or must be `User-To-User` (case insensitive)</code>

    <Frame style={{ marginTop: '1rem' }}>
      <img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/custom-sip-headers.png?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=e598e83c6f9a6a6b018a340f36f97e8e" width="380" height="178" data-path="images/cf/custom-sip-headers.png" />
    </Frame>
  </Step>
</Steps>

## Rest of Node Settings

* **Speak During Execution**: when enabled, a text input box will show up where you can write instructions for the agent to follow to generate an utterance like `Let me check that for you.` to say while the function is being executed. You can choose between `Prompt` and `Static Sentence`.
* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)
* **LLM**: choose a different model for this particular node. Will be used for function argument generation, and potentially speak during execution message generation.


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Press Digit Node

> Press digit nodes let Retell agents navigate IVR menus by inferring and pressing the correct keypad digit silently during an outbound phone call.

The Press Digit Node is used to navigate through IVR (Interactive Voice Response) systems. When in this node, the agent will not speak. Instead, it evaluates whether it should press a digit and determines which specific digit to press.

The node evaluates whether to press a digit each time the user (IVR system) finishes speaking. This timing is also affected by the detection delay setting. If a digit press is needed, the agent will infer the appropriate digit and press it.

<img src="https://mintcdn.com/retellai/i0NYIKgRtRqm3xFI/images/cf/press-digit-node.gif?s=fddd18cca34075a2c70ce43598015e93" alt="Press digit node navigating an IVR system" width="800" height="502" data-path="images/cf/press-digit-node.gif" />

## Configure Press Digit Behavior

<Steps>
  <Step title="Setup IVR Navigation Instructions">
    Provide clear instructions so the agent knows whether and what digit to press. Include keywords or phrases to listen for, as well as which ones to avoid.

    **Sample prompt:**

    ```
     Your goal is to reach the scheduling or appointments department.

     Preferred navigation keywords:
     • Scheduling
     • Appointments
     • New patients
     • Front desk

     Avoid:
     • Billing
     • Referrals
     • Medical records
     • Clinical departments

     If you are unsure which IVR option is correct:
     Choose the option most closely related to scheduling or appointments.
    ```
  </Step>

  <Step title="Configure Detection Delay">
    Some IVR systems speak slowly, so to make sure the agent does not make any decision prematurely, you can set a delay on pauses to make sure the whole IVR menu is captured. We recommend setting this to 1 second.
  </Step>

  <Step title="Configure Transitions">
    Transitions occur when the IVR system finishes speaking. When writing your transitions, ensure you cover both successful navigation and potential failure scenarios or edge cases.

    **Success scenario:** Define when the agent has successfully navigated to the target. For example, write conditions like `Reached scheduling department`. If the digit press was correct, the IVR response will confirm this.

    **Edge cases:** Cover scenarios like getting stuck in loops. For example, write conditions like `Menu repeated 3 times` to handle repetitive menus.

    **Example transition conditions:**

    ```
    You've reached the scheduling department.
    ```

    ```
    Menu repeated 3 times.
    ```

    ```
    You've reached the wrong department or company.
    ```

    ```
    You've reached an after-hours or voicemail message.
    ```
  </Step>
</Steps>

## Rest of Node Settings

* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)
* **LLM**: choose a different model for this particular node. Will be used for determining whether and what digit to press.


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# End Node

> Use an end node in a Retell conversation flow to terminate the call cleanly, optionally with a final farewell utterance generated from a prompt or static text.

End node is used to end the call. It does not have any edges. The call is ended the moment the agent enters this node.

You can create multiple end nodes within a single agent.

<img src="https://mintcdn.com/retellai/LPjiIxDz6s4F2qHE/images/cf/end-node.png?fit=max&auto=format&n=LPjiIxDz6s4F2qHE&q=85&s=05ab60919489306c63cc0fff022544f5" width="1386" height="434" data-path="images/cf/end-node.png" />

## Node Settings

* **Speak During Execution**: when enabled, a text input box will show up where you can write instructions for the agent to follow to generate an utterance like `Goodbye, have a nice day` to say while the function is being executed. You can choose between `Prompt` and `Static Sentence`.
* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Logic Split Node

> Use a logic split node to branch a Retell conversation flow based on rules — the agent evaluates conditions on entry and routes silently to the right next node.

Logic split node is used to branch out the conversation flow based on the conditions. When entering this node, the agent will immediately evaluate the conditions and branch out to the corresponding destination nodes. The agent would not speak in this node, and the time spent in this node is minimal.

It can come in handy when you want to further split the conversation flow based on the conditions, and do not want to stack all your conditions in previous nodes. It can also be hard for agent to handle a bunch of conditions all at once, so this node can help break it down. It can also be useful when you want to branch out based on dynamic variables.

<img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/logic-split-node.jpeg?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=bc5bf2d029c71ffe1c3931d58d694fe9" width="1003" height="444" data-path="images/cf/logic-split-node.jpeg" />

## When Can Transition Happen

Transition happens immediately when agent enters this node.

## Configure branching logic

* add conditions just like you would in other nodes
* set up the else destination: there will always be an else condition, which will be the default destination if none of the conditions are met, because this node is designed to be a split point and you want to make sure the conversation flow is not stuck here.

## Rest of Node Settings

* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)
* **Fine-tuning Examples**: Can finetune transition. Read more at [Finetune Examples](/build/conversation-flow/finetune-examples)

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Extract Dynamic Variable Node

> Add an extract dynamic variable node to a Retell conversation flow to pull values from the dialogue and store them as text, number, boolean, or enum variables.

Extract dynamic variable node is used to extract information from conversation and store them as dynamic variable. It's not intended for having a conversation with the user.

<Frame>
  <img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/extract-dv-node.png?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=51acd676170c4bfe361f6740ef0b80e0" width="334" height="284" data-path="images/cf/extract-dv-node.png" />
</Frame>

## Add a variable

To create a variable, fill in the following details:

* **Variable Name** – A short name to reference this variable.
* **Description** – A brief explanation of what this value should be.
* **Variable Type** – Choose from `Text`, `Number`, `Enum`, or `Boolean`.
* **Enum Options** - Options to choose from. Only when type is enum

***

## Variable Types

You can create variables of the following types:

* **Text** - Any word or sentence. Examples: `"headache"`, `"John Smith"`
* **Number** - A numeric value. Examples: `42`, `98.6`
* **Enum** - A value from a predefined list. Examples: `"Yes"`, `"No"`, `"Maybe"`
* **Boolean** - True or false.

<Frame>
  <img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/edv-add-variable.png?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=24b2f2cd65821dac10daa27b542844a6" width="800" height="804" data-path="images/cf/edv-add-variable.png" />
</Frame>

## Node Settings

* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)
* **LLM**: choose a different model for this particular node. Will be used for function argument generation, and potentially speak during execution message generation.
* **Fine-tuning Examples**: Can finetune transition. Read more at [Finetune Examples](/build/conversation-flow/finetune-examples)

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Agent Transfer Node

> Agent transfer nodes (agent swap) hand a Retell call from one AI agent to another — useful for specialized agents, language switches, and modular call flows.

In advanced call flows, it's common to switch the handling agent, transferring the conversation from one AI agent to another. **Agent Transfer** (also known as **Agent Swap**) enables you to modularize tasks and re-use specialized agents without relying on [traditional phone-based transfers](/build/single-multi-prompt/transfer-call). Examples include:

* Transferring from a front-desk agent to an appointment-booking agent based on task.
* Transferring from an agent speaking one language to another agent handling a different language, based on user preference.

## Why Use Agent Transfer Instead of Call Transfer?

Compared to transferring to another agent using [transfer call](/build/conversation-flow/call-transfer-node), **Agent Transfer** offers significant advantages:

* **Lower Latency**: The transition between agents is near-instant, much lower than transfer call.
* **Better Reliability**: No need to create a new phone call, avoiding potential telephony failures.
* **No Handoff Message Needed**: The destination agent has access to the full conversation history, eliminating the need for adding hand-off messages or repeated customer questions.
* **No Separate Numbers for Agents**: Agents receiving transfers don’t need their own phone numbers — one number is all you need, no matter how many agents you transfer to.

## Transfer Settings Behavior

The following settings of the first agent will be used throughout the call:

* optInSignedUrl
* optOutSensitiveDataStorage
* webHookUrl

All other settings — such as language, voice, and voiceModel — will reflect the currently active agent.

## Steps

<Steps>
  <Step title="Add Agent Transfer Node">
    Select "Agent Transfer" from the 'Add New Node' menu.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/cf/transfer-agent.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=2ef7134a79f1f01d4669f210d4ece158" data-path="images/cf/transfer-agent.png" />
    </Frame>
  </Step>

  <Step title="Configure Details">
    You can configure the following main settings:

    * **Transfer agent**: the ID and version of a specific agent to transfer to. You can select the latest version as well.
    * **Speak during execution and messages**: if the agent should speak something while performing the transfer.
    * **Post call analysis setting**: for post-call analysis, only extract dynamic variables for the transferred agent, or both agents.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/cf/transfer-agent-detail.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=ab78478de6dc987396e144e102738236" data-path="images/cf/transfer-agent-detail.png" />
    </Frame>
  </Step>

  <Step title="Test and Debug">
    You can test agent transfer both in web call and playground.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/cf/transfer-agent-test.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=bfbf835ca2e3dd2a68266df5d9d2ad60" data-path="images/cf/transfer-agent-test.png" />
    </Frame>
  </Step>
</Steps>

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# MCP node in conversation flow

> Add an MCP node to a Retell conversation flow to call remote MCP server tools during a live call, with custom headers and authentication.

MCP node is used to call tools on your MCP server. It's not intended for having a conversation with the user, but agent can still talk while in this node if needed.

<Frame>
  <img width="250px" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/cf/mcp/node.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=e0bfeacf317232bd2956dcd06f8190a7" data-path="images/cf/mcp/node.png" />
</Frame>

## Add MCP server

<Steps>
  <Step title="Add MCP server">
    To create an MCP node, we first need to add an MCP server.

    <Frame>
      <img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/mcp/add_mcp.png?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=6dee07c5d03c2be78acfce15d7d8e724" width="734" height="589" data-path="images/cf/mcp/add_mcp.png" />
    </Frame>
  </Step>

  <Step title="Set request headers (optional)">
    You can define custom headers to include with the request Retell sends to your MCP Server.

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/headers.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=44295c732912fcb1c3f29259e3f59609" data-path="images/custom-function/headers.png" />
    </Frame>
  </Step>

  <Step title="Set query parameters (optional)">
    You can define query parameters to include in the request URL that Retell appends to your MCP Server Endpoint.

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/YMPW7mFNipo6shGp/images/custom-function/query-params.png?fit=max&auto=format&n=YMPW7mFNipo6shGp&q=85&s=0a0ccd469644d04aa87c086a8dc68bfb" data-path="images/custom-function/query-params.png" />
    </Frame>
  </Step>

  <Step title="Add MCP Tool">
    Select MCP Tool

    <Frame>
      <img src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/cf/mcp/add_tool.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=ad49026f6f2a42a5e14a5abcd82e0cfa" width="725" height="365" data-path="images/cf/mcp/add_tool.png" />
    </Frame>
  </Step>

  <Step title="Set response variables (optional)">
    Extract values from the MCP tool response and save them as <strong>dynamic variables</strong> for use later in the conversation.

    For example, you can extract a user’s name from the response and reference it later using <code>\{\{user\_name}}</code>.

    Example response body

    ```javascript theme={null}
    {
    "properties": {
        "user": {
        "name": "John Doe",
        "age": 26
        }
    }
    }
    ```

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/custom-function/response-variables.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=389a898c0ab3705d3a83acb61a3a4634" data-path="images/custom-function/response-variables.png" />
    </Frame>
  </Step>
</Steps>

## Node Settings

* **Global Node**: read more at [Global Node](/build/conversation-flow/global-node)
* **Fine-tuning Examples**: Can finetune transition. Read more at [Finetune Examples](/build/conversation-flow/finetune-examples)


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Step 3: Add transition conditions

> Define transition conditions in a Retell conversation flow using prompts or strict rules to control when and which node the agent moves to next.

## What is a transition condition?

Transition conditions are used to determine whether and which node the agent will transition to. If no transition condition is met, the agent will transition to the next node. This is the most essential part of the conversation flow, as this gives you the utmost control, and this requires most careful testing.

## Types of transition conditions

There are two types of transition conditions:

* **Prompt**: The condition is a prompt that is evaluated by the LLM.
* **Equation**: The condition is a mathematical equation that is hardcoded. This is useful for testing if dynamic variables meet a certain condition.

All equation conditions are evaluated first, and then the prompt conditions are evaluated. Note that equation conditions are evaluated from top to bottom, and we travel on the first condition that evaluates to true.

Example of prompt conditions:

* `User said something about booking a meeting`
* `User said something about cancelling a meeting`
* `User claims to be over 18`
* `User said they lived in New York`
* `User said they lived in New York or Los Angeles`

Example of equation conditions:

```
- {{user_age}} > 18
- {{current_time}} > 9 AND {{current_time}} < 18
- {{user_location}} == "New York"
- {{user_location}} != "New York"
- "New York, Los Angeles" CONTAINS {{user_location}}
- "New York, Los Angeles" NOT CONTAINS {{user_location}}
- {{user_age}} < 18 OR {{user_location}} == "New York"
- {{name}} exists
```

Note: You can only use variables that are passed in as dynamic variables for equation conditions. If you need to use information extracted by the LLM (such as information learned during the call), you can use prompt conditions.

## Where to define transition conditions?

For different node types:

* Conversation & Function & Press Digit Node: can define conditions to transition out of the node.
* Call Transfer Node: can select a destination node to transition to when transfer is unsuccessful.

For features:

* Skip response: can select a destination node to transition to when agent done speaking content of that node.
* [Global node](/build/conversation-flow/global-node): When enabled, must define the condition to transition into this node.

## How to update transition conditions?

You can update transition conditions by clicking on the node and then clicking on the "+" button for adding a transition condition.
You can then choose to add either a prompt or an equation transition condition. See the picture below.

<img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/add-transition-condition.png?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=cbfe8baf022467b5d7098a19bb424388" width="284" height="183" data-path="images/cf/add-transition-condition.png" />

For prompt conditions, this will open the text on the transition condition editing.

For equation conditions, this will open the equation editor. See the picture below.

<img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/equation-editor.png?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=b8230b5f0933ccdef7b6ef9ef2b6cb0f" width="384" height="340" data-path="images/cf/equation-editor.png" />

This editor allows you to add and drop equations. You can click on the "Add equation" button to add a new equation.
You can delete an equation by clicking on the trash can icon. In addition, you can change the "ANY" to "ALL" to force all equations to be true instead of just one.

To change the order of the equations, you can click on the 6 dots on the left of the equation and drag it up or down. See the picture below.

<img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/equation-editor-reorder.png?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=a2408e26b4ae9149debbaf9f21ce5c43" width="1168" height="1164" data-path="images/cf/equation-editor-reorder.png" />

## New equation conditions

### Check Dynamic variable exists

You can check whether a dynamic variable exists or doesn't exist using the following equation conditions:

* `{{variable_name}} exists` - Returns true if the variable is defined and has a value (even an empty string is considered having a value)
* `{{variable_name}} does not exist` - Returns true if the variable is undefined

This is particularly useful when you want to handle cases where certain information may or may not be available. For example:

```
- {{user_email}} exists
- {{user_phone}} not exists
- {{preferred_language}} exists
```

<img src="https://mintcdn.com/retellai/YTmPqPUaDmLakDGZ/images/cf/equation-exists.png?fit=max&auto=format&n=YTmPqPUaDmLakDGZ&q=85&s=d7e2c521747433b7695323d5ff49b005" width="1286" height="953" data-path="images/cf/equation-exists.png" />

## When will the transition happen?

It usually happens after user speaks, but also has other cases based on node type. Check out specific docs for that node to learn more.

When you are testing in the dashboard (both audio and text), you can see what node is highlighted to find the current node, so you can see how and when the transition happens.

## What should I write inside the transition condition?

Although the agent will have access to the current node's instruction when evaluating the conditions, it's recommended to write conditions to be clear and not reference the instruction that much.

Here're some examples:

* `When user indicates they want to book a meeting`
* `User declines the invitation`
* `User responds to question of their age`
* example for function nodes where you can reference function results: `CRM lookup returned successful result`

To ensure a smooth transition (making sure your agent does not get stuck on a node), it's recommended to cover all possible cases inside transition condition. Some general cases can be covered by the global nodes (like objection handling), so you can focus on the specific cases that can happen inside the specific node.

For equation conditions, it's recommended to cover all branching paths that are determined solely by the dynamic variables.
This can be done if we want to treat users in California and New York differently, and we have access to the user's location before the call starts.
In this case, the equation conditions can be:

```
- {{user_location}} == "New York"
- {{user_location}} == "Los Angeles"
```

Note that the ==, Contains, Not Contains, and Not Equal are string comparisons. They do not require numerical input.
The other comparison operators require numerical input, and will always evaluate to false if the input is not a number.

## Improve transition condition

If you've observed an incorrect transition, you can

* prompt engineer the conditions
* add transition finetune examples (read more at [Finetune Examples](/build/conversation-flow/finetune-examples))

## FAQ

<AccordionGroup>
  <Accordion title="User said something totally unrelated to the transition condition, what would happen?">
    If what user said can be handled by a global node, the agent will transition to the global node. Otherwise the agent will stay in the current node.
  </Accordion>

  <Accordion title="How to see the transition for a past call?">
    You can find node transitions inside the call transcript in the history tab, it will show the node names that it transitions from and to. Thus you might want to name your nodes accordingly.
  </Accordion>

  <Accordion title="Is there a limit on the number of transition conditions?">
    No, but more conditions can make it harder for agent to choose the desired one.
  </Accordion>
</AccordionGroup>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Components

> Package conversation flow sub-flows into reusable Retell components so you can build complex agents once and share consistent logic across many flows.

## Conversation Flow Components

Make complex agents easier to build, reuse, and maintain by packaging parts of your conversation into Components. A Component is a mini flow (a group of nodes) that you can reuse across agents and flows.

### Why use Components?

* Reuse: Build once, drop into many agents and flows.
* Consistency: Keep behavior uniform across use cases (e.g., identity check).
* Clean canvas: Hide detailed logic inside a focused sub-flow.
* Faster iteration: Update a shared Component to improve every agent that uses it.

### Where to find it

<Frame>
  <img height="700" src="https://mintcdn.com/retellai/PP8J4G_S-0bVCFYm/images/cf/component-sidebar.png?fit=max&auto=format&n=PP8J4G_S-0bVCFYm&q=85&s=38d4dec599f6cb9bbc59808a4a779812" data-path="images/cf/component-sidebar.png" />
</Frame>

In the dashboard, open your agent’s builder:

* Left sidebar → Components tab
* Two sections:
  * Library Components: Account-level, shared across agents.
  * Agent Components: Local to the current agent.

## Create a Component

You can create either a library (shared) Component or an agent-level (local) one. Both open in a dedicated editor tab.

* Create a Component:
  1. In Components, click + Create.
  2. You’ll start with a "Begin" node, a basic conversation node and an “Exit Component” end node.
  3. Add nodes and connect edges to form your sub-flow.
  4. Set a start node by connecting the Begin tag to the first node.
  5. Make sure you link "Exit" node correctly so that you won't get stuck at this component.
  6. You can switch back to the main agent by clicking the bottom navigation bar.
  7. You can rename the component by clicking the "..." on the right of the Component name.

Notes:

* Components cannot contain other Components; you add regular nodes inside a Component.
* Available node types match your agent’s channel (voice vs chat).

<Frame>
  <img height="700" src="https://mintcdn.com/retellai/PP8J4G_S-0bVCFYm/images/cf/component-detail.png?fit=max&auto=format&n=PP8J4G_S-0bVCFYm&q=85&s=9c1128cc3aa47ee7226c5bacdca85c07" data-path="images/cf/component-detail.png" />
</Frame>

## Add a Component to your flow

* From the Components tab, click a Component. A single Component node appears in your canvas.
* Connect into the Component: link any node to the Component node.
* Connect out of the Component: select the Component node and connect its outgoing edge to where the conversation should continue.
* To edit what happens inside, click "Edit Component" (or open the Component tab) and modify its internal nodes.
* You can modify the Component node name, which will also be reflected in the Component.

Tip: End nodes inside the Component hand control back to the main flow. Back on the main canvas, make sure the Component node’s outgoing edge points to the next step.

<Frame>
  <img height="700" src="https://mintcdn.com/retellai/PP8J4G_S-0bVCFYm/images/cf/component-node.png?fit=max&auto=format&n=PP8J4G_S-0bVCFYm&q=85&s=812607422e2e10f5d95f1c79459e9e80" data-path="images/cf/component-node.png" />
</Frame>

## Shared vs Local Components

**Shared (Library Components)**:

* Account-level. Reusable across multiple agents.
* Edits sync to every agent that uses it — great for universal steps.

**Local (Agent Components)**:

* Live only in the current agent.
* Edits affect this agent only.

**Convert Between Shared & Local**:

* Turn on “Save component to library” to create a shared (library) version.
* Turn off syncing to convert the reference in your agent to a local copy that stops receiving updates.

<Frame>
  <img height="700" src="https://mintcdn.com/retellai/PP8J4G_S-0bVCFYm/images/cf/component-convert.png?fit=max&auto=format&n=PP8J4G_S-0bVCFYm&q=85&s=e50344ba5fd3b781a88a737ece7f08ea" data-path="images/cf/component-convert.png" />
</Frame>

**Deletion Behavior**:

* Deleting a shared Component from the library downgrades linked instances in agents to local copies and stops sync updates (your agents keep working).

**Publish Agent**:

When you publish an agent, we protect production behavior and keep draft work flexible:

* Published version snapshots shared Components as local copies.
  * This prevents future library updates from changing already-published calls.
  * The published artifact is stable and won’t auto-update from the library.
* Your latest editable draft stays linked to the shared Component.
  * You continue to benefit from library updates while iterating.
  * When you’re ready, publish again to roll out the latest changes.

Recommended workflow:

* Build using Library Components → test → Publish → keep iterating in draft.
* Publish again whenever you want to promote the latest shared/local changes to production.

## Testing

* In order to test the component under the component panel, the component needs to be added to the main Conversation Flow so that it would be initialized properly.
* The global prompt of the main Conversation Flow will be applied to all the component nodes implicitly.
* If you want to test the component alone, you can make it a shared component and create a new empty agent with only one component node.

## Best practices

* Keep Components focused: One clear job (e.g., “Collect Shipping Address”).
* Name clearly: Use action + outcome (e.g., “Verify Identity”).
* Design clean entry/exit: Always set a start node; include an end node to exit cleanly.
* Reuse variables: Use dynamic variables to pass captured data back to the main flow.
* Test in context: Open Test panel to simulate end-to-end behavior after inserting the Component.

## FAQ

* How do I update a shared Component used by many agents?
  * Under any agent, you can navigate to the component edit page. When you are editing, changes apply everywhere it’s used.

* Can I stop changes from affecting an agent?
  * Yes. In that agent, turn off syncing to convert its reference to a local copy.

* What happens if I delete a library Component?
  * Agents keep a local copy; they stop syncing with the deleted library item.

* Can I move a local Component into the library?
  * Yes. Use “Save component to library” to create a shared version and update references.

* Can Components include tools/functions?
  * Yes. Components can include function nodes and use your configured tools. Tools behave the same as in the main flow.
  * The tools need to be defined within the component and will not be visible outside at agent level.

* What if I did not link the Begin node in a component?
  * It transitions to the next node based on the Component node edges.

* What if I did not link the Exit node properly in a component?
  * It will stay stuck inside the component and cannot transition out.


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Flex Mode

> Flex Mode compiles a Retell conversation flow into a single structured prompt at runtime so the agent can handle varied user behavior while keeping flow logic.

Flex Mode combines the best of both worlds:

* Conversation Flow: clear, visual business logic that’s easy to manage.
* Single Prompt Agent: flexible, natural handling of varied user behavior.

You design your conversation flow as usual (nodes, edges, tools). At
runtime, Flex Mode compiles that flow into one structured prompt made of Tasks
and available Tools. The agent then navigates Tasks dynamically while still
following your global prompt.

## Cost Impact

<Warning>
  Flex mode can significantly increase your LLM costs. Because all node instructions,
  transitions, and tool descriptions are compiled into a single prompt, the total token
  count is much higher than in rigid mode (where only the active node's prompt is sent
  to the LLM). When the combined prompt exceeds 3,500 tokens, the
  [token scaling billing rule](/accounts/billing-exceptions#rule-2-llm-price-scaling-for--3500-token-prompt-length)
  applies, which can multiply your costs several times over.
</Warning>

To control costs, consider using **rigid mode** or **breaking your flow into smaller
components** so that fewer nodes are compiled into a single prompt. If you do use flex
mode, keep node instructions concise to minimize token usage.

## When To Use

* You want the clarity of a flowchart (business steps) but need the freedom of a
  single prompt:
  * You can easily switch context from different tasks e.g. every node would
    become global node
  * Could move on to the proper task if the user completed multiple tasks at the
    same time.
  * After switching the context to another flow, agent could resume on the previous
    task without repeating the already completed steps.

## How It Works

You can enable the 'Flex Mode' either at Component level or the Agent level.

<Frame>
  <img height="700" src="https://mintcdn.com/retellai/AUhKztTPT0AsIoSw/images/cf/flex-mode.png?fit=max&auto=format&n=AUhKztTPT0AsIoSw&q=85&s=2bef295b47ebd44512d35c417e1dcd3c" data-path="images/cf/flex-mode.png" />
</Frame>

When enabled at agent level, all the nodes get converted to a single flex
node. It will stay on the flex node and behave like a single prompt agent until
it reaches the 'End Call'.

When enabled on a component, only that component’s nodes are converted into a
single prompt; the rest stays as standard conversation flow.

## Tool Call / Function

There are some differences how flex mode (single prompt) and traditional
conversation flow handle the tool call/function.

* **Speak During Execution** The execution message part will still work the same.
* **Speak After Execution** There is no 'Speak After Execution' setting in Flex
  Mode. The agent will always speak after function execution.
* **Wait For Result** There is no 'waitForResult' setting in Flex Mode. Agent
  will always wait for the function to complete (similar to Single Prompt
  agent).

## Knowledge Base

Node-level knowledge base will be ignored in Flex Mode. You will need to configure the knowledge base at agent level.

## Best Practices & Known Issues

* Write the node instruction in a concise manner so that LLM could better focus
  on the task.
* Only use Prompt edge, avoid using Equation edge as LLM is really bad at
  interpreting equation conditions. You might see very weird behaviors.
* Be explicit on transitions: write crisp, observable conditions.
* If you use flex mode for more than 20 nodes, performance might degrade and
  agent might have higher hallucination risk. We recommend splitting into
  smaller components.
* LLM might not always follow the static text instruction.


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Global Node

> Global nodes in a Retell conversation flow can be reached from anywhere in the agent — ideal for handling universal intents like callbacks and human handoff.

Global nodes can be transitioned to from anywhere in the conversation flow, making them ideal for handling universal scenarios like user objections (e.g. `I want to talk a human / I need to call back later`). Toggle on `Global Node` in the node settings to enable this.

<img src="https://mintcdn.com/retellai/vQCQvVJr44vBuU_v/images/cf/global-node.png?fit=max&auto=format&n=vQCQvVJr44vBuU_v&q=85&s=bf50a33bb1176d166d3da91c48dbcb38" width="1712" height="1340" data-path="images/cf/global-node.png" />

## Configure Global Node

Set a condition for when the global node should be transitioned to. In the example above, the condition is `When user indicates this is not a good time to continue` — so whenever the user says something like `I need to call back later`, the agent transitions to this node.

Since a global node can be transitioned to from anywhere, it does not need to be connected to the rest of the graph.

## Global Node Examples

Add example conversations to help the AI better understand when to jump to this global node. Click `+ Add` to create examples that demonstrate scenarios where the global node should or should not be activated.

## Go Back to Previous Node

Enable **Go back to previous node** to let the conversation return to where it left off after the global node is handled. Once enabled, a **Go Back Condition** section appears on the node where you define when the agent should navigate back. In the example above, the condition is `User changed their mind and want to continue the call`.

Go back conditions support both prompt-based and equation-based conditions. You can add multiple conditions and reorder them by dragging.

## Prevent Immediate Re-Trigger

Enable **Prevent Immediate Re-Trigger** to pause the global node for a specified number of node steps after it has been triggered. Set the number of **Node steps** (defaults to 3) during which the global node will not be activated again. This prevents the conversation from looping when the user's phrasing keeps matching the global node condition.

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Finetune Examples

> Add finetune examples to Retell conversation, subagent, and function nodes to correct unexpected responses or transitions with concrete transcript snippets.

When agent response or transition is not meeting your expectation, you might want to supply some examples to finetune the behavior. You can do so by adding `finetune examples`.

Here are the nodes that support finetune examples:

* Conversation Node: support finetune examples for response and transition
* Subagent Node: support finetune examples for response and transition
* Function Node: support finetune examples for transition

When configuring the finetune example, you will provide a transcript as the context. You can select `user`, `agent`, `function` as the role of the transcript. When selecting `function` as the role, you can fill out both the invocation and result of the function. Refer to the History tab of the dashboard to see examples of transcripts.

## Finetune Examples for Conversation

<img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/finetune-conversation.jpeg?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=bd018081e36b4f1535b7cb9d06eb3596" width="790" height="895" data-path="images/cf/finetune-conversation.jpeg" />

Supplying a transcript as the context is everything you need to do. It's not necessary to provide the entire call transcript, you can simply provide the relevant part. Please note that at least one `agent` response is required, as this is finetuning agent's response.

## Finetune Examples for Transition

<img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/finetune-transition.jpeg?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=bb20a29af46e1714bb7dabbc6650da8e" width="797" height="626" data-path="images/cf/finetune-transition.jpeg" />

Here you need to provide both a transcript as context, and the transition result. If you cannot distinguish between the different nodes available as transition target, you can try to rename your nodes to make it easier to distinguish.


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Debug guide

> Diagnose and fix Retell conversation flow agent issues — wrong responses, missed transitions, and prompt problems — with a step-by-step troubleshooting guide.

Conversation flow is a powerful and flexible tool, which means that there's a lot of action items one can take when the agent's performance is not meeting your expectation. This guide is designed to help you identify the root cause of the issue, and provide actionable steps to improve the agent's responses and transitions.

<Note>This guide only covers the response part of the agent, if you have issues with agent audio, like pronunciation, please refer to other guides.</Note>

## Step 1: Identify the issue

When the agent is not responding as expected, there can be several reasons:

* The agent is not following instructions within a node
* Node transitions are not working as expected
* The actual conversation does not match the flow graph (e.g., users deviate from expected steps)

## Step 2: Fix the issue

Note that these issues are not mutually exclusive - you may need to implement multiple solutions to fully resolve the problem.

### Issue: Agent is not following instructions within a node

#### Split the node into multiple nodes

For example, if a node contains instructions to collect customer name, phone number, and address, the agent might inconsistently ask for only some of this information:

<Frame>
  <img src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/one_node.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=0084cbb508cb520b66d6290738a9fb95" alt="One node" width="874" height="826" data-path="images/one_node.png" />
</Frame>

You can improve consistency by splitting this into three separate nodes:

<Frame>
  <img src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/multiple_node.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=bd19b8e627feaf7bb2eb8763256406e2" alt="Three nodes" width="2086" height="1010" data-path="images/multiple_node.png" />
</Frame>

#### Change the node model

If the instructions are concise but the agent struggles to follow them, try using a more capable LLM model for this node.

#### Add conversation finetune examples

To achieve a specific response style, add conversation finetune examples. Learn more in our [Finetune Examples](/build/conversation-flow/finetune-examples) guide.

#### Adjust the LLM temperature

If the agent's responses are inconsistent, try adjusting the LLM temperature:

<img src="https://mintcdn.com/retellai/32uO5g9DswfoJ9j7/images/cf/model-selection.png?fit=max&auto=format&n=32uO5g9DswfoJ9j7&q=85&s=2632d79da8f65a5e95cf32d7447e7cb9" width="766" height="698" data-path="images/cf/model-selection.png" />

### Issue: Node transitions are not working as expected

If the agent isn't transitioning to the expected node, try these solutions:

* Review your transition conditions: Ensure they precisely match your intended triggers. Consider prompt engineering or breaking down complex conditions into multiple simpler ones.
* Add transition finetune examples: Provide examples to help the model understand your expectations. See our [Finetune Examples](/build/conversation-flow/finetune-examples) guide.

To handle missing transition scenarios:

* Add more nodes to cover edge cases, particularly global nodes for handling unexpected situations. Learn more about [Global Nodes](/build/conversation-flow/global-node).
* Make transition conditions more flexible and general.

### Issue: Actual conversation does not match the flow graph

When users deviate from the defined flow:

* Add key steps as global nodes to allow users to skip or jump between nodes. This is particularly useful for inbound support cases without a rigid call structure. See our [Global Node](/build/conversation-flow/global-node) guide.
* Make node instructions more flexible and let the model handle the details naturally.

