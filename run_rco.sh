
NUM_NODES=10
python cs4545/system/util.py compose $NUM_NODES topologies/dolev.yaml rco
docker compose build
docker compose up