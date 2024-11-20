import re
from collections import defaultdict

log_lines = \
"""
node0-1  | Node 0 is broadcasting message f46d5a5f2f7d4bc2b5664401bccc02d1: Message example 1                                                                                                            
node0-1  | Node 0 is starting the algorithm
node4-1  | Node 4 is broadcasting message f4572ef9b6494541b4805132851b2127: Message example 2                                                                                                            
node4-1  | Node 4 is broadcasting message 8f4e90778c9b4e9685216f62a6c2d169: Message example 3
node4-1  | Node 4 is starting the algorithm                                                                                                                                                              
node2-1  | Node 2 is broadcasting message bc3c00cf275546e593ff67e68134cf9b: Malicious message                                                                                                            
node2-1  | Node 2 is maliciously starting the algorithm
node2-1  | Node 2 has chosen to send to 1 neighbors.                                                                                                                                                     
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node7-1  | Node 7 Delivered message bc3c00cf275546e593ff67e68134cf9b, Malicious message.                                                                                                                 
node6-1  | Node 6 Delivered message f46d5a5f2f7d4bc2b5664401bccc02d1, Message example 1.
node2-1  | Helloooo
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node4-1  | Node 4 is starting the algorithm                                                                                                                                                              
node1-1  | Node 1 Delivered message f46d5a5f2f7d4bc2b5664401bccc02d1, Message example 1.
node7-1  | Node 7 Delivered message f46d5a5f2f7d4bc2b5664401bccc02d1, Message example 1.
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node9-1  | Node 9 Delivered message f4572ef9b6494541b4805132851b2127, Message example 2.                                                                                                                 
node5-1  | Node 5 Delivered message f46d5a5f2f7d4bc2b5664401bccc02d1, Message example 1.
node1-1  | Node 1 Delivered message f4572ef9b6494541b4805132851b2127, Message example 2.
node8-1  | Node 8 Delivered message f46d5a5f2f7d4bc2b5664401bccc02d1, Message example 1.
node2-1  | Helloooo
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node3-1  | Node 3 Delivered message f4572ef9b6494541b4805132851b2127, Message example 2.                                                                                                                 
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | hello?
node1-1  | Node 1 Delivered message de11ea9868e74d77948cc5a3fc13a50e, Tampered content 95182.                                                                                                            
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node5-1  | Node 5 Delivered message f4572ef9b6494541b4805132851b2127, Message example 2.                                                                                                                 
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node6-1  | Node 6 Delivered message f4572ef9b6494541b4805132851b2127, Message example 2.                                                                                                                 
node2-1  | Helloooo
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node4-1  | Node 4 Delivered message de11ea9868e74d77948cc5a3fc13a50e, Tampered content 95182.                                                                                                            
node7-1  | Node 7 Delivered message f4572ef9b6494541b4805132851b2127, Message example 2.
node9-1  | Node 9 Delivered message f46d5a5f2f7d4bc2b5664401bccc02d1, Message example 1.
node2-1  | Helloooo
node2-1  | hello?
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?
node0-1  | Node 0 Delivered message f4572ef9b6494541b4805132851b2127, Message example 2.                                                                                                                 
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node8-1  | Node 8 Delivered message 5f5b4b496d2441bcb4020fd6d0c9ac9b, Tampered content 7933.                                                                                                             
node4-1  | Node 4 Delivered message f46d5a5f2f7d4bc2b5664401bccc02d1, Message example 1.
node2-1  | Helloooo
node2-1  | hello?
node2-1  | empty path from byzantine
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node1-1  | Node 1 Delivered message 2975086961004b039a8c882b11de3530, Tampered content 62816.                                                                                                            
node0-1  | Node 0 Delivered message 7e520b555e4a4bf2b3f83585515a89a6, Tampered content 70723.
node5-1  | Node 5 Delivered message 8f4e90778c9b4e9685216f62a6c2d169, Message example 3.
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node8-1  | Node 8 Delivered message f4572ef9b6494541b4805132851b2127, Message example 2.                                                                                                                 
node2-1  | Helloooo
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | hello?
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node8-1  | Node 8 Delivered message 933551f8af7a48d682f993d82504094e, Tampered content 68174.                                                                                                            
node0-1  | Node 0 Delivered message 7c91e53257b347ffa4ca301a0bab821f, Tampered content 32373.
node6-1  | Node 6 Delivered message 5f5b4b496d2441bcb4020fd6d0c9ac9b, Tampered content 7933.
node9-1  | Node 9 Delivered message 8f4e90778c9b4e9685216f62a6c2d169, Message example 3.
node3-1  | Node 3 Delivered message f46d5a5f2f7d4bc2b5664401bccc02d1, Message example 1.                                                                                                                 
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | hello?                                                                                                                                                                                        
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | hello?
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node1-1  | Node 1 Delivered message 1da7bdcdee524ccb8140f1fa9d38039f, Message example 2.
node5-1  | Node 5 Delivered message ba573460f3554c74ac44f19df5f70419, Tampered content 17977.
node6-1  | Node 6 Delivered message 8f4e90778c9b4e9685216f62a6c2d169, Message example 3.                                                                                                                 
node8-1  | Node 8 Delivered message af4b4e6dc5694d86aa325a1d96597235, Tampered content 81202.
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine
node6-1  | Node 6 Delivered message af4b4e6dc5694d86aa325a1d96597235, Tampered content 81202.                                                                                                            
node8-1  | Node 8 Delivered message 1da7bdcdee524ccb8140f1fa9d38039f, Message example 2.
node7-1  | Node 7 Delivered message ba573460f3554c74ac44f19df5f70419, Tampered content 17977.
node8-1  | Node 8 Delivered message c7b1adc35281464ca63593291e9f368d, Tampered content 75533.
node1-1  | Node 1 Delivered message 8f4e90778c9b4e9685216f62a6c2d169, Message example 3.
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node3-1  | Node 3 Delivered message 8f4e90778c9b4e9685216f62a6c2d169, Message example 3.                                                                                                                 
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node8-1  | Node 8 Delivered message d1303d37441249ada711416518ffad1c, Tampered content 11604.                                                                                                            
node2-1  | empty path from byzantine
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node4-1  | Node 4 Delivered message 6dcda1651ac34df5ac88858f39df95cb, Tampered content 23717.                                                                                                            
node1-1  | Node 1 Delivered message d1303d37441249ada711416518ffad1c, Tampered content 11604.                                                                                                            
node4-1  | Node 4 Delivered message 7da5caeb05474fdc85509c779dcb25f1, Tampered content 29704.
node3-1  | Node 3 Delivered message 7c91e53257b347ffa4ca301a0bab821f, Tampered content 32373.
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node5-1  | Node 5 Delivered message 0fe365c55a5c4514b9aec674c721d09d, Tampered content 98949.                                                                                                            
node0-1  | Node 0 Delivered message 8f4e90778c9b4e9685216f62a6c2d169, Message example 3.
node8-1  | Node 8 Delivered message 7e520b555e4a4bf2b3f83585515a89a6, Tampered content 70723.
node0-1  | Node 0 Delivered message 1da7bdcdee524ccb8140f1fa9d38039f, Message example 2.                                                                                                                 
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node3-1  | Node 3 Delivered message a8aadfe0964d492d890d9755c667ed5f, Tampered content 8070.                                                                                                             
node6-1  | Node 6 Delivered message 7da5caeb05474fdc85509c779dcb25f1, Tampered content 29704.
node0-1  | Node 0 Delivered message 0fe365c55a5c4514b9aec674c721d09d, Tampered content 98949.
node8-1  | Node 8 Delivered message d88a9a66598e489996d7d64b27e0059d, Tampered content 18909.                                                                                                            
node8-1  | Node 8 Delivered message 8f4e90778c9b4e9685216f62a6c2d169, Message example 3.
node4-1  | Node 4 Delivered message 7e520b555e4a4bf2b3f83585515a89a6, Tampered content 70723.
node2-1  | Helloooo
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node0-1  | Node 0 Delivered message 70e7326663ba47b1b3bb3f0950c02640, Tampered content 89168.                                                                                                            
node3-1  | Node 3 Delivered message 70e7326663ba47b1b3bb3f0950c02640, Tampered content 89168.
node2-1  | Helloooo
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | hello?                                                                                                                                                                                        
node2-1  | empty path from byzantine                                                                                                                                                                     
node9-1  | Node 9 Delivered message 7c91e53257b347ffa4ca301a0bab821f, Tampered content 32373.                                                                                                            
node7-1  | Node 7 Delivered message 8f4e90778c9b4e9685216f62a6c2d169, Message example 3.
node9-1  | Node 9 Delivered message 70e7326663ba47b1b3bb3f0950c02640, Tampered content 89168.
node8-1  | Node 8 Delivered message 406c89e15cf94cc9b6e6d63c46ca2722, Tampered content 87781.
node2-1  | Helloooo
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node8-1  | Node 8 Delivered message d4dec37eb18e433e8889a25ab73de854, Tampered content 97668.                                                                                                            
node4-1  | Node 4 Delivered message f0f2bee5a92140179dfe002d230e394a, Tampered content 29707.                                                                                                            
node4-1  | Node 4 Delivered message 1da7bdcdee524ccb8140f1fa9d38039f, Message example 2.
node2-1  | Helloooo
node2-1  | hello?
node2-1  | empty path from byzantine                                                                                                                                                                     
node2-1  | hello?                                                                                                                                                                                        
node2-1  | hello?                                                                                                                                                                                        
node4-1  | Node 4 Delivered message a4d597837a1949398530359786b38547, Tampered content 7394.                                                                                                             
node2-1  | hello?                                                                                                                                                                                        
node0-1  | Node 0 Delivered message d1303d37441249ada711416518ffad1c, Tampered content 11604.                                                                                                            
node6-1  | Node 6 Delivered message 933551f8af7a48d682f993d82504094e, Tampered content 68174.
node4-1  | Node 4 Delivered message d1303d37441249ada711416518ffad1c, Tampered content 11604.
node7-1  | Node 7 Delivered message 77dc59d5b9e5425182d5b54ceee34234, Tampered content 34648.
node0-1  | Node 0 Delivered message 64e927b2012840dfbf8ab41803518fd2, Tampered content 87441.
node7-1  | Node 7 Delivered message 831ca85e667f4947acd91b4e4e2b45d1, Tampered content 22006.
node0-1  | Node 0 Delivered message 15bea4239b6c446b99f710b85ddb92c3, Tampered content 87166.
node0-1  | Node 0 Delivered message c7b1adc35281464ca63593291e9f368d, Tampered content 75533.                                                                                                            
node1-1  | Node 1 Delivered message c7b1adc35281464ca63593291e9f368d, Tampered content 75533.
node6-1  | Node 6 Delivered message d4dec37eb18e433e8889a25ab73de854, Tampered content 97668.
node9-1  | Node 9 Delivered message 64e927b2012840dfbf8ab41803518fd2, Tampered content 87441.
node2-1  | Helloooo                                                                                                                                                                                      
node2-1  | hello?
node2-1  | empty path from byzantine
node8-1  | Node 8 Delivered message e531488cba0d4d9ca52896077db16c53, Tampered content 59456.                                                                                                            
node1-1  | Node 1 Delivered message 80ef101166d3419dac8ac149cbfd21f2, Tampered content 35075.                                                                                                            
node4-1  | Node 4 Delivered message 55c210dbb9534d6ba60add5a2fba0d02, Tampered content 32941.
node8-1  | Node 8 Delivered message 80ef101166d3419dac8ac149cbfd21f2, Tampered content 35075.
node3-1  | Node 3 Delivered message 64e927b2012840dfbf8ab41803518fd2, Tampered content 87441.
node4-1  | Node 4 Delivered message 8adc4f8d77594effa3960317924d102f, Tampered content 96073.                                                                                                            
node6-1  | Node 6 Delivered message a4d597837a1949398530359786b38547, Tampered content 7394.
node5-1  | Node 5 Delivered message 79306ef6425e4d5ab7cf905f1acedcf2, Tampered content 63606.
node6-1  | Node 6 Delivered message 5db9d0774ef34c4387dd3ac1d7202974, Tampered content 97875.
node1-1  | Node 1 Delivered message 8c3623e0160b44dba292b1abe5ea4904, Tampered content 93395.
node9-1  | Node 9 Delivered message a8aadfe0964d492d890d9755c667ed5f, Tampered content 8070.
node4-1  | Node 4 Delivered message f1428161a2c24d43b465147e860b54dd, Tampered content 6870.
node4-1  | Node 4 Delivered message f0ec47d793ce490a902015d67d3cc59f, Tampered content 49190.
node4-1  | Node 4 Delivered message c7b1adc35281464ca63593291e9f368d, Tampered content 75533.
node9-1  | Node 9 Delivered message 15bea4239b6c446b99f710b85ddb92c3, Tampered content 87166.                                                                                                            
node1-1  | Node 1 Delivered message 34b613fa91f44466899eb4c0e0714da0, Tampered content 40660.
node8-1  | Node 8 Delivered message 68a2b1e84627456697306606e9822687, Tampered content 21312.
node5-1  | Node 5 Delivered message 90297d10668941da86cbf53dff5f6380, Tampered content 7412.                                                                                                             
node0-1  | Node 0 Delivered message 79306ef6425e4d5ab7cf905f1acedcf2, Tampered content 63606.
node4-1  | Node 4 Delivered message 8c3623e0160b44dba292b1abe5ea4904, Tampered content 93395.                                                                                                            
node8-1  | Node 8 Delivered message 96912eb3258649e2b509ef96429a333d, Tampered content 48878.
node7-1  | Node 7 Delivered message f7d5f513131a4ec8abe7be32d9097565, Tampered content 42115.                                                                                                            
node1-1  | Node 1 Delivered message 446878fa5ca4408cbcea510db5efd886, Tampered content 13370.                                                                                                            
node4-1  | Node 4 Delivered message 5db9d0774ef34c4387dd3ac1d7202974, Tampered content 97875.
node1-1  | Node 1 Delivered message 52014fce7bf640babb9e4131f9292f71, Tampered content 34087.                                                                                                            
node9-1  | Node 9 Delivered message 24f6b411853e4ad3b8a515cd1cf408c7, Tampered content 69362.
node3-1  | Node 3 Delivered message 24f6b411853e4ad3b8a515cd1cf408c7, Tampered content 69362.                                                                                                            
node6-1  | Node 6 Delivered message 150c1f1e640f40cbad60dc0063a3139d, Tampered content 43243.
node6-1  | Node 6 Delivered message 80ef101166d3419dac8ac149cbfd21f2, Tampered content 35075.
node9-1  | Node 9 Delivered message f7d5f513131a4ec8abe7be32d9097565, Tampered content 42115.
node3-1  | Node 3 Delivered message 0aa5bf09a92c465d82691bca1c1869bd, Tampered content 27063.                                                                                                            
node3-1  | Node 3 Delivered message ddfbc583001345349d147e39308126ec, Tampered content 48203.                                                                                                            
node1-1  | Node 1 Delivered message 984e922a9cf14bafa5195d6671839c2e, Tampered content 2081.
node0-1  | Node 0 Delivered message ddfbc583001345349d147e39308126ec, Tampered content 48203.                                                                                                            
node4-1  | Node 4 Delivered message 2b024a1e60394cfbb44fd1f728da4065, Tampered content 20161.
node6-1  | Node 6 Delivered message 446878fa5ca4408cbcea510db5efd886, Tampered content 13370.
node6-1  | Node 6 Delivered message e531488cba0d4d9ca52896077db16c53, Tampered content 59456.
node6-1  | Node 6 Delivered message 55c210dbb9534d6ba60add5a2fba0d02, Tampered content 32941.
node9-1  | Node 9 Delivered message 80ef101166d3419dac8ac149cbfd21f2, Tampered content 35075.
node0-1  | Node 0 Delivered message 77dc59d5b9e5425182d5b54ceee34234, Tampered content 34648.                                                                                                            
node9-1  | Node 9 Delivered message ddfbc583001345349d147e39308126ec, Tampered content 48203.
node1-1  | Node 1 Delivered message 8adc4f8d77594effa3960317924d102f, Tampered content 96073.
node7-1  | Node 7 Delivered message 7df66a533fcb45608403987ed571afd3, Tampered content 56293.
node7-1  | Node 7 Delivered message 15bea4239b6c446b99f710b85ddb92c3, Tampered content 87166.                                                                                                            
node8-1  | Node 8 Delivered message 446878fa5ca4408cbcea510db5efd886, Tampered content 13370.
node4-1  | Node 4 Delivered message cdda025928fd4b899bca64f1eea605dd, Tampered content 43074.
node6-1  | Node 6 Delivered message 2b024a1e60394cfbb44fd1f728da4065, Tampered content 20161.
node9-1  | Node 9 Delivered message 90297d10668941da86cbf53dff5f6380, Tampered content 7412.
node0-1  | Node 0 Delivered message 427565aa481742ffa5ffb9258847fe8a, Tampered content 93872.
node8-1  | Node 8 Delivered message 34b613fa91f44466899eb4c0e0714da0, Tampered content 40660.
node9-1  | Node 9 Delivered message 427565aa481742ffa5ffb9258847fe8a, Tampered content 93872.
node0-1  | Node 0 Delivered message cdda025928fd4b899bca64f1eea605dd, Tampered content 43074.
node6-1  | Node 6 Delivered message 34b613fa91f44466899eb4c0e0714da0, Tampered content 40660.                                                                                                            
node0-1  | Node 0 Delivered message 7df66a533fcb45608403987ed571afd3, Tampered content 56293.
node6-1  | Node 6 Delivered message f0ec47d793ce490a902015d67d3cc59f, Tampered content 49190.
node6-1  | Node 6 Delivered message f1428161a2c24d43b465147e860b54dd, Tampered content 6870.                                                                                                             
node0-1  | Node 0 Delivered message f7d5f513131a4ec8abe7be32d9097565, Tampered content 42115.
node6-1  | Node 6 Delivered message 984e922a9cf14bafa5195d6671839c2e, Tampered content 2081.                                                                                                             
node7-1  | Node 7 Delivered message 29f3511ff86d4055b4f1ab517bd26cd6, Tampered content 33864.
node6-1  | Node 6 Delivered message 68a2b1e84627456697306606e9822687, Tampered content 21312.                                                                                                            
node9-1  | Node 9 Delivered message 34b613fa91f44466899eb4c0e0714da0, Tampered content 40660.
node0-1  | Node 0 Delivered message 6ab6fa0d8d54402ca2398b91ec9dce47, Tampered content 90556.
node1-1  | Node 1 Delivered message cdda025928fd4b899bca64f1eea605dd, Tampered content 43074.
node5-1  | Node 5 Delivered message 7df66a533fcb45608403987ed571afd3, Tampered content 56293.
node9-1  | Node 9 Delivered message 52014fce7bf640babb9e4131f9292f71, Tampered content 34087.
node6-1  | Node 6 Delivered message 96912eb3258649e2b509ef96429a333d, Tampered content 48878.
node1-1  | Node 1 Delivered message 146d3942380341bea61afb9abbbee4fa, Tampered content 57188.                                                                                                            
node4-1  | Node 4 Delivered message 150c1f1e640f40cbad60dc0063a3139d, Tampered content 43243.
node9-1  | Node 9 Delivered message 0425b107816f4025b8f3f6e9a8d5c0be, Tampered content 71813.
node8-1  | Node 8 Delivered message 984e922a9cf14bafa5195d6671839c2e, Tampered content 2081.
node6-1  | Node 6 Delivered message 1bb73a43dc384823a5d110e1a3f49e0a, Tampered content 44557.
node8-1  | Node 8 Delivered message cdda025928fd4b899bca64f1eea605dd, Tampered content 43074.                                                                                                            
node7-1  | Node 7 Delivered message e40ad75bd36b412d8a655de1d73167a7, Tampered content 1263.
node8-1  | Node 8 Delivered message f61163eeee6e402e9295c695141f00bc, Tampered content 16315.
node0-1  | Node 0 Delivered message 29f3511ff86d4055b4f1ab517bd26cd6, Tampered content 33864.
node1-1  | Node 1 Delivered message 8b66efa2f1894d4abcae86eeeb9c1564, Tampered content 73670.
node4-1  | Node 4 Delivered message 6ab6fa0d8d54402ca2398b91ec9dce47, Tampered content 90556.
node8-1  | Node 8 Delivered message 52014fce7bf640babb9e4131f9292f71, Tampered content 34087.                                                                                                            
node9-1  | Node 9 Delivered message 446878fa5ca4408cbcea510db5efd886, Tampered content 13370.                                                                                                            
node0-1  | Node 0 Delivered message 3bbc085efbec4283926ebc8b1a124571, Tampered content 87344.
node1-1  | Node 1 Delivered message 6ab6fa0d8d54402ca2398b91ec9dce47, Tampered content 90556.                                                                                                            
node4-1  | Node 4 Delivered message e50800bc6b70435284f7143bb54c16f0, Tampered content 84047.
node9-1  | Node 9 Delivered message d9027e941abb41d2b6a7ddcedb2e595b, Tampered content 16602.                                                                                                            
node6-1  | Node 6 Delivered message 52014fce7bf640babb9e4131f9292f71, Tampered content 34087.
node9-1  | Node 9 Delivered message 984e922a9cf14bafa5195d6671839c2e, Tampered content 2081.
node8-1  | Node 8 Delivered message 6ab6fa0d8d54402ca2398b91ec9dce47, Tampered content 90556.
node4-1  | Node 4 Delivered message 146d3942380341bea61afb9abbbee4fa, Tampered content 57188.
node0-1  | Node 0 Delivered message e40ad75bd36b412d8a655de1d73167a7, Tampered content 1263.                                                                                                             
node8-1  | Node 8 Delivered message 0dfff4b442174b11973ce5679313174a, Tampered content 50256.
node5-1  | Node 5 Delivered message d9027e941abb41d2b6a7ddcedb2e595b, Tampered content 16602.                                                                                                            
node0-1  | Node 0 Delivered message 146d3942380341bea61afb9abbbee4fa, Tampered content 57188.
node5-1  | Node 5 Delivered message 18b3a52d011a49db831402075547c96a, Tampered content 57813.
node8-1  | Node 8 Delivered message 3bbc085efbec4283926ebc8b1a124571, Tampered content 87344.
node4-1  | Node 4 Delivered message 1bb73a43dc384823a5d110e1a3f49e0a, Tampered content 44557.
node9-1  | Node 9 Delivered message 8db7e462b9174493af9a97b613d8d72f, Tampered content 89743.
node9-1  | Node 9 Delivered message e40ad75bd36b412d8a655de1d73167a7, Tampered content 1263.
node9-1  | Node 9 Delivered message 18b3a52d011a49db831402075547c96a, Tampered content 57813.
node6-1  | Node 6 Delivered message 0dfff4b442174b11973ce5679313174a, Tampered content 50256.
node6-1  | Node 6 Delivered message e50800bc6b70435284f7143bb54c16f0, Tampered content 84047.
node0-1  | Node 0 Delivered message 8db7e462b9174493af9a97b613d8d72f, Tampered content 89743.
node8-1  | Node 8 Delivered message 146d3942380341bea61afb9abbbee4fa, Tampered content 57188.
node9-1  | Node 9 Delivered message 29f3511ff86d4055b4f1ab517bd26cd6, Tampered content 33864.
node7-1  | Node 7 Delivered message 8db7e462b9174493af9a97b613d8d72f, Tampered content 89743.
node8-1  | [Node 8] Stopping due to inactivity. Last message received 10.83 seconds ago.
node8-1  | [Node 8] Stopping algorithm
node8-1  | [Node 8] Algorithm output saved to output/node-8.out in /home/python/output/node-8.out                                                                                                        
node8-1  | [Node 8] Node stats saved to output/node-8.yml in /home/python/output/node-8.yml                                                                                                              
node8-1 exited with code 0
node3-1  | Node 3 Delivered message 427565aa481742ffa5ffb9258847fe8a, Tampered content 93872.
node3-1  | Node 3 Delivered message d9027e941abb41d2b6a7ddcedb2e595b, Tampered content 16602.
node3-1  | Node 3 Delivered message 0425b107816f4025b8f3f6e9a8d5c0be, Tampered content 71813.
node3-1  | Node 3 Delivered message 18b3a52d011a49db831402075547c96a, Tampered content 57813.
node4-1  | Node 4 Delivered message 8b66efa2f1894d4abcae86eeeb9c1564, Tampered content 73670.
"""
message_counts = defaultdict(int)

delivered_pattern = re.compile(
    r'Delivered message ([a-f0-9]+), (.+?)(?:\.|$)', re.IGNORECASE
)

for line in log_lines.strip().split('\n'):
    match = delivered_pattern.search(line)
    if match:
        message_id = match.group(1)
        content = match.group(2)
        key = (message_id, content)
        message_counts[key] += 1

print(f"{'Message ID':<40} | {'Content':<30} | {'Count'}")
print("-" * 80)
for (msg_id, content), count in message_counts.items():
    print(f"{msg_id:<40} | {content:<30} | {count}")