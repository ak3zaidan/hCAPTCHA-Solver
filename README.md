# hCAPTCHA solver

> This repo contains 90% of the code needed to solve hCap *request based*

- order.py: This file parsers a real N data and extracts the correct order for the data
- cache_key.py: Run this file when a new version is released, this will cache all the keys needed to solve the challenge
- autoUpdate.py: This uses **Playwright** to intercept a real N-data to get the order
- api.py: Basic flask api with a solver EP
- SolvePayload.py and RequestPayload.py: these file generate the Request/solution payloads
- Solve.py: Main solving logic and flow
- Motion.py: This generates cursor motion data for the request and solution payloads
- FingerPrintManager.py: This grabs new FP's from the database to use for solving
- Decrypt.py: Important file with 2 classes for encrypting/decrypting any payload

The included code will give you almost everything needed to create a production solver, the current solve.py file included is an old version and only included for flow context.

Check out this [X article](https://x.com/Ahm3dZaidan/status/2015347609242857522?s=20) for an in-depth explanation for solving this antibot
