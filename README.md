# Arduino based fail safe system
The goal of this project was to teach myself safety logic using an arduino and sensors. I started with making a [LED blink](https://github.com/JoranSt/Fail-Safe-Arduino/blob/main/Code/Arduino/blinkingLed.ino/blinkingLed.ino.ino). After that i worked on the [startup](https://github.com/JoranSt/Fail-Safe-Arduino/blob/main/Code/Arduino/Startup.ino/Startup.ino.ino) with the LCD and made a start with the arming logic. After that I implemented the [automatic disarm logic](https://github.com/JoranSt/Fail-Safe-Arduino/blob/main/Code/Arduino/StartupWithAutomaticDisarm/StartupWithAutomaticDisarm.ino). What the automatic disarm does is it automatically disarms the system after its been idle for too long. This is implemented so the system can't be accidently turned on. Then I added an ultrasonic sensor and a fan as displayed [here](https://github.com/JoranSt/Fail-Safe-Arduino/blob/main/Code/Arduino/SystemWithUltrasonicSensor.ino/SystemWithUltrasonicSensor.ino.ino). I wanted to make the system bigger but I didn't have the necessary equipment. 

Once I finished building the physical system I started building a [simulation](https://github.com/JoranSt/Fail-Safe-Arduino/blob/main/Code/Python/Simulation.py). The simulation was a great learning experience since I started thinking about how to make the simulation with objects in mind. I implemented 2 out of 3 voting and learned about sensor noise. I struggled a lot with the [ui](https://github.com/JoranSt/Fail-Safe-Arduino/blob/main/Code/Python/Ui.py) and integrating it with the simulation and the logging/replay feature. I display every group state at the same time and the system state. Every group has its own graphs from the sensor in that group. I made the ui future proof by making sure it automatically adds new sensors if sensors are added in the config file.
## How it works
I have made the system with the current hardware avalaible. As mentioned above I started with the LED en arming state. To arm the system you need to hold the button for 2 seconds, after arming the system goes into idle mode. When the system is in idle mode you have 5 seconds (or another time depending on the preferences) to turn the system on.  If this does not happen the system goes back in arming state. As expected the sensors need to not be givin a dangerous value otherwise the system state is danger. To check the states I have used an ultrasonicsensor that measures at a frequency of 20 Hz. When the system is in danger and the sensors go back to being safe the system goes into arming mode with a message "arm the system if safe". The LED also represents the system state. When the system is on, the fan spins. 

The sensor value is passed to a python script that displays the sensor values together with the states. I have decided (since in my simulation i use 2 out of 3 voting) to use the same sensor value with a slight variation 3 times. This is displayed in an ui built with pyqt6 and logs the values when the system goes into the danger state. I have noticed that every update a small delay is added (with the arduino data the simulation and replay are fine), this creates quite a big problem because the delay adds up. I have not found a solution for this but I take it as a learning moment. To change what you want to display on the ui you change the mode in [config](https://github.com/JoranSt/Fail-Safe-Arduino/blob/main/Code/Python/config.yaml). Images and gifs will be added later.
## How to run
(Digital diagram of how the arduino is wired)

## What I learned (so far)
- I learned how important it is to write memory efficient code when using microcontrollers.
- I learned that blocking code (like long loops or delay()) should be avoided, because it caused the system to lag heavily
- I learned about enums and how to use them to represent a system state e.g Safe, Warning, Unsafe
- I learned about bit‑flags, which save memory and let me store multiple warning conditions in a single variable using binary
- I Learned to structure the program modularly by splitting up logic in functions after the loop function became too complex
- I learned the basics of fail‑safe behavior and how to make the system react safely when something goes wrong.
- I learned why naming things logically is important for readability and maintenance
- I learned how to design a system with future proof in mind. (Using bitflags and enums even though there werent that many variables. Good for if the system ever get expanded)
- I learned why I should use #define for pin numbers.
- I learned how to make a config file and integrate it in a simulation
- I learned the importance of majority voting in sensors
- I learned that the importance of the reading of the serial data and the displaying (I have not found a solution for this as of now)
- 
## What I can do better (so far)
- I can group the logic even more, it will make the code easier to read and follow. It will also make the code more clean.
- I can structure the system from the start moduraly. That will safe headaches later when I need to refactor everything into modular logic.
- I can do better cable management on the breadboard. this will make things easier to see if something needs troubleshooting, to be added or to be changed.
- I should take into account the (potential) bounces from sensors (I have noticed this while testing).
- I should keep modular thinking in mind even when learning new things. I usually fall back to deepnesting when im learning.
- I should synchronize the reading and the displaying of data
- I should be less reliant on AI. I have used it for the structure but also for debugging. I should learn to debug myself.

## Future improvements
- Adding a relay that detects when the system freezes and shuts down the actuator. (I dont have the hardware for it)
- Since i mostly focused on the logic I should make the design better. (mostly visually with the wires and maybe a dedicated spot for the lcd and sensors)
- Multiple sensors for the same thing. It is safer and can handle sensor failure
- Adding specific noise values to the sensors with their own algorithms
- Making the code cleaner.
## Limitations

