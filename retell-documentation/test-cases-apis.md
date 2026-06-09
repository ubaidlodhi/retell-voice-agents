> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Create Test Case Definition

> Create a new test case definition



## OpenAPI

````yaml openapi-final post /create-test-case-definition
openapi: 3.0.3
info:
  title: Retell SDK
  version: 3.0.0
  contact:
    name: Retell Support
    url: https://www.retellai.com/
    email: support@retellai.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
servers:
  - url: https://api.retellai.com
    description: The production server.
security:
  - api_key: []
paths:
  /create-test-case-definition:
    post:
      description: Create a new test case definition
      operationId: createTestCaseDefinition
      requestBody:
        required: true
        content:
          application/json:
            schema:
              allOf:
                - $ref: '#/components/schemas/TestCaseDefinitionInput'
                - type: object
                  required:
                    - name
                    - response_engine
                    - user_prompt
                    - metrics
      responses:
        '201':
          description: Test case definition created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TestCaseDefinition'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '402':
          $ref: '#/components/responses/PaymentRequired'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      x-codeSamples:
        - lang: JavaScript
          source: >-
            import Retell from 'retell-sdk';


            const client = new Retell({
              apiKey: process.env['RETELL_API_KEY'], // This is the default and can be omitted
            });


            const testCaseDefinitionResponse = await
            client.tests.createTestCaseDefinition({
              metrics: ['string'],
              name: 'name',
              response_engine: { llm_id: 'llm_id', type: 'retell-llm' },
              user_prompt: 'user_prompt',
            });


            console.log(testCaseDefinitionResponse.test_case_definition_id);
        - lang: Python
          source: >-
            import os

            from retell import Retell


            client = Retell(
                api_key=os.environ.get("RETELL_API_KEY"),  # This is the default and can be omitted
            )

            test_case_definition_response =
            client.tests.create_test_case_definition(
                metrics=["string"],
                name="name",
                response_engine={
                    "llm_id": "llm_id",
                    "type": "retell-llm",
                },
                user_prompt="user_prompt",
            )

            print(test_case_definition_response.test_case_definition_id)
components:
  schemas:
    TestCaseDefinitionInput:
      type: object
      properties:
        name:
          type: string
          description: Name of the test case definition
        response_engine:
          $ref: '#/components/schemas/RetellResponseEngine'
          description: >-
            Response engine to use for the test case. Custom LLM is not
            supported.
        user_prompt:
          type: string
          description: User prompt to simulate in the test case
        metrics:
          type: array
          items:
            type: string
          description: Array of metric names to evaluate
        dynamic_variables:
          type: object
          additionalProperties:
            type: string
          description: Dynamic variables to inject into the response engine
        tool_mocks:
          type: array
          items:
            $ref: '#/components/schemas/ToolMock'
          description: Mock tool calls for testing
        llm_model:
          $ref: '#/components/schemas/LLMModel'
          description: LLM model to use for simulation
    TestCaseDefinition:
      allOf:
        - $ref: '#/components/schemas/TestCaseDefinitionInput'
        - type: object
          required:
            - name
            - response_engine
            - metrics
            - user_prompt
            - dynamic_variables
            - tool_mocks
            - llm_model
            - test_case_definition_id
            - type
            - creation_timestamp
            - user_modified_timestamp
          properties:
            test_case_definition_id:
              type: string
              description: Unique identifier for the test case definition
            type:
              type: string
              enum:
                - simulation
              description: Type of test case definition
            creation_timestamp:
              type: integer
              description: >-
                Timestamp when the test case definition was created
                (milliseconds since epoch)
            user_modified_timestamp:
              type: integer
              description: >-
                Timestamp when the test case definition was last modified
                (milliseconds since epoch)
    RetellResponseEngine:
      oneOf:
        - $ref: '#/components/schemas/ResponseEngineRetellLm'
        - $ref: '#/components/schemas/ResponseEngineConversationFlow'
      description: Response engine for test cases. Custom LLM is not supported.
    ToolMock:
      type: object
      required:
        - tool_name
        - input_match_rule
        - output
      properties:
        tool_name:
          type: string
          description: Name of the tool to mock
        input_match_rule:
          $ref: '#/components/schemas/ToolMockInputMatchRule'
          description: Rule for matching tool calls
        output:
          type: string
          maxLength: 15000
          description: >-
            The output of the tool call that will be fed into the LLM. Should be
            a JSON string.
        result:
          type: boolean
          nullable: true
          description: >-
            For tool calls like transfer_call that require a boolean result.
            Optional for most tools.
    LLMModel:
      type: string
      enum:
        - gpt-4.1
        - gpt-4.1-mini
        - gpt-4.1-nano
        - gpt-5
        - gpt-5-mini
        - gpt-5-nano
        - gpt-5.1
        - gpt-5.2
        - gpt-5.4
        - gpt-5.4-mini
        - gpt-5.4-nano
        - gpt-5.5
        - claude-4.5-sonnet
        - claude-4.6-sonnet
        - claude-4.5-haiku
        - gemini-2.5-flash-lite
        - gemini-3.0-flash
        - gemini-3.1-flash-lite
      description: Available LLM models for agents.
    ResponseEngineRetellLm:
      type: object
      required:
        - type
        - llm_id
      properties:
        type:
          type: string
          enum:
            - retell-llm
          description: type of the Response Engine.
        llm_id:
          type: string
          description: id of the Retell LLM Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Retell LLM Response Engine.
          nullable: true
    ResponseEngineConversationFlow:
      type: object
      required:
        - type
        - conversation_flow_id
      properties:
        type:
          type: string
          enum:
            - conversation-flow
          description: type of the Response Engine.
        conversation_flow_id:
          type: string
          description: ID of the Conversation Flow Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Conversation Flow Response Engine.
          nullable: true
    ToolMockInputMatchRule:
      oneOf:
        - type: object
          required:
            - type
          properties:
            type:
              type: string
              enum:
                - any
              description: Match any input of the tool
        - type: object
          required:
            - type
            - args
          properties:
            type:
              type: string
              enum:
                - partial_match
              description: Match only calls with specific arguments
            args:
              type: object
              description: Arguments to match. Only provided fields will be checked
  responses:
    BadRequest:
      description: Bad Request
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Invalid request format, please check API reference.
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: API key is missing or invalid.
    PaymentRequired:
      description: Payment Required
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Trial has ended, please add payment method.
    TooManyRequests:
      description: Too Many Requests
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Account rate limited, please throttle your requests.
    InternalServerError:
      description: Internal Server Error
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: An unexpected server error occurred.
  securitySchemes:
    api_key:
      type: http
      scheme: bearer
      bearerFormat: string
      description: >-
        Authentication header containing API key (find it in dashboard). The
        format is "Bearer YOUR_API_KEY"

````


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Get Test Case Definition

> Get a test case definition by ID



## OpenAPI

````yaml openapi-final get /get-test-case-definition/{test_case_definition_id}
openapi: 3.0.3
info:
  title: Retell SDK
  version: 3.0.0
  contact:
    name: Retell Support
    url: https://www.retellai.com/
    email: support@retellai.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
servers:
  - url: https://api.retellai.com
    description: The production server.
security:
  - api_key: []
paths:
  /get-test-case-definition/{test_case_definition_id}:
    get:
      description: Get a test case definition by ID
      operationId: getTestCaseDefinition
      parameters:
        - in: path
          name: test_case_definition_id
          schema:
            type: string
          required: true
          description: ID of the test case definition to retrieve
      responses:
        '200':
          description: Test case definition retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TestCaseDefinition'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      x-codeSamples:
        - lang: JavaScript
          source: >-
            import Retell from 'retell-sdk';


            const client = new Retell({
              apiKey: process.env['RETELL_API_KEY'], // This is the default and can be omitted
            });


            const testCaseDefinitionResponse = await
            client.tests.getTestCaseDefinition(
              'test_case_definition_id',
            );


            console.log(testCaseDefinitionResponse.test_case_definition_id);
        - lang: Python
          source: >-
            import os

            from retell import Retell


            client = Retell(
                api_key=os.environ.get("RETELL_API_KEY"),  # This is the default and can be omitted
            )

            test_case_definition_response =
            client.tests.get_test_case_definition(
                "test_case_definition_id",
            )

            print(test_case_definition_response.test_case_definition_id)
components:
  schemas:
    TestCaseDefinition:
      allOf:
        - $ref: '#/components/schemas/TestCaseDefinitionInput'
        - type: object
          required:
            - name
            - response_engine
            - metrics
            - user_prompt
            - dynamic_variables
            - tool_mocks
            - llm_model
            - test_case_definition_id
            - type
            - creation_timestamp
            - user_modified_timestamp
          properties:
            test_case_definition_id:
              type: string
              description: Unique identifier for the test case definition
            type:
              type: string
              enum:
                - simulation
              description: Type of test case definition
            creation_timestamp:
              type: integer
              description: >-
                Timestamp when the test case definition was created
                (milliseconds since epoch)
            user_modified_timestamp:
              type: integer
              description: >-
                Timestamp when the test case definition was last modified
                (milliseconds since epoch)
    TestCaseDefinitionInput:
      type: object
      properties:
        name:
          type: string
          description: Name of the test case definition
        response_engine:
          $ref: '#/components/schemas/RetellResponseEngine'
          description: >-
            Response engine to use for the test case. Custom LLM is not
            supported.
        user_prompt:
          type: string
          description: User prompt to simulate in the test case
        metrics:
          type: array
          items:
            type: string
          description: Array of metric names to evaluate
        dynamic_variables:
          type: object
          additionalProperties:
            type: string
          description: Dynamic variables to inject into the response engine
        tool_mocks:
          type: array
          items:
            $ref: '#/components/schemas/ToolMock'
          description: Mock tool calls for testing
        llm_model:
          $ref: '#/components/schemas/LLMModel'
          description: LLM model to use for simulation
    RetellResponseEngine:
      oneOf:
        - $ref: '#/components/schemas/ResponseEngineRetellLm'
        - $ref: '#/components/schemas/ResponseEngineConversationFlow'
      description: Response engine for test cases. Custom LLM is not supported.
    ToolMock:
      type: object
      required:
        - tool_name
        - input_match_rule
        - output
      properties:
        tool_name:
          type: string
          description: Name of the tool to mock
        input_match_rule:
          $ref: '#/components/schemas/ToolMockInputMatchRule'
          description: Rule for matching tool calls
        output:
          type: string
          maxLength: 15000
          description: >-
            The output of the tool call that will be fed into the LLM. Should be
            a JSON string.
        result:
          type: boolean
          nullable: true
          description: >-
            For tool calls like transfer_call that require a boolean result.
            Optional for most tools.
    LLMModel:
      type: string
      enum:
        - gpt-4.1
        - gpt-4.1-mini
        - gpt-4.1-nano
        - gpt-5
        - gpt-5-mini
        - gpt-5-nano
        - gpt-5.1
        - gpt-5.2
        - gpt-5.4
        - gpt-5.4-mini
        - gpt-5.4-nano
        - gpt-5.5
        - claude-4.5-sonnet
        - claude-4.6-sonnet
        - claude-4.5-haiku
        - gemini-2.5-flash-lite
        - gemini-3.0-flash
        - gemini-3.1-flash-lite
      description: Available LLM models for agents.
    ResponseEngineRetellLm:
      type: object
      required:
        - type
        - llm_id
      properties:
        type:
          type: string
          enum:
            - retell-llm
          description: type of the Response Engine.
        llm_id:
          type: string
          description: id of the Retell LLM Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Retell LLM Response Engine.
          nullable: true
    ResponseEngineConversationFlow:
      type: object
      required:
        - type
        - conversation_flow_id
      properties:
        type:
          type: string
          enum:
            - conversation-flow
          description: type of the Response Engine.
        conversation_flow_id:
          type: string
          description: ID of the Conversation Flow Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Conversation Flow Response Engine.
          nullable: true
    ToolMockInputMatchRule:
      oneOf:
        - type: object
          required:
            - type
          properties:
            type:
              type: string
              enum:
                - any
              description: Match any input of the tool
        - type: object
          required:
            - type
            - args
          properties:
            type:
              type: string
              enum:
                - partial_match
              description: Match only calls with specific arguments
            args:
              type: object
              description: Arguments to match. Only provided fields will be checked
  responses:
    BadRequest:
      description: Bad Request
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Invalid request format, please check API reference.
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: API key is missing or invalid.
    NotFound:
      description: Not Found
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: The requested resource was not found.
    TooManyRequests:
      description: Too Many Requests
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Account rate limited, please throttle your requests.
    InternalServerError:
      description: Internal Server Error
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: An unexpected server error occurred.
  securitySchemes:
    api_key:
      type: http
      scheme: bearer
      bearerFormat: string
      description: >-
        Authentication header containing API key (find it in dashboard). The
        format is "Bearer YOUR_API_KEY"

````

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List Test Case Definitions

> List test case definitions with pagination



## OpenAPI

````yaml openapi-final get /v2/list-test-case-definitions
openapi: 3.0.3
info:
  title: Retell SDK
  version: 3.0.0
  contact:
    name: Retell Support
    url: https://www.retellai.com/
    email: support@retellai.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
servers:
  - url: https://api.retellai.com
    description: The production server.
security:
  - api_key: []
paths:
  /v2/list-test-case-definitions:
    get:
      description: List test case definitions with pagination
      operationId: listTestCaseDefinitionsV2
      parameters:
        - in: query
          name: type
          schema:
            type: string
            enum:
              - retell-llm
              - conversation-flow
          required: true
          description: Type of response engine
        - in: query
          name: llm_id
          schema:
            type: string
          description: LLM ID (required when type is retell-llm)
        - in: query
          name: conversation_flow_id
          schema:
            type: string
          description: Conversation flow ID (required when type is conversation-flow)
        - $ref: '#/components/parameters/LimitParam'
        - $ref: '#/components/parameters/PaginationKeyParam'
      responses:
        '200':
          description: Test case definitions retrieved successfully
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResponseBase'
                  - type: object
                    properties:
                      items:
                        type: array
                        items:
                          $ref: '#/components/schemas/TestCaseDefinition'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      x-codeSamples:
        - lang: JavaScript
          source: >-
            import Retell from 'retell-sdk';


            const client = new Retell({
              apiKey: process.env['RETELL_API_KEY'], // This is the default and can be omitted
            });


            const response = await client.tests.listTestCaseDefinitions({ type:
            'retell-llm' });


            console.log(response.has_more);
        - lang: Python
          source: |-
            import os
            from retell import Retell

            client = Retell(
                api_key=os.environ.get("RETELL_API_KEY"),  # This is the default and can be omitted
            )
            response = client.tests.list_test_case_definitions(
                type="retell-llm",
            )
            print(response.has_more)
components:
  parameters:
    LimitParam:
      in: query
      name: limit
      schema:
        type: integer
        default: 50
        maximum: 1000
      description: Maximum number of items to return.
    PaginationKeyParam:
      in: query
      name: pagination_key
      schema:
        type: string
      description: Pagination key for fetching the next page.
  schemas:
    PaginatedResponseBase:
      type: object
      properties:
        pagination_key:
          type: string
          description: Pagination key for the next page.
        has_more:
          type: boolean
          description: Whether more results are available.
    TestCaseDefinition:
      allOf:
        - $ref: '#/components/schemas/TestCaseDefinitionInput'
        - type: object
          required:
            - name
            - response_engine
            - metrics
            - user_prompt
            - dynamic_variables
            - tool_mocks
            - llm_model
            - test_case_definition_id
            - type
            - creation_timestamp
            - user_modified_timestamp
          properties:
            test_case_definition_id:
              type: string
              description: Unique identifier for the test case definition
            type:
              type: string
              enum:
                - simulation
              description: Type of test case definition
            creation_timestamp:
              type: integer
              description: >-
                Timestamp when the test case definition was created
                (milliseconds since epoch)
            user_modified_timestamp:
              type: integer
              description: >-
                Timestamp when the test case definition was last modified
                (milliseconds since epoch)
    TestCaseDefinitionInput:
      type: object
      properties:
        name:
          type: string
          description: Name of the test case definition
        response_engine:
          $ref: '#/components/schemas/RetellResponseEngine'
          description: >-
            Response engine to use for the test case. Custom LLM is not
            supported.
        user_prompt:
          type: string
          description: User prompt to simulate in the test case
        metrics:
          type: array
          items:
            type: string
          description: Array of metric names to evaluate
        dynamic_variables:
          type: object
          additionalProperties:
            type: string
          description: Dynamic variables to inject into the response engine
        tool_mocks:
          type: array
          items:
            $ref: '#/components/schemas/ToolMock'
          description: Mock tool calls for testing
        llm_model:
          $ref: '#/components/schemas/LLMModel'
          description: LLM model to use for simulation
    RetellResponseEngine:
      oneOf:
        - $ref: '#/components/schemas/ResponseEngineRetellLm'
        - $ref: '#/components/schemas/ResponseEngineConversationFlow'
      description: Response engine for test cases. Custom LLM is not supported.
    ToolMock:
      type: object
      required:
        - tool_name
        - input_match_rule
        - output
      properties:
        tool_name:
          type: string
          description: Name of the tool to mock
        input_match_rule:
          $ref: '#/components/schemas/ToolMockInputMatchRule'
          description: Rule for matching tool calls
        output:
          type: string
          maxLength: 15000
          description: >-
            The output of the tool call that will be fed into the LLM. Should be
            a JSON string.
        result:
          type: boolean
          nullable: true
          description: >-
            For tool calls like transfer_call that require a boolean result.
            Optional for most tools.
    LLMModel:
      type: string
      enum:
        - gpt-4.1
        - gpt-4.1-mini
        - gpt-4.1-nano
        - gpt-5
        - gpt-5-mini
        - gpt-5-nano
        - gpt-5.1
        - gpt-5.2
        - gpt-5.4
        - gpt-5.4-mini
        - gpt-5.4-nano
        - gpt-5.5
        - claude-4.5-sonnet
        - claude-4.6-sonnet
        - claude-4.5-haiku
        - gemini-2.5-flash-lite
        - gemini-3.0-flash
        - gemini-3.1-flash-lite
      description: Available LLM models for agents.
    ResponseEngineRetellLm:
      type: object
      required:
        - type
        - llm_id
      properties:
        type:
          type: string
          enum:
            - retell-llm
          description: type of the Response Engine.
        llm_id:
          type: string
          description: id of the Retell LLM Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Retell LLM Response Engine.
          nullable: true
    ResponseEngineConversationFlow:
      type: object
      required:
        - type
        - conversation_flow_id
      properties:
        type:
          type: string
          enum:
            - conversation-flow
          description: type of the Response Engine.
        conversation_flow_id:
          type: string
          description: ID of the Conversation Flow Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Conversation Flow Response Engine.
          nullable: true
    ToolMockInputMatchRule:
      oneOf:
        - type: object
          required:
            - type
          properties:
            type:
              type: string
              enum:
                - any
              description: Match any input of the tool
        - type: object
          required:
            - type
            - args
          properties:
            type:
              type: string
              enum:
                - partial_match
              description: Match only calls with specific arguments
            args:
              type: object
              description: Arguments to match. Only provided fields will be checked
  responses:
    BadRequest:
      description: Bad Request
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Invalid request format, please check API reference.
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: API key is missing or invalid.
    TooManyRequests:
      description: Too Many Requests
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Account rate limited, please throttle your requests.
    InternalServerError:
      description: Internal Server Error
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: An unexpected server error occurred.
  securitySchemes:
    api_key:
      type: http
      scheme: bearer
      bearerFormat: string
      description: >-
        Authentication header containing API key (find it in dashboard). The
        format is "Bearer YOUR_API_KEY"

````

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Update Test Case Definition

> Update a test case definition



## OpenAPI

````yaml openapi-final put /update-test-case-definition/{test_case_definition_id}
openapi: 3.0.3
info:
  title: Retell SDK
  version: 3.0.0
  contact:
    name: Retell Support
    url: https://www.retellai.com/
    email: support@retellai.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
servers:
  - url: https://api.retellai.com
    description: The production server.
security:
  - api_key: []
paths:
  /update-test-case-definition/{test_case_definition_id}:
    put:
      description: Update a test case definition
      operationId: updateTestCaseDefinition
      parameters:
        - in: path
          name: test_case_definition_id
          schema:
            type: string
          required: true
          description: ID of the test case definition to update
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TestCaseDefinitionInput'
      responses:
        '200':
          description: Test case definition updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TestCaseDefinition'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      x-codeSamples:
        - lang: JavaScript
          source: >-
            import Retell from 'retell-sdk';


            const client = new Retell({
              apiKey: process.env['RETELL_API_KEY'], // This is the default and can be omitted
            });


            const testCaseDefinitionResponse = await
            client.tests.updateTestCaseDefinition(
              'test_case_definition_id',
            );


            console.log(testCaseDefinitionResponse.test_case_definition_id);
        - lang: Python
          source: >-
            import os

            from retell import Retell


            client = Retell(
                api_key=os.environ.get("RETELL_API_KEY"),  # This is the default and can be omitted
            )

            test_case_definition_response =
            client.tests.update_test_case_definition(
                test_case_definition_id="test_case_definition_id",
            )

            print(test_case_definition_response.test_case_definition_id)
components:
  schemas:
    TestCaseDefinitionInput:
      type: object
      properties:
        name:
          type: string
          description: Name of the test case definition
        response_engine:
          $ref: '#/components/schemas/RetellResponseEngine'
          description: >-
            Response engine to use for the test case. Custom LLM is not
            supported.
        user_prompt:
          type: string
          description: User prompt to simulate in the test case
        metrics:
          type: array
          items:
            type: string
          description: Array of metric names to evaluate
        dynamic_variables:
          type: object
          additionalProperties:
            type: string
          description: Dynamic variables to inject into the response engine
        tool_mocks:
          type: array
          items:
            $ref: '#/components/schemas/ToolMock'
          description: Mock tool calls for testing
        llm_model:
          $ref: '#/components/schemas/LLMModel'
          description: LLM model to use for simulation
    TestCaseDefinition:
      allOf:
        - $ref: '#/components/schemas/TestCaseDefinitionInput'
        - type: object
          required:
            - name
            - response_engine
            - metrics
            - user_prompt
            - dynamic_variables
            - tool_mocks
            - llm_model
            - test_case_definition_id
            - type
            - creation_timestamp
            - user_modified_timestamp
          properties:
            test_case_definition_id:
              type: string
              description: Unique identifier for the test case definition
            type:
              type: string
              enum:
                - simulation
              description: Type of test case definition
            creation_timestamp:
              type: integer
              description: >-
                Timestamp when the test case definition was created
                (milliseconds since epoch)
            user_modified_timestamp:
              type: integer
              description: >-
                Timestamp when the test case definition was last modified
                (milliseconds since epoch)
    RetellResponseEngine:
      oneOf:
        - $ref: '#/components/schemas/ResponseEngineRetellLm'
        - $ref: '#/components/schemas/ResponseEngineConversationFlow'
      description: Response engine for test cases. Custom LLM is not supported.
    ToolMock:
      type: object
      required:
        - tool_name
        - input_match_rule
        - output
      properties:
        tool_name:
          type: string
          description: Name of the tool to mock
        input_match_rule:
          $ref: '#/components/schemas/ToolMockInputMatchRule'
          description: Rule for matching tool calls
        output:
          type: string
          maxLength: 15000
          description: >-
            The output of the tool call that will be fed into the LLM. Should be
            a JSON string.
        result:
          type: boolean
          nullable: true
          description: >-
            For tool calls like transfer_call that require a boolean result.
            Optional for most tools.
    LLMModel:
      type: string
      enum:
        - gpt-4.1
        - gpt-4.1-mini
        - gpt-4.1-nano
        - gpt-5
        - gpt-5-mini
        - gpt-5-nano
        - gpt-5.1
        - gpt-5.2
        - gpt-5.4
        - gpt-5.4-mini
        - gpt-5.4-nano
        - gpt-5.5
        - claude-4.5-sonnet
        - claude-4.6-sonnet
        - claude-4.5-haiku
        - gemini-2.5-flash-lite
        - gemini-3.0-flash
        - gemini-3.1-flash-lite
      description: Available LLM models for agents.
    ResponseEngineRetellLm:
      type: object
      required:
        - type
        - llm_id
      properties:
        type:
          type: string
          enum:
            - retell-llm
          description: type of the Response Engine.
        llm_id:
          type: string
          description: id of the Retell LLM Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Retell LLM Response Engine.
          nullable: true
    ResponseEngineConversationFlow:
      type: object
      required:
        - type
        - conversation_flow_id
      properties:
        type:
          type: string
          enum:
            - conversation-flow
          description: type of the Response Engine.
        conversation_flow_id:
          type: string
          description: ID of the Conversation Flow Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Conversation Flow Response Engine.
          nullable: true
    ToolMockInputMatchRule:
      oneOf:
        - type: object
          required:
            - type
          properties:
            type:
              type: string
              enum:
                - any
              description: Match any input of the tool
        - type: object
          required:
            - type
            - args
          properties:
            type:
              type: string
              enum:
                - partial_match
              description: Match only calls with specific arguments
            args:
              type: object
              description: Arguments to match. Only provided fields will be checked
  responses:
    BadRequest:
      description: Bad Request
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Invalid request format, please check API reference.
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: API key is missing or invalid.
    NotFound:
      description: Not Found
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: The requested resource was not found.
    TooManyRequests:
      description: Too Many Requests
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Account rate limited, please throttle your requests.
    InternalServerError:
      description: Internal Server Error
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: An unexpected server error occurred.
  securitySchemes:
    api_key:
      type: http
      scheme: bearer
      bearerFormat: string
      description: >-
        Authentication header containing API key (find it in dashboard). The
        format is "Bearer YOUR_API_KEY"

````

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Delete Test Case Definition

> Delete a test case definition



## OpenAPI

````yaml openapi-final delete /delete-test-case-definition/{test_case_definition_id}
openapi: 3.0.3
info:
  title: Retell SDK
  version: 3.0.0
  contact:
    name: Retell Support
    url: https://www.retellai.com/
    email: support@retellai.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
servers:
  - url: https://api.retellai.com
    description: The production server.
security:
  - api_key: []
paths:
  /delete-test-case-definition/{test_case_definition_id}:
    delete:
      description: Delete a test case definition
      operationId: deleteTestCaseDefinition
      parameters:
        - in: path
          name: test_case_definition_id
          schema:
            type: string
          required: true
          description: ID of the test case definition to delete
      responses:
        '204':
          description: Test case definition deleted successfully
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      x-codeSamples:
        - lang: JavaScript
          source: >-
            import Retell from 'retell-sdk';


            const client = new Retell({
              apiKey: process.env['RETELL_API_KEY'], // This is the default and can be omitted
            });


            await
            client.tests.deleteTestCaseDefinition('test_case_definition_id');
        - lang: Python
          source: |-
            import os
            from retell import Retell

            client = Retell(
                api_key=os.environ.get("RETELL_API_KEY"),  # This is the default and can be omitted
            )
            client.tests.delete_test_case_definition(
                "test_case_definition_id",
            )
components:
  responses:
    BadRequest:
      description: Bad Request
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Invalid request format, please check API reference.
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: API key is missing or invalid.
    NotFound:
      description: Not Found
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: The requested resource was not found.
    TooManyRequests:
      description: Too Many Requests
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Account rate limited, please throttle your requests.
    InternalServerError:
      description: Internal Server Error
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: An unexpected server error occurred.
  securitySchemes:
    api_key:
      type: http
      scheme: bearer
      bearerFormat: string
      description: >-
        Authentication header containing API key (find it in dashboard). The
        format is "Bearer YOUR_API_KEY"

````

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Create Batch Test

> Create a batch test to run multiple test cases



## OpenAPI

````yaml openapi-final post /create-batch-test
openapi: 3.0.3
info:
  title: Retell SDK
  version: 3.0.0
  contact:
    name: Retell Support
    url: https://www.retellai.com/
    email: support@retellai.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
servers:
  - url: https://api.retellai.com
    description: The production server.
security:
  - api_key: []
paths:
  /create-batch-test:
    post:
      description: Create a batch test to run multiple test cases
      operationId: createBatchTest
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - test_case_definition_ids
                - response_engine
              properties:
                test_case_definition_ids:
                  type: array
                  minItems: 1
                  maxItems: 1000
                  items:
                    type: string
                  description: Array of test case definition IDs to run
                response_engine:
                  $ref: '#/components/schemas/RetellResponseEngine'
                  description: >-
                    Response engine to use for the test cases. Custom LLM is not
                    supported.
      responses:
        '201':
          description: Test case batch job created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TestCaseBatchJob'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '402':
          $ref: '#/components/responses/PaymentRequired'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      x-codeSamples:
        - lang: JavaScript
          source: |-
            import Retell from 'retell-sdk';

            const client = new Retell({
              apiKey: process.env['RETELL_API_KEY'], // This is the default and can be omitted
            });

            const batchTestResponse = await client.tests.createBatchTest({
              response_engine: { llm_id: 'llm_id', type: 'retell-llm' },
              test_case_definition_ids: ['string'],
            });

            console.log(batchTestResponse.test_case_batch_job_id);
        - lang: Python
          source: |-
            import os
            from retell import Retell

            client = Retell(
                api_key=os.environ.get("RETELL_API_KEY"),  # This is the default and can be omitted
            )
            batch_test_response = client.tests.create_batch_test(
                response_engine={
                    "llm_id": "llm_id",
                    "type": "retell-llm",
                },
                test_case_definition_ids=["string"],
            )
            print(batch_test_response.test_case_batch_job_id)
components:
  schemas:
    RetellResponseEngine:
      oneOf:
        - $ref: '#/components/schemas/ResponseEngineRetellLm'
        - $ref: '#/components/schemas/ResponseEngineConversationFlow'
      description: Response engine for test cases. Custom LLM is not supported.
    TestCaseBatchJob:
      type: object
      required:
        - test_case_batch_job_id
        - status
        - response_engine
        - pass_count
        - fail_count
        - error_count
        - total_count
        - creation_timestamp
        - user_modified_timestamp
      properties:
        test_case_batch_job_id:
          type: string
          description: Unique identifier for the test case batch job
        status:
          type: string
          enum:
            - in_progress
            - complete
          description: Status of the batch job
        response_engine:
          $ref: '#/components/schemas/ResponseEngine'
        pass_count:
          type: integer
          description: Number of test cases that passed
          minimum: 0
        fail_count:
          type: integer
          description: Number of test cases that failed
          minimum: 0
        error_count:
          type: integer
          description: Number of test cases that encountered errors
          minimum: 0
        total_count:
          type: integer
          description: Total number of test cases in the batch
          minimum: 0
        creation_timestamp:
          type: integer
          description: Timestamp when the batch job was created (milliseconds since epoch)
        user_modified_timestamp:
          type: integer
          description: >-
            Timestamp when the batch job was last modified (milliseconds since
            epoch)
    ResponseEngineRetellLm:
      type: object
      required:
        - type
        - llm_id
      properties:
        type:
          type: string
          enum:
            - retell-llm
          description: type of the Response Engine.
        llm_id:
          type: string
          description: id of the Retell LLM Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Retell LLM Response Engine.
          nullable: true
    ResponseEngineConversationFlow:
      type: object
      required:
        - type
        - conversation_flow_id
      properties:
        type:
          type: string
          enum:
            - conversation-flow
          description: type of the Response Engine.
        conversation_flow_id:
          type: string
          description: ID of the Conversation Flow Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Conversation Flow Response Engine.
          nullable: true
    ResponseEngine:
      oneOf:
        - $ref: '#/components/schemas/ResponseEngineRetellLm'
        - $ref: '#/components/schemas/ResponseEngineCustomLm'
        - $ref: '#/components/schemas/ResponseEngineConversationFlow'
    ResponseEngineCustomLm:
      type: object
      required:
        - type
        - llm_websocket_url
      properties:
        type:
          type: string
          enum:
            - custom-llm
          description: type of the Response Engine.
        llm_websocket_url:
          type: string
          description: LLM websocket url of the custom LLM.
  responses:
    BadRequest:
      description: Bad Request
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Invalid request format, please check API reference.
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: API key is missing or invalid.
    PaymentRequired:
      description: Payment Required
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Trial has ended, please add payment method.
    TooManyRequests:
      description: Too Many Requests
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Account rate limited, please throttle your requests.
    InternalServerError:
      description: Internal Server Error
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: An unexpected server error occurred.
  securitySchemes:
    api_key:
      type: http
      scheme: bearer
      bearerFormat: string
      description: >-
        Authentication header containing API key (find it in dashboard). The
        format is "Bearer YOUR_API_KEY"

````

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Get Batch Test

> Get a batch test job by ID



## OpenAPI

````yaml openapi-final get /get-batch-test/{test_case_batch_job_id}
openapi: 3.0.3
info:
  title: Retell SDK
  version: 3.0.0
  contact:
    name: Retell Support
    url: https://www.retellai.com/
    email: support@retellai.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
servers:
  - url: https://api.retellai.com
    description: The production server.
security:
  - api_key: []
paths:
  /get-batch-test/{test_case_batch_job_id}:
    get:
      description: Get a batch test job by ID
      operationId: getBatchTest
      parameters:
        - in: path
          name: test_case_batch_job_id
          schema:
            type: string
          required: true
          description: ID of the batch test job to retrieve
      responses:
        '200':
          description: Batch test job retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TestCaseBatchJob'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      x-codeSamples:
        - lang: JavaScript
          source: >-
            import Retell from 'retell-sdk';


            const client = new Retell({
              apiKey: process.env['RETELL_API_KEY'], // This is the default and can be omitted
            });


            const batchTestResponse = await
            client.tests.getBatchTest('test_case_batch_job_id');


            console.log(batchTestResponse.test_case_batch_job_id);
        - lang: Python
          source: |-
            import os
            from retell import Retell

            client = Retell(
                api_key=os.environ.get("RETELL_API_KEY"),  # This is the default and can be omitted
            )
            batch_test_response = client.tests.get_batch_test(
                "test_case_batch_job_id",
            )
            print(batch_test_response.test_case_batch_job_id)
components:
  schemas:
    TestCaseBatchJob:
      type: object
      required:
        - test_case_batch_job_id
        - status
        - response_engine
        - pass_count
        - fail_count
        - error_count
        - total_count
        - creation_timestamp
        - user_modified_timestamp
      properties:
        test_case_batch_job_id:
          type: string
          description: Unique identifier for the test case batch job
        status:
          type: string
          enum:
            - in_progress
            - complete
          description: Status of the batch job
        response_engine:
          $ref: '#/components/schemas/ResponseEngine'
        pass_count:
          type: integer
          description: Number of test cases that passed
          minimum: 0
        fail_count:
          type: integer
          description: Number of test cases that failed
          minimum: 0
        error_count:
          type: integer
          description: Number of test cases that encountered errors
          minimum: 0
        total_count:
          type: integer
          description: Total number of test cases in the batch
          minimum: 0
        creation_timestamp:
          type: integer
          description: Timestamp when the batch job was created (milliseconds since epoch)
        user_modified_timestamp:
          type: integer
          description: >-
            Timestamp when the batch job was last modified (milliseconds since
            epoch)
    ResponseEngine:
      oneOf:
        - $ref: '#/components/schemas/ResponseEngineRetellLm'
        - $ref: '#/components/schemas/ResponseEngineCustomLm'
        - $ref: '#/components/schemas/ResponseEngineConversationFlow'
    ResponseEngineRetellLm:
      type: object
      required:
        - type
        - llm_id
      properties:
        type:
          type: string
          enum:
            - retell-llm
          description: type of the Response Engine.
        llm_id:
          type: string
          description: id of the Retell LLM Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Retell LLM Response Engine.
          nullable: true
    ResponseEngineCustomLm:
      type: object
      required:
        - type
        - llm_websocket_url
      properties:
        type:
          type: string
          enum:
            - custom-llm
          description: type of the Response Engine.
        llm_websocket_url:
          type: string
          description: LLM websocket url of the custom LLM.
    ResponseEngineConversationFlow:
      type: object
      required:
        - type
        - conversation_flow_id
      properties:
        type:
          type: string
          enum:
            - conversation-flow
          description: type of the Response Engine.
        conversation_flow_id:
          type: string
          description: ID of the Conversation Flow Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Conversation Flow Response Engine.
          nullable: true
  responses:
    BadRequest:
      description: Bad Request
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Invalid request format, please check API reference.
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: API key is missing or invalid.
    NotFound:
      description: Not Found
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: The requested resource was not found.
    TooManyRequests:
      description: Too Many Requests
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Account rate limited, please throttle your requests.
    InternalServerError:
      description: Internal Server Error
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: An unexpected server error occurred.
  securitySchemes:
    api_key:
      type: http
      scheme: bearer
      bearerFormat: string
      description: >-
        Authentication header containing API key (find it in dashboard). The
        format is "Bearer YOUR_API_KEY"

````

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.retellai.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List Batch Tests

> List batch test jobs with pagination



## OpenAPI

````yaml openapi-final get /v2/list-batch-tests
openapi: 3.0.3
info:
  title: Retell SDK
  version: 3.0.0
  contact:
    name: Retell Support
    url: https://www.retellai.com/
    email: support@retellai.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
servers:
  - url: https://api.retellai.com
    description: The production server.
security:
  - api_key: []
paths:
  /v2/list-batch-tests:
    get:
      description: List batch test jobs with pagination
      operationId: listBatchTestsV2
      parameters:
        - in: query
          name: type
          schema:
            type: string
            enum:
              - retell-llm
              - conversation-flow
          required: true
          description: Type of response engine
        - in: query
          name: llm_id
          schema:
            type: string
          description: LLM ID (required when type is retell-llm)
        - in: query
          name: conversation_flow_id
          schema:
            type: string
          description: Conversation flow ID (required when type is conversation-flow)
        - in: query
          name: version
          schema:
            type: integer
          description: Version of the response engine (defaults to latest)
        - $ref: '#/components/parameters/LimitParam'
        - $ref: '#/components/parameters/PaginationKeyParam'
      responses:
        '200':
          description: Batch test jobs retrieved successfully
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResponseBase'
                  - type: object
                    properties:
                      items:
                        type: array
                        items:
                          $ref: '#/components/schemas/TestCaseBatchJob'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      x-codeSamples:
        - lang: JavaScript
          source: >-
            import Retell from 'retell-sdk';


            const client = new Retell({
              apiKey: process.env['RETELL_API_KEY'], // This is the default and can be omitted
            });


            const response = await client.tests.listBatchTests({ type:
            'retell-llm' });


            console.log(response.has_more);
        - lang: Python
          source: |-
            import os
            from retell import Retell

            client = Retell(
                api_key=os.environ.get("RETELL_API_KEY"),  # This is the default and can be omitted
            )
            response = client.tests.list_batch_tests(
                type="retell-llm",
            )
            print(response.has_more)
components:
  parameters:
    LimitParam:
      in: query
      name: limit
      schema:
        type: integer
        default: 50
        maximum: 1000
      description: Maximum number of items to return.
    PaginationKeyParam:
      in: query
      name: pagination_key
      schema:
        type: string
      description: Pagination key for fetching the next page.
  schemas:
    PaginatedResponseBase:
      type: object
      properties:
        pagination_key:
          type: string
          description: Pagination key for the next page.
        has_more:
          type: boolean
          description: Whether more results are available.
    TestCaseBatchJob:
      type: object
      required:
        - test_case_batch_job_id
        - status
        - response_engine
        - pass_count
        - fail_count
        - error_count
        - total_count
        - creation_timestamp
        - user_modified_timestamp
      properties:
        test_case_batch_job_id:
          type: string
          description: Unique identifier for the test case batch job
        status:
          type: string
          enum:
            - in_progress
            - complete
          description: Status of the batch job
        response_engine:
          $ref: '#/components/schemas/ResponseEngine'
        pass_count:
          type: integer
          description: Number of test cases that passed
          minimum: 0
        fail_count:
          type: integer
          description: Number of test cases that failed
          minimum: 0
        error_count:
          type: integer
          description: Number of test cases that encountered errors
          minimum: 0
        total_count:
          type: integer
          description: Total number of test cases in the batch
          minimum: 0
        creation_timestamp:
          type: integer
          description: Timestamp when the batch job was created (milliseconds since epoch)
        user_modified_timestamp:
          type: integer
          description: >-
            Timestamp when the batch job was last modified (milliseconds since
            epoch)
    ResponseEngine:
      oneOf:
        - $ref: '#/components/schemas/ResponseEngineRetellLm'
        - $ref: '#/components/schemas/ResponseEngineCustomLm'
        - $ref: '#/components/schemas/ResponseEngineConversationFlow'
    ResponseEngineRetellLm:
      type: object
      required:
        - type
        - llm_id
      properties:
        type:
          type: string
          enum:
            - retell-llm
          description: type of the Response Engine.
        llm_id:
          type: string
          description: id of the Retell LLM Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Retell LLM Response Engine.
          nullable: true
    ResponseEngineCustomLm:
      type: object
      required:
        - type
        - llm_websocket_url
      properties:
        type:
          type: string
          enum:
            - custom-llm
          description: type of the Response Engine.
        llm_websocket_url:
          type: string
          description: LLM websocket url of the custom LLM.
    ResponseEngineConversationFlow:
      type: object
      required:
        - type
        - conversation_flow_id
      properties:
        type:
          type: string
          enum:
            - conversation-flow
          description: type of the Response Engine.
        conversation_flow_id:
          type: string
          description: ID of the Conversation Flow Response Engine.
        version:
          type: number
          example: 0
          description: Version of the Conversation Flow Response Engine.
          nullable: true
  responses:
    BadRequest:
      description: Bad Request
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Invalid request format, please check API reference.
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: API key is missing or invalid.
    TooManyRequests:
      description: Too Many Requests
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: Account rate limited, please throttle your requests.
    InternalServerError:
      description: Internal Server Error
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                enum:
                  - error
              message:
                type: string
                example: An unexpected server error occurred.
  securitySchemes:
    api_key:
      type: http
      scheme: bearer
      bearerFormat: string
      description: >-
        Authentication header containing API key (find it in dashboard). The
        format is "Bearer YOUR_API_KEY"

````