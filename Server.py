from flask import Flask, request, jsonify
from app.groqAgent import GroqAgent

import base64
from flask_cors import CORS
from dotenv import load_dotenv
from utils.helper import Helper

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})


@app.route("/chat", methods=['POST'])
async def sendChat():
    # agent = AgentHub("Amara")
    agent = GroqAgent()
    helper = Helper()
    try:
        # Ensure request method is POST
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405

        # Parse the incoming JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        message = ""
        # Define output paths
        save_out_path = "app/audio/out/ai_voice.mp3"
        save_out_path_wav = "app/audio/out/ai_voice.wav"
        
        lip_sync_path = "app/audio/out/ai_lipsync.json"
        save_path = "app/audio/input_audio.webm"
        
        
        
        
        # Ensure audio field exists in the request
        if "audio" in data and data["audio"] is not None:
            print("Got in here!")
            # return jsonify({"error": "Missing 'audio' field in request"}), 400

            # Extract the base64 audio data
            audio_base64 = data["audio"]
            if not audio_base64:
                return jsonify({"error": "Empty 'audio' field"}), 400

            # Decode and save the audio file
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(audio_base64))

                # Process the audio and generate text
            message = agent.generateTextFromVoice(save_path)
        
        
        elif "textInput" in data:            
            message = data["textInput"]
        
        # Generate agent's response
        response_message = agent.predict(message)
        
        data_list = []
        
        # get json data
        parsed_data = helper.getJsonData(response_message)
        
        # format response
        data_list = helper.prepResponseForClient(parsed_data=parsed_data,agent=agent, save_out_path=save_out_path, save_out_path_wav=save_out_path_wav, lip_sync_path=lip_sync_path, data_list=data_list)
        if parsed_data["action"]:
            result  = helper.handleCryptoInteraction(parsed_data["action"])
            blockchain_response = agent.predict(f"{result}")
            block_parsed_data = helper.getJsonData(blockchain_response)
            data_list = helper.prepResponseForClient(parsed_data=block_parsed_data,agent=agent, save_out_path=save_out_path, save_out_path_wav=save_out_path_wav, lip_sync_path=lip_sync_path, data_list=data_list)
            print(result)
        
       
        # Return the response
        return jsonify({
            "messages": data_list
        })

    except Exception as e:
        data_list = []
        print(e, "ERROR")
        error_audio_response_path = "app/audio/error_response/ai_voice.wav"
        error_json_lipSync_path = "app/audio/error_response/ai_lipsync.json"
        lip_sync_json_data = helper.load_json_file(error_json_lipSync_path)
        base64_audio = helper.audio_to_base64(error_audio_response_path)
        data_list.append({
                "message": "Sorry Something Is Wrong on my end chill a bit, and send again",
                "animation": "Idle",
                "facialExpression": "default",
                "audio": base64_audio,
                "lipsync": lip_sync_json_data
            })
        return jsonify({"messages": data_list}), 500

if "__main__" == __name__:
    app.run()