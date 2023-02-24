FROM python:slim-buster

# Args provided by docker-compose
ARG PORT
ARG IP
ARG ENTRY_NODE_ADDRESS
ARG FLASK_PORT

ENV my_ip "${IP}"
ENV my_port "${PORT}"
ENV entry_node_address "${ENTRY_NODE_ADDRESS}"

ENV flask_port "${FLASK_PORT}"

# Install requirements
COPY docker_run_requirements.txt docker_run_requirements.txt
RUN pip3 install -r docker_run_requirements.txt

COPY . src/
COPY run_all.sh /
RUN chmod +x /run_all.sh

# exposing ports   TODO find dynamic solution
EXPOSE ${PORT}

# start node
#CMD [ "python3", "./src/grpc_server.py"]
CMD ["./run_all.sh"]
#/CMD [ "python3", "./src/API_frontend.py"]