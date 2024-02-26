import ni_mon_client, ni_nfvo_client
import ni_custom_client
from create_dashboard import create_dashboard
from ni_mon_client.rest import ApiException
from ni_nfvo_client.rest import ApiException
from datetime import datetime, timedelta, timezone
from config import cfg
from server.models.traffic_info import Traffic_Scenario_Info


import numpy as np
import threading
import datetime as dt
import math
import os
import time
import subprocess
import paramiko
from pprint import pprint
import random

# Parameters
# OpenStack Parameters
openstack_network_id = cfg["openstack_network_id"] # Insert OpenStack Network ID to be used for creating SFC

# Global values
sample_user_data = "#cloud-config\n password: %s\n chpasswd: { expire: False }\n ssh_pwauth: True\n manage_etc_hosts: true\n runcmd:\n - sysctl -w net.ipv4.ip_forward=1"
traffic_list = []
traffic_id_helper = 0
monitoring_status = False
mydashboard_url = "test"

#ni_nfvo_client_api
ni_nfvo_client_cfg = ni_nfvo_client.Configuration()
ni_nfvo_client_cfg.host=cfg["ni_nfvo"]["host"]
ni_nfvo_vnf_api = ni_nfvo_client.VnfApi(ni_nfvo_client.ApiClient(ni_nfvo_client_cfg))
ni_nfvo_sfc_api = ni_nfvo_client.SfcApi(ni_nfvo_client.ApiClient(ni_nfvo_client_cfg))
ni_nfvo_sfcr_api = ni_nfvo_client.SfcrApi(ni_nfvo_client.ApiClient(ni_nfvo_client_cfg))

#ni_autoscaling_api
ni_auto_scaling_client_cfg = ni_custom_client.Configuration()
ni_auto_scaling_client_cfg.host=cfg["ni_auto_scaling"]["host"]
ni_auto_scaling_api = ni_custom_client.ScalingApi(ni_custom_client.ApiClient(ni_auto_scaling_client_cfg))

#ni_monitoring_api
ni_mon_client_cfg = ni_mon_client.Configuration()
ni_mon_client_cfg.host = cfg["ni_mon"]["host"]
ni_mon_api = ni_mon_client.DefaultApi(ni_mon_client.ApiClient(ni_mon_client_cfg))

udp_port = 16000


def find_traffic_by_traffic_id(traffic_id):
    for traffic in traffic_list:
        if traffic.traffic_id == traffic_id:
            return traffic
    return None


def is_multi_flow(traffic):
    for other_traffic in traffic_list:
        if other_traffic != traffic and other_traffic.sfcr_id == traffic.sfcr_id:
            return True
    return False


def already_installed_client_server(traffic):

    for other_traffic in traffic_list:
        if (
            other_traffic != traffic
            and other_traffic.src == traffic.src
            and other_traffic.dst == traffic.dst
        ):
            return other_traffic



    return False


def deploy_vnf(vnf_spec):
    api_response = ni_nfvo_vnf_api.deploy_vnf(vnf_spec)

    return api_response


def get_sfcr_by_name(sfcr_name):
    query = ni_nfvo_sfcr_api.get_sfcrs()

    sfcr_info = [ sfcri for sfcri in query if sfcri.name == sfcr_name ]
    
    if sfcr_info != []:
        sfcr_info = sfcr_info[-1]

    return sfcr_info


def get_sfc_by_name(sfc_name):
    query = ni_nfvo_sfc_api.get_sfcs()

    sfc_info = [ sfci for sfci in query if sfci.sfc_name == sfc_name ]

    if len(sfc_info) == 0:
        return False

    sfc_info = sfc_info[-1]

    return sfc_info


def get_sfcr_by_id(sfcr_id):

    query = ni_nfvo_sfcr_api.get_sfcrs()

    sfcr_info = [ sfcri for sfcri in query if sfcri.id == sfcr_id ]
    sfcr_info = sfcr_info[-1]

    return sfcr_info



def get_ip_from_id(id):
    api_response = ni_mon_api.get_vnf_instance(id)
    ## Get ip address of specific network
    ports = api_response.ports
    #print(ports)
    network_id = openstack_network_id
    #print(network_id)

    for port in ports:
        if port.network_id == network_id:
            return port.ip_addresses[-1]



def destroy_vnf(id):
    api_response = ni_nfvo_vnf_api.destroy_vnf(id)

    return api_response

def destroy_sfcr(id):
    api_response = ni_nfvo_sfcr_api.del_sfcr(id)

    return api_response

def destroy_sfc(id):
    api_response = ni_nfvo_sfc_api.del_sfc(id)

    return api_response

def get_node_info():
    query = ni_mon_api.get_nodes()

    response = [ node_info for node_info in query if node_info.type == "compute" and node_info.status == "enabled"]
    response = [ node_info for node_info in response if not (node_info.name).startswith("NI-Compute-82-9")]

    return response


def check_active_instance(id):
    status = ni_mon_api.get_vnf_instance(id).status

    if status == "ACTIVE":
        return True
    else:
        return False

def get_nfvo_vnf_spec():
#    print("5")

    t = ni_nfvo_client.ApiClient(ni_nfvo_client_cfg)

    ni_nfvo_vnf_spec = ni_nfvo_client.VnfSpec(t)
    ni_nfvo_vnf_spec.flavor_id = cfg["flavor"]["default"]
    ni_nfvo_vnf_spec.user_data = sample_user_data % cfg["instance"]["password"]

    return ni_nfvo_vnf_spec


def set_vnf_spec(traffic, type_name, node_name):
    vnf_spec = get_nfvo_vnf_spec()
    vnf_spec.vnf_name = traffic.prefix + cfg["instance"]["prefix_splitter"] + traffic.traffic_id + cfg["instance"]["prefix_splitter"] +  type_name
    vnf_spec.image_id = cfg["image"][type_name] #client or server
    vnf_spec.node_name = node_name

    return vnf_spec 
 


def get_ssh(ssh_ip, ssh_username, ssh_password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_ip, username=ssh_username, password=ssh_password)
    return ssh



def ssh_keygen(ip):

    host_ssh = get_ssh(cfg["traffic_controller"]["ip"], cfg["traffic_controller"]["username"], cfg["traffic_controller"]["password"])

    command = "sudo ssh-keygen -f '/home/ubuntu/.ssh/known_hosts' -R %s" % ip
    stdin, stdout, stderr = host_ssh.exec_command(command)

    host_ssh.close()
    return True


def install_client_and_server(traffic):
    print("Start installing VNFs and SFCR for traffic %s" % traffic.traffic_id)
    global mydashboard_url
    node_info = get_node_info()
    client_id, server_id = 0, 0

    for info in node_info: #should not use elif..cuz src and destination can be same..(ofcourse it is not usual traffic anyway)
        if info.ip == traffic.src:
            client_id = info.id
        if info.ip == traffic.dst:
            server_id = info.id


    if client_id == 0 or server_id == 0:
        print("Failed to get client or server id.[install error]")
        return False

    elif (not check_available_resource(client_id)) or (not check_available_resource(server_id)):
        print("No available resource for installing client or server")
        return False

    else :#For Testing
        object_traffic = already_installed_client_server(traffic)
        if object_traffic:
            print("Skipped installing client and server VNF cause they are already installed")
            traffic.set_src_id(object_traffic.src_id)
            traffic.set_dst_id(object_traffic.dst_id)
            traffic.set_sfcr_id(object_traffic.sfcr_id)
            return True

        target_sfcr = get_sfcr_by_name("auto-scaling-0")
        #For Auto-scaling (Temporal)
        if traffic.prefix == "auto-scaling" and target_sfcr:
            print("testing")
            traffic.set_src_id(target_sfcr.source_client)
            traffic.set_dst_id(target_sfcr.destination_client)
            traffic.set_sfcr_id(target_sfcr.id)
            return True

    vnf_spec=[set_vnf_spec(traffic, 'client', client_id), set_vnf_spec(traffic, 'server', server_id)]

    id_list = []
    for spec in vnf_spec:
        instance_id = deploy_vnf(spec)
        id_list.append(instance_id)
        limit = 300
        for i in range(0, limit):
            time.sleep(2)

            # Success to create VNF instance
            if check_active_instance(instance_id):
                break
            elif i == (limit-1):
                destroy_vnf(instance_id)
                print("Failed to deploy VNF")
                return False

    traffic.set_src_id(id_list[0])
    traffic.set_dst_id(id_list[1])
    traffic.sfcr_id = create_sfcr(traffic)

    ssh_keygen(get_ip_from_id(traffic.src_id))
    ssh_keygen(get_ip_from_id(traffic.dst_id))

    print("Succes to install SFCR for traffic generation")

    client_info = ni_mon_api.get_vnf_instance(id_list[0])
    server_info = ni_mon_api.get_vnf_instance(id_list[1])

    mydashboard_url = create_dashboard([[client_info],[server_info]],"TG")

    return True


# lable_resource(flavor_id): check whether there are enough resource in nodes
# Input: node_id
# Output: True (enough), False (otherwise)
def check_available_resource(node_id):
#    print("20")

    node_info = get_node_info()
    selected_node = [ node for node in node_info if node.id == node_id ][-1]
    flavor = ni_mon_api.get_vnf_flavor(cfg["flavor"]["default"])

    if selected_node.n_cores_free >= flavor.n_cores and selected_node.ram_free_mb >= flavor.ram_mb:
        return True

    return False

def create_sfcr(traffic):
#    print("23")

    nf_chain = traffic.service_type

    name = traffic.prefix + cfg["instance"]["prefix_splitter"] + traffic.traffic_id
    sfcr_spec = ni_nfvo_client.SfcrSpec(name=name,
                                 src_ip_prefix=(get_ip_from_id(traffic.src_id) + "/32"),
                                 dst_ip_prefix=(get_ip_from_id(traffic.dst_id) + "/32"),
                                 nf_chain=traffic.service_type,
                                 source_client=traffic.src_id,
                                 destination_client=traffic.dst_id)

    api_response = ni_nfvo_sfcr_api.add_sfcr(sfcr_spec)

    print("Success to pass for creating sfcr")
    return api_response


def create_sfc(traffic):
    #Create SFCR using src,dst_id and 
    name = traffic.prefix + cfg["instance"]["prefix_splitter"] + traffic.traffic_id
    sfc_spec =ni_nfvo_client.SfcSpec(sfc_name=name,
                                 sfcr_ids=[traffic.sfcr_id],
                                 vnf_instance_ids=[[traffic.src_id],[traffic.dst_id]],
                                 is_symmetric=False)


    api_response = ni_nfvo_sfc_api.set_sfc(sfc_spec)

    print("Success to pass for creating sfc")
    return api_response

def parse_lsof_output(output):
    parsed_results = []
    for line in output.splitlines():
        fields = line.strip().split()
        if len(fields) == 2:
            pid, port = fields
            parsed_results.append((pid, port))
    return parsed_results

def find_missing_traffic(output):
    missing_traffic = [
    traffic
    for traffic in traffic_list
    if all(traffic.process_id != pid or traffic.port != port for pid, port in result)
    ]
    return missing_traffic

def find_pid_port(response):
    for pid_port in response:
        pid, port = pid_port.strip().split()
        is_duplicate = False
        #if '.' in port or '->' in port:
        #    continue
        
        for traffic in traffic_list:
            if traffic.process_id == pid or traffic.port == port:
                is_duplicate = True
                break

        if not is_duplicate:
            return pid, port

    return False


def iperf3_activate(traffic):

    global udp_port

    host_ssh = get_ssh(cfg["traffic_controller"]["ip"], cfg["traffic_controller"]["username"], cfg["traffic_controller"]["password"])
    iperf3_server = (cfg["instance"]["password"], cfg["instance"]["username"], get_ip_from_id(traffic.dst_id))
    iperf3_client = (cfg["instance"]["password"], cfg["instance"]["username"], get_ip_from_id(traffic.src_id))
    sshpass_command = "sshpass -p %s ssh -o stricthostkeychecking=no %s@%s "
    
    
    object_command = "lsof -i -P -n | grep iperf3 | awk '$9 !~ /[>]/ {print $2, $9}' | tr -d ':*'"
    command = (sshpass_command + object_command) % iperf3_server
    stdin, stdout, stderr = host_ssh.exec_command(command)  
    stdout = stdout.readlines()
    num_current_iperf3 = len(stdout)
    
    
    object_command = "nohup iperf3 -s -D -p %s &" % udp_port
    command = (sshpass_command + object_command) % iperf3_server
    print("command : ", command)
    
    
    limit = 10
    for i in range(0, limit):
        time.sleep(10)
        try:
            stdin, stdout, stderr = host_ssh.exec_command(command)

            object_command = "lsof -i -P -n | grep iperf3 | awk '$9 !~ /[>]/ {print $2, $9}' | tr -d ':*'"
            command = (sshpass_command + object_command) % iperf3_server
            stdin, stdout, stderr = host_ssh.exec_command(command)  
            stdout = stdout.readlines()
            
            if len(stdout) > num_current_iperf3 : 
                print("Server VNF activate iperf3 server on {}".format(get_ip_from_id(traffic.dst_id)))
                pid, port = find_pid_port(stdout)
                udp_port = udp_port + 1
                traffic.set_process_id(pid)
                traffic.set_port(port)                  
                break
                
        except:
            print("Server VNF does not respond yet. Waiting for server in %s times" % (limit+1))
        
        if limit == 9:
            print("There are problmes in Server VNF.")
            return
  

    #Iperf3 on client
    object_command = "nohup iperf3 -c %s -b %sM -u -t %s --length 1200 -p %s &" % (get_ip_from_id(traffic.dst_id), traffic.bandwidth, traffic.duration, traffic.port)
    command = (sshpass_command + object_command) % iperf3_client
    stdin, stdout, stderr = host_ssh.exec_command(command)
    
    print("Iperf3 is activated on {}".format(get_ip_from_id(traffic.src_id)))
    
    host_ssh.close()
    return 






def iperf3_terminate(traffic):

    #paramiko + sshpass
    host_ssh = get_ssh(cfg["traffic_controller"]["ip"], cfg["traffic_controller"]["username"], cfg["traffic_controller"]["password"])
    iperf3_server = (cfg["instance"]["password"], cfg["instance"]["username"], get_ip_from_id(traffic.dst_id))

    sshpass_command = "sshpass -p %s ssh -o stricthostkeychecking=no %s@%s " % (iperf3_server)
    object_command = "kill %s" % traffic.process_id

    command = sshpass_command + object_command

    stdin, stdout, stderr = host_ssh.exec_command(command)

    host_ssh.close()
    '''
    sshpass + sshpass
    ssh_command = "sshpass -p %s ssh -o stricthostkeychecking=no %s@%s "
    traffic_controller = (cfg["traffic_controller"]["password"], cfg["traffic_controller"]["username"], cfg["traffic_controller"]["ip"])
    iperf3_server = (cfg["instance"]["password"], cfg["instance"]["username"], get_ip_from_id(traffic.dst_id))

    #kill command
    inner_command = "kill %s" % traffic.process_id
    inner_command = (ssh_command + inner_command) % iperf3_server
    command = (ssh_command + inner_command) % traffic_controller
    response = subprocess.check_output(command, shell=True).strip().decode("utf-8")
    '''
    return











def set_random_gen_info(traffic_gen_info):
    node_info = get_node_info()
    flavor = ni_mon_api.get_vnf_flavor(cfg["flavor"]["default"])
    max_attempts= 100
    attempts = 0
    bandwidth_min, bandwidth_max = 1000, 10000
    duration_min, duration_max = 60, 600
    service_type = cfg["sfc"]["types"]#[['firewall', 'dpi', 'ids'], ['firewall', 'dpi'], ['firewall', 'ids'], ['ids'], ['firewall']]

    while attempts < max_attempts:
        selected_nodes = random.sample(node_info, 2)
        node_1, node_2 = selected_nodes

        if (
            node_1.n_cores_free >= flavor.n_cores and node_2.n_cores_free >= flavor.n_cores
            and node_1.ram_free_mb >= flavor.ram_mb and node_2.ram_free_mb >= flavor.ram_mb
        ):
           break
       
        attempts += 1

    traffic_gen_info.src = node_1.ip
    traffic_gen_info.dst = node_2.ip
    traffic_gen_info.bandwidth = random.randint(bandwidth_min, bandwidth_max)
    traffic_gen_info.duration = random.randint(duration_min, duration_max)
    traffic_gen_info.service_type = random.choices(service_type, cfg["sfc"]["prob"])

    return 

def remove_traffic(traffic):
    sfcs = ni_nfvo_sfc_api.get_sfcs()
    try:
        iperf3_terminate(traffic)
        print("Iperf3 is terminated")
    except:
        print("already iperf3 is teriminated")

    if (not is_multi_flow(traffic)) and traffic.prefix == "s1":
        #Check wether SFC is installed or not
        for sfc in sfcs:
            if traffic.sfcr_id in sfc.sfcr_ids:
                print("sfc is running on the openstack. skipping destroy sfcr and vnf.")
                traffic_list.remove(traffic)
                return
                
        #destroy_sfcr(traffic.sfcr_id)
        #destroy_vnf(traffic.src_id)
        #destroy_vnf(traffic.dst_id)
        
    traffic_list.remove(traffic)

    return

def traffic_monitoring():

    monitoring_status = True
    while True:
        current_time = time.time()
        if not traffic_list:
            continue

        for traffic in traffic_list:
            elapsed_time = current_time - traffic.start_time
            if elapsed_time >= traffic.duration:
                remove_traffic(traffic)

        time.sleep(10)
    return


def read_scenario_from_file():
    traffic_scenario_list = []
    with open("scenario", 'r') as file:
        header = file.readline().strip().split(',')
        #next(file)

        for line in file:
            data = line.strip().split(',')
            s_type = data[0]

            if s_type == "add":
                prefix, traffic_id, src, dst, bandwidth, duration, *service_type = data[1:]
                traffic_scenario = Traffic_Scenario_Info(s_type=s_type, prefix=prefix, traffic_id=traffic_id, src=src, dst=dst, bandwidth=int(bandwidth), duration=int(duration), service_type=service_type)
            elif s_type == "remove":
                traffic_id = data[1]
                traffic_scenario = Traffic_Scenario_Info(s_type=s_type, traffic_id=traffic_id)
            elif s_type == "change":
                prefix, traffic_id, bandwidth, duration, *service_type = data[1:]
                traffic_scenario = Traffic_Scenario_Info(s_type=s_type, prefix=prefix, traffic_id=traffic_id, bandwidth=int(bandwidth), duration=int(duration), service_type=service_type)
            elif s_type == "wait":
                duration = data[1]
                traffic_scenario = Traffic_Scenario_Info(s_type=s_type, duration=int(duration))
            else:
                raise ValueError(f"Invalid s_type: {s_type}")

            traffic_scenario_list.append(traffic_scenario)

    return traffic_scenario_list



