from flask import Flask, request, Response, json
import requests
from uuid import uuid4
import time

app = Flask(__name__)

MODEL_MAPPING = {
   "deepseek": "deepseek/deepseek-chat",
   "gpt-4o-mini": "openai/gpt-4o-mini", 
   "gemini-flash-1.5": "google/gemini-flash-1.5",
   "deepseek-reasoner": "deepseek-reasoner",
   "minimax-01": "minimax/minimax-01"
}

def make_heck_request(question, session_id, messages, actual_model):
   previous_question = previous_answer = None
   if len(messages) >= 2:
       for i in range(len(messages)-2, -1, -1):
           if messages[i]["role"] == "user":
               previous_question = messages[i]["content"]
               if i+1 < len(messages) and messages[i+1]["role"] == "assistant":
                   previous_answer = messages[i+1]["content"]
               break

   payload = {
       "model": actual_model,
       "question": question,
       "language": "Chinese",
       "sessionId": session_id,
       "previousQuestion": previous_question,
       "previousAnswer": previous_answer
   }
   
   headers = {
       "Content-Type": "application/json",
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
   }

   return requests.post(
       "https://gateway.aiapilab.com/api/ha/v1/chat",
       json=payload,
       headers=headers,
       stream=True
   )

def stream_response(question, session_id, messages, request_model, actual_model):
   resp = make_heck_request(question, session_id, messages, actual_model)
   is_answering = False
   
   for line in resp.iter_lines():
       if line:
           line = line.decode('utf-8')
           if not line.startswith('data: '):
               continue
           
           content = line[6:].strip()
           
           if content == "[ANSWER_START]":
               is_answering = True
               chunk = {
                   "id": session_id,
                   "object": "chat.completion.chunk",
                   "created": int(time.time()),
                   "model": request_model,
                   "choices": [{
                       "index": 0,
                       "delta": {"role": "assistant"},
                   }]
               }
               yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
               continue
           
           if content == "[ANSWER_DONE]":
               chunk = {
                   "id": session_id,
                   "object": "chat.completion.chunk",
                   "created": int(time.time()),
                   "model": request_model,
                   "choices": [{
                       "index": 0,
                       "delta": {},
                       "finish_reason": "stop"
                   }]
               }
               yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
               break
           
           if is_answering and content and not content.startswith("[RELATE_Q"):
               chunk = {
                   "id": session_id,
                   "object": "chat.completion.chunk",
                   "created": int(time.time()),
                   "model": request_model,
                   "choices": [{
                       "index": 0,
                       "delta": {"content": content},
                   }]
               }
               yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

def normal_response(question, session_id, messages, request_model, actual_model):
   resp = make_heck_request(question, session_id, messages, actual_model)
   full_content = []
   is_answering = False
   
   for line in resp.iter_lines():
       if line:
           line = line.decode('utf-8')
           if line.startswith('data: '):
               content = line[6:].strip()
               if content == "[ANSWER_START]":
                   is_answering = True
               elif content == "[ANSWER_DONE]":
                   break
               elif is_answering:
                   full_content.append(content)
   
   response = {
       "id": session_id,
       "object": "chat.completion",
       "created": int(time.time()),
       "model": request_model,
       "choices": [{
           "index": 0,
           "message": {
               "role": "assistant",
               "content": "".join(full_content)
           },
           "finish_reason": "stop"
       }]
   }
   return response

@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
   data = request.json
   model = MODEL_MAPPING.get(data["model"])
   if not model:
       return {"error": "Unsupported Model"}, 400

   question = next((msg["content"] for msg in reversed(data["messages"]) 
                   if msg["role"] == "user"), None)
   session_id = str(uuid4())

   if data.get("stream"):
       return Response(
           stream_response(question, session_id, data["messages"], 
                         data["model"], model),
           mimetype="text/event-stream"
       )
   else:
       return normal_response(question, session_id, data["messages"], 
                            data["model"], model)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=8801)