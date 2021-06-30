@echo off
TITLE Tesla Robo
:: Enables virtual env mode and then starts TeslaRobo
env\scripts\activate.bat && py -m TeslaRobot
