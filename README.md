# multiplayer-snake

A multiplayer snake game using sockets and Pygame. The objective is to gain the necessary amount of points to win and out-live your opponent.

## Disclaimer

**This project is in alpha. It may be very buggy, and there are still features that need to be added.**

## Setting up the client and server

### Server

1. Download `server.py` from the latest release and run the file. 
2. Then, find your IP. This will be important under the client subsection.

### Client

1. Install the dependencies using `pip install pygame`
2. Download `client.py` from the latest release and and run the program.
3. Connect to the server (ask the server host if you do not have it)
4. Input the port (this is 9850 by default)

## Contributing

### Issues

Please do the following before making an issue:
- Make sure it is not in the known issues section of this readme.
- Clearly state the issue
- Describe how to replicate the issue
- If the issue crashes the client or server, please give the error message (you may need to run the python file in the console to see the error)

### Pull requests

Please clearly state what you changed in the pull request and I will review it.

## To do

### Server

No features planned

### Client

Planned features:
- Graceful disconnection
- Win/lose screen
- IP input screen using pygame
- Eyes for the snake
- Designate your board vs enemy board

## Known issues

### Server

No server-side known issues

### Client

No client-side known issues
