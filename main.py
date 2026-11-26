#importing  all the libraries--------------

import cv2                 #accesses the webcam and processes video.
import mediapipe as mp      #detects hand landmarks.        -m pip install mediapipe
import pyautogui            #controls the mouse and cursor.
import math                 #calculates the distance between fingers.
import speech_recognition as sr         #listens to your voice and recognizes commands.
import threading              #allows voice recognition and hand tracking to run concurrently.



# setting of camera and the mouse ----------------

#Initializing the webcam and hand tracking
cap = cv2.VideoCapture(0)  #opens the default webcam. The number 0 generally represents the first camera.

mp_hands = mp.solutions.hands   #accesses MediaPipe's hand-tracking solution.
hands = mp_hands.Hands(max_num_hands=1) #configures the program to detect at most one hand.
mp_draw = mp.solutions.drawing_utils        #helps draw the detected hand landmarks and connections on the video.


#MediaPipe can identify 21 points on a hand. Some important landmark indexes are:
#Landmark index	Meaning
#0	Wrist
#4	Thumb tip
#8	Index finger tip
#12	Middle finger tip
#16	Ring finger tip
#20	Little finger tip
#our code mainly uses landmarks 4 and 8 to detect a click.

#Getting the screen size------------
screen_w, screen_h = pyautogui.size()  #returns the width and height of your computer screen.

prev_x, prev_y = 0, 0       #store the previous cursor position.
smoothening = 5     #controls how gradually the cursor follows your finger.

running = True   #True is a control flag used by the voice thread and the main loop.

# voice command function ----------------––---

#This function listens to your microphone and tries to convert your speech into text.
def take_command():
    r = sr.Recognizer()     #creates a speech recognizer.

    with sr.Microphone() as source:     #opens the microphone.
        print(" Listening...")
        r.adjust_for_ambient_noise(source) #estimates background noise.

        try:
            audio = r.listen(source, timeout=5)    #captures audio.
            command = r.recognize_google(audio)     #sends the captured audio to Google's recognition service and returns recognized text.
            print("Voice Command:", command.lower())  
                                    
            return command.lower() #converts the text to lowercase, making comparisons easier.

        except:
            return ""   #If recognition fails or the timeout occurs, the function returns an empty string.

#  voice thread ----------------

#Executing voice commands

#This function checks the recognized text and performs the corresponding mouse action.
def voice_control():
    global running

    while running:
        command = take_command()

        if "click" in command:
            pyautogui.click()

        elif "right click" in command:
            pyautogui.rightClick()

        elif "double click" in command:
            pyautogui.doubleClick()

        elif "scroll up" in command:
            pyautogui.scroll(500)

        elif "scroll down" in command:
            pyautogui.scroll(-500)

        elif "stop" in command or "exit" in command:
            print("🛑 Stopping program...")
            running = False
            break


        #Voice command	      Intended action
        #"Click"	              Left-click
        #"Right click"	      Right-click
        #"Double click"	      Double-click
       #"Scroll up"	          Scroll upward
        #"Scroll down"	      Scroll downward
        #"Stop" or "Exit"	   Stop the control loop
        

# starting of  voice thread-------------------

#Without threading, the program might wait for voice input before processing the next webcam frame. 
# The cursor could become unresponsive while the microphone is listening.
#daemon=True means the background thread will not, by itself, keep the Python process alive after all non-daemon threads have finished. 
# It does not automatically release the webcam or microphone safely.

threading.Thread(target=voice_control, daemon=True).start()   

#  main hand tracking loop is here----------------
#Capturing and processing webcam frames
while running:         #continues processing while the control flag remains true.
    success, frame = cap.read()

    if not success:
        print(" Cannot access camera")
        break

    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result = hands.process(rgb)
#cap.read(): captures a frame from the webcam.
#success: tells you whether a frame was captured successfully.
#frame: contains the image.
#cv2.flip(frame, 1): mirrors the frame horizontally, making it feel like looking into a mirror.
#frame.shape: gets the image height, width, and channel count.
#cv2.cvtColor(...): converts OpenCV's BGR image to RGB.
#hands.process(rgb): sends the frame to MediaPipe to detect the hand.

#If the webcam cannot provide a frame, your loop exits. This is why checking success is important.

#Detecting the index finger and thumb----------------
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            index_finger = hand_landmarks.landmark[8]
            thumb_finger = hand_landmarks.landmark[4]

            #result.multi_hand_landmarks contains the detected hand landmarks, if a hand is found.
            #The for loop processes each detected hand. Since you configured one hand, it normally processes zero or one hand.
            #draw_landmarks() displays the hand skeleton.
            #landmark[8] selects the index finger tip.
            #landmark[4] selects the thumb tip.


            #Converting finger position into cursor position------------------

            #x1, y1: the index finger's position in the webcam frame.
            #screen_x, screen_y: the corresponding position on the computer screen.
            #For example, if the index finger's normalized horizontal coordinate is 0.5 and the screen width is 1920:
            #The cursor is mapped to the middle of the screen horizontally.  

            x1 = int(index_finger.x * w)
            y1 = int(index_finger.y * h)

            screen_x = int(index_finger.x * screen_w)
            screen_y = int(index_finger.y * screen_h)

            # smooth cursor movement---------------
            curr_x = prev_x + (screen_x - prev_x) / smoothening
            curr_y = prev_y + (screen_y - prev_y) / smoothening

            pyautogui.moveTo(curr_x, curr_y)
            prev_x, prev_y = curr_x, curr_y

            #The cursor does not jump immediately to the new position. Instead, it moves gradually from the previous position toward the new position.
        
            # gesture click (thumb + index close) detection ------------
            #our project calculates the distance between the index finger tip and thumb tip.
            #The math.hypot() function calculates the straight-line distance between the two points.
            distance = math.hypot(    
                x1 - int(thumb_finger.x * w),
                y1 - int(thumb_finger.y * h)
            )

            if distance < 40:
                pyautogui.click()


              
#Displaying the video and exiting-----------------------
    cv2.imshow("AI Virtual Mouse + Voice", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    #cv2.imshow() displays the webcam feed and detected hand landmarks.
    #cv2.waitKey(1) waits briefly for a keyboard event.
    #Pressing q exits the main webcam loop.

#  clean exit ----------------
cap.release()  #cap.release() releases the webcam.
cv2.destroyAllWindows(q) #cv2.destroyAllWindows() closes the OpenCV display windows.



