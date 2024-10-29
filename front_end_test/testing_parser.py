import yaml
from typing import Dict
import component
import queue
# /home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/fileprocessing/flat_workflow.yaml
# /home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/illgal_recognizer/flat_workflow.yaml
WORKFLOW_YAML_ADDR = {'fileprocessing': '/home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/fileprocessing/flat_workflow.yaml',
                  'illgal_recognizer': '/home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/illgal_recognizer/flat_workflow.yaml',
                  'video': '/home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/video/flat_workflow.yaml',
                  'wordcount': '/home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/wordcount/flat_workflow.yaml',
                  'cycles': '/home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/generator/cycles/flat_workflow.yaml',
                  'epigenomics': '/home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/generator/epigenomics/flat_workflow.yaml',
                  'genome': '/home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/generator/genome/flat_workflow.yaml',
                  'soykb': '/home/weikang/Documents/workflow_orch/FaaSFlow_orch/benchmark/generator/soykb/flat_workflow.yaml'}
NETWORK_BANDWIDTH = 25 * 1024 * 1024 / 4 # 25MB/s / 4

yaml_file_addr = WORKFLOW_YAML_ADDR

def parse(workflow_name):           # parse yaml file to workflow object
    data = yaml.load(open(yaml_file_addr[workflow_name]), Loader=yaml.FullLoader)
    global_input = dict()
    start_functions = []
    nodes = dict()
    parent_cnt = dict()
    foreach_functions = set()
    merge_funtions = set()
    total = 0
    if 'global_input' in data:
        for key in data['global_input']:
            parameter = data['global_input'][key]['value']['parameter']
            global_input[parameter] = data['global_input'][key]['size']
    functions = data['functions']
    parent_cnt[functions[0]['name']] = 0
    for function in functions:
        name = function['name']
        source = function['source']
        runtime = function['runtime']
        input_files = dict()
        output_files = dict()
        next = list()
        nextDis = list()
        send_byte = 0
        if 'input' in function:
            for key in function['input']:
                input_files[key] = {'function': function['input'][key]['value']['function'],
                                    'parameter': function['input'][key]['value']['parameter'],
                                    'size': function['input'][key]['size'], 'arg': key,
                                    'type': function['input'][key]['type']}
        if 'output' in function:
            for key in function['output']:
                output_files[key] = {'size': function['output'][key]['size'], 'type': function['output'][key]['type']}
                send_byte += function['output'][key]['size']
        send_time = send_byte / NETWORK_BANDWIDTH
        conditions = list()
        if 'next' in function:
            foreach_flag = False
            if function['next']['type'] == 'switch':
                conditions = function['next']['conditions']
            elif function['next']['type'] == 'foreach':
                foreach_flag = True
            for n in function['next']['nodes']:
                if name in foreach_functions:
                    merge_funtions.add(n)
                if foreach_flag:
                    foreach_functions.add(n)
                next.append(n)
                nextDis.append(send_time)
                if n not in parent_cnt:
                    parent_cnt[n] = 1
                else:
                    parent_cnt[n] = parent_cnt[n] + 1
        current_function = component.function(name, [], next, nextDis, source, runtime,
                                              input_files, output_files, conditions)
        if 'scale' in function:
            current_function.set_scale(function['scale'])
        if 'mem_usage' in function:
            current_function.set_mem_usage(function['mem_usage'])
        if 'split_ratio' in function:
            current_function.set_split_ratio(function['split_ratio'])
        total = total + 1
        nodes[name] = current_function
    for name in nodes:
        if name not in parent_cnt or parent_cnt[name] == 0:
            parent_cnt[name] = 0
            start_functions.append(name)
        for next_node in nodes[name].next:
            nodes[next_node].prev.append(name)
    return component.workflow(workflow_name, start_functions, nodes, global_input, total, parent_cnt, foreach_functions, merge_funtions)

def get_max_mem_usage(workflow: component.workflow):
    global max_mem_usage
    for name in workflow.nodes:
        if not name.startswith('virtual'):
            max_mem_usage += (1 - config.RESERVED_MEM_PERCENTAGE - workflow.nodes[name].mem_usage) * config.CONTAINER_MEM * workflow.nodes[name].split_ratio
    return max_mem_usage

def init_graph(workflow, group_set, node_info):
    global group_ip, group_scale
    ip_list = list(node_info.keys())
    in_degree_vec = dict()
    q = queue.Queue()
    for name in workflow.start_functions:
        q.put(workflow.nodes[name])
        group_set.append((name, ))
    while q.empty() is False:
        node = q.get()
        for next_node_name in node.next:
            if next_node_name not in in_degree_vec:
                in_degree_vec[next_node_name] = 1
                q.put(workflow.nodes[next_node_name])
                group_set.append((next_node_name, ))
            else:
                in_degree_vec[next_node_name] += 1
    for s in group_set:
        group_ip[s] = ip_list[hash(s) % len(ip_list)]
        group_scale[s] = workflow.nodes[s[0]].scale
        node_info[group_ip[s]] -= workflow.nodes[s[0]].scale
    return in_degree_vec


def grouping(workflow: component.workflow, node_info):

    # initialization: get in-degree of each node
    group_set = list()
    critical_path_functions = set()
    write_to_mem_nodes = []
    in_degree_vec = init_graph(workflow, group_set, node_info)

    while True:

        # break if every node is in same group
        if len(group_set) == 1:
            break

        # topo dp: find each node's longest dis and it's predecessor
        dist_vec, prev_vec = topo_search(workflow, in_degree_vec.copy(), group_set)
        crit_length, tmp_node_name = get_longest_dis(workflow, dist_vec)
        # print('crit_length: ', crit_length)

        # find the longest path, edge descent sorted
        critical_path_functions.clear()
        crit_vec = dict()
        while tmp_node_name not in workflow.start_functions:
            crit_vec[tmp_node_name] = prev_vec[tmp_node_name]
            tmp_node_name = prev_vec[tmp_node_name][0]
        crit_vec = sorted(crit_vec.items(), key=lambda c: c[1][1], reverse=True)
        for k, v in crit_vec:
            critical_path_functions.add(k)
            critical_path_functions.add(v[0])

        # if can't merge every edge of this path, just break
        if not merge_path(crit_vec, group_set, workflow, write_to_mem_nodes, node_info):
            break
    return group_set, critical_path_functions

def get_grouping_config(workflow: component.workflow, node_info_dict):      # get grouping config from the workflow for the grouping and scheduling algorithm

    global max_mem_usage, group_ip

    # grouping algorithm
    max_mem_usage = get_max_mem_usage(workflow)
    # print('max_mem_usage', max_mem_usage)
    group_detail, critical_path_functions = grouping(workflow, node_info_dict)
    print(group_detail)
    
    # print(query(workflow, group_detail))

    # building function info: both optmized and raw version
    ip_list = list(node_info_dict.keys())
    function_info_dict = {}
    function_info_raw_dict = {}
    for node_name in workflow.nodes:
        node = workflow.nodes[node_name]
        to = get_type(workflow, node, group_detail)
        ip = group_ip[find_set(node_name, group_detail)]
        function_info = {'function_name': node.name, 'runtime': node.runtime, 'to': to, 'ip': ip,
                         'parent_cnt': workflow.parent_cnt[node.name], 'conditions': node.conditions}
        function_info_raw = {'function_name': node.name, 'runtime': node.runtime, 'to': 'DB', 'ip': ip_list[hash(node.name) % len(ip_list)],
                             'parent_cnt': workflow.parent_cnt[node.name], 'conditions': node.conditions}
        function_input = dict()
        function_input_raw = dict()
        for arg in node.input_files:
            function_input[arg] = {'size': node.input_files[arg]['size'],
                                   'function': node.input_files[arg]['function'],
                                   'parameter': node.input_files[arg]['parameter'],
                                   'type': node.input_files[arg]['type']}
            function_input_raw[arg] = {'size': node.input_files[arg]['size'],
                                       'function': node.input_files[arg]['function'],
                                       'parameter': node.input_files[arg]['parameter'],
                                       'type': node.input_files[arg]['type']}
        function_output = dict()
        function_output_raw = dict()
        for arg in node.output_files:
            function_output[arg] = {'size': node.output_files[arg]['size'], 'type': node.output_files[arg]['type']}
            function_output_raw[arg] = {'size': node.output_files[arg]['size'], 'type': node.output_files[arg]['type']}
        function_info['input'] = function_input
        function_info['output'] = function_output
        function_info['next'] = node.next
        function_info_raw['input'] = function_input_raw
        function_info_raw['output'] = function_output_raw
        function_info_raw['next'] = node.next
        function_info_dict[node_name] = function_info
        function_info_raw_dict[node_name] = function_info_raw
    
    # if successor contains 'virtual', then the destination of storage should be propagated
    for name in workflow.nodes:
        for next_name in workflow.nodes[name].next:
            if next_name.startswith('virtual'):
                if function_info_dict[next_name]['to'] != function_info_dict[name]['to']:
                    function_info_dict[name]['to'] = 'DB+MEM'

    return node_info_dict, function_info_dict, function_info_raw_dict, critical_path_functions

def save_grouping_config(workflow: component.workflow, node_info, info_dict, info_raw_dict, critical_path_functions):   
    # save grouping config from the workflow for the grouping and scheduling algorithm
    repo = repository.Repository(workflow.workflow_name)
    repo.save_function_info(info_dict, workflow.workflow_name + '_function_info')
    repo.save_function_info(info_raw_dict, workflow.workflow_name + '_function_info_raw')
    repo.save_basic_input(workflow.global_input, workflow.workflow_name + '_workflow_metadata')
    repo.save_start_functions(workflow.start_functions, workflow.workflow_name + '_workflow_metadata')
    repo.save_foreach_functions(workflow.foreach_functions, workflow.workflow_name + '_workflow_metadata')
    repo.save_merge_functions(workflow.merge_functions, workflow.workflow_name + '_workflow_metadata')
    repo.save_all_addrs(list(node_info.keys()), workflow.workflow_name + '_workflow_metadata')
    repo.save_critical_path_functions(critical_path_functions, workflow.workflow_name + '_workflow_metadata')


#Get the node configuration
node_info_list = yaml.load(open('node_info.yaml'), Loader=yaml.FullLoader)
node_info_dict = {}
for node_info in node_info_list['nodes']:
    node_info_dict[node_info['worker_address']] = node_info['scale_limit'] * 0.8

#Read the wrorkflow yaml file and parse it
for key, value in yaml_file_addr .items():
    workflow = parse(key)
    print(vars(workflow))
    node_info, function_info, function_info_raw, critical_path_functions = get_grouping_config(workflow, node_info_dict)
    save_grouping_config(workflow, node_info, function_info, function_info_raw, critical_path_functions)

