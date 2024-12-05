
NUM_NODES=5
python cs4545/system/util.py compose $NUM_NODES topologies/dolev.yaml bracha
docker compose build
docker compose up