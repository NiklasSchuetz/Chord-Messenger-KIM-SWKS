#!/bin/bash

exec python3 /src/grpc_server.py &
exec python3 /src/API_frontend.py