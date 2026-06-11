> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Knowledge Base

> Attach a knowledge base of URLs, documents, and custom text to a Retell agent so it can retrieve relevant context during calls and answer with higher accuracy.

## Overview

Knowledge bases are a collection of sources of information that your agent can access to retrieve relevant information during the call, that can provide additional context to the conversation. It can greatly improve the quality of the responses and the overall experience, especially in cases where there is a lot of information available (too long for putting in prompt), but having the information is essential for the agent to respond correctly. This feature is quite useful for use cases like support, helpdesk, FAQ, etc.

Supported sources:

* Website content (via URLs)
* Documents (supported formats: .bmp, .csv, .doc, .docx, .eml, .epub, .heic, .html, .jpeg, .png, .md, .msg, .odt, .org, .p7s, .pdf, .png, .ppt, .pptx, .rst, .rtf, .tiff, .txt, .tsv, .xls, .xlsx, .xml)
* Custom text snippets

### How it works

You can create knowledge bases, and link them to your agents. When a knowledge base is linked to an agent, the agent will always try to retrieve information from the knowledge base before responding. There's no need to change your prompt for it to trigger, as it will be done automatically, for every response generation.

During the creation of knowledge bases, it will chunk the source, embed them and store into a vector database.

During the call, when the agent is about to respond, it will use the transcript so far (prompt is not included) to find the most relevant chunks from the knowledge base, and feed them to the LLM as context.

### Auto-refreshing and auto-crawling

You can enable auto-refreshing and/or auto-crawling for URL sources in your knowledge base.

* Auto-refreshing: When enabled, the system re-fetches all URLs in the knowledge base every 24 hours to ensure the latest content is reflected.

* Auto-crawling: You can enable this feature for specific URL paths. The system will automatically crawl all pages under each path every 24 hours, excluding any URLs you’ve added to the exclusion list. All pages found—except those explicitly excluded—will be stored.

### Limits

Each knowledge base has the following limits:

* URL: at max 500 urls.
* Auto-Crawling URL Paths: at max 200 exclusion urls for each auto-crawling path, and at max 500 exclusion URLs per knowledge base.
* Text: at max 50 text snippets
* File: at max 25 files, with each file at max 50MB. For CSV, TSV, XLS, and XLSX, the row limit is 1000 rows and the column limit is 50 columns.

You can create multiple knowledge bases to overcome these limits. An agent can have more than one knowledge base linked to it.

## Best Practices

* Prefer `.md` (Markdown) files over `.txt`. Well-structured Markdown is chunked and retrieved more accurately.
  * Use clear, descriptive headings and keep each `##` section focused and reasonably short. If a `##` becomes long, split it into multiple `##`/`###` sections.
  * Write short paragraphs and lists to separate concepts; avoid walls of text.
  * For tabular or image-heavy content, retrieval may be less reliable; consider adding explanatory text so related information stays in the same chunk.
* Group related information within the same section so chunks remain cohesive and relevant.
* Avoid ambiguity and use specificity in references. Include names, dates, units, and avoid ambiguous pronouns like `it` or `this`, because prior chunks may not be present.
* Use more granular paths for auto-crawling instead of broad paths with many exclusion URLs. This improves crawl performance and helps avoid hitting the exclusion URL limits.
* Use the knowledge base to supply supporting information, not agent instructions or prompts. Put instructions in the agent's prompt.

## Use Knowledge Base

<Steps>
  <Step title="Access Knowledge Base Settings">
    1. Navigate to your dashboard
    2. Select the "Knowledge Base" tab
    3. Click the "Add" button in the top-right corner

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/knowledge-base/kb_1.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=974ecc2568c9daa93a127192903985ca" alt="Knowledge Base dashboard view" data-path="images/knowledge-base/kb_1.png" />
    </Frame>
  </Step>

  <Step title="Create Knowledge Base Items">
    Choose from three types of knowledge sources:

    1. **URL**: Import content from web pages
       * Supports single pages or entire websites
       * Automatically updates when content changes

    2. **File**: Upload documents
       * Supported formats: PDF, TXT, DOCX, etc.
       * Maximum file size: 50MB

    3. **Text**: Add custom content
       * Paste or type direct information
       * Ideal for specific instructions or data

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/knowledge-base/kb_2.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=1da9a44858f03c1e9191af5958e8edf9" alt="Adding knowledge base items" data-path="images/knowledge-base/kb_2.png" />
    </Frame>
  </Step>

  <Step title="Enable auto-crawling">
    Auto-crawling can be enabled for individual URL paths. URLs that are not selected will be added to the exclusion list and excluded from the knowledge base.

    You can edit auto-crawling paths to add or remove URLs from the exclusion list. Previously crawled URLs (displayed in bold) can be excluded, and URLs currently on the exclusion list can be reinstated.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/knowledge-base/auto-crawling.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=61c357b664e835ca7d4ff717f2330b20" alt="Adding an auto-crawling path" data-path="images/knowledge-base/auto-crawling.png" />
    </Frame>

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/knowledge-base/edit-path.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=1b77966facefdb4ffa8f84e955c9fb3b" alt="Editing an auto-crawling path" data-path="images/knowledge-base/edit-path.png" />
    </Frame>

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/knowledge-base/edit-path-detail.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=3baa775e95cb3b2e6007a5669ef7a810" alt="Editing the exclusion list" data-path="images/knowledge-base/edit-path-detail.png" />
    </Frame>
  </Step>

  <Step title="Verify Added Items">
    After adding items, they will appear in your knowledge base list. You can:

    * View all added items
    * Edit existing items
    * Delete items when no longer needed

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/knowledge-base/kb_3.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=5f5d1360d08fcb8d673eab1f10f3e90a" alt="Knowledge base items list" data-path="images/knowledge-base/kb_3.png" />
    </Frame>
  </Step>

  <Step title="Connect to Your Agent">
    1. Open the agent editor
    2. Locate the "Knowledge Base" section
    3. Select the knowledge base items you want to use

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/M9QYKZE4hbt00HfL/images/knowledge-base/kb_4.png?fit=max&auto=format&n=M9QYKZE4hbt00HfL&q=85&s=afe2ceb218350d06914c9d053c9ec939" alt="Connecting knowledge base to agent" data-path="images/knowledge-base/kb_4.png" />
    </Frame>
  </Step>

  <Step title="Configure Knowledge Base Settings">
    After connecting a knowledge base to your agent, you can configure how many chunks are retrieved via "Adjust KB Retrieval Chunks and Similarity".

    * Chunks to retrieve: The max number of chunks to retrieve from the knowledge base, range 1-10. Default: 3.
    * Similarity Threshold: Adjust how strict the system is when matching chunks to the context. A higher setting gives you fewer, but more similar, matches. Default: 0.6.

    Note: Increasing "Chunks to retrieve" gives the LLM more context, but also increases the prompt length and can interfere with generation quality. For most cases, the recommended settings are 3 chunks and a 0.60 similarity threshold.

    <Frame>
      <img height="400" src="https://mintcdn.com/retellai/bQa8HG9t8oKhk9Vc/images/knowledge-base/kb_5.png?fit=max&auto=format&n=bQa8HG9t8oKhk9Vc&q=85&s=bb733e15ab2217a894c78212904b8abe" alt="Adjust knowledge base retrieval chunks and similarity settings" data-path="images/knowledge-base/kb_5.png" />
    </Frame>
  </Step>

  <Step title="Setup Node Level Knowledge Base">
    For Conversation Flow Agent, you can configure knowledge base at both Conversation Node level and Subagent Node level. Node-level knowledge base will be combined with the agent-level knowledge base to provide more accurate context for a specific topic.

    1. Open the agent editor
    2. Click the Conversation Node or Subagent Node you want to configure.
    3. Similar to agent level knowledge base config above, you can select and add the knowledge base items you want to use.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/bhoR2p9MQ_lRE5vG/images/knowledge-base/node-level-kb.png?fit=max&auto=format&n=bhoR2p9MQ_lRE5vG&q=85&s=a2c2412f394cbfdd7cd0f6cb0f385a15" alt="Config node level knowledge base" data-path="images/knowledge-base/node-level-kb.png" />
    </Frame>
  </Step>
</Steps>

Your agent will now use this information when responding to queries related to the added content. Retrieved knowledge base content will be appended to the LLM prompt under the header **## Related Knowledge Base Contexts**.

## FAQ

<AccordionGroup>
  <Accordion title="Do I need to change my prompt to use knowledge base?">
    No, you don't need to change your prompt. It will be used automatically when added to an agent.
  </Accordion>

  <Accordion title="How can I prevent the LLM from generating information not found in the knowledge base?">
    You can add the following prompt to the agent:

    ```
    Only answer using the information in ## Related Knowledge Base Contexts.
    If ## Related Knowledge Base Contexts is missing or does not contain relevant information, respond:
    "There is no related information in knowledge base."
    ```
  </Accordion>

  <Accordion title="The agent response is not correct, what should I do?">
    Please check the knowledge base documents to see if the information is correct. And check the format of the source as suggested above, markdown format with clear paragraphs is recommended.
  </Accordion>

  <Accordion title="Will this add a long latency to the call?">
    We've optimized Knowledge Base retrieval latency for real time use case, so it should generally be under 100ms of latency impact.
  </Accordion>

  <Accordion title="Is there a way to check what's getting retrieved from the knowledge base?">
    We're working on adding this feature to expose this information soon.
  </Accordion>

  <Accordion title="Will the knowledge base name influence the retrieval?">
    No, the name is for display purpose only. It's not included in the retrieval process.
  </Accordion>
</AccordionGroup>

## Pricing

* Knowledge base creation:
  * First 10 knowledge bases are free.
  * Additional ones are billed at \$8 / month per knowledge base.
* Using knowledge base:
  * \$0.005 per minute of calls that have knowledge base enabled.
  * it does not matter if your agent is using 1 or many knowledge bases, the billing is the same.

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Dynamic Variables

> Inject per-call data into Retell agents using `{{variable_name}}` syntax for personalized greetings, context-aware responses, and dynamic call routing.

## Overview

Dynamic variables allow you to inject personalized data into your agent's responses for each specific call. Using the `{{variable_name}}` syntax, you can create agents that adapt to different contexts while maintaining consistent conversation flows.

### Common Use Cases

* **Personalized greetings**: "Hello `{{customer_name}}`, thanks for calling!"
* **Context-aware responses**: "I see you're calling about order `{{order_id}}`"
* **Dynamic routing**: Transfer to different numbers based on `{{department}}`
* **Time-sensitive information**: Reference `{{appointment_date}}` or `{{deadline}}`

### Where Dynamic Variables Work

Dynamic variables can be used in:

* **Prompts**: Agent instructions and personality
* **Begin message**: Opening greeting
* **Tool configurations**:
  * Custom function URLs
  * Tool descriptions
  * Property descriptions
* **Call handling**:
  * Voicemail prompts and messages
  * Transfer call phone numbers
  * Warm transfer instructions
* Webhook url

## Add & test dynamic variables

<Steps>
  <Step title="Add dynamic variables in your prompts">
    Dynamic variables are placeholders surrounded by double curly braces. For example:

    ```json theme={null}
    "Hello {{user_name}}, I understand you're interested in {{product_name}}. How can I help you today?"
    ```

    Supported fields include a **variable picker** so you do not have to remember exact names:

    1. Type **`{{`** where you want a variable. A dropdown opens listing variables that apply in that context (for example, default system variables plus variables defined for the agent or flow).
    2. **Filter** the list by typing more characters after `{{`.
    3. **Choose a variable** with **Enter**, a **click**, or **Tab**. The editor inserts the full placeholder and closes the braces, for example `{{customer_name}}`.

    <Note>
      You can still type `{{variable_name}}` by hand in supported fields. The picker is optional.
    </Note>
  </Step>

  <Step title="Test your dynamic variables">
    Before deploying, test your dynamic variables using the web interface

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/dynamic.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=d7fd0be7594df5ff87f27d5d551b03fb" alt="Testing dynamic variables in dashboard" data-path="images/dynamic.png" />
    </Frame>
  </Step>

  <Step title="Configure agent-level default dynamic variables">
    You can set default values for dynamic variables at the agent level. Default variables serve as a fallback and will only be used when specific variables aren't included in the call request.

    <Frame>
      <img height="700" src="https://mintcdn.com/retellai/rxvYffEkEJPRL1KD/images/dynamic-default.png?fit=max&auto=format&n=rxvYffEkEJPRL1KD&q=85&s=38eebb99b95332428477860824d46e71" alt="Default dynamic variable values in agent settings" data-path="images/dynamic-default.png" />
    </Frame>
  </Step>

  <Step title="Implement in production">
    ### For Outbound Calls

    When using the [Create Phone Call](/api-references/create-phone-call) API, set your variables in the
    `retell_llm_dynamic_variables` field. Note that all values must be strings:

    ```json theme={null}
    {
        "user_name": "John Smith",
        "product_name": "Premium Plan",
        "account_status": "active"
    }
    ```

    ### For Inbound Calls

    You can supply dynamic variables in the [Inbound Call Webhook](/features/inbound-call-webhook). More details are at the linked doc.
  </Step>
</Steps>

> **Important:** All values in `retell_llm_dynamic_variables` must be strings. Numbers, booleans, or other data types are
> not supported.

<Note>The spaces around the variable name will be trimmed when evaluating the variable.</Note>

## Default System Variables

Retell automatically provides these system variables - no configuration required:

| Variable                          | Description                                                                                          | Example                                                                                                               |
| --------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `{{current_agent_state}}`         | Current state name (for multi-state agents)                                                          | "greeting"                                                                                                            |
| `{{previous_agent_state}}`        | Previous state name (for multi-state agents)                                                         | "qualification"                                                                                                       |
| `{{current_time}}`                | Current time in `America/Los_Angeles`                                                                | "Thursday, March 28, 2024 at 11:46 PM PST"                                                                            |
| `{{current_time_[timezone]}}`     | Current time in specified `timezone`, for example: `{{current_time_Australia/Sydney}}`               | "Thursday, March 28, 2024 at 11:46 PM AEDT"                                                                           |
| `{{current_hour}}`                | Current hour as a fraction in `America/Los_Angeles`                                                  | "3.5"                                                                                                                 |
| `{{current_hour_[timezone]}}`     | Current hour as a fraction in specified `timezone`, for example: `{{current_hour_Australia/Sydney}}` | "3.5"                                                                                                                 |
| `{{current_calendar}}`            | 14-day calendar in `America/Los_Angeles`                                                             | "Thursday, March 28, 2024 PST (Today)<br />Friday, March 29, 2024 PST<br />...<br />Wednesday, April 10, 2024 PST"    |
| `{{current_calendar_[timezone]}}` | 14-day calendar in specified `timezone`, for example: `{{current_calendar_Australia/Sydney}}`        | "Thursday, March 28, 2024 AEDT (Today)<br />Friday, March 29, 2024 AEDT<br />...<br />Wednesday, April 10, 2024 AEDT" |
| `{{session_type}}`                | Session type, `voice` or `chat`                                                                      | `voice`                                                                                                               |
| `{{session_duration}}`            | How long the session has been running, available after call / chat starts                            | `20 minutes 30 seconds`                                                                                               |

### Phone Call Variables

These variables are only available for phone calls:

| Variable           | Description                                                              | Example                            |
| ------------------ | ------------------------------------------------------------------------ | ---------------------------------- |
| `{{direction}}`    | Call direction, `inbound` or `outbound`                                  | `inbound`                          |
| `{{user_number}}`  | User's phone number (from\_number for inbound, to\_number for outbound)  | `+12137771234`                     |
| `{{agent_number}}` | Agent's phone number (to\_number for inbound, from\_number for outbound) | `+12137771235`                     |
| `{{call_id}}`      | Current call session id                                                  | `call_12345678906eaa0222bd3dd2a6c` |
| `{{call_type}}`    | Call type, `web_call` or `phone_call`                                    | "phone\_call"                      |

### Chat Variables

These variables are only available for chat sessions:

| Variable      | Description                                        | Example                            |
| ------------- | -------------------------------------------------- | ---------------------------------- |
| `{{chat_id}}` | The unique identifier for the current chat session | `chat_12345678906eaa0222bd3dd2a6c` |

## Nested Variables

Retell supports nested variables, you can use the following syntax to create nested variables:

```
{{current_time_{{my_timezone}} }}
```

Now if you have set `my_timezone` to `America/Los_Angeles`, this would evaluate to `{{current_time_America/Los_Angeles }}` first, and will then evaluate to the actual time, as this is a system default variable.

## Handling Missing Variables

### Default Behavior

When a dynamic variable has no assigned value, it remains in its raw form with the curly braces intact:

**Example:**

* Prompt: `"Hello {{user_name}}, how can I help you today?"`
* If `user_name` is not provided: `"Hello {{user_name}}, how can I help you today?"`
* If `user_name` is "John": `"Hello John, how can I help you today?"`

### Checking for Unset Variables

#### In Conversation Flow (Equations)

To check if a variable is set in conversation flow conditions:

```
Equation: {{user_name}} exists
Result: True if variable is defined (even an empty string is considered having a value)
```

#### In Prompts

To handle unset variables in your prompts, you can add conditional logic:

```markdown theme={null}
If {{user_name}} appears with curly braces, use a generic greeting.
Otherwise, greet the customer by name.
```

### Best Practices for Missing Variables

1. **Set defaults at agent level**: Configure fallback values in agent settings
2. **Use defensive prompting**: Design prompts that work with or without variables
3. **Test thoroughly**: Always test with both set and unset variables
4. **Document requirements**: Clearly indicate which variables are required vs optional

## 🎦 Video Tutorial

<iframe width="360" height="200" src="https://www.youtube.com/embed/19Z2OYBF_jA?si=WXPEC46NVE6ehIEl" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen />

### Additional Resources

* [Community Templates](https://docs.google.com/document/d/1hx6hdTEjAR4y4xXZ7RLMH2byQNVW1ABxC8S4FwvTx_Y/edit?tab=t.0#heading=h.wf5bktkelope): Examples and patterns from the Retell community
* [API Reference](/api-references/create-phone-call): Full documentation on passing dynamic variables
* [Inbound Webhook Guide](/features/inbound-call-webhook): Setting variables for incoming calls
