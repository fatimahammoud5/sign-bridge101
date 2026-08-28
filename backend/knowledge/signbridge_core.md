SignBridge Overview

SignBridge is an assistive application designed to improve communication and day-to-day accessibility for deaf and non-speaking users. The application combines sign-language tools, environmental sound awareness, education, communication assistance, and an AI chatbot in one application.

SignBridge AI

SignBridge AI is the chatbot inside the application. It should answer ordinary general questions as a normal AI assistant, but it also has special knowledge of SignBridge through Retrieval-Augmented Generation (RAG). For questions about the user's current app state, it can use live application memory such as recent speech, the latest detected sound, recent sign translation, and Education progress.

The chatbot includes Live Speech, Smart Replies, Speak for Me, saved conversations, copy actions, and normal AI chat.

Live Speech

Live Speech uses speech recognition to convert nearby spoken conversation into text so the user can read what another person is saying. Partial recognition results are shown while speech is being recognized. The most recent recognized sentence can also be stored as context for SignBridge AI.

Smart Replies

After Live Speech recognizes another person's sentence, the user can request suggested replies. SignBridge AI generates several short replies that are directly relevant to the sentence that was heard. The replies can be used, copied, or spoken aloud.

Speak for Me

Speak for Me is a direct communication feature. The user types a sentence and the phone speaks exactly what the user typed using text-to-speech. It does not need to rewrite the user's sentence.

Voice Assist and Sound Analysis

Voice Assist helps a deaf user become aware of important environmental sounds. The sound-analysis system uses an audio classification model based on YAMNet/TFLite. The system analyzes recorded audio windows and produces a detected sound label together with confidence/reliability information. The application can classify sounds such as speech, alarms, animals, vehicles, music, birds, and other environmental sound families when the model has enough confidence.

Sound events can trigger visual, vibration, and notification-based alerts. Detected sounds may also be stored in notification history. SignBridge AI should use the latest saved sound event when the user asks questions such as "What was the last detected sound?" instead of inventing an answer.

Education

The Education section is organized into levels. Each level teaches sign language through a sequence of stages. The learning flow contains four main learning stages:

Learn new signs.

Guess the signs.

Challenge.

Final test.

A completed level is represented separately after the final test. Education progress is stored locally using SharedPreferences, including the current stage, stage indexes, whether a level is unlocked/completed, and the best score. SignBridge AI should use this saved progress when the user asks where they reached, what stage they are on, or what they should continue next.

Sign Translation

SignBridge contains a sign-language translation feature that interprets sign-language input from video/camera and converts recognized signs into understandable text. The translation system is part of the assistive communication workflow and is separate from the chatbot's general knowledge.

Dictionary

The Dictionary section provides sign-language vocabulary reference material. It is intended to let users look up words and view the corresponding sign-language examples. SignBridge has used ASL video resources for dictionary content.

Avatar

The SignBridge concept includes an avatar-based sign-language output feature. Its purpose is to convert textual information into sign-language presentation so information can be communicated visually.

Games

SignBridge includes a Games section intended to make learning and practicing signs more interactive.

SOS

SignBridge includes an SOS feature for urgent situations. Consequential emergency actions should require user confirmation before being sent or triggered.

RAG Behavior Rules

When the user asks about SignBridge features, use retrieved SignBridge knowledge rather than inventing implementation details. If the retrieved project information does not contain the answer, say that the project knowledge base does not contain that detail yet.

When the user asks a general question that is not about SignBridge, answer normally using the AI model's general knowledge.

When the user asks about personal application state such as the last detected sound, current Education progress, recent Live Speech, or recent sign translation, use the saved app-state memory. Never fabricate app-state values.