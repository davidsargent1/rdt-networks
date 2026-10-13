import sys
import random

# RDT 3.0
class StateMachine:
    def __init__(self):
        self.state = 0
        self.lastAck = None
    
    def send_packet(self, pkt):
        if self.msg_loss(): # Packet dropped
            return ""

        if str(self.state) == pkt[-1]: # Compare packet to state and update accordingly
            self.state = 1 - self.state
            self.lastAck = self.state
        
        if self.msg_loss(): # Packet recieved, but ack dropped
            return ""
        
        if self.lastAck == None: # If ack1 is sent first, don't want to respond
            return "Unexpected packet. Discarding..."
        
        return f"ack{1 - self.state}" # Send ack
    
    def msg_loss(self):
        loss = random.randint(0,9)
        if loss == 5:
            return True 
        else:
            return False



mach = StateMachine()

while True:
    try:
        pkt = input("Send packet: ")
        print(mach.send_packet(pkt))
    except KeyboardInterrupt:
        sys.exit("Connection closed")