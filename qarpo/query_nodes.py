#!/usr/bin/env python3

import subprocess
import xml.etree.ElementTree as ET
import os

# Queries node on a queue server with specific properties
# and counts how many slots are available for job submission.
# Only "free" and "job-exclusive" nodes are counted
# Nodes that are "offline" or "down" are not included in the count
def getFreeJobSlots(query_queue_server, search_for_node_properties, verbose = False):

    # Query pbsnodes, output in XML format
    pbsnodes_output = subprocess.run(['pbsnodes', '-x', '-s', query_queue_server], stdout=subprocess.PIPE)

    # Parse the XML output
    nodes_report = ET.fromstring(pbsnodes_output.stdout)

    # Initialize counters
    free_slots_total = 0
    available_slots_total = 0

    # Loop through all nodes
    for node in nodes_report:
        node_hostname = node.find('name').text
        node_properties = node.find('properties').text.split(',')
        node_state = node.find('state').text
        node_np = int(node.find('np').text)

        # Check if any of the node's properties match the properties listed in search_for_node_properties:
        if len(list(set(node_properties) & set(search_for_node_properties))) > 0:
            available_slots_in_node = 0
            taken_slots_in_node = 0
            free_slots_in_node = 0

            # Only count online nodes towards the slot counts (ignore down and offline nodes)
            if node_state in ['free', 'job-exclusive']:
                available_slots_in_node = node_np

                # Go through all the jobs running on the node
                node_jobs = node.find('jobs')
                if node_jobs is None:
                    # No jobs running on the node
                    taken_slots_in_node = 0
                else:
                    # There are jobs on the node. Parse and traverse the list of jobs
                    jobs = node_jobs.text.split(',')
                    for job in jobs:
                        # Get the list of the job's slots
                        slots = job.split('/')[0]
                        if slots.isnumeric():
                            # Jobs taking one slot will have just the slot number
                            taken_slots_in_node += 1
                        else:
                            # Jobs taking multiple slots will have a range of slot numbers
                            slot_start = slots.split('-')[0]
                            slot_end = slots.split('-')[1]
                            taken_slots_in_node += int(slot_end) - int(slot_start) + 1

            # Calculate the free slots and update the global counters    
            free_slots_in_node = available_slots_in_node - taken_slots_in_node
            available_slots_total += available_slots_in_node
            free_slots_total += free_slots_in_node

            # Display output if requested
            if verbose:
                print('{} is {} and has {} total slots and {} free slots'.format(node_hostname, node_state, available_slots_in_node, free_slots_in_node))

    # The function returns a tuple of available and free slots
    return available_slots_total, free_slots_total
    

# In Jupyter jobs, PBS_DEFAULT will be set to the default queue server
# If we want to use a specific queue server other than PBS_DEFAULT, this value
# will need to be changed accordingly:
#queue_server = os.getenv('PBS_DEFAULT')

# A list of properties of nodes on which we want to count slots.
# If a node has any of the properties in this list, it will be counted
#match_properties = ['workbench']

# Call the function and receive the result as a tuple.
# For production, do not set verbose or set it to False
#available_slots, free_slots = getFreeJobSlots(queue_server, match_properties, verbose=True)

# Print results for information (debug):
#print("On queue server {}, among nodes with properties {}, we have {} available job slots and {} free slots".format(queue_server, str(match_properties), available_slots, free_slots))

