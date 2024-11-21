
NUM_NODES=9
python cs4545/system/util.py compose $NUM_NODES topologies/dolev.yaml dolev 4
docker compose build
docker compose up