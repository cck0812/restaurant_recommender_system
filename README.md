# restaurant_recommender_system

## Usage

Before starting Airflow for the first time, You need to prepare your environment

    echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env

On all operating systems, you need to run database migrations and create the first user account. To do it, run.

    docker-compose up airflow-init

After initialization is complete, you should see a message like below.

    airflow-init_1       | Upgrades done
    airflow-init_1       | Admin user airflow created
    airflow-init_1       | 2.1.3
    start_airflow-init_1 exited with code 0

The account created has the login `airflow` and the password `airflow`.

## Running All Services

    docker-compose up

In the second terminal you can check the condition of the containers and make sure that no containers are in unhealthy condition.

To get the public URL of the tunnel just open `http://localhost:4040` in a web browser.

## Cleaning-up the environment

- Run `docker-compose down --volumes --remove-orphans`
