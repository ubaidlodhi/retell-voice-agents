> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Agent Handbook

> Turn on Retell Agent Handbook presets to add best-practice prompts for personality, accuracy, and safety with one toggle — no manual prompt writing required.

The Agent Handbook is a collection of ready-to-use prompt presets that improve how your agent communicates. Each preset encodes a specific best practice — toggle it on and the behavior is added automatically, no prompt writing needed.

<Note>New agents are created with **Default Personality** and **AI Disclosure When Asked** enabled by default.</Note>

## How It Works

The Agent Handbook organizes presets into three categories:

* **Personality & Tone** — Shape how the agent sounds and feels in conversation
* **Accuracy & Format** — Improve how the agent handles names, numbers, and data (voice agents only)
* **Trust & Safety** — Control transparency and scope of responses

Toggle any preset on or off from the Agent Handbook panel. Each preset adds a small number of tokens to every interaction — estimated token counts are shown on hover.

<Frame>
  <img src="https://mintcdn.com/retellai/g8lJ9lRJyMqfuCCn/images/agent-handbook/handbook-button.png?fit=max&auto=format&n=g8lJ9lRJyMqfuCCn&q=85&s=8836c2deb797ee4b2ac5f6a960c4e1df" alt="Agent Handbook button in agent settings" width="361" height="841" data-path="images/agent-handbook/handbook-button.png" />
</Frame>

To open the Agent Handbook, click the **Agent Handbook** button in the prompt section of your agent settings.

<Frame>
  <img src="https://mintcdn.com/retellai/g8lJ9lRJyMqfuCCn/images/agent-handbook/handbook-panel.png?fit=max&auto=format&n=g8lJ9lRJyMqfuCCn&q=85&s=c5d251f33468a1b897817bcdf9b9b4c2" alt="Agent Handbook panel with preset toggles" width="454" height="672" data-path="images/agent-handbook/handbook-panel.png" />
</Frame>

## Presets

### Personality & Tone

<AccordionGroup>
  <Accordion title="Default Personality (~480 tokens)">
    **Available for:** Voice and Chat agents | **Default:** Enabled

    Makes your agent sound like a professional representative. It follows an **Acknowledge → Statement → Next Step** response structure, limits filler acknowledgments, avoids robotic phrases like "Certainly!" or "Absolutely!", and keeps responses concise and conversational.

    **When to use:** Leave enabled unless you have a highly custom personality defined in your own prompt.

    **Example:** *"I understand this is frustrating — let me look into that for you."*
  </Accordion>

  <Accordion title="Natural Filler Words (~100 tokens)">
    **Available for:** Voice agents only | **Default:** Disabled

    Adds occasional filler words like "um", "uh", and "you know" to make the agent sound more human and conversational. Fillers are used sparingly — roughly once every 2–3 sentences.

    **When to use:** Great for sales, customer success, or casual conversations. Avoid for formal or regulated contexts (medical, legal).

    **Example:** *"So yeah, let me just pull that up for you real quick."*
  </Accordion>

  <Accordion title="High Empathy (~70 tokens)">
    **Available for:** Voice and Chat agents | **Default:** Disabled

    Guides the agent to use empathetic language when the situation calls for it — acknowledging concerns, making callers feel heard, and reassuring them before moving to a solution.

    **When to use:** Useful for support agents, complaint handling, or any scenario where callers may be frustrated or emotional.

    **Example:** *"I'm sorry you're dealing with this. Let's get it sorted."*
  </Accordion>
</AccordionGroup>

### Accuracy & Format

<Note>All presets in this category are available for voice agents only. They are automatically disabled for chat agents.</Note>

<AccordionGroup>
  <Accordion title="Echo Verification (~190 tokens)">
    **Default:** Disabled

    The agent repeats back names, phone numbers, and other critical details for confirmation. For uncommon names, it spells them out letter by letter.

    **When to use:** Enable for appointment booking, data collection, or any workflow where accurate information capture is critical.

    **Example:** *"Just to confirm, your first name is Ryan, last name is James — is that correct?"*
  </Accordion>

  <Accordion title="NATO Phonetic Alphabet (~190 tokens)">
    **Default:** Disabled

    When spelling is needed, the agent uses the NATO phonetic alphabet (A as in Alfa, B as in Bravo, etc.) with natural pauses for clarity.

    **When to use:** Useful for confirming email addresses, reference numbers, account IDs, or names over the phone.

    **Example:** *"That's B as in Bravo, 7, K as in Kilo, 2 — correct?"*
  </Accordion>

  <Accordion title="Speech Normalization (~910 tokens)">
    **Default:** Disabled

    Formats numbers, dates, money, phone numbers, addresses, and emails into natural spoken form. For example, "\$758.08" becomes "seven fifty-eight dollars and eight cents" and phone numbers are read digit by digit with pauses.

    **When to use:** Enable when your agent frequently reads back structured data like prices, dates, or contact information. Note the higher token cost (\~910 tokens).

    <Tip>This preset tells the LLM how to format its text output for natural speech. For converting text to spoken form at the audio level, enable the `speech_normalization` option in `handbook_config`. Both can be used together.</Tip>

    **Example:** *"Your total is seventy dollars and eighty-four cents."*
  </Accordion>

  <Accordion title="Smart Matching (~110 tokens)">
    **Default:** Disabled

    Handles common speech recognition variations of names gracefully. If a caller confirms their name but the transcription is slightly different (e.g., "Brandon" vs. "Brendon"), the agent treats it as a match and continues naturally.

    **When to use:** Enable when your agent looks up names in a database or CRM and needs tolerance for transcription variations.

    **Example:** Agent asks "Are you Brandon?" and the caller says "Yes, this is Brendon" — the agent continues without flagging the difference.
  </Accordion>
</AccordionGroup>

### Trust & Safety

<AccordionGroup>
  <Accordion title="AI Disclosure When Asked (~30 tokens)">
    **Available for:** Voice and Chat agents | **Default:** Enabled

    When someone asks if they're speaking to a human or an AI, the agent clearly acknowledges that it's a virtual assistant.

    **When to use:** Recommended for transparency and compliance. Only disable if your use case has specific reasons not to disclose.

    **Example:** *"Yes — I'm an AI assistant here to help."*
  </Accordion>

  <Accordion title="Scope Boundaries (~60 tokens)">
    **Available for:** Voice and Chat agents | **Default:** Disabled

    Restricts the agent to only answer questions based on information available in its prompt and knowledge base. If it doesn't know, it says so instead of guessing.

    **When to use:** Enable for any agent where factual accuracy is critical, such as healthcare, finance, or legal use cases.

    **Example:** *"I don't have that information, but I can connect you to someone who can help."*
  </Accordion>
</AccordionGroup>

## Token Cost Summary

| Preset                   | Est. Tokens | Voice | Chat | Default |
| ------------------------ | ----------- | ----- | ---- | ------- |
| Default Personality      | \~480       | ✓     | ✓    | On      |
| Natural Filler Words     | \~100       | ✓     | —    | Off     |
| High Empathy             | \~70        | ✓     | ✓    | Off     |
| Echo Verification        | \~190       | ✓     | —    | Off     |
| NATO Phonetic Alphabet   | \~190       | ✓     | —    | Off     |
| Speech Normalization     | \~910       | ✓     | —    | Off     |
| Smart Matching           | \~110       | ✓     | —    | Off     |
| AI Disclosure When Asked | \~30        | ✓     | ✓    | On      |
| Scope Boundaries         | \~60        | ✓     | ✓    | Off     |

<Note>Token counts are approximate. The token cost of all enabled presets is added to every interaction.</Note>

## FAQ

<AccordionGroup>
  <Accordion title="Can I customize the content of a preset?">
    No — presets are fixed best-practice prompts. For custom instructions, write them directly in your agent's prompt. See the [Prompt Engineering Guide](/build/prompt-engineering-guide) for tips.
  </Accordion>

  <Accordion title="Do handbook presets conflict with my custom prompt?">
    Handbook presets work alongside your custom prompt. If your prompt gives instructions that overlap with a preset (e.g., you wrote your own empathy guidelines), you may want to disable the overlapping preset to avoid inconsistent behavior.
  </Accordion>

  <Accordion title="Why are some presets grayed out for my chat agent?">
    Five presets — Natural Filler Words, Echo Verification, NATO Phonetic Alphabet, Speech Normalization, and Smart Matching — are designed specifically for voice interactions and are not applicable to chat agents.
  </Accordion>
</AccordionGroup>


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Prompt Engineering Guide

> Best practices for writing Retell agent prompts that produce reliable, natural-sounding phone conversations — structure, examples, edge cases, and pitfalls.

## Introduction

Prompt engineering is the foundation of creating effective AI phone agents. A well-crafted prompt determines how your agent interprets situations, responds to users, and handles edge cases. This guide provides proven strategies for writing prompts that agents can follow reliably.

<Note>
  This guide focuses on general prompt engineering principles. For agent-specific implementation:

  * **Single/Multi Prompt Agents**: Apply these principles directly in your prompts
  * **Conversation Flow Agents**: Use these principles within individual node instructions
</Note>

## Getting Started

To see examples of effective prompts, create a new agent in the Dashboard and explore our pre-built templates. These templates demonstrate best practices for various use cases.

## Best Practice 1: Use Sectional Prompts

Break large prompts into focused sections for better organization and LLM comprehension. This structured approach offers several benefits:

* **Reusability**: Sections can be adapted across different agents
* **Maintainability**: Easy to update specific behaviors without affecting others
* **Clarity**: LLMs process structured information more accurately

### Recommended Prompt Structure

```markdown theme={null}
## Identity
You are a friendly AI assistant for [Company Name].
Your role is to [specific purpose].
You have expertise in [relevant domains].

## Style Guardrails
Be concise: Keep responses under 2 sentences unless explaining complex topics.
Be conversational: Use natural language, contractions, and acknowledge what the caller says.
Be empathetic: Show understanding for the caller's situation.

## Response Guidelines
Return dates in spoken form: Say "January fifteenth" not "1/15".
Ask one question at a time: Avoid overwhelming the caller with multiple questions.
Confirm understanding: Paraphrase important information back to the caller.

## Task Instructions
[Specific steps the agent should follow]

## Objection Handling
If the caller says they're not interested: "I understand. Is there anything specific..."
If the caller is frustrated: "I hear your frustration, let me help resolve this..."
```

## Best Practice 2: Use Conversation Flow for Complex Tasks

When your agent needs to handle complex logic or multiple tools, consider using Conversation Flow agents instead of trying to manage everything in a single prompt.

### When to Switch to Conversation Flow:

* **Multiple decision branches**: More than 3-4 conditional paths
* **Tool coordination**: Using 5+ different functions/tools
* **State management**: Tracking multiple variables throughout the conversation
* **Reliability concerns**: Single prompt shows inconsistent behavior

### Benefits of Conversation Flow:

* Each node focuses on one specific task
* Deterministic tool calling and transitions
* Easier to debug and optimize individual steps
* More predictable agent behavior

## Best Practice 3: Explicit Tool Calling Instructions

<Note>This section applies only to Single/Multi Prompt Agents. Conversation Flow Agents handle function calls deterministically through their node configuration.</Note>

### The Challenge

LLMs often struggle to determine when to call tools based solely on tool descriptions. Without explicit instructions, agents may:

* Call tools at inappropriate times
* Fail to call tools when needed
* Use the wrong tool for a situation

### Solution: Define Clear Triggers

Always specify exact conditions for tool usage in your prompts. Reference tools by their exact names.

#### Example: Customer Service Agent

```markdown theme={null}
## Tool Usage Instructions

1. Gather initial information about the customer's issue.

2. Determine the type of request:
   - If customer mentions "refund" or "money back":
     → Call function `transfer_to_support` immediately
   - If customer needs order status:
     → Call function `check_order_status` with order_id
   - If customer wants to change their order:
     → First call `check_order_status`
     → Then transition to modification_state

3. After retrieving information:
   - Always summarize what you found
   - Ask if they need additional help
   - If yes, determine next appropriate action
```

### Best Practices for Tool Instructions

1. **Use trigger words**: List specific words/phrases that should trigger tool calls
2. **Define sequences**: Specify when tools should be called in order
3. **Set boundaries**: Clarify when NOT to call certain tools
4. **Provide context**: Explain why each tool is being called


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Prompt guide & examples for specific situations

> Prompt examples for common voice agent situations — phone numbers, emails, dates, spellings, confirmations — many also available as Agent Handbook presets.

Here are some specific prompt guides and examples for common situations you might encounter in building a voice agent.

<Tip>Many of these patterns — including phone number pronunciation, email spelling, and speech normalization — are now available as one-click presets in the [Agent Handbook](/build/agent-handbook).</Tip>

## Pronounce the phone numbers

We'll utilize the Read Slowly feature to add pauses between words. For more information, see the [Speech Controllability documentation](https://docs.retellai.com/agent/speech-controllability#add-pauses-how-to-read-slowly).

It's recommended to include a prompt as a guideline for the LLM to follow. This ensures that the agent can consistently reply with the correct format, even if customers double-check the phone number.

```
When people ask about your phone number, your phone number is 4158923245

## Guideline
When speaking the phone number, transform the format as follows:
- Input formats like 4158923245, (415) 892-3245, or 415-892-3245
- Should be pronounced as: "four one five - eight nine two - three two four five"
- Important: Don't omit the space around the dash when speaking
```

Listen to this audio clip for a demonstration of proper phone number pronunciation:

[Speak Phone Number Example](https://retell-utils-public.s3.us-west-2.amazonaws.com/speak_phone_number.wav)

## Pronounce the email

```
## How to spell out
The possible email format is name@company.com 
to spell out an email address is n-a-m-e-@-c-o-m-p-a-n-y-dot-com,
@ is pronounced by "at". 
```

## Pronounce the website

```
Whenever you encounter a website URL, please:
Identify each segment of the domain name.
If a segment consists of individual letters (e.g., "NK"), pronounce each letter using its spoken form in English (e.g., "N" → "en," "K" → "kay").
If a segment is a recognizable word (e.g., "laundry"), pronounce it normally as that word.
Pronounce "dot" before stating the top-level domain (e.g., "dot com," "dot net," "dot org," etc.).
Example:
"nklaundry.com" → "en-kay-laundry dot com"
"abctest.net" → "A B C test dot net"
"xyzco.org" → "ex-why-zee-co dot org"
Adhere to this phonetic breakdown carefully to ensure clarity and proper pronunciation for customers.
```

## Pronounce the time

```
For State Numbers, Times & Dates
For 1:00 PM, say "One PM."
For 3:30 PM, say "Three thirty PM."
For 8:45 AM, say "Eight forty-five AM."
Never say O'clock, Instead just say O-Clock.
Always say "AM" or "PM".
```

## Handle being put on hold / no response needed

### For non-reasoning models

We hard-coded a stop sequence in the LLM: `NO_RESPONSE_NEEDED`. Whenever this sequence is met, the response generation stops.
You can then prompt the LLM to output nothing by writing something like:

```
- when user says hold on, reply exactly the following: "NO_RESPONSE_NEEDED".
```

### For reasoning models

<Warning>
  Reasoning models like `gpt 5`, `gpt-5.1` do not support this feature. You need to prompt engineer it differently to achieve this.
</Warning>

You can try the following prompt: `When user says hold on, simply do not respond`.

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Configure LLM Options

> Tune Retell LLM settings — temperature, fast tier, structured output, retries, and timeouts — to balance reliability, latency, and cost for your voice agent.

## Overview

LLM (Large Language Model) configuration options allow you to fine-tune how your agent processes and responds to conversations. Different settings can dramatically impact your agent's behavior, reliability, and cost.

<Note>
  Not all options are available for every model. Check your dashboard for model-specific capabilities.
</Note>

<Frame>
  <img width="300" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/llm-options.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=0c099397152efe520f6069348ca7b3e0" alt="LLM configuration panel showing temperature, structured output, and fast tier options" data-path="images/llm-options.png" />
</Frame>

## Temperature Settings

### What is Temperature?

Temperature controls the randomness and creativity of your agent's responses. It's a value typically between 0 and 1 that affects how the model selects its next words.

### Temperature Guidelines

| Temperature   | Behavior                           | Best For                                             |
| ------------- | ---------------------------------- | ---------------------------------------------------- |
| **0.0 - 0.3** | Highly consistent, deterministic   | Function calling, data collection, technical support |
| **0.4 - 0.7** | Balanced consistency and variation | General customer service, sales calls                |
| **0.8 - 1.0** | Creative, varied responses         | Creative brainstorming, casual conversation          |

### Recommendations by Use Case

* **Appointment Booking**: Use 0.1-0.3 for accurate data capture
* **Customer Support**: Use 0.3-0.5 for consistent yet natural responses
* **Sales Outreach**: Use 0.5-0.7 for engaging but focused conversations
* **Virtual Companion**: Use 0.7-0.9 for more human-like variation

## Structured Output

### Purpose

Structured Output ensures that LLM responses strictly follow predefined schemas, particularly important for reliable function calling. When enabled, the model is constrained to output only valid function calls with all required parameters.

### Benefits

* **Increased Reliability**: Eliminates missing or malformed function arguments
* **Better Error Handling**: Prevents invalid function calls from being attempted
* **Consistent Data Format**: Ensures all outputs match expected schemas

### Trade-offs

* **Slower Auto-save**: Schema caching may delay agent configuration saves
* **Less Flexibility**: Model cannot deviate from defined structures
* **Initial Setup Time**: First load after changes may be slower

### When to Use

✅ **Enable for:**

* Production agents with critical function calls
* Agents handling financial or medical data
* Integration with strict API requirements

❌ **Consider disabling for:**

* Development and testing phases
* Agents with simple or flexible function needs
* When rapid iteration is more important than reliability

## Fast Tier (Premium Performance)

### What is Fast Tier?

Fast Tier routes your LLM calls through dedicated, high-priority infrastructure for superior performance and consistency. This premium option eliminates the variability you might experience with standard routing.

### Key Benefits

1. **Consistent Latency**: Predictable response times for every call
2. **Higher Availability**: Priority access to compute resources
3. **Reduced Variance**: Minimal fluctuation in processing speeds
4. **Better User Experience**: Smoother, more natural conversations

### Cost Consideration

<Warning>
  Fast Tier pricing is **1.5x the standard rate** for your selected model. Calculate the ROI based on your use case before enabling.
</Warning>

### When to Use Fast Tier

✅ **Ideal for:**

* High-value customer interactions
* Time-sensitive operations (emergency services, urgent support)
* Premium service tiers
* Demonstrations and sales calls

❌ **May not be necessary for:**

* Internal testing
* Low-volume or non-critical calls
* Cost-sensitive applications

<Frame>
  <img height="400" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/fast_tier.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=62b74c4d61be835df7a4ed82e4a33e60" alt="Performance comparison chart showing improved latency consistency with Fast Tier enabled" data-path="images/fast_tier.png" />
</Frame>

### Performance Impact

Based on our benchmarks:

* **50% reduction** in latency variance
* **25% improvement** in average response time
* **99.9% availability** vs 99.5% standard
