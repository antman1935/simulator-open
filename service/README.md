# Running the Server

We're currently set up for one simulation. Change it in /simulating/Simulation.py.
To run the server on MacOS, run the following from the root folder:
`sim_id='...' uvicorn service.fastapi.Service:app --reload`

To run the server on Windows, run the following from the root folder:
`SET SIM_ID=...`
`uvicorn service.fastapi.Service:app --reload`

`sim_id` must be the name of a simulation definition file in the simulating/simulations folder.

To stop the server, press `ctrl+z` to exit.