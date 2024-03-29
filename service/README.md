# Running the Server

We're currently set up for one simulation. Change it in /simulating/Simulation.py.
To run the server, run the following from the root folder:
`uvicorn service.fastapi.Service:app --reload`

To stop the server, press `ctrl+z` to exit.