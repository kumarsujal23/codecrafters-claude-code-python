import argparse
import os
import sys
import json
import subprocess

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

def call_api(messages):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=messages,
        tools=[{
  "type": "function",
  "function": {
    "name": "Read",
    "description": "Read and return the contents of a file",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "The path to the file to read"
        }
      },
      "required": ["file_path"]
    }
  }
},{
  "type": "function",
  "function": {
    "name": "Write",
    "description": "Write content to a file",
    "parameters": {
      "type": "object",
      "required": ["file_path", "content"],
      "properties": {
        "file_path": {
          "type": "string",
          "description": "The path of the file to write to"
        },
        "content": {
          "type": "string",
          "description": "The content to write to the file"
        }
      }
    }
  }
},{
  "type": "function",
  "function": {
    "name": "Bash",
    "description": "Execute a shell command",
    "parameters": {
      "type": "object",
      "required": ["command"],
      "properties": {
        "command": {
          "type": "string",
          "description": "The command to execute"
        }
      }
    }
  }
}]
    )
    if not chat.choices or len(chat.choices) == 0:
        raise RuntimeError("no choices in response")
    else:
        return chat

def execute_tool(tool):

    arguments = json.loads(tool.function.arguments)
    if tool.function.name == "Read":

        file_path = arguments["file_path"]
        with open(file_path,'r') as f:
            content=f.read()
        return content    
    elif tool.function.name == "Write":
        file_path = arguments["file_path"]
        content = arguments["content"]
        with open(file_path,'w') as f:
            f.write(content)
        return "File written successfully"  
    elif tool.function.name == "Bash":
        command = arguments["command"]
        result=subprocess.run(command,shell=True,capture_output=True,text=True)
        return result.stderr + result.stdout




def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")


    print("Logs from your program will appear here!", file=sys.stderr)

    
    messages=[{"role": "user", "content": args.p}]
    while(True):
        chat=call_api(messages)
        m = chat.choices[0].message
        messages.append({
            "role": "assistant",
            "content": m.content,
            "tool_calls": m.tool_calls
            })
        
        if not m.tool_calls:
            print(m.content)
            break
        for tool in m.tool_calls:           
            res = execute_tool(tool)
            messages.append({"role":"tool","tool_call_id":tool.id,"content":res})



if __name__ == "__main__":
    main()
