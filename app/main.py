import argparse
import os
import sys
import json

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



def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

#     client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

#     chat = client.chat.completions.create(
#         model="anthropic/claude-haiku-4.5",
#         messages=[{"role": "user", "content": args.p}],
#         tools=[{
#   "type": "function",
#   "function": {
#     "name": "Read",
#     "description": "Read and return the contents of a file",
#     "parameters": {
#       "type": "object",
#       "properties": {
#         "file_path": {
#           "type": "string",
#           "description": "The path to the file to read"
#         }
#       },
#       "required": ["file_path"]
#     }
#   }
# }]
#     )

    # if not chat.choices or len(chat.choices) == 0:
    #     raise RuntimeError("no choices in response")

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # TODO: Uncomment the following line to pass the first stage
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


            


    # print(chat.choices[0].message.content)

    # message=chat.choices[0].message
    # if message.tool_calls:
    #     tool_call = message.tool_calls[0]
    #     function_name=tool_call.function.name
    #     if function_name == "Read":
    #          arguments = json.loads(tool_call.function.arguments)
    #          file_path = arguments["file_path"]
    #          with open(file_path,'r') as f:
    #              content=f.read()
    #          print(content)
    # else:
    #     print(message.content)             



if __name__ == "__main__":
    main()
