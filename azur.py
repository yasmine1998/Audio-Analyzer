import azure.cognitiveservices.speech as speechsdk
import time as t

def recognize_from_microphone():
    fillers = ["uh","uhh","um","umm","uhm","er","hm","hmm","mhm","huh"]
    speech_config = speechsdk.SpeechConfig(subscription="99f9cd4c910c445ca030c8059fcab9b9", region="uaenorth")
    speech_config.speech_recognition_language="en-US"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
   
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    print("Speak into your microphone.")
    start = t.time()
    speech_recognition_result = speech_recognizer.recognize_once_async().get()
    end = t.time()
    time_spent = end - start
    #print(int(time_spent))
    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        
        #if int(time_spent) == 1:
        #print("Recognized: {}".format(speech_recognition_result.text))
        words = speech_recognition_result.text.split()
        print("Speech rate: ",len(words)/time_spent)
            
        filler_words = [word[:-1] for word in words if not word[-1].isalpha()]
        filler_words = [word for word in filler_words if word.lower() in fillers]
        print("Number of filler words: ",len(filler_words))
        
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")

while True:
    recognize_from_microphone()

