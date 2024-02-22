import connexion
import six
import json


import threading
import time
from server import util
import traffic_gen
from server.models.traffic_info import Traffic_Info
from server.models.traffic_info import Traffic_Gen_Info
from server.models.traffic_info import Traffic_Scenario_Info


def generate_deployment_traffic(scenario):
    print("[swagger] generate_deployment_traffic is requested")
    if not isinstance(scenario, int) or scenario > 2 or scenario < 0 :
        return "wrong scenario number"

    test_0 = Traffic_Gen_Info("test-deployment", "0", "141.223.181.155", "141.223.181.158", 100, 36000, ["firewall","dpi","ids"])
    test_1 = Traffic_Gen_Info("test-deployment", "1", "141.223.181.155", "141.223.181.156", 100, 36000, ["firewall","dpi"])
    test_2 = Traffic_Gen_Info("test-deployment", "2", "141.223.181.203", "141.223.181.155", 100, 36000, ["firewall","ids"])

    test_box = [[test_0], [test_1], [test_2]]

    for test in test_box[scenario]: 
        response = generate_custom_traffic(test)
    
    return response


def generate_auto_scaling_traffic(scenario):
    print("[swagger] generate_auto_scaling_traffic is requested")

    if not isinstance(scenario, int) or scenario > 2 or scenario < 0 :
        return "wrong scenario number"

    test_0  = Traffic_Gen_Info("test-auto-scaling", "0", "141.223.181.155", "141.223.181.158", 100, 36000, ["firewall","flowmonitor","dpi","ids","proxy"])
    test_1  = Traffic_Gen_Info("test-auto-scaling", "1", "141.223.181.155", "141.223.181.158", 100, 36000, ["firewall","flowmonitor","dpi","ids","proxy"])
    test_2  = Traffic_Gen_Info("test-auto-scaling", "2", "141.223.181.203", "141.223.181.155", 100, 36000, ["firewall","flowmonitor","dpi","ids","proxy"])

    test_box = [[test_0, test_0, test_0, test_0], [test_1, test_1, test_1, test_1], [test_2, test_2, test_2, test_2]]

    for test in test_box[scenario]: 
        response = generate_custom_traffic(test)
    
    return response


def generate_sfc_traffic(scenario):
    print("[swagger] generate_sfc_traffic is requested")

    if not isinstance(scenario, int) or scenario > 2 or scenario < 0 :
        return "wrong scenario number"

    test_0  = Traffic_Gen_Info("test-sfc", "0", "141.223.181.155", "141.223.181.158", 100, 36000, ["firewall","flowmonitor","dpi","ids","proxy"])
    test_1  = Traffic_Gen_Info("test-sfc", "1", "141.223.181.155", "141.223.181.156", 100, 36000, ["firewall","flowmonitor","dpi","ids","proxy"])
    test_2  = Traffic_Gen_Info("test-sfc", "2", "141.223.181.203", "141.223.181.155", 100, 36000, ["firewall","flowmonitor","dpi","ids","proxy"])

    test_box = [[test_0], [test_1], [test_2]]

    for test in test_box[scenario]: 
        response = generate_custom_traffic(test)
    
    return response


def generate_power_management_traffic(scenario):
    print("[swagger] generate_power_management_traffic is requested")

    if not isinstance(scenario, int) or scenario > 2 or scenario < 0 :
        return "wrong scenario number"

    test_0  = Traffic_Gen_Info("test-power-management", "0", "141.223.181.155", "141.223.181.156", 100, 36000, ["firewall"])
    test_1  = Traffic_Gen_Info("test-power-management", "1", "141.223.181.155", "141.223.181.156", 100, 36000, ["firewall","flowmonitor","dpi"])
    test_2  = Traffic_Gen_Info("test-power-management", "2", "141.223.181.157", "141.223.181.158", 100, 36000, ["firewall","flowmonitor","dpi"])
    test_3  = Traffic_Gen_Info("test-power-management", "3", "141.223.181.203", "141.223.181.158", 100, 36000, ["firewall","flowmonitor","dpi","ids","proxy"])
    test_4  = Traffic_Gen_Info("test-power-management", "0", "141.223.181.158", "141.223.181.203", 100, 36000, ["firewall"])


    test_box = [[test_1], [test_0, test_3, test_4], [test_1, test_2]]

    for test in test_box[scenario]: 
        response = generate_custom_traffic(test)
    
    return response


def get_traffics_info():

    response = []

    for traffic in traffic_gen.traffic_list:
        response.append(traffic.get_info())

    return response


def get_traffics():


    return traffic_gen.traffic_list
 

def generate_custom_traffic(traffic_info):
      
    if not traffic_gen.monitoring_status :
        threading.Thread(target=traffic_gen.traffic_monitoring, args=()).start()

    if connexion.request.is_json:
        try:
            traffic_info = Traffic_Gen_Info.from_dict(connexion.request.get_json())
            response = Traffic_Info(traffic_info)
        except:
            response = Traffic_Info(traffic_info)

        if response.traffic_id == "0" or response.traffic_id == 0:
           response.set_traffic_id(str(traffic_gen.traffic_id_helper))

        elif any(response.traffic_id == traffic.traffic_id for traffic in traffic_gen.traffic_list):
           response.set_traffic_id(str(traffic_gen.traffic_id_helper))

    else:
        response = Traffic_Info(traffic_info)
        if response.traffic_id == "0":
           response.set_traffic_id(str(traffic_gen.traffic_id_helper))
        elif any(response.traffic_id == traffic.traffic_id for traffic in traffic_gen.traffic_list):
           response.set_traffic_id(str(traffic_gen.traffic_id_helper))



    traffic_gen.traffic_id_helper += 1        
    if traffic_gen.install_client_and_server(response):
        traffic_gen.iperf3_activate(response)
    else:
        return "failed to install client and server"

    traffic_gen.traffic_list.append(response)
    print(traffic_gen.mydashboard_url)

    return ("grafana dashboard : "+traffic_gen.mydashboard_url)


def change_traffic(traffic_id, bandwidth, duration):

    target_traffic = traffic_gen.find_traffic_by_traffic_id(traffic_id)

    traffic_gen.iperf3_terminate(target_traffic)  

    target_traffic.set_bandwidth(bandwidth)
    target_traffic.set_duration(duration)
    target_traffic.set_start_time(time.time())
    traffic_gen.iperf3_activate(target_traffic)

    return target_traffic.get_info()

def clean_traffic(traffic_id):

    target_traffic = traffic_gen.find_traffic_by_traffic_id(traffic_id)
    traffic_gen.remove_traffic(target_traffic)    

    return "success"


def generate_scenario():

    traffic_scenario_list = traffic_gen.read_scenario_from_file()
    #activate_scenario(traffic_scenario_list)
    threading.Thread(target=traffic_gen.activate_scenario, args=(traffic_scenario_list,)).start()

    return 

def activate_scenario(traffic_scenario_list):

    print("start to activate scenario")
    while traffic_scenario_list:

        traffic_scenario = traffic_scenario_list[0]
        s_type = traffic_scenario.s_type
    
        if s_type == "add":
            print("add traffic")
            # traffic_scenario를 Traffic_Gen_Info 객체로 변환
            traffic_info = Traffic_Gen_Info(
                prefix=traffic_scenario.prefix,
                traffic_id=traffic_scenario.traffic_id,
                src=traffic_scenario.src,
                dst=traffic_scenario.dst,
                bandwidth=traffic_scenario.bandwidth,
                duration=traffic_scenario.duration,
                service_type=traffic_scenario.service_type
            )
            # generate_custom_traffic 실행
            generate_custom_traffic(traffic_info)
        elif s_type == "remove":
            print("remove traffic")
            # clean_traffic 실행
            clean_traffic(traffic_scenario.traffic_id)
        elif s_type == "change":
            print("change traffic")
            # change_traffic 실행
            change_traffic(
                traffic_id=traffic_scenario.traffic_id,
                bandwidth=traffic_scenario.bandwidth,
                duration=traffic_scenario.duration
            )
        elif s_type == "wait":
            print("wait")
            # wait 실행
            time.sleep(traffic_scenario.duration)

        traffic_scenario_list.pop(0)
        print(traffic_scenario_list)

     
    return 



