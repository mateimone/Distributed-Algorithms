import re

# Sample log lines (as a list of strings). In practice, you might read this from a file.
log_lines = """
node0-1  | RCO Node 0 is broadcasting message c5334e12dd8643ae8f0747da0bb96555: Message example 1
node0-1  | RCO Node 0 is broadcasting message bd248c057cf9475db761b3641a60ba18: Message example 2
node0-1  | RCO Node 0 is broadcasting message 26f9830b73e040a88799d423520e38db: Message example 3
node0-1  | [RCO Delivered] Message example 1 at 0.0002789497375488281, my VC [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node0-1  | [RCO Delivered] Message example 2 at 0.0004329681396484375, my VC [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node0-1  | [RCO Delivered] Message example 3 at 0.0005741119384765625, my VC [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node6-1  | [RCO Delivered] Message example 1 at 0.2102806568145752, my VC [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node8-1  | [RCO Delivered] Message example 1 at 0.23587894439697266, my VC [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node7-1  | [RCO Delivered] Message example 1 at 0.24976563453674316, my VC [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node7-1  | [RCO Delivered] Message example 2 at 0.26169729232788086, my VC [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node7-1  | [RCO Delivered] Message example 3 at 0.26174235343933105, my VC [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node8-1  | [RCO Delivered] Message example 2 at 0.27224063873291016, my VC [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node5-1  | [RCO Delivered] Message example 1 at 0.2887883186340332, my VC [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node5-1  | [RCO Delivered] Message example 2 at 0.288818359375, my VC [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node5-1  | [RCO Delivered] Message example 3 at 0.288820743560791, my VC [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node3-1  | [RCO Delivered] Message example 1 at 0.298565149307251, my VC [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node3-1  | [RCO Delivered] Message example 2 at 0.29860711097717285, my VC [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]                                                                                                                           
node8-1  | [RCO Delivered] Message example 3 at 0.31090521812438965, my VC [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]                                                                                                                           
node6-1  | [RCO Delivered] Message example 2 at 0.3494889736175537, my VC [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node6-1  | [RCO Delivered] Message example 3 at 0.34954214096069336, my VC [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node9-1  | [RCO Delivered] Message example 1 at 0.38065052032470703, my VC [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]                                                                                                                           
node9-1  | [RCO Delivered] Message example 2 at 0.38071703910827637, my VC [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node9-1  | [RCO Delivered] Message example 3 at 0.3807227611541748, my VC [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]                                                                                                                            
node3-1  | [RCO Delivered] Message example 3 at 0.40052151679992676, my VC [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]                                                                                                                           
node2-1  | [RCO Delivered] Message example 1 at 0.4475388526916504, my VC [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node1-1  | [RCO Delivered] Message example 1 at 0.45531654357910156, my VC [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node1-1  | [RCO Delivered] Message example 2 at 0.45535945892333984, my VC [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]                                                                                                                           
node2-1  | [RCO Delivered] Message example 2 at 0.45630526542663574, my VC [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]                                                                                                                           
node1-1  | [RCO Delivered] Message example 3 at 0.4553649425506592, my VC [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]                                                                                                                            
node2-1  | [RCO Delivered] Message example 3 at 0.4563605785369873, my VC [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]
node2-1  | [RCO Delivered] Tampered Content121 at 0.9303371906280518, my VC [3, 0, 0, 0, 1, 0, 0, 0, 0, 0]                                                                                                                          
node1-1  | [RCO Delivered] Tampered Content121 at 0.9337730407714844, my VC [3, 0, 0, 0, 1, 0, 0, 0, 0, 0]
node5-1  | [RCO Delivered] Tampered Content121 at 1.0903205871582031, my VC [3, 0, 0, 0, 1, 0, 0, 0, 0, 0]                                                                                                                          
node6-1  | [RCO Delivered] Tampered Content121 at 1.1104459762573242, my VC [3, 0, 0, 0, 1, 0, 0, 0, 0, 0]
node3-1  | [RCO Delivered] Tampered Content121 at 1.112215518951416, my VC [3, 0, 0, 0, 1, 0, 0, 0, 0, 0]
node7-1  | [RCO Delivered] Tampered Content121 at 1.1143019199371338, my VC [3, 0, 0, 0, 1, 0, 0, 0, 0, 0]                                                                                                                          
node8-1  | [RCO Delivered] Tampered Content121 at 1.1673948764801025, my VC [3, 0, 0, 0, 1, 0, 0, 0, 0, 0]
node9-1  | [RCO Delivered] Tampered Content121 at 1.177255392074585, my VC [3, 0, 0, 0, 1, 0, 0, 0, 0, 0]
node0-1  | [RCO Delivered] Tampered Content121 at 1.1848571300506592, my VC [3, 0, 0, 0, 1, 0, 0, 0, 0, 0]                                                                                                                          
node1-1  | RCO Node 1 is broadcasting message 360d538cd8c64ae49c0227fcdcfffb56: Message example 4
node1-1  | RCO Node 1 is broadcasting message e2657e3ab2c54a778799c390fa99b1ce: Message example 5
node1-1  | [RCO Delivered] Message example 4 at 0.00014710426330566406, my VC [3, 1, 0, 0, 1, 0, 0, 0, 0, 0]                                                                                                                        
node1-1  | [RCO Delivered] Message example 5 at 0.00024366378784179688, my VC [3, 2, 0, 0, 1, 0, 0, 0, 0, 0]                                                                                                                        
node3-1  | RCO Node 3 is broadcasting message 28829ea188c549e18469ebf797ef049f: Message example 6                                                                                                                                   
node3-1  | RCO Node 3 is broadcasting message 10b2915a60674ea09f057bef7b34ce32: Message example 7
node3-1  | [RCO Delivered] Message example 6 at 0.0001957416534423828, my VC [3, 0, 0, 1, 1, 0, 0, 0, 0, 0]
node3-1  | [RCO Delivered] Message example 7 at 0.0003464221954345703, my VC [3, 0, 0, 2, 1, 0, 0, 0, 0, 0]                                                                                                                         
node8-1  | [RCO Delivered] Message example 4 at 0.24505281448364258, my VC [3, 1, 0, 0, 1, 0, 0, 0, 0, 0]                                                                                                                           
node2-1  | [RCO Delivered] Message example 6 at 0.22278761863708496, my VC [3, 0, 0, 1, 1, 0, 0, 0, 0, 0]
node2-1  | [RCO Delivered] Message example 7 at 0.22281837463378906, my VC [3, 0, 0, 2, 1, 0, 0, 0, 0, 0]                                                                                                                           
node1-1  | [RCO Delivered] Message example 6 at 0.26044297218322754, my VC [3, 2, 0, 1, 1, 0, 0, 0, 0, 0]                                                                                                                           
node1-1  | [RCO Delivered] Message example 7 at 0.2604849338531494, my VC [3, 2, 0, 2, 1, 0, 0, 0, 0, 0]
node0-1  | [RCO Delivered] Message example 6 at 0.3256206512451172, my VC [3, 0, 0, 1, 1, 0, 0, 0, 0, 0]                                                                                                                            
node5-1  | [RCO Delivered] Message example 6 at 0.3253188133239746, my VC [3, 0, 0, 1, 1, 0, 0, 0, 0, 0]
node5-1  | [RCO Delivered] Message example 7 at 0.32537174224853516, my VC [3, 0, 0, 2, 1, 0, 0, 0, 0, 0]                                                                                                                           
node8-1  | [RCO Delivered] Message example 6 at 0.34299802780151367, my VC [3, 1, 0, 1, 1, 0, 0, 0, 0, 0]                                                                                                                           
node8-1  | [RCO Delivered] Message example 7 at 0.3430359363555908, my VC [3, 1, 0, 2, 1, 0, 0, 0, 0, 0]                                                                                                                            
node2-1  | [RCO Delivered] Message example 4 at 0.38346385955810547, my VC [3, 1, 0, 2, 1, 0, 0, 0, 0, 0]
node9-1  | [RCO Delivered] Message example 4 at 0.386981725692749, my VC [3, 1, 0, 0, 1, 0, 0, 0, 0, 0]                                                                                                                             
node0-1  | [RCO Delivered] Message example 7 at 0.3628203868865967, my VC [3, 0, 0, 2, 1, 0, 0, 0, 0, 0]
node5-1  | [RCO Delivered] Message example 4 at 0.38904476165771484, my VC [3, 1, 0, 2, 1, 0, 0, 0, 0, 0]                                                                                                                           
node6-1  | [RCO Delivered] Message example 6 at 0.4146091938018799, my VC [3, 0, 0, 1, 1, 0, 0, 0, 0, 0]                                                                                                                            
node6-1  | [RCO Delivered] Message example 7 at 0.41466784477233887, my VC [3, 0, 0, 2, 1, 0, 0, 0, 0, 0]
node7-1  | [RCO Delivered] Message example 6 at 0.43433499336242676, my VC [3, 0, 0, 1, 1, 0, 0, 0, 0, 0]                                                                                                                           
node7-1  | [RCO Delivered] Message example 7 at 0.434368371963501, my VC [3, 0, 0, 2, 1, 0, 0, 0, 0, 0]
node9-1  | [RCO Delivered] Message example 6 at 0.45662856101989746, my VC [3, 1, 0, 1, 1, 0, 0, 0, 0, 0]
node9-1  | [RCO Delivered] Message example 7 at 0.4566988945007324, my VC [3, 1, 0, 2, 1, 0, 0, 0, 0, 0]
node3-1  | [RCO Delivered] Message example 4 at 0.48576998710632324, my VC [3, 1, 0, 2, 1, 0, 0, 0, 0, 0]                                                                                                                           
node8-1  | [RCO Delivered] Message example 5 at 0.49515438079833984, my VC [3, 2, 0, 2, 1, 0, 0, 0, 0, 0]                                                                                                                           
node0-1  | [RCO Delivered] Message example 4 at 0.5014076232910156, my VC [3, 1, 0, 2, 1, 0, 0, 0, 0, 0]
node6-1  | [RCO Delivered] Message example 4 at 0.5155110359191895, my VC [3, 1, 0, 2, 1, 0, 0, 0, 0, 0]                                                                                                                            
node7-1  | [RCO Delivered] Message example 4 at 0.5652711391448975, my VC [3, 1, 0, 2, 1, 0, 0, 0, 0, 0]
node2-1  | [RCO Delivered] Message example 5 at 0.6276421546936035, my VC [3, 2, 0, 2, 1, 0, 0, 0, 0, 0]
node9-1  | [RCO Delivered] Message example 5 at 0.6723461151123047, my VC [3, 2, 0, 2, 1, 0, 0, 0, 0, 0]
node5-1  | [RCO Delivered] Message example 5 at 0.6939096450805664, my VC [3, 2, 0, 2, 1, 0, 0, 0, 0, 0]
node0-1  | [RCO Delivered] Message example 5 at 0.7078640460968018, my VC [3, 2, 0, 2, 1, 0, 0, 0, 0, 0]
node7-1  | [RCO Delivered] Message example 5 at 0.7951562404632568, my VC [3, 2, 0, 2, 1, 0, 0, 0, 0, 0]
node3-1  | [RCO Delivered] Message example 5 at 0.811995267868042, my VC [3, 2, 0, 2, 1, 0, 0, 0, 0, 0]
node6-1  | [RCO Delivered] Message example 5 at 0.8827641010284424, my VC [3, 2, 0, 2, 1, 0, 0, 0, 0, 0]
""".strip().splitlines()

delivery_pattern = re.compile(
    r'^(node\d+-\d+).*?\[RCO Delivered\]\s+((?:Message example|Byzantine message) \d+)'
)

messages_per_node = {}

for line in log_lines:
    match = delivery_pattern.match(line)
    if match:
        node = match.group(1)
        message = match.group(2)

        if node not in messages_per_node:
            messages_per_node[node] = []
        messages_per_node[node].append(message)

for node, messages in messages_per_node.items():
    print(f"{node}: {messages}")
