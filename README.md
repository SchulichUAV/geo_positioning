# geo_target_positioning
Repository for Direct Geolocation methods for autonomously identified targets

LED Command modes:

- COM1> This is the communication port prompt it means you are sending the command over serial port COM1. The receiver listens for ASCII commands here.

- slm, This stands for setLEDMode — a command used to set the blinking mode of one of the receiver’s LEDs. (The counterpart glm is for getLEDMode.)


- DIFFCORLED This is the mode you’re setting. It tells the receiver to configure the LED to indicate Differential Correction (DIFFCOR) status — it will blink according to that event.

<CR> This means “Carriage Return” (pressing Enter). It tells the receiver that the command is complete and ready to execute.

