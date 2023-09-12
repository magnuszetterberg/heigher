Simply build the image

    docker build -t heigher .

Then start the container through the docker-compose

    docker-compose up -d

Or, install the requirements

    pip install -r requirements.txt

and run the application

    python3 main.py


Then send curl-request to it like this

    curl "http://localhost:5000/get_height?lat=58.393236&lon=15.656319"
