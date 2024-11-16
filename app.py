from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure API keys
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")

# Add this new route for text-to-speech
@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    try:
        text = request.json.get('text', '')
        
        # ElevenLabs API endpoint (using "Josh" voice - you can change this ID)
        VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"  # Josh voice ID
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_LABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Convert audio data to base64
            import base64
            audio_base64 = base64.b64encode(response.content).decode('utf-8')
            return jsonify({"audio": audio_base64})
        else:
            return jsonify({"error": "Failed to generate speech"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Generation settings for Gemini
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Chat Assistant</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
            font-family: 'Inter', sans-serif;
        }

        body {
            background: linear-gradient(120deg, #f6f7f9 0%, #e9eef5 100%);
            min-height: 100vh;
        }

        #chat-container { 
            display: flex; 
            height: 100vh;
            max-width: 1600px;
            margin: 0 auto;
            box-shadow: 0 15px 40px rgba(0,0,0,0.08);
            border-radius: 24px;
            overflow: hidden;
            background: #ffffff;
        }

        #character-container { 
            flex: 1.4;
            background: linear-gradient(145deg, #ffffff 0%, #f8fafd 100%);
            position: relative;
            margin: 0;
            padding: 0;
        }

        #chat-interface {
            width: 450px;
            padding: 32px;
            background: #ffffff;
            display: flex;
            flex-direction: column;
            box-shadow: -5px 0 25px rgba(0,0,0,0.03);
            margin: 0;
        }

        #chat-header {
            padding-bottom: 24px;
            border-bottom: 2px solid #f0f2f5;
            margin-bottom: 24px;
        }

        #chat-header h1 {
            font-size: 28px;
            color: #1a1f36;
            font-weight: 600;
            margin-bottom: 8px;
        }

        #chat-header p {
            font-size: 15px;
            color: #64748b;
            line-height: 1.5;
        }

        #chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px 5px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            max-width: 85%;
            padding: 14px 18px;
            border-radius: 16px;
            font-size: 15px;
            line-height: 1.5;
            position: relative;
            transition: transform 0.2s ease;
        }

        .message:hover {
            transform: translateY(-1px);
        }

        .user-message {
            background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.1);
        }

        .ai-message {
            background: #f8fafc;
            color: #1e293b;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        }

        #input-container {
            margin-top: 24px;
            position: relative;
            display: flex;
            gap: 8px;
            align-items: center;
            width: 100%;
        }

        #user-input {
            flex: 1;
            padding: 16px;
            border: 2px solid #e2e8f0;
            border-radius: 16px;
            font-size: 15px;
            transition: all 0.3s ease;
            outline: none;
            box-shadow: 0 2px 10px rgba(0,0,0,0.02);
            min-width: 0; /* Prevents input from overflowing */
        }

        #send-button {
            padding: 16px 24px;
            background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
            color: white;
            border: none;
            border-radius: 16px;
            cursor: pointer;
            font-weight: 500;
            font-size: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.1);
            white-space: nowrap;
        }

        #mic-button {
            padding: 16px 24px;
            background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
            color: white;
            border: none;
            border-radius: 16px;
            cursor: pointer;
            font-weight: 500;
            font-size: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.1);
            white-space: nowrap;
        }

        /* Updated responsive styles */
        @media (max-width: 600px) {
            #input-container {
                flex-wrap: wrap;
                gap: 8px;
            }

            #user-input {
                width: 100%;
                flex: 100%;
            }

            #send-button, #mic-button {
                flex: 1;
                padding: 16px 12px;
                font-size: 14px;
            }
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 4px;
            transition: background 0.3s ease;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }

        /* Loading Animation */
        .loading {
            display: inline-flex;
            gap: 4px;
            margin-left: 8px;
        }

        .loading span {
            width: 6px;
            height: 6px;
            background-color: #3b82f6;
            border-radius: 50%;
            animation: bounce 0.5s infinite alternate;
        }

        .loading span:nth-child(2) { animation-delay: 0.15s; }
        .loading span:nth-child(3) { animation-delay: 0.3s; }

        @keyframes bounce {
            to { transform: translateY(-4px); }
        }

        /* Responsive Design */
        @media (max-width: 1200px) {
            #chat-container {
                border-radius: 0;
                height: 100vh;
            }

            #character-container {
                flex: 1;
            }

            #chat-interface {
                width: 400px;
            }
        }

        @media (max-width: 900px) {
            #chat-container {
                flex-direction: column;
            }

            #character-container {
                height: 40vh;
            }

            #chat-interface {
                width: 100%;
                height: 60vh;
            }
        }

        @media (max-width: 600px) {
            #chat-interface {
                padding: 20px;
            }

            #chat-header h1 {
                font-size: 24px;
            }

            .message {
                max-width: 90%;
                padding: 12px 16px;
            }

            #speak-button {
                bottom: 20px;
                right: 20px;
                width: 54px;
                height: 54px;
            }
        }
    </style>
    <link rel="shortcut icon" href="#">
</head>
<body>
    <div id="chat-container">
        <div id="character-container"></div>
        <div id="chat-interface">
            <div id="chat-header">
                <h1>AI Assistant</h1>
                <p>Ask me anything in Hindi or English</p>
            </div>
            <div id="chat-messages"></div>
            <div id="input-container">
                <input type="text" id="user-input" placeholder="Type your message...">
                <button id="send-button">Send</button>
                <button id="mic-button">🎤 Hold to Speak</button>
            </div>
        </div>
    </div>

    <script>
        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f0f0);

        // Get the character container dimensions
        const container = document.getElementById('character-container');
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;

        // Camera setup specifically for half-body framing
        const camera = new THREE.PerspectiveCamera(35, containerWidth / containerHeight, 0.1, 1000);
        camera.position.set(0, 1.6, 2.5);

        // Renderer setup - match container size exactly
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(containerWidth, containerHeight);
        renderer.shadowMap.enabled = true;
        renderer.outputEncoding = THREE.sRGBEncoding;
        document.getElementById('character-container').appendChild(renderer.domElement);

        // Add resize handler to keep canvas matched to container
        window.addEventListener('resize', () => {
            const newWidth = container.clientWidth;
            const newHeight = container.clientHeight;
            camera.aspect = newWidth / newHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(newWidth, newHeight);
        });

        // Restricted controls for better framing
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enablePan = false;
        controls.enableZoom = false;
        controls.minPolarAngle = Math.PI/2.2; // Restrict vertical rotation
        controls.maxPolarAngle = Math.PI/1.8;
        controls.minAzimuthAngle = -Math.PI/4; // Restrict horizontal rotation
        controls.maxAzimuthAngle = Math.PI/4;
        controls.target.set(0, 1.5, 0);
        controls.update();

        // Enhanced lighting for better visuals
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);

        const mainLight = new THREE.DirectionalLight(0xffffff, 1);
        mainLight.position.set(5, 5, 5);
        scene.add(mainLight);

        const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
        fillLight.position.set(-5, 0, 5);
        scene.add(fillLight);

        // Animation system
        const clock = new THREE.Clock();
        let mixer;
        let character;
        let morphTargetMeshes = [];
        let currentExpression = { mouthOpen: 0, mouthSmile: 0 };
        let targetExpression = { mouthOpen: 0, mouthSmile: 0 };

        // Smooth animation parameters
        const LERP_FACTOR = 0.2;
        const EXPRESSION_SMOOTHING = 0.25;

        // Enhanced phoneme and expression mapping
        const expressionMap = {
            // Basic expressions with multiple morphs
            neutral: {
                mouthOpen: 0,
                mouthSmile: 0.1,
                mouthRound: 0,
                eyesClosed: 0,
                eyebrowRaise: 0,
                eyebrowFrown: 0
            },
            speaking: {
                // Base expression while talking
                mouthOpen: 0.2,
                mouthSmile: 0.2,
                eyebrowRaise: 0.2,
                eyesClosed: 0
            },
            emphasis: {
                // For emphasized words
                eyebrowRaise: 0.4,
                mouthSmile: 0.3
            }
        };

        const phonemeMap = {
            'A': { mouthOpen: 0.7, mouthSmile: 0.2, mouthRound: 0.1, eyebrowRaise: 0.1 },
            'B': { mouthOpen: 0.3, mouthSmile: 0.1, mouthRound: 0.2, eyebrowRaise: 0 },
            'O': { mouthOpen: 0.8, mouthSmile: 0, mouthRound: 0.8, eyebrowRaise: 0.1 },
            'closed': { mouthOpen: 0.1, mouthSmile: 0.1, mouthRound: 0.1, eyebrowRaise: 0 }
        };

        // Add this state tracking
        let isSpeaking = false;
        let currentAnimation = null;
        let facialAnimations = null;

        // Updated facial animation setup
        function setupFacialAnimations(character) {
            let faceMeshes = [];
            let currentState = {
                mouthOpen: 0,
                mouthSmile: 0.1,
                mouthRound: 0,
                eyebrowRaise: 0,
                eyesClosed: 0
            };
            let targetState = { ...currentState };
            
            // Find meshes with morph targets
            character.traverse((node) => {
                if (node.morphTargetDictionary) {
                    faceMeshes.push(node);
                    console.log('Found morph targets:', node.morphTargetDictionary);
                }
            });

            const phonemeMap = {
                'A': { mouthOpen: 1.0, mouthSmile: 0.3, mouthRound: 0.1, eyebrowRaise: 0.2 },
                'E': { mouthOpen: 0.8, mouthSmile: 0.7, mouthRound: 0.1, eyebrowRaise: 0.3 },
                'I': { mouthOpen: 0.6, mouthSmile: 0.8, mouthRound: 0.1, eyebrowRaise: 0.2 },
                'O': { mouthOpen: 0.9, mouthSmile: 0.1, mouthRound: 0.9, eyebrowRaise: 0.2 },
                'U': { mouthOpen: 0.7, mouthSmile: 0.1, mouthRound: 0.8, eyebrowRaise: 0.2 },
                'closed': { mouthOpen: 0.1, mouthSmile: 0.1, mouthRound: 0.1, eyebrowRaise: 0 }
            };

            function updateFacialExpression(delta) {
                if (!isSpeaking && !isTransitioning()) return;

                // Increased interpolation speed from 10 to 15
                Object.keys(currentState).forEach(key => {
                    currentState[key] = THREE.MathUtils.lerp(
                        currentState[key],
                        targetState[key],
                        delta * 15
                    );
                });

                // Increased subtle movement frequency from 8 to 10
                if (isSpeaking) {
                    const time = Date.now() * 0.001;
                    const subtleMovement = Math.sin(time * 10) * 0.1;
                    currentState.mouthOpen += subtleMovement;
                    currentState.eyebrowRaise += subtleMovement * 0.3;
                }

                // Apply to all face meshes
                faceMeshes.forEach(mesh => {
                    Object.keys(currentState).forEach(key => {
                        const idx = mesh.morphTargetDictionary[key];
                        if (idx !== undefined) {
                            mesh.morphTargetInfluences[idx] = currentState[key];
                        }
                    });
                });
            }

            function isTransitioning() {
                return Object.keys(currentState).some(key => 
                    Math.abs(currentState[key] - targetState[key]) > 0.01
                );
            }

            return {
                update: updateFacialExpression,
                setPhoneme: (phoneme) => {
                    if (phonemeMap[phoneme]) {
                        targetState = { ...phonemeMap[phoneme] };
                    }
                },
                startSpeaking: () => {
                    isSpeaking = true;
                    // Start with slightly open mouth
                    targetState = phonemeMap['closed'];
                },
                stopSpeaking: () => {
                    isSpeaking = false;
                    targetState = { ...phonemeMap['closed'] };
                }
            };
        }

        // Simple blink animation
        function setupBlinking() {
            let leftEye, rightEye;
            let isBlinking = false;
            
            // Find the eye meshes
            character.traverse((node) => {
                if (node.name === 'EyeLeft') leftEye = node;
                if (node.name === 'EyeRight') rightEye = node;
            });

            if (!leftEye || !rightEye) {
                console.log('Could not find eye meshes');
                return;
            }

            // Store original scales separately for each eye
            const leftOriginalScale = leftEye.scale.y;
            const rightOriginalScale = rightEye.scale.y;

            // Start random blinking
            const blinkInterval = setInterval(() => {
                if (!isBlinking) {
                    isBlinking = true;
                    
                    // Close eyes one at a time
                    leftEye.scale.y = 0.1;
                    
                    // Force update right eye
                    rightEye.scale.set(rightEye.scale.x, 0.1, rightEye.scale.z);
                    rightEye.updateMatrix();
                    
                    // Open eyes after 150ms
                    setTimeout(() => {
                        leftEye.scale.y = leftOriginalScale;
                        
                        // Force update right eye
                        rightEye.scale.set(rightEye.scale.x, rightOriginalScale, rightEye.scale.z);
                        rightEye.updateMatrix();
                        
                        isBlinking = false;
                    }, 150);
                }
            }, 3000 + Math.random() * 2000); // Random interval between 3-5 seconds

            // Store the interval ID on the character object so it doesn't get garbage collected
            character.blinkInterval = blinkInterval;
        }

        // Load character
        const loader = new THREE.GLTFLoader();
        loader.load(
            'https://models.readyplayer.me/6737560f478002db197d3b84.glb',
            function (gltf) {
                character = gltf.scene;
                scene.add(character);

                // Debug: Log initial bone rotations
                character.traverse((node) => {
                    if (node.type === 'Bone' && (node.name === 'Head' || node.name === 'Neck')) {
                        console.log(`${node.name} initial rotation:`, {
                            x: node.rotation.x,
                            y: node.rotation.y,
                            z: node.rotation.z
                        });
                    }
                });

                // Initialize facial animations
                facialAnimations = setupFacialAnimations(character);
                
                // Start blinking
                setupBlinking();
                
                // Add head movements
                setupHeadMovements();
                
                // Add arm movements
                setupArmMovements();
                
                // Center camera on face
                const box = new THREE.Box3().setFromObject(character);
                const center = box.getCenter(new THREE.Vector3());
                controls.target.set(center.x, center.y + 0.5, center.z);
                camera.position.set(center.x, center.y + 0.5, center.z + 2);
                controls.update();

                animate();
            }
        );

        // Smooth expression handling
        function lerpExpression(current, target, factor) {
            return {
                mouthOpen: THREE.MathUtils.lerp(current.mouthOpen, target.mouthOpen, factor),
                mouthSmile: THREE.MathUtils.lerp(current.mouthSmile, target.mouthSmile, factor)
            };
        }

        // Expression presets with smoother transitions
        const expressions = {
            'A': { mouthOpen: 0.7, mouthSmile: 0.3 },
            'E': { mouthOpen: 0.5, mouthSmile: 0.4 },
            'I': { mouthOpen: 0.3, mouthSmile: 0.6 },
            'O': { mouthOpen: 0.8, mouthSmile: 0.1 },
            'U': { mouthOpen: 0.4, mouthSmile: 0.2 },
            'closed': { mouthOpen: 0, mouthSmile: 0.1 }
        };

        function setExpression(expressionName) {
            if (!character || !expressions[expressionName]) return;
            targetExpression = expressions[expressionName];
        }

        // Define more varied mouth animations that simulate talking patterns
        const talkingAnimations = [
            // Basic talking movements
            { mouthOpen: 0.3, mouthSmile: 0.2, mouthRound: 0.1 },    // slight open
            { mouthOpen: 0.5, mouthSmile: 0.3, mouthRound: 0.2 },    // medium open
            { mouthOpen: 0.7, mouthSmile: 0.2, mouthRound: 0.1 },    // wide open
            
            // Side movements
            { mouthOpen: 0.4, mouthSmile: 0.6, mouthRound: 0.1 },    // smile talk
            { mouthOpen: 0.3, mouthSmile: -0.2, mouthRound: 0.3 },   // side movement
            
            // Round shapes for O and U sounds
            { mouthOpen: 0.4, mouthSmile: 0.1, mouthRound: 0.7 },    // round shape
            { mouthOpen: 0.6, mouthSmile: 0.1, mouthRound: 0.5 },    // oval shape
            
            // Nearly closed positions
            { mouthOpen: 0.1, mouthSmile: 0.2, mouthRound: 0.1 },    // almost closed
            { mouthOpen: 0.2, mouthSmile: 0.3, mouthRound: 0.2 }     // slightly open
        ];

        // Define speech animation states and transitions
        const speechAnimator = {
            currentState: 'neutral',
            transitionTime: 0,
            
            states: {
                neutral: {
                    values: { mouthOpen: 0.1, mouthSmile: 0.1, mouthRound: 0.1, eyebrowRaise: 0, eyesClosed: 0 },
                    transitions: ['startTalk', 'smile', 'rest']
                },
                startTalk: {
                    values: { mouthOpen: 0.3, mouthSmile: 0.2, mouthRound: 0.2, eyebrowRaise: 0.1, eyesClosed: 0 },
                    transitions: ['wideOpen', 'roundShape', 'smile'],
                    maxDuration: 200
                },
                wideOpen: {
                    values: { mouthOpen: 0.7, mouthSmile: 0.2, mouthRound: 0.1, eyebrowRaise: 0.2, eyesClosed: 0 },
                    transitions: ['narrowOpen', 'smile', 'startTalk'],
                    maxDuration: 150
                },
                narrowOpen: {
                    values: { mouthOpen: 0.4, mouthSmile: 0.3, mouthRound: 0.2, eyebrowRaise: 0.1, eyesClosed: 0 },
                    transitions: ['roundShape', 'wideOpen', 'rest'],
                    maxDuration: 180
                },
                roundShape: {
                    values: { mouthOpen: 0.5, mouthSmile: 0.1, mouthRound: 0.8, eyebrowRaise: 0.2, eyesClosed: 0 },
                    transitions: ['narrowOpen', 'startTalk'],
                    maxDuration: 160
                },
                smile: {
                    values: { mouthOpen: 0.3, mouthSmile: 0.6, mouthRound: 0.1, eyebrowRaise: 0.3, eyesClosed: 0 },
                    transitions: ['wideOpen', 'startTalk'],
                    maxDuration: 200
                },
                rest: {
                    values: { mouthOpen: 0.15, mouthSmile: 0.2, mouthRound: 0.1, eyebrowRaise: 0.1, eyesClosed: 0 },
                    transitions: ['startTalk', 'neutral'],
                    maxDuration: 120
                }
            },

            // Get next state based on current transitions
            getNextState() {
                const currentStateObj = this.states[this.currentState];
                const possibleTransitions = currentStateObj.transitions;
                return possibleTransitions[Math.floor(Math.random() * possibleTransitions.length)];
            },

            // Add natural variations to movements
            addVariation(values) {
                const variation = Math.random() * 0.15 - 0.075;
                const result = { ...values };
                Object.keys(result).forEach(key => {
                    result[key] = Math.max(0, Math.min(1, result[key] + variation));
                });
                return result;
            },

            // Add blink handling
            updateBlink() {
                const now = Date.now();
                
                // Start a new blink if it's time
                if (!blinkConfig.isBlinking && 
                    now - blinkConfig.lastBlink > Math.random() * 
                    (blinkConfig.maxInterval - blinkConfig.minInterval) + blinkConfig.minInterval) {
                    
                    blinkConfig.isBlinking = true;
                    blinkConfig.lastBlink = now;
                    return 1; // Eyes fully closed
                }
                
                // End the blink if it's been long enough
                if (blinkConfig.isBlinking && now - blinkConfig.lastBlink > blinkConfig.blinkDuration) {
                    blinkConfig.isBlinking = false;
                    return 0; // Eyes fully open
                }
                
                // During blink animation
                if (blinkConfig.isBlinking) {
                    const blinkProgress = (now - blinkConfig.lastBlink) / blinkConfig.blinkDuration;
                    // Create a smooth blink animation
                    if (blinkProgress < 0.5) {
                        return blinkProgress * 2; // Close eyes
                    } else {
                        return 2 - (blinkProgress * 2); // Open eyes
                    }
                }
                
                return 0; // Eyes open by default
            }
        };

        // Add eye blinking configuration
        const blinkConfig = {
            isBlinking: false,
            lastBlink: Date.now(),
            minInterval: 1000,    // Minimum time between blinks (ms)
            maxInterval: 5000,    // Maximum time between blinks (ms)
            blinkDuration: 150    // How long a blink lasts (ms)
        };

        // Updated speak function using state machine
        async function speak(text) {
            try {
                const response = await fetch('/text-to-speech', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: text })
                });

                const data = await response.json();
                if (data.audio) {
                    const audio = new Audio('data:audio/mpeg;base64,' + data.audio);
                    
                    if (facialAnimations) {
                        let animationFrame;
                        let lastStateChange = Date.now();
                        
                        const animate = () => {
                            if (!isSpeaking) return;

                            const now = Date.now();
                            const currentState = speechAnimator.states[speechAnimator.currentState];
                            
                            // Check if it's time to transition to next state
                            if (now - lastStateChange > currentState.maxDuration) {
                                speechAnimator.currentState = speechAnimator.getNextState();
                                lastStateChange = now;
                            }

                            // Get base values and add variations
                            const values = speechAnimator.addVariation(currentState.values);
                            
                            // Add blink value
                            values.eyesClosed = speechAnimator.updateBlink();
                            
                            facialAnimations.setPhoneme(values);

                            animationFrame = requestAnimationFrame(animate);
                        };

                        audio.onplay = () => {
                            isSpeaking = true;
                            speechAnimator.currentState = 'startTalk';
                            lastStateChange = Date.now();
                            animate();
                        };

                        audio.onended = () => {
                            isSpeaking = false;
                            cancelAnimationFrame(animationFrame);
                            
                            // Smooth transition to neutral
                            speechAnimator.currentState = 'neutral';
                            facialAnimations.setPhoneme(speechAnimator.states.neutral.values);
                        };
                    }
                    
                    await audio.play();
                }
            } catch (error) {
                console.error('Error playing audio:', error);
            }
        }

        // Main animation loop
        function animate() {
            requestAnimationFrame(animate);
            const delta = clock.getDelta();

            if (facialAnimations) {
                facialAnimations.update(delta);
            }

            // Update controls if they exist
            if (controls) {
                controls.update();
            }

            renderer.render(scene, camera);
        }

        // Window resize handler
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / 2 / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth / 2, window.innerHeight);
        });

        // Chat interface
        const input = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        const messagesContainer = document.getElementById('chat-messages');

        function addMessage(text, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
            messageDiv.textContent = text;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Update your sendMessage function to use the new addMessage function
        async function sendMessage() {
            const message = input.value.trim();
            if (message) {
                // Add user message
                addMessage(message, true);
                
                // Disable input while processing
                input.disabled = true;
                sendButton.disabled = true;

                try {
                    const response = await fetch('/get_response', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: 'user_input=' + encodeURIComponent(message)
                    });
                    
                    const data = await response.json();
                    const aiResponse = data.response;
                    
                    // Add AI message
                    addMessage(aiResponse, false);
                    
                    await speak(aiResponse);
                } catch (error) {
                    console.error('Error:', error);
                    addMessage('Error: Failed to get response', false);
                }

                // Re-enable input
                input.disabled = false;
                sendButton.disabled = false;
                
                input.value = '';
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }

        sendButton.addEventListener('click', sendMessage);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        function setupHeadMovements() {
            let headBone, neckBone;
            
            // Find the head and neck bones
            character.traverse((node) => {
                if (node.type === 'Bone') {
                    if (node.name === 'Head') headBone = node;
                    if (node.name === 'Neck') neckBone = node;
                }
            });

            if (!headBone || !neckBone) {
                console.log('Could not find head or neck bones');
                return;
            }

            // Store original rotations
            const originalRotation = {
                x: neckBone.rotation.x - 0.1,  // Lift head up slightly
                y: neckBone.rotation.y,
                z: neckBone.rotation.z
            };

            function updateHeadMovement() {
                const time = Date.now() * 0.001;
                
                // Base position - slightly lifted, looking forward
                const baseX = -0.1; // Lift head up
                const baseY = 0;
                const baseZ = 0;
                
                // Engagement movements (like nodding while explaining)
                const engagementX = Math.sin(time * 0.7) * 0.05;  // Occasional nods
                const engagementY = Math.sin(time * 0.4) * 0.08;  // Looking side to side while explaining
                
                // Micro movements for naturalness
                const microX = Math.sin(time * 2.5) * 0.02;
                const microY = Math.cos(time * 2.1) * 0.02;
                const microZ = Math.sin(time * 1.8) * 0.01;
                
                // Very slow drift
                const driftX = Math.sin(time * 0.1) * 0.02;
                const driftY = Math.cos(time * 0.15) * 0.02;
                
                // Combine all movements
                neckBone.rotation.x = originalRotation.x + baseX + engagementX + microX + driftX;
                neckBone.rotation.y = originalRotation.y + baseY + engagementY + microY + driftY;
                neckBone.rotation.z = originalRotation.z + baseZ + microZ;

                // Head follows neck but with slightly reduced movement
                headBone.rotation.x = neckBone.rotation.x * 0.3;
                headBone.rotation.y = neckBone.rotation.y * 0.3;
                headBone.rotation.z = neckBone.rotation.z * 0.3;

                // Force update matrices
                neckBone.updateMatrix();
                neckBone.updateMatrixWorld(true);
                headBone.updateMatrix();
                headBone.updateMatrixWorld(true);
            }

            // Add to main animation loop
            const existingAnimate = animate;
            animate = function() {
                existingAnimate();
                updateHeadMovement();
            };
        }

        function setupArmMovements() {
            let leftArm, rightArm, leftForeArm, rightForeArm, leftHand, rightHand;
            
            // Find arm bones
            character.traverse((node) => {
                if (node.type === 'Bone') {
                    switch(node.name) {
                        case 'LeftArm': leftArm = node; break;
                        case 'RightArm': rightArm = node; break;
                        case 'LeftForeArm': leftForeArm = node; break;
                        case 'RightForeArm': rightForeArm = node; break;
                        case 'LeftHand': leftHand = node; break;
                        case 'RightHand': rightHand = node; break;
                    }
                }
            });

            // Base position (arms straight down)
            const basePosition = {
                arm: { x: 1.4, y: 0, z: 0.1 },
                foreArm: { x: 0, y: 0, z: 0 },
                hand: { x: 0, y: 0, z: 0 }
            };

            // Explaining gestures for forearms with wrist movements
            const gestures = [
                // Neutral
                {
                    leftForeArm: { x: 0, y: 0, z: 1.40 },
                    rightForeArm: { x: 0, y: 0.0, z:-1.4 },
                    rightHand: { x: 0, y: 0, z: 0 },
                    duration: 1000
                },
                // Right arm explaining gesture with wrist emphasis
                {
                    leftForeArm: { x: 0, y: 0, z: 1.40 },
                    rightForeArm: { x: 0, y: 0.3, z:-1.4 },
                    rightHand: { x: 0.2, y: 0, z: 0 },
                    duration: 1500
                },
                // Both arms subtle gesture
                {
                    leftForeArm: { x: 0, y: -0.2, z: 1.40 },
                    rightForeArm: { x: 0, y: 0.2, z:-1.4 },
                    rightHand: { x: -0.2, y: 0, z: 0 },
                    duration: 1800
                }
            ];

            let currentGesture = 0;
            let lastGestureTime = Date.now();
            let transitionProgress = 0;
            let currentTarget = { ...gestures[0] };
            let previousTarget = { ...gestures[0] };

            function updateArmMovements() {
                if (!isSpeaking) {
                    // Return all arm parts to base position when not speaking
                    if (leftArm && rightArm && leftForeArm && rightForeArm && leftHand && rightHand) {
                        // Set arms straight down with smooth transition
                        leftArm.rotation.x = THREE.MathUtils.lerp(leftArm.rotation.x, basePosition.arm.x, 0.1);
                        leftArm.rotation.y = THREE.MathUtils.lerp(leftArm.rotation.y, basePosition.arm.y, 0.1);
                        leftArm.rotation.z = THREE.MathUtils.lerp(leftArm.rotation.z, basePosition.arm.z, 0.1);
                        
                        rightArm.rotation.x = THREE.MathUtils.lerp(rightArm.rotation.x, basePosition.arm.x, 0.1);
                        rightArm.rotation.y = THREE.MathUtils.lerp(rightArm.rotation.y, basePosition.arm.y, 0.1);
                        rightArm.rotation.z = THREE.MathUtils.lerp(rightArm.rotation.z, basePosition.arm.z, 0.1);
                        
                        // Reset forearms
                        leftForeArm.rotation.x = THREE.MathUtils.lerp(leftForeArm.rotation.x, basePosition.foreArm.x, 0.1);
                        leftForeArm.rotation.y = THREE.MathUtils.lerp(leftForeArm.rotation.y, basePosition.foreArm.y, 0.1);
                        leftForeArm.rotation.z = THREE.MathUtils.lerp(leftForeArm.rotation.z, basePosition.foreArm.z, 0.1);
                        
                        rightForeArm.rotation.x = THREE.MathUtils.lerp(rightForeArm.rotation.x, basePosition.foreArm.x, 0.1);
                        rightForeArm.rotation.y = THREE.MathUtils.lerp(rightForeArm.rotation.y, basePosition.foreArm.y, 0.1);
                        rightForeArm.rotation.z = THREE.MathUtils.lerp(rightForeArm.rotation.z, basePosition.foreArm.z, 0.1);
                        
                        // Reset hands
                        leftHand.rotation.x = THREE.MathUtils.lerp(leftHand.rotation.x, basePosition.hand.x, 0.1);
                        leftHand.rotation.y = THREE.MathUtils.lerp(leftHand.rotation.y, basePosition.hand.y, 0.1);
                        leftHand.rotation.z = THREE.MathUtils.lerp(leftHand.rotation.z, basePosition.hand.z, 0.1);
                        
                        rightHand.rotation.x = THREE.MathUtils.lerp(rightHand.rotation.x, basePosition.hand.x, 0.1);
                        rightHand.rotation.y = THREE.MathUtils.lerp(rightHand.rotation.y, basePosition.hand.y, 0.1);
                        rightHand.rotation.z = THREE.MathUtils.lerp(rightHand.rotation.z, basePosition.hand.z, 0.1);
                        
                        // Update all matrices
                        leftArm.updateMatrix();
                        rightArm.updateMatrix();
                        leftForeArm.updateMatrix();
                        rightForeArm.updateMatrix();
                        leftHand.updateMatrix();
                        rightHand.updateMatrix();
                    }
                    return;
                }

                const now = Date.now();
                const time = now * 0.001;
                const timeSinceLastGesture = now - lastGestureTime;

                if (timeSinceLastGesture > gestures[currentGesture].duration) {
                    previousTarget = { ...currentTarget };
                    
                    let nextGesture;
                    do {
                        nextGesture = Math.floor(Math.random() * gestures.length);
                    } while (nextGesture === currentGesture);
                    
                    currentGesture = nextGesture;
                    lastGestureTime = now;
                    transitionProgress = 0;

                    currentTarget = { ...gestures[currentGesture] };
                }

                transitionProgress = Math.min(1, transitionProgress + 0.03);
                const wristMovement = Math.sin(time * 1.5) * 0.1;

                if (leftForeArm && rightForeArm && rightHand) {
                    const ease = t => t * t * (3 - 2 * t);
                    const t = ease(transitionProgress);

                    rightForeArm.rotation.x = THREE.MathUtils.lerp(
                        previousTarget.rightForeArm.x,
                        currentTarget.rightForeArm.x,
                        t
                    );
                    rightForeArm.rotation.y = THREE.MathUtils.lerp(
                        previousTarget.rightForeArm.y,
                        currentTarget.rightForeArm.y,
                        t
                    );
                    rightForeArm.rotation.z = currentTarget.rightForeArm.z;

                    rightHand.rotation.x = THREE.MathUtils.lerp(
                        previousTarget.rightHand.x,
                        currentTarget.rightHand.x + wristMovement,
                        t
                    );

                    // Update matrices
                    leftForeArm.updateMatrix();
                    rightForeArm.updateMatrix();
                    rightHand.updateMatrix();
                }
            }

            // Add to animation loop
            const existingAnimate = animate;
            animate = function() {
                existingAnimate();
                updateArmMovements();
            };
        }

        // Update the voice input setup function
        function setupVoiceInput() {
            const micButton = document.getElementById('mic-button'); // Changed to use the inline button

            // Speech recognition setup
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                micButton.innerHTML = 'Voice input not supported';
                micButton.disabled = true;
                return;
            }

            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            let isListening = false;
            let currentTranscript = '';

            recognition.onresult = (event) => {
                currentTranscript = '';
                for (const result of event.results) {
                    if (result.isFinal) {
                        currentTranscript += result[0].transcript;
                    }
                }
                
                document.getElementById('user-input').value = currentTranscript;
            };

            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                stopListening();
            };

            function startListening() {
                if (!isListening) {
                    isListening = true;
                    recognition.start();
                    micButton.style.backgroundColor = '#ff4444';
                    micButton.innerHTML = '🎤 Release to Send';
                }
            }

            function stopListening() {
                if (isListening) {
                    isListening = false;
                    recognition.stop();
                    micButton.style.background = 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)';
                    micButton.innerHTML = '🎤 Hold to Speak';

                    if (currentTranscript.trim()) {
                        document.getElementById('user-input').value = currentTranscript;
                        sendMessage();
                        currentTranscript = '';
                    }
                }
            }

            // Add button event listeners
            micButton.addEventListener('mousedown', startListening);
            micButton.addEventListener('mouseup', stopListening);
            micButton.addEventListener('mouseleave', stopListening);

            // Add touch support for mobile devices
            micButton.addEventListener('touchstart', (e) => {
                e.preventDefault();
                startListening();
            });
            micButton.addEventListener('touchend', (e) => {
                e.preventDefault();
                stopListening();
            });
        }

        // Add this to your initialization code
        document.addEventListener('DOMContentLoaded', () => {
            setupVoiceInput();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def chat():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form.get("user_input", "").strip()
    
    if user_input:
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.0-pro",
                generation_config=generation_config
            )

            # Updated context to request Hindi responses
            context = f"""You are a helpful AI assistant. Keep your responses concise and natural, as they will be spoken by a 3D character. 
            Please respond in Hindi (using Devanagari script) to the following query: {user_input}"""
            
            response = model.generate_content(context)
            response_text = response.text if response else "मैं क्षमा चाहता हूं, लेकिन मैं जवाब नहीं दे पाया।"
            
            return {"response": response_text}
        except Exception as e:
            return {"response": f"क्षमा करें, एक त्रुटि हुई: {str(e)}"}
    
    return {"response": "मुझे कोई इनपुट नहीं मिला। कृपया फिर से प्रयास करें।"}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

