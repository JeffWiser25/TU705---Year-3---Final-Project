# TU705---Year-3---Final-Project
Final Year Engineering Project: STM32 Motor Control, PWM Testing &amp; Closed-Loop PID Speed Control System
# STM32 Closed-Loop Motor Control System – Final Year Engineering Project

## Overview

This repository contains the source code, experimental work, and supporting software developed as part of my final year engineering project at Technological University Dublin.

The project focused on the design, development, and implementation of a low-cost closed-loop DC motor speed control system using the STM32 G491RE Nucleo microcontroller platform. The system was developed using bare metal embedded C programming techniques alongside MATLAB/Simulink modelling and supplementary Python scripts for testing, monitoring, and analysis.

The project explored practical embedded systems development, PWM motor control, ADC interfacing, timer configuration, PI/PID control strategies, and real-world motor control behaviour using laboratory hardware and safe experimental methods.

---

## Project Objectives

* Develop a practical embedded motor control system using an STM32 microcontroller
* Implement PWM-based DC motor speed control
* Investigate PI/PID closed-loop regulation techniques
* Gain practical experience with low-level peripheral configuration
* Explore real-world power electronics and control system behaviour
* Compare simulated and practical system responses
* Develop supporting software tools using Python

---

## Hardware Used

* STM32 G491RE Nucleo Development Board
* 24V PMDC Motor
* Motor Driver Module
* Laboratory Power Supply
* Potentiometers and Analogue Inputs
* Breadboard and Supporting Circuitry
* Flywheel Mechanical Load
* Oscilloscope and Laboratory Test Equipment

---

## Embedded Systems Features

The embedded firmware was developed primarily using bare metal C programming techniques within STM32CubeIDE.

Implemented features include:

* GPIO configuration
* External interrupts
* ADC configuration and analogue input sampling
* Timer configuration
* PWM generation
* Duty cycle control
* Basic PI/PID control structures
* Peripheral interfacing
* Real-time signal handling
* Motor speed regulation experiments

---

## Software & Tools

* STM32CubeIDE
* Embedded C
* MATLAB / Simulink
* Python
* GitHub
* Oscilloscope-based testing and analysis

---

## Repository Contents

| Folder / File      | Description                                    |
| ------------------ | ---------------------------------------------- |
| `/Embedded_C_Code` | STM32 bare metal firmware source files         |
| `/Python_Scripts`  | Python scripts used for testing and analysis   |
| `/Simulink_Models` | MATLAB/Simulink modelling and simulation files |
| `/Images`          | Hardware setup images and screenshots          |
| `/Videos`          | Demonstration links and media                  |
| `/Documentation`   | Supporting documentation and notes             |

---

## Project Outcomes

The completed project successfully demonstrated practical closed-loop motor control using embedded systems techniques and PWM-based power control. Extensive testing was carried out to evaluate controller responsiveness, tuning behaviour, hardware limitations, and safe system operation.

The project received positive feedback during demonstration and evaluation stages and was later selected for presentation during an engineering open day to demonstrate the work to prospective engineering students.

---

## Notes

This repository represents academic project work developed for educational and experimental purposes. Some areas remain open for further refinement and future development, including advanced control optimisation, improved sensing methods, and expanded HMI functionality.

---

## Author

Daryl Sweeney

LinkedIn: [LinkedIn Profile](https://www.linkedin.com/in/daryl-sweeney-b662bb250/?utm_source=chatgpt.com)
