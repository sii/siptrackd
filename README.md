# Siptrackd

Siptrackd is the backend API part of Siptrack, to make documentation easier all docs are found in the [siptrackweb repo](https://github.com/sii/siptrackweb).

# Quickstart

    $ git clone https://github.com/sii/siptrackd
    $ cd siptrackd
    $ virtualenv .venv
    $ source .venv/bin/activate
    (.venv) $ pip install -r requirements.txt
    (.venv) $ python setup.py install
    (.venv) $ siptrackd -l - -b stsqlite -s storage.cfg --searcher=whoosh --searcher-args=./st-whoosh

That will start the API backend on port 9242 without SSL.

Now use [siptrack client](https://github.com/sii/siptrack) to access it.