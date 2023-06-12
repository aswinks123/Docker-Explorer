import time

import pywebio
from plotly.io._orca import psutil
from pywebio.input import input, input_group
from pywebio.output import put_text, put_success, put_error, put_table, put_buttons, put_html, popup, put_image, \
    put_code, put_markdown, put_processbar, set_processbar, put_row
import docker
from pywebio.input import *
from docker.errors import APIError
from pywebio.session import set_env, run_js

def create_container():



    # Create a Docker client
    client = docker.from_env()

    # Collect input from the user using input_group
    container_data = input_group("Create Container", [
        input("Container Name", name="name"),
        input("Image", name="image"),
        input("Command", name="command"),
        select("Detach?", options=["Yes", "No"], name="detach"),
    ])

    # Get the input values
    container_name = container_data['name']
    image = container_data['image']
    command = container_data['command']
    detach = container_data['detach'] == "Yes"

    try:
        # Create the container
        container = client.containers.create(image, command, detach=detach, name=container_name)
        # Start the container
        container.start()
        put_processbar('bar')
        for i in range(1, 3):
            set_processbar('bar', i / 2)
            time.sleep(0.2)
        put_text(f"Container '{container_name}' created and started successfully!")
        time.sleep(0.5)
        run_js('window.location.reload()')
    except docker.errors.APIError as e:
        put_text(f"Failed to create and start container: {str(e)}")

def format_size(size):
    # Convert size to human-readable format
    power = 2 ** 10
    n = 0
    while size > power:
        size /= power
        n += 1
    size = round(size, 2)
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    return f"{size} {suffixes[n]}"


def get_container_counts():
    try:
        # Create a Docker client
        client = docker.from_env()

        # Get the list of containers
        containers = client.containers.list(all=True)

        # Count the number of running and stopped containers
        running_containers = sum(1 for container in containers if container.status == 'running')
        stopped_containers = sum(1 for container in containers if container.status == 'exited')

        return running_containers, stopped_containers

    except docker.errors.APIError as e:
        put_error(f"Failed to retrieve containers: {str(e)}")
        return 0, 0

def count_containers():
    # Get the counts of running and stopped containers
    running_containers, stopped_containers = get_container_counts()

    # Create labels to display the counts
    running_label = put_markdown(f"**<span style='color: green'>Running Containers:</span>** {running_containers}",sanitize=False)
    stopped_label = put_markdown(f"**<span style='color: orange'>Stopped Containers:</span>** {stopped_containers}",sanitize=False)


def show_resource_usage(container_id):

        try:
            # Create a Docker client
            client = docker.from_env()

            # Get the container object
            container = client.containers.get(container_id)

            # Get the container's resource usage
            stats = container.stats(stream=False)
            usage = stats['cpu_stats']['cpu_usage']['total_usage']
            memory_usage = stats['memory_stats']['usage']

            usage_info = f"CPU Usage: {usage} units\nMemory Usage: {format_size(memory_usage)}\n\n"


            # Display the resource usage information in a popup
            popup('Resource Usage', usage_info )

        except APIError as e:
            put_error(f"Failed to retrieve resource usage for container '{container_id}': {str(e)}")
def show_logs(container_id):



    client = docker.from_env()

    # Get the container object
    container = client.containers.get(container_id)

    # Get the container logs
    logs = container.logs().decode('utf-8')

    # Display the logs in a popup
    #popup(put_text, 'Container Logs', logs)
    popup('Logs of: '+container_id,logs)





def remove_container(container_id):
    pass

def stop_container(container_id):

    try:
        # Create a Docker client
        client = docker.from_env()

        # Stop the container
        container = client.containers.get(container_id)
        container.stop()

        put_error(f"Container '{container_id}' stopped successfully!")
        time.sleep(0.5)
        run_js('window.location.reload()')

    except APIError as e:
        put_error(f"Failed to stop container '{container_id}': {str(e)}")

def list_containers():

    img = open('dockers.png', 'rb').read()
    put_image(img, width='75')
    put_html(r"""<h1  align="center"><strong>Docker-Explorer</strong></h1>""")  # App Name in Main screen
    put_code("Webapp to manage Docker resources. Created by : Aswin KS",
             'python')
    count_containers()


    def clear_button():
        run_js('window.location.reload()')




    button_pressed = put_buttons(['Create Container', 'Clear'], onclick=[create_container, clear_button])


    try:
        # Create a Docker client
        client = docker.from_env()

        # Get the list of containers
        containers = client.containers.list()

        if not containers:
            put_error("No containers found.")
        else:
            # Prepare the table data
            table_data = [['Container ID', 'Container Name', 'Image', 'Status', 'Stop', 'Logs','Resource Usage']]
            for container in containers:
                container_id = container.id[:12]
                container_name = container.name
                image = container.image.tags[0]
                status = container.status

                # Create a "Stop" button for each container
                stop_button = put_buttons(
                    ['Stop'],
                    onclick=[lambda container_id=container_id: stop_container(container_id)]

                )

                # Create a "Logs" button for each container
                log_button = put_buttons(
                    ['Logs'],
                    onclick=[lambda container_id=container_id: show_logs(container_id)]
                )
                usage_button = put_buttons(
                    ['Resource Usage'],
                    onclick=[lambda container_id=container_id: show_resource_usage(container_id)]
                )

                table_data.append([container_id, container_name, image, status, stop_button, log_button, usage_button])
            # Display the table
            put_table(table_data)
    except APIError as e:
        put_error(f"Failed to retrieve containers: {str(e)}")

if __name__ == '__main__':
    pywebio.start_server(list_containers, port=8000, static_dir='.', debug=True)
