> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Single/Multi Prompt Agent Overview

> Choose between Retell single-prompt and multi-prompt agents based on call complexity — simple single prompt or staged prompts for state-driven conversations.

## Introduction

Retell offers two prompt-based approaches for building conversational agents, each suited to different complexity levels and use cases. Understanding when to use each approach is crucial for creating effective AI phone agents.

## Agent Architecture Options

<Frame>
  <img height="300" src="https://mintcdn.com/retellai/__ejvYecdVsguhU2/images/create_agent.png?fit=max&auto=format&n=__ejvYecdVsguhU2&q=85&s=2106bd94b9fb2692c4a8e530c82dc417" alt="Create Agent Interface" data-path="images/create_agent.png" />
</Frame>

1. Single Prompt: Design your agent with one comprehensive prompt
2. Multi-Prompt Tree: Structure your agent with multiple organized prompts

### Single Prompt Agent

A single prompt agent uses one comprehensive prompt to define all agent behaviors, making it the simplest approach to get started.

<Frame>
  <img height="300" src="https://mintcdn.com/retellai/pRGcctz_zOqy0mSt/images/single_prompt.png?fit=max&auto=format&n=pRGcctz_zOqy0mSt&q=85&s=d6e9732f018667bdd2357552afaad217" alt="Single prompt configuration interface showing a unified prompt field" data-path="images/single_prompt.png" />
</Frame>

#### When to Use Single Prompt

✅ **Best for:**

* Simple, straightforward conversations
* Quick prototypes and testing
* Agents with 1-3 functions
* Linear conversation flows

#### Limitations at Scale

As complexity increases, single prompt agents may experience:

1. **Behavioral Drift**: Agent deviates from instructions in edge cases
2. **Function Calling Issues**: Unreliable tool usage with multiple functions
3. **Maintenance Challenges**: Large prompts become difficult to debug and update
4. **Context Confusion**: Agent struggles to track conversation state

<Note>
  Consider using conversation flow agent or multi-prompt agent when your single prompt exceeds 1000 words or uses more than 5 functions.
</Note>

### Multi-Prompt Agent

Multi-prompt agents organize conversations into a structured tree of states, each with its own focused prompt and behavior.

<Frame>
  <img height="300" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/d_2.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=9005f7c8238d0c3e361717831b377319" alt="Multi-prompt tree structure showing connected conversation states" data-path="images/d_2.png" />
</Frame>

#### Key Features

Each state in a multi-prompt agent includes:

* **Focused Prompt**: Specific instructions for that conversation phase
* **State-Specific Functions**: Only relevant tools available in each state
* **Transition Logic**: Clear conditions for moving between states
* **Context Preservation**: Variables and information flow between states

#### Real-World Example: Lead Qualification

<Frame>
  <img height="300" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/multi.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=6e40e61c6d297d119c4983acc9071f9e" alt="Lead qualification template showing two-state structure" data-path="images/multi.png" />
</Frame>

This template demonstrates effective state separation:

**State 1: Lead Qualification**

* Gather customer information
* Validate requirements
* No appointment booking functions available

**State 2: Appointment Scheduling**

* Only accessible after qualification complete
* Booking functions enabled
* Context from qualification available

#### Benefits of Multi-Prompt Structure

1. **Predictable Behavior**: Each state has a clear, focused purpose
2. **Easier Debugging**: Issues isolated to specific states
3. **Better Function Control**: Tools available only when appropriate
4. **Scalable Design**: Add new states without affecting existing ones
5. **Team Collaboration**: Different team members can work on different states

<Tip>
  Start with our templates to see multi-prompt best practices in action, then customize for your use case.
</Tip>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Build a multi-prompt agent

> Build a Retell multi-prompt agent by breaking the conversation into prompted states with explicit transitions between them — like a lead qualification flow.

<Frame>
  <img height="300" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/multi.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=6e40e61c6d297d119c4983acc9071f9e" alt="Multi Prompt Agent" data-path="images/multi.png" />
</Frame>

<Steps>
  <Step title="Break down the conversation into steps">
    In each step, you can define a prompt.
  </Step>

  <Step title="Define state transition logic">
    Just like in the "Lead qualification" template, you can have this prompt to define when to transition to the next step like if users say "yes" to the question, transition to `your_next_state` state.

    ```
    7. Ask if user is interested in an in person tour.
     - if yes, transition to schedule_tour.
     - if no or hesitant, call function end_call to hang up politely and say will reach out if any other interesting properties pop up.
    ```
  </Step>

  <Step title="Define when to call the function">
    Just like in the "Lead qualification" template, you can have this prompt to define when to call the function like call the `your_function_name` function to book the appointment.

    ```
    3. Confirm the date, time, and timezone selected by user: "Just to confirm, you want to book the appointment at ...". Make sure this is a time from the available slots.
    4. Once confirmed, call function book_appointment to book the appointment.
    ```
  </Step>
</Steps>

### Video tutorial

<iframe width="360" height="200" src="https://www.youtube.com/embed/fowitg78XGQ?si=brUOa58Icxeelp88" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen />

See community templates in [docs](https://docs.google.com/document/d/1hx6hdTEjAR4y4xXZ7RLMH2byQNVW1ABxC8S4FwvTx_Y/edit?tab=t.0#heading=h.wf5bktkelope)


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Step 2: Configure the basic settings

> Configure a Retell single or multi-prompt agent: choose the LLM, voice, language, denoising, and other foundational settings before writing the prompt.

Follow these steps to configure the fundamental settings for your agent, optimizing it for your specific business requirements.

<Steps>
  <Step title="Select a Language Model">
    We recommend starting with GPT-4.1, which offers an optimal balance of:

    * Response quality
    * Latency
    * Cost-effectiveness

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/pRGcctz_zOqy0mSt/images/recommended-text-model-sp.png?fit=max&auto=format&n=pRGcctz_zOqy0mSt&q=85&s=935a1e365e616bc5e3f48bf564a29fdf" alt="GPT-4 Turbo model selection" data-path="images/recommended-text-model-sp.png" />
    </Frame>
  </Step>

  <Step title="Configure Voice Settings">
    1. Open the voice selection dropdown menu:

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/_FxJdxv7mQoPqyGs/images/voice_dropdown.png?fit=max&auto=format&n=_FxJdxv7mQoPqyGs&q=85&s=3879ab1b2020a20db31b88e8c55b102c" alt="Voice selection dropdown" data-path="images/voice_dropdown.png" />
    </Frame>

    2. Listen to the available voice samples and note the voice ID of your preferred option:

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/_FxJdxv7mQoPqyGs/images/voice_selector.png?fit=max&auto=format&n=_FxJdxv7mQoPqyGs&q=85&s=40ff7b9492455e981de9e35ed5f4d21c" alt="Voice preview and selection" data-path="images/voice_selector.png" />
    </Frame>

    **Custom Voices**: You can also add voices from the ElevenLabs community by clicking "Add custom voice". Learn more in our [voice configuration guide](/build/voice).

    **Voice Speed**: You can adjust the agent's speaking speed using the Voice Speed slider (ranging from 0.5x to 2.0x) in the voice settings popover. If you check "Dynamically adjust based on user input", the agent will automatically adapt its speaking speed to match the user's pace during the call. It does this by tracking the user's words per minute and gradually shifting its own speed to align, making the conversation feel more natural. When dynamic voice speed is enabled, the user can also explicitly ask the agent to speak faster or slower, and the agent will adjust on the fly.
  </Step>

  <Step title="Configure Conversation Initiation">
    Define how your agent starts conversations:

    * **User-First**: Agent waits for user input
    * **Agent-First**: Agent initiates the conversation
      * Set a fixed welcome message
      * Use prompts to guide the agent's opening message

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/pRGcctz_zOqy0mSt/images/speak_first.png?fit=max&auto=format&n=pRGcctz_zOqy0mSt&q=85&s=c9136a4443e9b230e66a6124c6a0cf70" alt="Conversation initiation settings" data-path="images/speak_first.png" />
    </Frame>
  </Step>
</Steps>

### More Settings

You can further customize your agent by setting the following settings:

<Steps>
  <Step title="Write Global Prompt">
    Here's where you specify the agent's persona, identity, guardrails, etc. This set of text will be available in every node, and will influence all response generation.
  </Step>

  <Step title="Configure Knowledge Base">
    Here's where you can supply contexts to agent via documents, urls, texts. Read more at [Knowledge Base Guide](/build/knowledge-base).
  </Step>

  <Step title="Configure Speech Settings">
    Here's a lot of options that allow you to finetune how your agent interacts with user.

    * Background sound: select a background sound that plays throughout the whole call to mimic an environment like call center, making the conversation more humanlike and engaging.
    * Responsiveness: how responsive the agent is. Set it lower if you want the agent to wait longer before responding, which can be useful when talking to folks like the elderly. The lower the value, the more wait time is added before the agent responds. You can also check "Dynamically adjust based on user input" to let the agent automatically tune its response timing during the call. When enabled, the agent observes how quickly the user speaks and adjusts accordingly — slower speakers get more patient response timing, while faster speakers get quicker responses.
    * Interruption Sensitivity: how fast the agent gets interrupted by user interruptions. Set it lower if you want agent to be more resilient to background speech.
    * Backchanneling: Set up how often and what words the agent uses to acknowledge users.
    * Boosted Keywords: Provides some biases towards certain words, making it easier to get recognized. Common ones are brand names, people's names, etc.
    * Speech Normalization: convert entities like date, currency, numbers into plain words, which can help prevent issues where audio generated was not pronouncing those right.
    * Reminder frequency: how often the agent will remind the user when user is inactive.
    * Pronunciation: set up pronunciation guide for specific words.
  </Step>

  <Step title="Configure Call Settings">
    Here's a couple of settings that's more call operation related.

    * Voicemail related settings: set up voicemail detection and what to do when voicemail is detected. See more at [Handle Voicemail](/build/handle-voicemail).
    * End call on silence: set up if user is inactive for a certain amount of time, the call will be ended.
    * Call duration: set up maximum duration of the call.
    * Pause before speaking: For the beginning of the call, if agent speaks first, it will wait for the configured duration before speaking, useful to handle scenarios when user is still picking up the phone.
  </Step>

  <Step title="Configure Post Call Analysis">
    Probably set up later, read more at [Post Call Analysis Guide](/features/post-call-analysis-overview).
  </Step>

  <Step title="Configure Privacy & Webhook">
    Here's where you can set up whether to opt out sensitive data storage, and configure webhook settings for receiving call related events.
  </Step>
</Steps>

### Video Tutorial

<iframe width="360" height="200" src="https://www.youtube.com/embed/um2mU8KhOBI?si=vO3Y86FVFbBh_UCB" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen />

See community templates in [docs](https://docs.google.com/document/d/1hx6hdTEjAR4y4xXZ7RLMH2byQNVW1ABxC8S4FwvTx_Y/edit?tab=t.0#heading=h.wf5bktkelope)

## Next Steps

Once you've configured these basic settings, your agent is ready for basic interactions. To enhance its capabilities, proceed to [adding capabilities by using function calling](/build/single-multi-prompt/function-calling).

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Function Calling Overview

> Function calling lets Retell single or multi-prompt agents take real actions — transfer calls, end calls, book appointments, send SMS, and call external APIs.

## Introduction

Function calling transforms your AI agent from a conversational interface into an action-oriented assistant. By connecting your agent to functions, you enable it to interact with external systems, manage call flows, and perform real-world tasks.

## Common Use Cases

Function calling enables your agent to:

### Call Management

* **Transfer calls**: Route to human agents or other departments
* **End calls**: Gracefully terminate conversations
* **Send DTMF tones**: Navigate phone menus

### Business Operations

* **Book appointments**: Integrate with scheduling systems
* **Check availability**: Query calendars or inventory
* **Process orders**: Create, modify, or cancel orders

### Data Integration

* **Retrieve information**: Pull data from CRMs, databases, or APIs
* **Update records**: Modify customer information or case details
* **Send notifications**: Trigger emails, SMS, or push notifications

## How Function Calling Works

### The Process

1. **Agent Decision**: Based on the conversation context, the LLM determines when a function is needed
2. **Parameter Extraction**: The agent extracts required information from the conversation
3. **Function Execution**: Retell calls your function with the extracted parameters
4. **Response Handling**: The function result is processed and incorporated into the conversation

### Technical Overview

Function calling uses structured JSON to communicate between the LLM and your systems:

```json theme={null}
{
  "function": "book_appointment",
  "arguments": {
    "date": "2024-03-15",
    "time": "14:00",
    "customer_name": "John Smith"
  }
}
```

### Additional Resources

* [OpenAI's Function Calling Guide](https://platform.openai.com/docs/guides/function-calling): Technical deep dive
* [Function Calling Tutorial](https://semaphoreci.com/blog/function-calling): Step-by-step implementation guide

## Configuring Tool Calls

### Dashboard Configuration

Access and manage tools in the agent detail page under the "Functions" section.

<Frame>
  <img height="700" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/multi-prompt/functions.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=0c6fcd4ff45d3ebc43bef2fb728caed9" alt="Functions section in dashboard" data-path="images/multi-prompt/functions.png" />
</Frame>

## Available Function Types

### 1. Pre-built Functions

Retell provides ready-to-use functions for common scenarios:

| Function                                                      | Purpose                           | Common Use Cases                             |
| ------------------------------------------------------------- | --------------------------------- | -------------------------------------------- |
| [**End Call**](/build/single-multi-prompt/end-call)           | Terminate conversation gracefully | After completing tasks, when caller requests |
| [**Transfer Call**](/build/single-multi-prompt/transfer-call) | Route to human agents             | Escalation, department routing               |
| [**Press Digits**](/build/single-multi-prompt/press-digit)    | Send DTMF tones                   | Navigate IVR systems, enter codes            |
| [**Check Availability**](/build/check-availability)           | Query available time slots        | Appointment scheduling                       |
| [**Book Calendar**](/build/book-calendar)                     | Create calendar events            | Confirm appointments, meetings               |
| [**Send SMS**](/build/single-multi-prompt/send-sms)           | Send text messages                | Confirmations, follow-ups                    |

### 2. Custom Functions

Create your own functions to:

* **Integrate with your APIs**: Connect to CRM, ERP, or custom systems
* **Execute business logic**: Validate data, calculate prices, check inventory
* **Trigger workflows**: Start processes in other systems

#### Custom Function Features

* **Flexible parameters**: Define any input structure
* **Async execution**: Run in background without blocking conversation
* **Error handling**: Graceful fallbacks for failures
* **Response control**: Customize what the agent says during/after execution

[Learn more about custom functions →](/build/single-multi-prompt/custom-function)

### 3. Code Tool

Run JavaScript code directly in Retell's sandbox without setting up an external server. Useful for:

* **Data transformation**: Format, combine, or compute values from dynamic variables
* **Simple API calls**: Fetch data using the built-in `fetch()` function
* **Logic and calculations**: Implement conditional logic, math, or string operations

[Learn more about Code Tool →](/build/single-multi-prompt/code-tool)

## Video Tutorial

<iframe width="360" height="200" src="https://www.youtube.com/embed/0iGAFUYhuoE?si=_IYtfQNmb1haneif" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen />
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

### Additional Resources

* [Community Templates](https://docs.google.com/document/d/1hx6hdTEjAR4y4xXZ7RLMH2byQNVW1ABxC8S4FwvTx_Y/edit?tab=t.0#heading=h.wf5bktkelope): Real-world function examples
* [API Reference](/api-references/create-agent): Technical documentation
* [Best Practices](/build/prompt-engineering-guide): Writing effective function prompts


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Transfer call tool for single & multi-prompt agents

> Add the Transfer Call tool to a Retell single or multi-prompt agent to route phone calls to human agents or other numbers — supports cold and warm transfers.

<Warning>
  This feature only works during phone calls instead of web calls. It's available for Retell numbers and imported numbers.
</Warning>

It is common in call operation to transfer the call to another human agent or another AI agent.

<Steps>
  <Step title="Add Transfer Call Tool">
    Click "+ Add" in the tools section and select "Transfer Call" from the dropdown menu.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/end_call.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=53ae902cbe4dbfa4edff788fff3ca94e" data-path="images/end_call.png" />
    </Frame>
  </Step>

  <Step title="Setup Transfer To Target">
    Set transfer number to be either:

    * a number in e.164 format, or a SIP URI in the format of `sip:username@domain` (e.g. `sip:user@retellai.com`).
    * [dynamic variable](/build/dynamic-variables) that gets substituted at runtime
    * (Optional) if your transfer destination is not in e.164 format then you can choose to keep the input as is by choosing raw format. This only applies when you are using custom telephony and does not apply when you are using Retell Telephony

    <Frame>
      <img src="https://mintcdn.com/retellai/KbPnDie7AMuPy50b/images/transfer_call_function_e164.png?fit=max&auto=format&n=KbPnDie7AMuPy50b&q=85&s=79a165e0c4774a6905f90becb99fa244" width="1254" height="1048" data-path="images/transfer_call_function_e164.png" />
    </Frame>

    Set the transfer number extension if needed. Extension must be 0-9, '\*', '#' (E.g. 123#)
  </Step>

  <Step title="Update the Prompt">
    Enhance the agent's understanding by incorporating the transfer call conditions into the prompt. Include specific instructions such as:

    "If the user is angry or frustrated, use the transfer\_call tool to transfer the conversation to a human agent."

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/end_call_3.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=c9f4683f55f36dae81c83b91bd607ad0" data-path="images/end_call_3.png" />
    </Frame>
  </Step>

  <Step title="Configure Transfer Type">
    Choose between cold transfer or warm transfer:

    * **Cold transfer**: The call is transferred to a destination number and that's it.
    * **Warm transfer**: After the call is transferred to the destination number, the AI agent can attempt to detect if the other side is human, leave private messages that are not heard by user, do a three-way introduction, etc. (more details in Step 5).
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

  <Step title="Configure Warm Transfer Specific Settings">
    For warm transfers, you can configure the following settings:

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

  <Step title="Add Custom SIP Headers (Optional)">
    Add custom SIP headers for outbound calls. These headers are forwarded to your SIP provider on the SIP INVITE and can be used for custom routing, tagging, or metadata.

    <Warning>Custom SIP headers are preserved only when transferring the call directly to a SIP endpoint. They may be stripped if you are transferring the call to a PSTN number.</Warning>

    <code>All header names must start with `X-` or must be `User-To-User` (case insensitive)</code>

    <br />

    <Frame style={{ marginTop: '1rem' }}>
      <img src="https://mintcdn.com/retellai/zL2HeUqUnagEN9eK/images/cf/custom-sip-headers.png?fit=max&auto=format&n=zL2HeUqUnagEN9eK&q=85&s=e598e83c6f9a6a6b018a340f36f97e8e" width="380" height="178" data-path="images/cf/custom-sip-headers.png" />
    </Frame>
  </Step>
</Steps>

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Press digit (IVR navigation)

> Enable Retell single or multi-prompt agents to navigate DTMF-input IVR menus by pressing keypad digits during outbound calls to reach the right department.

When making outbound phone calls, voice agents often encounter IVR (Interactive Voice Response) systems. The agent needs to navigate the IVR to reach the right department or person, or to enter necessary information.

There are two types of IVR systems:

* **Audio input IVR**: Accepts spoken responses. Your agent can navigate these through standard prompting.
* **DTMF input IVR**: Requires pressing digits on the phone keypad (Dual-Tone Multi-Frequency signals).

This guide shows you how to configure your agent to navigate DTMF-based IVR systems by pressing digits.

***

## Steps

<Steps>
  <Step title="Add a Press Digit Tool">
    Give your agent the ability to press digits. The tool description is optional—you can specify when and what digits to press if desired.

    <img height="200" src="https://mintcdn.com/retellai/O79pc0YgHPZo-0L5/images/telephony/press-digit-tool.gif?s=a91feaa9b9d5bd5053d164ea79300776" data-path="images/telephony/press-digit-tool.gif" />
  </Step>

  <Step title="Add Navigation Prompts">
    Provide clear instructions on when and what digits to press. Include preferred keywords/phrases, keywords to avoid, and guidance for uncertain situations.

    **Example prompt:**

    ```
        ## IVR Navigation
        When interacting with automated systems, menus, or IVR prompts:

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

    **Alternative approach:** If you know the exact digit sequence beforehand, you can provide direct instructions:

    ```
        Press digit 1 to reach the support department.
    ```
  </Step>

  <Step title="Add Interaction Rules">
    Provide detailed instructions on when to press digits and how to handle edge cases, such as reaching the wrong person or needing to hang up.

    **Example prompt:**

    ```
        ## IVR Interaction Rules
        1) If the IVR allows you to speak a department name or short phrase:
            - Speak the appropriate department name clearly.

        2) If the IVR explicitly instructs you to press a number:
           - Use the press_digit function with the instructed digit.

        3) If the IVR does not accept speech and requires numeric input:
           - Use the press_digit function to select the best option.

        4) If the IVR indicates that you have reached the wrong company:
           - Immediately call end_call.

        5) If you are transferred:
           - Wait silently or respond with NO_RESPONSE_NEEDED if prompted to hold.
           - Resume navigation or follow the live agent flow once connected.
    ```
  </Step>

  <Step title="Extract IVR Post-Call Data (Optional)">
    Extract IVR navigation data for deeper insights. Below are field-by-field extraction prompts you can add in your agent's Post-Call Data Extraction settings:

    <img height="200" src="https://mintcdn.com/retellai/O79pc0YgHPZo-0L5/images/telephony/extract-ivr-post-call-data.gif?s=a73b31c3d3ef69db6a399ade6d6dfefc" data-path="images/telephony/extract-ivr-post-call-data.gif" />

    <AccordionGroup>
      <Accordion title="hit_ivr (boolean)">
        Was an IVR or automated phone system encountered at any point before reaching a human? Count menus, "press 1", speech menus, automated routing, or virtual assistants as IVR. Do NOT count hold music after a human answers. Output ONLY true or false.
      </Accordion>

      <Accordion title="reached_human (boolean)">
        Did the caller speak with a real human staff member at any point during the call (not an automated system, recording, voicemail, or virtual assistant)? Output ONLY true or false.
      </Accordion>

      <Accordion title="ivr_loop (boolean)">
        Did the IVR appear to loop or repeat the same menu/prompt due to misunderstanding or invalid input (e.g., repeated "I'm sorry, I didn't get that" or returning to the main menu multiple times)? Output ONLY true or false.
      </Accordion>

      <Accordion title="ivr_type (enum)">
        **Allowed values:** `none` | `basic_menu` | `speech_ivr` | `voicemail_greeting_only` | `after_hours_message_only`

        Classify the type of automated system encountered:

        * **none**: no automation, human answered directly
        * **basic\_menu**: "press 1/2/3" style DTMF menu
        * **speech\_ivr**: system asks spoken questions like "tell me why you're calling" and responds conversationally
        * **voicemail\_greeting\_only**: immediately reached voicemail greeting/leave-a-message flow (no menus)
        * **after\_hours\_message\_only**: only an after-hours closed message (may mention hours), without offering routing to staff
      </Accordion>

      <Accordion title="ivr_outcome (enum)">
        **Allowed values:** `reached_human` | `left_voicemail` | `hung_up` | `blocked_by_ivr` | `callback_required` | `transferred` | `ivr_loop_detected` | `invalid_extension` | `after_hours_info_only`

        What was the final outcome of the IVR/automated navigation portion of the call?

        * **reached\_human**: successfully got to a human
        * **left\_voicemail**: reached voicemail and a message was left or the voicemail prompt occurred as the end state
        * **hung\_up**: call ended before any resolution (caller or system disconnected)
        * **blocked\_by\_ivr**: could not proceed due to IVR requirements or no matching menu option
        * **callback\_required**: system instructed to call back later or offered callback as the only option
        * **transferred**: IVR transferred to a line/department (even if later hold)
        * **ivr\_loop\_detected**: looping prevented progress
        * **invalid\_extension**: extension entry failed (invalid/not recognized)
        * **after\_hours\_info\_only**: ended at after-hours info message with no human reached
      </Accordion>

      <Accordion title="ivr_steps_count (number)">
        How many distinct IVR steps occurred (menu prompts or bot questions that required an input/response) before reaching a human or ending? Output ONLY an integer. If none, output 0.
      </Accordion>

      <Accordion title="ivr_retries_count (number)">
        How many times did the IVR/bot request the same input again or say it didn't understand (e.g., "please repeat", "invalid entry", returning to same menu)? Output ONLY an integer. If none, output 0.
      </Accordion>

      <Accordion title="ivr_path (text)">
        Summarize the IVR navigation path as a breadcrumb using > separators, capturing the main menu choices or intents.

        **Example:** `Main Menu > Providers > Authorizations > Hold`
      </Accordion>

      <Accordion title="ivr_notes (short text)">
        In 1–2 sentences, summarize the key IVR insights that matter operationally (e.g., required identifiers, department options heard, barriers like "portal only", after-hours).
      </Accordion>

      <Accordion title="ivr_tree_text (multiline text)">
        Create a concise step-by-step IVR tree in numbered lines. Each line must be:

        `N. Prompt: "<summary>" | Action: "<pressed/said>" | Result: "<next state>"`.

        Include only steps that occurred.
      </Accordion>
    </AccordionGroup>
  </Step>

  <Step title="Test Your Configuration">
    After saving your agent, test it by:

    * Placing an outbound call to a number with an IVR system, or
    * Calling yourself and mimicking an IVR system by saying phrases like "Press 1 for customer service"
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

# Code Tool

> Code Tool runs JavaScript directly inside a Retell single or multi-prompt agent — call it as a function for formatting, calculations, and lightweight lookups.

Code Tool lets your agent execute JavaScript code as a function call — no external server needed. Unlike [custom functions](/build/single-multi-prompt/custom-function) that send HTTP requests to your endpoint, code tools run directly in Retell's sandbox.

The LLM decides when to call the code tool based on the function name, description, and conversation context.

<Warning>
  Code Tool is designed for lightweight logic like formatting, calculations, and simple read-only lookups. Do not use it to access internal systems, write to production databases, or handle sensitive credentials. Both `dv` and `metadata` values are stored in plaintext with every call record. For integrations that require authentication, secrets management, or write access, use a [Custom Function](/build/single-multi-prompt/custom-function) hosted on your own backend. See [Security and Architecture Guidance](#security-and-architecture-guidance) for details.
</Warning>

## Create a Code Tool

<Steps>
  <Step title="Add a Code Tool">
    In the agent's **Functions** section, click **+ Add** and select **Code**.

    <Frame>
      <img src="https://mintcdn.com/retellai/9xto-Or-KLZnnbLr/images/cf/add-code-tool.png?fit=max&auto=format&n=9xto-Or-KLZnnbLr&q=85&s=392f0cafd7a3e574d6058240c6dfc3b3" alt="Function type dropdown showing the Code option" width="307" height="379" data-path="images/cf/add-code-tool.png" />
    </Frame>
  </Step>

  <Step title="Set name and description">
    * **Name**: A unique identifier (alphanumeric, dashes, underscores). Example: `calculate_shipping_cost`
    * **Description**: Explain what the tool does and when to call it. The LLM uses this to decide when the function is appropriate. Example: "Calculate shipping cost based on the customer's zip code and order weight."
  </Step>

  <Step title="Write JavaScript">
    Write your JavaScript code in the editor. You have access to dynamic variables, call metadata, and the `fetch` function for HTTP requests. See [JavaScript Environment](#javascript-environment) below for details.

    <Frame>
      <img src="https://mintcdn.com/retellai/9xto-Or-KLZnnbLr/images/cf/code-tool-modal.png?fit=max&auto=format&n=9xto-Or-KLZnnbLr&q=85&s=93ad1747681e3e6bc6b5ebb8a267e3c9" alt="Code Tool editor with name, description, code, and configuration options" width="1078" height="815" data-path="images/cf/code-tool-modal.png" />
    </Frame>

    ```javascript theme={null}
    // Example: calculate shipping based on dynamic variables
    const weight = parseFloat(dv.order_weight);
    const zone = dv.shipping_zone;

    let cost;
    if (zone === "local") {
      cost = weight * 0.5;
    } else if (zone === "domestic") {
      cost = weight * 1.2;
    } else {
      cost = weight * 3.0;
    }
    return { shipping_cost: "$" + cost.toFixed(2), zone: zone };
    ```
  </Step>

  <Step title="Set response variables (optional)">
    Use **Store Fields as Variables** to extract values from your code's return value and save them as dynamic variables. Specify a variable name and the JSON path to the value.

    For example, if your code returns `{ "shipping_cost": "$6.00", "zone": "domestic" }`:

    | Variable Name   | JSON Path       | Extracted Value |
    | --------------- | --------------- | --------------- |
    | `shipping_cost` | `shipping_cost` | `"$6.00"`       |
    | `shipping_zone` | `zone`          | `"domestic"`    |
  </Step>

  <Step title="Configure speech settings">
    * **Speak During Execution**: When enabled, the agent says something while the code runs (e.g., "Let me calculate that for you."). Choose **Prompt** or **Static Text**.
    * **Speak After Execution**: When enabled (default), the LLM speaks about the result. Turn off if you want the tool to run silently.
  </Step>

  <Step title="Update your prompt">
    Guide the LLM on when to use the code tool in your agent's prompt. For example:

    ```
    When the customer asks about shipping costs, use the calculate_shipping_cost
    tool to compute the cost based on their order details.
    ```
  </Step>

  <Step title="Test your code">
    Click **Run Code** at the bottom of the editor to test. Use the **Dynamic Variables** dropdown in the editor to set test values for your variables (e.g., give `order_weight` a value of "5") — these values are only used during testing and won't affect your live agent. The output panel will show the result and any `console.log()` output.

    <Frame>
      <img src="https://mintcdn.com/retellai/9xto-Or-KLZnnbLr/images/cf/code-tool-test.png?fit=max&auto=format&n=9xto-Or-KLZnnbLr&q=85&s=0e00e34a3e166424c1d7c919251255e8" alt="Code Tool editor showing test output after clicking Run Code" width="1078" height="815" data-path="images/cf/code-tool-test.png" />
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

Log output for debugging. Logs appear in the test output panel when using **Run Code**.

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

Code Tool is best for lightweight, low-risk logic that runs entirely within Retell's sandbox. As your integration needs grow, use a [Custom Function](/build/single-multi-prompt/custom-function) hosted on your own backend where you control the security boundary.

| Use case                                                                             | Recommended             |
| ------------------------------------------------------------------------------------ | ----------------------- |
| Formatting, calculations, string cleanup                                             | Code Tool               |
| Simple read-only lookups to low-risk public APIs                                     | Code Tool, with caution |
| Accessing internal systems or private APIs                                           | Custom Function         |
| Writing to CRM, EHR, booking, payment, or ticketing systems                          | Custom Function         |
| Workflows requiring secrets, audit logs, retries, idempotency, or policy enforcement | Custom Function         |

<Warning>
  **Do not treat dynamic variables or metadata as a secret vault.** Avoid placing long-lived API keys, database credentials, or other sensitive secrets in dynamic variables or call metadata for use in Code Tool. Both `dv` and `metadata` values are stored in plaintext with every call record — anything you pass in will be visible in call logs and API responses. They are not designed for secret management. Prefer short-lived tokens where possible, and use a [Custom Function](/build/single-multi-prompt/custom-function) for integrations that require sensitive credentials or customer-controlled secret handling.
</Warning>

<Warning>
  **Use `fetch()` with caution.** Enabling outbound HTTP requests from an LLM-invoked tool increases security and operational risk. Treat any use of `fetch()` as an external integration surface. Prefer read-only requests to low-risk, public endpoints. Avoid direct state-changing actions (writes, payments, deletions) unless you fully understand the risks and have appropriate controls in place.
</Warning>

<Note>
  **Keep production logic in your own backend.** For anything involving sensitive credentials, direct writes to production systems, payment actions, regulated data workflows, or business-critical operations that require strict authentication, validation, audit logging, idempotency, or approval controls — use a [Custom Function](/build/single-multi-prompt/custom-function) hosted on your own backend. Code Tool should be reserved for data transformation, calculations, and simple read-only lookups.
</Note>

## Response Variables

Response variables let you extract specific values from your code's return value and store them as dynamic variables.

Specify each variable as a **name** and a **JSON path** using dot notation:

| Path Syntax     | Example         | Extracts               |
| --------------- | --------------- | ---------------------- |
| Top-level field | `status`        | `result.status`        |
| Nested field    | `data.order.id` | `result.data.order.id` |
| Array element   | `items[0].name` | First item's name      |

If a path doesn't exist in the return value, the variable is skipped (no error).

## Configuration

* **Timeout**: How long the code can run before timing out. Range: 5–60 seconds. Default: 30 seconds.
* **Speak During Execution**: When enabled, the agent says something while the code runs. Choose between **Prompt** (LLM generates the message) or **Static Text** (exact text you provide). Recommended when your code takes more than 1 second.
* **Speak After Execution**: When enabled (default), the LLM speaks about the result after execution. Turn off to run the tool silently (e.g., for background logging).

<Note>
  The code result is capped at 15,000 characters to prevent overloading the LLM context.
</Note>

## FAQ

<AccordionGroup>
  <Accordion title="Can I use npm packages or external libraries?">
    No. The code runs in a lightweight JavaScript sandbox without access to `require` or `import`. You can use all standard JavaScript built-ins (`Math`, `JSON`, `Date`, `Array` methods, etc.) and the `fetch()` function for external API calls.
  </Accordion>

  <Accordion title="What happens if my code times out or throws an error?">
    If your code exceeds the timeout or throws an error, the execution is marked as failed and the error message is returned to the LLM. Response variables will not be extracted.
  </Accordion>

  <Accordion title="Can I use async/await?">
    Yes. The `fetch()` function is async, so you can use `await` to wait for HTTP responses. Top-level `await` is supported.
  </Accordion>

  <Accordion title="When should I use Code Tool vs Custom Function?">
    Use **Code Tool** for lightweight, low-risk logic — data formatting, calculations, and simple read-only lookups to public APIs. Use **Custom Function** when you need access to internal systems, databases, sensitive credentials, or any workflow that requires authentication, audit logging, idempotency, or write access to production systems. See [Security and Architecture Guidance](#security-and-architecture-guidance) for a detailed breakdown.
  </Accordion>
</AccordionGroup>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Extract Dynamic Variables

> Add the Extract Dynamic Variable tool to a Retell single or multi-prompt agent to pull values from user replies and store them as typed dynamic variables.

This tool lets you extract values from a user’s response and save them as dynamic variables.

## Steps

<Steps>
  <Step title="Add an Extract Dynamic Variable Tool">
    This would give your agent the ability to extract variable. The description is optional here.

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/extract-dv/dropdown.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=49f0432ef7c2341ae1d8f3c6db45cbaa" data-path="images/extract-dv/dropdown.png" />
    </Frame>
  </Step>

  <Step title="Add Variables">
    Click "+Add" at the bottom and fill in the following details:

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/extract-dv/modal.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=302f541fdcbf9953dec485f91b0a6424" data-path="images/extract-dv/modal.png" />
    </Frame>

    * **Variable Name** – A short name to reference this variable.
    * **Description** – A brief explanation of what this value should be.
    * **Variable Type** – Choose from `Text`, `Number`, `Enum`, or `Boolean`.
    * **Enum Options** - Options to choose from. Only when type is enum

    #### Variable Types

    You can create variables of the following types:

    * **Text** - Any word or sentence. Examples: `"headache"`, `"John Smith"`
    * **Number** - A numeric value. Examples: `42`, `98.6`
    * **Enum** - A value from a predefined list. Examples: `"Yes"`, `"No"`, `"Maybe"`
    * **Boolean** - True or false.

    Click **Save** to add variable.

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/extract-dv/add-variable.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=1186a4aafcbfadd4702dd8579dcddb5b" data-path="images/extract-dv/add-variable.png" />
    </Frame>

    Add more variables as per requirement
  </Step>

  <Step title="Save the Extract Dynamic Variable Tool">
    Click the save button

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/extract-dv/variable-added.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=bb02abc71dcc49c80ecde11c93dc42df" data-path="images/extract-dv/variable-added.png" />
    </Frame>
  </Step>

  <Step title="Update prompt for function">
    It’s best to include in the prompt explicitly when is the best time to invoke the extract variable function. For example:

    ```
    When user states his name and phone number, please extract the information by calling the `extract_user_details` function.
    ```
  </Step>
</Steps>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Agent Transfer

> Agent Transfer (agent swap) lets a Retell single or multi-prompt agent hand the conversation to another AI agent — for specialized tasks or language switches.

In advanced call flows, it's common to switch the handling agent, transferring the conversation from one AI agent to another. **Agent Transfer** (also known as **Agent Swap**) enables you to modularize tasks and re-use specialized agents without relying on [traditional phone-based transfers](/build/single-multi-prompt/transfer-call). Examples include:

* Transferring from a front-desk agent to an appointment-booking agent based on task.
* Transferring from an agent speaking one language to another agent handling a different language, based on user preference.

## Why Use Agent Transfer Instead of Call Transfer?

Compared to transferring to another agent using [transfer call](/build/single-multi-prompt/transfer-call), **Agent Transfer** offers significant advantages:

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

## What context the destination agent receives

When the conversation is handed off via Agent Transfer, the destination agent automatically inherits:

* **Full conversation history** — the transcript of the call up to the transfer point, so the new agent has the same context the previous agent did and the caller does not need to repeat information.
* **Call-level `metadata`** — set on the original call (for example, via [Create Phone Call](/api-references/create-phone-call) or the [Inbound Call Webhook](/features/inbound-call-webhook)) and shared across all agents on the same call.
* **Dynamic variables** — both the `retell_llm_dynamic_variables` provided when the call started and any variables extracted earlier in the call (see [Extract dynamic variables](/build/single-multi-prompt/extract-dv)) remain available to the destination agent's prompt.

There is no separate "pass variables" parameter on the Agent Transfer tool — the mechanism is the shared call context above. If you need the destination agent to act on a specific value, extract it into a dynamic variable on the source agent and reference that variable in the destination agent's prompt.

## Steps

<Steps>
  <Step title="Add Agent Transfer Tool">
    Click Add in the tools section and select "Agent Transfer" from the dropdown menu.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/multi-prompt/transfer_agent.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=93cc0e90a6ef55b5d919bd04368a1fb1" data-path="images/multi-prompt/transfer_agent.png" />
    </Frame>
  </Step>

  <Step title="Configure Details">
    You can configure the following main settings:

    * **Transfer agent**: the ID and version of a specific agent to transfer to. You can select the latest version as well.
    * **Speak during execution and messages**: if the agent should speak something while performing the transfer.
    * **Post call analysis setting**: for post-call analysis, only extract dynamic variables for the transferred agent, or both agents.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/multi-prompt/transfer_agent_detail.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=2dbaafc521eb828d82ba37c75eb6881b" data-path="images/multi-prompt/transfer_agent_detail.png" />
    </Frame>
  </Step>

  <Step title="Update the Prompt to Enable Agent Transfer">
    Ensure the AI agent knows when and why to trigger the agent transfer. Add clear instructions in the prompt such as:

    * `"If the user asks to book an appointment, use the agent_transfer tool to transfer to the Appointment Agent."`

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/multi-prompt/agent_transfer_prompt.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=3b2f7d8e892240fbc46ca0fbe0096ad5" data-path="images/multi-prompt/agent_transfer_prompt.png" />
    </Frame>
  </Step>

  <Step title="Test and Debug">
    You can test agent transfer both in web call and playground.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/multi-prompt/playground_test.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=c349f16a44ce7c1f69b0d58a711c7e3e" data-path="images/multi-prompt/playground_test.png" />
    </Frame>
  </Step>
</Steps>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# MCP tools for single and multi-prompt agents

> Connect a Retell single or multi-prompt agent to a remote MCP server so it can call external MCP tools during prompt-driven voice conversations.

MCP allows you to extend your agent's capabilities by integrating external MCPs and utilizing MCP tools.

## Steps

<Steps>
  <Step title="Add MCP">
    To use MCP tools, you first need to connect your agent to the MCP server. This step will allow you to authenticate and set up the connection.

    Click on + Add MCP

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/mcp/sp_mcp.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=5c3db9b44c10bb543b0a12ab2140cb61" data-path="images/mcp/sp_mcp.png" />
    </Frame>

    Add MCP Configuration

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/mcp/add_mcp.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=13912eadf9db9240e285b4fcc1ac8326" data-path="images/mcp/add_mcp.png" />
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

  <Step title="Select Tool">
    Select the MCP tool from the list of tools available

    <Frame>
      <img height="200" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/mcp/add_tool.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=846b1eede893d7dafb2bb1a151cef77b" data-path="images/mcp/add_tool.png" />
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

  <Step title="Save the MCP Tool">
    Click the save button
  </Step>

  <Step title="Update prompt for function">
    It’s best to include in the prompt explicitly when is the best time to invoke the mcp tool. For example:

    ```
    When user states his name and phone number, please call tool `verify_user` function.
    ```
  </Step>
</Steps>
