# Test environment setup

## DB

Pull [this docker image](https://hub.docker.com/_/mariadb/).

Then run ``run_test_db.sh`` from the tools directory to start the container with some test data.

See the header of ``run_test_db.sh`` for db info.

## API

Run like this for example:

    ./siptrackd -l - -b stmysql -s tools/dev_local.cfg --searcher=whoosh --searcher-args=./st-whoosh