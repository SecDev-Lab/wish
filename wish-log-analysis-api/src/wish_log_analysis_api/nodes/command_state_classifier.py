"""Command state classifier node functions for the log analysis graph."""

import os

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.command_result.command_state import CommandState
from wish_models.settings import Settings

from ..models import GraphState

# Define the prompt template
COMMAND_STATE_CLASSIFIER_PROMPT = """
As a security operations analyst, your task is to determine if a command output indicates successful
initial access to a target system.

# PRIORITY ORDER FOR CLASSIFICATION:

1. FIRST: Check for Initial Access Success
   - If ANY initial access indicators are found, classify as "SUCCESS_INITIAL_ACCESS" regardless of exit_code
   - This takes absolute precedence over all other classifications

2. SECOND: Check for Normal Success
   - Only if NO initial access indicators were found AND exit_code is "0", classify as "SUCCESS"
   - Even if exit_code is 0, do not classify as "SUCCESS" if there are initial access indicators
     (use "SUCCESS_INITIAL_ACCESS" instead)

3. THIRD: Check for Specific Error Types
   - Only if neither of the above conditions are met

# MOST IMPORTANT RULE: Check for Initial Access Success REGARDLESS of exit_code

Even if the command timed out (exit_code 124) or had any other error, FIRST check if there are ANY signs
of successful initial access in the output.

# FIRST PRIORITY: Check for Initial Access Success

Before any other analysis, check if the command output indicates successful initial access to the target system.
Classify as "SUCCESS_INITIAL_ACCESS" if ANY of the following indicators are present:

## 1. Meterpreter or shell session establishment (HIGHEST PRIORITY)
- ANY line containing "Meterpreter session" AND "opened" (This is the strongest indicator)
- ANY line containing "Session" AND "created"
- ANY line containing "Command shell session" AND "opened"
- ANY line containing "WIN" surrounded by special characters (like =-=-=WIN=-=-=)
- "Successful connection established"
- "Successfully opened reverse shell"

## 2. Successful remote command execution proving access
- Evidence of successful `whoami` execution on target
- Evidence of successful `id` execution on target
- Evidence of successful `hostname` execution on target
- Evidence of successful `ipconfig`/`ifconfig` execution on target
- Evidence of successful `ls`/`dir` execution on target

## 3. Explicit access confirmation
- "Access gained to target system"
- "Successfully compromised target"
- "Initial foothold established"
- "Initial access achieved"
- "Successfully exploited vulnerability"

# IMPORTANT: The exit_code does NOT override initial access indicators
If ANY of the above indicators are found, classify as "SUCCESS_INITIAL_ACCESS" regardless of the exit_code.
This includes cases where the command timed out (exit_code 124) but still managed to establish a session.

# SECOND PRIORITY: Standard Command State Analysis

Only if NONE of the above initial access indicators are found, proceed with standard command state analysis:

1. If the `exit_code` is "0", classify as "SUCCESS" and end.
   - This includes successful port scans that found open ports
   - This includes successful reconnaissance commands
   - This includes ANY command that completed normally with exit_code 0

2. Otherwise, check the command output from `stdout` and `stderr`. Then choose the most appropriate
   code from the following:
   - TIMEOUT: When command execution times out or when the output indicates a timeout occurred.
     Look for indicators such as:
     * Messages containing phrases like "timeout", "timed out", "Read timeout expired"
     * Messages containing "connection timeout" or similar connection-related timeout phrases
     * Log entries indicating that a command was terminated due to exceeding time limits
     * Warning messages about waiting too long for command completion
     * `exit_code` is "124" or "-1" (reserved for timeout)
   - COMMAND_NOT_FOUND: When the command is not found on the local machine
   - FILE_NOT_FOUND: When a local file referenced in the command is not found (excluding remote files like smb)
   - REMOTE_OPERATION_FAILED: When an operation on a remote machine (e.g., file reference, command execution) fails
   - NETWORK_ERROR: When a network error occurs
   - OTHERS: When an error not listed above occurs

3. Classify with the selected error code and end.

# NOTE

- SUCCESS_INITIAL_ACCESS takes precedence over all other states, including SUCCESS and TIMEOUT.
  OTHERS is the last resort.

# OUTPUT FORMAT

You must output your response in JSON format with the following structure:
{{
  "command_state": "STATE_HERE",
  "reason": "Detailed explanation of why this state was chosen"
}}

Where STATE_HERE is one of: SUCCESS_INITIAL_ACCESS, SUCCESS, COMMAND_NOT_FOUND, FILE_NOT_FOUND, 
REMOTE_OPERATION_FAILED, TIMEOUT, NETWORK_ERROR, or OTHERS.

Example output:
{{
  "command_state": "SUCCESS",
  "reason": "The command executed successfully with exit code 0 and produced expected output."
}}

# command
{command}

# exit_code
{exit_code}

# stdout
{stdout}

# stderr
{stderr}
"""


def classify_command_state(state: GraphState, settings_obj: Settings) -> GraphState:
    """Classify the command state from a command result.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with command state.
    """
    import json
    import logging
    from wish_tools.tool_step_trace import main as step_trace

    # Create a new state object to avoid modifying the original
    # Only set the fields this node is responsible for
    new_state = GraphState(
        command_result=state.command_result,
        log_summary=state.log_summary,
        analyzed_command_result=state.analyzed_command_result,
        api_error=state.api_error,
        run_id=state.run_id,
    )

    # Get the command and exit code from the state
    command = state.command_result.command
    exit_code = state.command_result.exit_code

    # Read stdout and stderr from log_files
    stdout = ""
    stderr = ""
    if state.command_result.log_files:
        if state.command_result.log_files.stdout and os.path.exists(state.command_result.log_files.stdout):
            with open(state.command_result.log_files.stdout, "r", encoding="utf-8") as f:
                stdout = f.read()
        if state.command_result.log_files.stderr and os.path.exists(state.command_result.log_files.stderr):
            with open(state.command_result.log_files.stderr, "r", encoding="utf-8") as f:
                stderr = f.read()

    # Create the prompt
    prompt = PromptTemplate.from_template(COMMAND_STATE_CLASSIFIER_PROMPT)

    # Initialize the OpenAI model
    model = ChatOpenAI(
        model=settings_obj.OPENAI_MODEL, 
        api_key=settings_obj.OPENAI_API_KEY, 
        use_responses_api=True,
        model_kwargs={"response_format": {"type": "json_object"}}
    )

    # Create the chain
    chain = prompt | model | JsonOutputParser()

    # Generate the classification
    try:
        classification_data = chain.invoke(
            {"command": command, "exit_code": exit_code, "stdout": stdout, "stderr": stderr}
        )

        # Process the JSON response (already parsed by JsonOutputParser)
        try:
            command_state_str = classification_data.get("command_state")
            reason = classification_data.get("reason", "No reason provided")
            
            # Log the classification result and reason
            logging.info(f"Command state classification: {command_state_str}")
            logging.info(f"Reason: {reason}")
            
            # Send to StepTrace if run_id is available
            if state.run_id:
                trace_message = json.dumps({
                    "command_state": command_state_str,
                    "reason": reason
                }, ensure_ascii=False)
                
                try:
                    step_trace(
                        run_id=state.run_id,
                        trace_name="command_state_classification",
                        trace_message=trace_message
                    )
                    logging.info(f"StepTrace sent for run_id: {state.run_id}")
                except Exception as trace_error:
                    logging.error(f"Error sending StepTrace: {str(trace_error)}")
            
            # Convert the classification string to CommandState
            if command_state_str == "SUCCESS_INITIAL_ACCESS":
                command_state = CommandState.SUCCESS_INITIAL_ACCESS
            elif command_state_str == "SUCCESS":
                command_state = CommandState.SUCCESS
            elif command_state_str == "COMMAND_NOT_FOUND":
                command_state = CommandState.COMMAND_NOT_FOUND
            elif command_state_str == "FILE_NOT_FOUND":
                command_state = CommandState.FILE_NOT_FOUND
            elif command_state_str == "REMOTE_OPERATION_FAILED":
                command_state = CommandState.REMOTE_OPERATION_FAILED
            elif command_state_str == "TIMEOUT":
                command_state = CommandState.TIMEOUT
            elif command_state_str == "NETWORK_ERROR":
                command_state = CommandState.NETWORK_ERROR
            elif command_state_str == "OTHERS":
                command_state = CommandState.OTHERS
            else:
                raise ValueError(f"Unknown command state classification: {command_state_str}")
                
        except Exception as json_error:
            logging.error(f"Failed to process JSON response: {classification_data}")
            logging.error(f"Error: {str(json_error)}")
            raise ValueError(f"Invalid JSON response from LLM: {str(json_error)}")

        # Set the command state and reason in the new state
        new_state.command_state = command_state
        new_state.reason = reason

    except Exception as e:
        # In case of any error, log it and set API_ERROR state
        error_message = f"Error classifying command state: {str(e)}"

        # Log the error
        logging.error(error_message)
        logging.error(f"Command: {command}")
        logging.error(f"Exit code: {exit_code}")

        # Set error information in the new state
        new_state.command_state = CommandState.API_ERROR
        new_state.api_error = True

    # Return the new state
    return new_state
