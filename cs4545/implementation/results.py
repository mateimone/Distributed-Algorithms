import re
from collections import defaultdict

# Example usage
log_lines = \
"""
node3-1  | Node 3 is broadcasting message 4a2742e558314ef3b38f2fca5dff3f13: Malicious message
node3-1  | Node 3 is starting the algorithm
node8-1  | Node 8 is broadcasting message a1952901340c4cc8af461b89fe370155: Message example 2
node8-1  | Node 8 is starting the algorithm
node6-1  | Node 6 is broadcasting message 517a3b4b599849c188a01dc7017c7199: Message example 1
node6-1  | Node 6 is starting the algorithm
node4-1  | Node 4 Delivered message a1952901340c4cc8af461b89fe370155, Message example 2.
node7-1  | Node 7 Delivered message 4a2742e558314ef3b38f2fca5dff3f13, Malicious message.
node3-1  | Node 3 Delivered message 517a3b4b599849c188a01dc7017c7199, Message example 1.
node6-1  | Node 6 Delivered message a1952901340c4cc8af461b89fe370155, Message example 2.
node6-1  | Node 6 Delivered message 4a2742e558314ef3b38f2fca5dff3f13, Malicious message.
node4-1  | Node 4 Delivered message e8de67d8c5d14550b23bdc88c5f0976c, Tampered content 38142.
node5-1  | Node 5 Delivered message 41023050e1574274afad88a2a3a19658, Tampered content 96281.
node8-1  | Node 8 Delivered message 517a3b4b599849c188a01dc7017c7199, Message example 1.
node9-1  | Node 9 Delivered message e8de67d8c5d14550b23bdc88c5f0976c, Tampered content 38142.
node5-1  | Node 5 Delivered message 517a3b4b599849c188a01dc7017c7199, Message example 1.
node9-1  | Node 9 Delivered message a1952901340c4cc8af461b89fe370155, Message example 2.                                                                                                                 
node1-1  | Node 1 Delivered message 41023050e1574274afad88a2a3a19658, Tampered content 96281.
node4-1  | Node 4 Delivered message c76fe50005ef4241b7d51c0265a3a709, Tampered content 97946.
node8-1  | Node 8 Delivered message 1d5150125b014abf87ad33257531de52, Tampered content 31329.
node4-1  | Node 4 Delivered message 517a3b4b599849c188a01dc7017c7199, Message example 1.                                                                                                                 
node3-1  | Node 3 Delivered message 5fb4eafd6df549f884f46c4db22fba50, Tampered content 76497.
node3-1  | Node 3 Delivered message 28e8ed4fe87d4b258d358bb351694e9c, Tampered content 76538.
node1-1  | Node 1 Delivered message c76fe50005ef4241b7d51c0265a3a709, Tampered content 97946.
node6-1  | Node 6 Delivered message e8de67d8c5d14550b23bdc88c5f0976c, Tampered content 38142.                                                                                                            
node5-1  | Node 5 Delivered message a1952901340c4cc8af461b89fe370155, Message example 2.
node9-1  | Node 9 Delivered message 4a2742e558314ef3b38f2fca5dff3f13, Malicious message.                                                                                                                 
node0-1  | Node 0 Delivered message 1f38018c67ae43e7bacce5d1565d8645, Tampered content 17901.
node6-1  | Node 6 Delivered message c76fe50005ef4241b7d51c0265a3a709, Tampered content 97946.
node7-1  | Node 7 Delivered message a1952901340c4cc8af461b89fe370155, Message example 2.
node5-1  | Node 5 Delivered message 30a10030accb4a169089451dc9d347c3, Tampered content 70958.
node8-1  | Node 8 Delivered message 41023050e1574274afad88a2a3a19658, Tampered content 96281.
node4-1  | Node 4 Delivered message 4a2742e558314ef3b38f2fca5dff3f13, Malicious message.
node0-1  | Node 0 Delivered message 517a3b4b599849c188a01dc7017c7199, Message example 1.                                                                                                                 
node0-1  | Node 0 Delivered message 28e8ed4fe87d4b258d358bb351694e9c, Tampered content 76538.
node9-1  | Node 9 Delivered message 517a3b4b599849c188a01dc7017c7199, Message example 1.
node8-1  | Node 8 Delivered message 4a2742e558314ef3b38f2fca5dff3f13, Malicious message.                                                                                                                 
node5-1  | Node 5 Delivered message 4a2742e558314ef3b38f2fca5dff3f13, Malicious message.
node1-1  | Node 1 Delivered message 517a3b4b599849c188a01dc7017c7199, Message example 1.                                                                                                                 
node0-1  | Node 0 Delivered message 7a1672262f0a426cbeee5508e74fd922, Tampered content 58526.                                                                                                            
node0-1  | Node 0 Delivered message a1952901340c4cc8af461b89fe370155, Message example 2.
node5-1  | Node 5 Delivered message 1d5150125b014abf87ad33257531de52, Tampered content 31329.
node1-1  | Node 1 Delivered message 4a2742e558314ef3b38f2fca5dff3f13, Malicious message.                                                                                                                 
node8-1  | Node 8 Delivered message 7bdb60347c044f1390dcc117135f315a, Tampered content 7175.
node0-1  | Node 0 Delivered message 4a2742e558314ef3b38f2fca5dff3f13, Malicious message.
node8-1  | Node 8 Delivered message 04663269fb0042758148b966d818f592, Tampered content 47215.                                                                                                            
node7-1  | Node 7 Delivered message 517a3b4b599849c188a01dc7017c7199, Message example 1.
node1-1  | Node 1 Delivered message a1952901340c4cc8af461b89fe370155, Message example 2.
node4-1  | Node 4 Delivered message 18441663cffa4fe4adb5999a00faac80, Tampered content 73028.
node0-1  | Node 0 Delivered message 7bdb60347c044f1390dcc117135f315a, Tampered content 7175.
node5-1  | Node 5 Delivered message 04663269fb0042758148b966d818f592, Tampered content 47215.
node3-1  | Node 3 Delivered message a1952901340c4cc8af461b89fe370155, Message example 2.
node7-1  | Node 7 Delivered message 0265a4028cf14edfae01a6dfe46e53c9, Tampered content 6049.
node9-1  | Node 9 Delivered message 697d06e210c64bc09f7af81181576680, Tampered content 74269.
node6-1  | Node 6 Delivered message 18441663cffa4fe4adb5999a00faac80, Tampered content 73028.
node1-1  | Node 1 Delivered message 0265a4028cf14edfae01a6dfe46e53c9, Tampered content 6049.
node1-1  | Node 1 Delivered message 697d06e210c64bc09f7af81181576680, Tampered content 74269.
node5-1  | Node 5 Delivered message d0b8719983c84fafb26e4b759b5c7bcc, Tampered content 88190.                                                                                                            
node1-1  | Node 1 Delivered message d0b8719983c84fafb26e4b759b5c7bcc, Tampered content 88190.
node4-1  | Node 4 Delivered message 1dd1494f77574a30b20048e01c0128ca, Tampered content 87029.
node5-1  | Node 5 Delivered message 1dd1494f77574a30b20048e01c0128ca, Tampered content 87029.
"""
# Initialize a default dictionary to hold counts
message_counts = defaultdict(int)

# Regular expression to match Delivered messages
delivered_pattern = re.compile(
    r'Delivered message ([a-f0-9]+), (.+?)(?:\.|$)', re.IGNORECASE
)

# Process each line
for line in log_lines.strip().split('\n'):
    match = delivered_pattern.search(line)
    if match:
        message_id = match.group(1)
        content = match.group(2)
        key = (message_id, content)
        message_counts[key] += 1

# Display the results
print(f"{'Message ID':<40} | {'Content':<30} | {'Count'}")
print("-" * 80)
for (msg_id, content), count in message_counts.items():
    print(f"{msg_id:<40} | {content:<30} | {count}")