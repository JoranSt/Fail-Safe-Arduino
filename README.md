# Arduino Failsafe Shutdown System
I'm developing a fail-safe Arduino system that monitors multiple sensors and controls an actuator (fan) based on state logic and interlocks. Each sensor will have an LED indicator, and a system-wide LED signals any fault. The project demonstrates (once finished) fail-safe design, modular control logic, and safety-first principles in embedded systems. Right now im focusing on adding more sensors and integrating everything together. Im planning on logging all the readings and making a model in python to simulate the logic. Flowcharts and diagrams will be added later.
---

## What I learned (so far)
---
- I learned about enums and how to use them to represant a system state e.g Safe, Warning, Unsafe
- I learned about bitflags to save memory and have 1 variable for all the warnings using binary (bitflags)
- Learned to structure the program modulary by splitting up logic in functions after loop function became too complex
- I learned the basics of fail‑safe behavior and how to make the system react safely when something goes wrong.
- Learned why naming things logically is important for readibility and maintenance
- Designing a system with future proof in mind. (Using bitflags and enums even tho there werent that many variables. Good for if the system ever get expanded)
---
## What I can do better (so far)
- I can group the logic even more, it will make the code easier to read and follow. It will also make the code more clean.
- I can structure the system from the start moduraly. That will safe headaches later when I need to refactor everything into modular logic.
---
## How it works
## Future improvements
## Limitations
## How to run
(Digital diagram of how the arduino is wired)
