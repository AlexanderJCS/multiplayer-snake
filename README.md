# multiplayer-snake

A multiplayer snake game using sockets and Pygame. The objective is to gain the necessary amount of points to win and/or to out-live your opponent.

## Disclaimer - Alpha

**This project is in alpha. It may be very buggy, and there are still features that need to be added.**

## Setting up the server and client

### Server

1. Download `server.py` from the latest release and run the file. 
2. Then, find your IP. This will be important under the client subsection.

### Client

1. Install the dependencies using `pip install pygame`
2. Download `client.py` from the latest release and and run the program.
3. If the program does not fit your screen, Alt + F4. Open `preferences.json` and set `small_gui` to `true`.
3. Input the IP by clicking on the box. Ask the server host if you do not have the IP.
4. Input the port (this is 9850 by default)
5. Press enter.

## Contributing

### Issues

Please do the following before making an issue:
- Make sure it is not in the known issues section of this readme.
- Clearly state the issue
- Describe how to replicate the issue
- If the issue crashes the client or server, please give the error message (you may need to run the python file in the console to see the error)

### Pull requests

Please clearly state what you changed in the pull request and I will review it.

## Planned features

### Server

Planned features for alpha:
- Win/loss detection is server-side to avoid cheating

### Client

Planned features for alpha:
- Eyes for the snake
- Green enemy snake
- Replay

Planned features for beta:
- Code refactor
- Bugfixes

## Known issues

### Server known issues

No known server side issues

### Client known issues

Tapping the arrow keys may not register the move
