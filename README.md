# htc-media
dev server for getting basic info on image files.

This flask app is designed to run locally on the user's machine to get a list of files/folders for a given path as well as get info on for a specified file path. It appears that there is memory leak in a FileMaker plugin, so doing curl requests avoids using the the plugin.

This app is build against python 3.7, but should work with all 3.x versions.

To start the microservice, run the `run.sh`. Once the service is up do curl requests to `127.0.0.0:5000`

### Endpoints
`/ping` test microservice is running

*NOTE: the endpoints below expect a JSON object of `{"file_path":"«UTF-8 encoded file path»"}`*

`/get-folder-list` list all folders for the specified path

`/get-file-list` list all files for the specified path

`/info` get file info for the specified file.
