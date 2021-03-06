# -*-coding: <Utf-8> -*-
""" Comments for all the librairy """

import requests
import re
import time
import asyncio
from pint import UnitRegistry

ureg = UnitRegistry()

ip_master_n = []
ip_slave_n = []

MotorSpreader = 2
MotorCrab = 1
MotorChassis = 3

MotorDirectionForward = 1
MotorDirectionBackward = -1

# The amount of time to use before the HTTP connection to the board is considered as too long and we thus exit
# by throwing an RuntimeError of type requests.RuntimeErrors.ConnectTimoutRuntimeError. 

timeout = 2.5


def get_motor_info_from_number(sNr, n = 0):
    """ 
    It takes the number of the motor and the crane as input and returns the  number of the motor with its IP address.
    :param : see def start (sNr, turn) parameters
    
    """
    
    
    if not isinstance(n, int):
        raise TypeError("The value of n must be an integer but got  "+str(n))
        
    if not isinstance(sNr, int):
        raise TypeError(" The value of n must be an integer but got " +str(sNr))
    
    ip_master = ip_master_n[n] 
    ip_slave = ip_slave_n[n] 
    
    
    
    if MotorSpreader == sNr:
        return (ip_slave, 1)
    elif MotorCrab == sNr:
        return (ip_slave, 2)
    elif MotorChassis == sNr:
        return (ip_master, 1)
        
    raise RuntimeError("Invalid motor number, must be MotorSpreader, MotorCrab or MotorChassis, got "+str(sNr))
    
    
def step(sNr,turn,n=0):
    """ 
        :param sNr: This is the first of the arguments. It indicates the engine number that we would like to start. It takes the values ​​1 2 3 which indicates motors 1 2 and 3 respectively
        :param turn: It indicates the direction in which we would like to run the engine. 1 for moving forward and -1 for moving backward.

    Example:
        start(MotorSpreader, MotorDirectionBackward)  turns the spreader backwards
    """
    start(sNr, turn, n)
    stop(sNr,n)


def start_for(t, sNr, turn , n = 0):
    """
    :param t : This is the time during which we decide to run a motor. The syntax is t * ureg.second
        It is noted that we can also write t * ureg.millisecond in case we decide to run the engine for t millisecond.
     :param sNr : See the start function
     :param turn :See the start function
     :param n :  See the start function   
     
        example
         start_for(5000*ureg.nanosecond,MotorChassis,MotorDirectionForward)
         Here we decide to rotate the Chassis forward for 5000 nanosecond
    """
    
    if t < 0:
        raise ValueError("t must be greater than 0 but got "+str(t))
   
    init_time = time.time()*ureg.second
    while time.time()*ureg.second - init_time < t:
        step(sNr, turn, n)
   

def start(sNr, turn, n = 0):
    """ 
        :param sNr: This is the first of the arguments. It indicates the engine number that we would like to start. It takes the values ​​1 2 3 which indicates motors 1 2 and 3 respectively
        :param turn: It indicates the direction in which we would like to run the engine. 1 for moving forward and -1 for moving backward.


    """
    global timeout
           
    print("start")         
           
    if turn not in [MotorDirectionForward, MotorDirectionBackward]:
        raise RuntimeError("Invalid parameter, turn must be either MotorDirectionForward or MotorDirectionBackward. Got " +str(turn))			
    
    ip, numMotor = get_motor_info_from_number( sNr, n)
    r = requests.get("http://"+ip+"/startM?sNr="+str(numMotor)+"&turn="+str(turn),timeout=timeout)
 
    if r.status_code !=200:
        raise RuntimeError("Unable to control the motor, "+str(r.status_code))

    if r.text != "ok":
        raise RuntimeError("Able to controle the motor but got not OK answer: "+r.text)
    return r.text
    
  
  
def stop(sNr, n=0):
    """ 
        :param sNr: This is the first of the arguments. It indicates the engine number that we would like to start. It takes the values ​​1 2 3 which indicates motors 1 2 and 3 respectively


    """
    global timeout
           
    ip, numMotor = get_motor_info_from_number( sNr, n)
    r = requests.get("http://"+ip+"/stopM?sNr="+str(numMotor),timeout=timeout)
 
    if r.status_code !=200:
        raise RuntimeError("Unable to control the motor, "+str(r.status_code))

    if r.text != "ok":
        raise RuntimeError("Able to controle the motor but got not OK answer: "+r.text)
    return r.text  
  
        
def set_speed(sNr, speed, n = 0):
    """ set the speed for a motor """    	

    if not isinstance(n, int):
        raise TypeError(" The value of n must be an integer ")
  
    current = change_speed(sNr, 0, n) 
    diff = speed - current 
    return change_speed(sNr, diff , n)    





def change_speed(sNr, diff, n=0):
	"""
	This function allows us to modify the engine speed while varying its cyclic ratio. 
	
		:param sNr:  see def start (sNr, turn, n = 0) parameters
	:param diff: This parameter is used to vary the speed of the motor. Il s'agit d'un entier.
		It should be noted that the maximum speed that the motor can reach is 100 and the motor speed cannot drop below 30
		:n : Il is the number of the crane
	Example:
		change_speed( MotorSpreader, -60, 2 ) : allows to decrease the motorspeed 3 by 60
	"""
	global ip_master, ip_slave, timeout
		
	
	if not isinstance (diff, int):
		raise TypeError()
	ip, numMotor = get_motor_info_from_number(sNr, n)
	r = requests.get("http://"+ip+"/changePWMTV?sNr="+str(numMotor)+"&diff="+str(diff), timeout=timeout)
	
	if r.status_code != 200: 
		raise RuntimeError("Unable to change the speed of the motor,"+str(r.status_code))
	
	result = re.search("neuer Speed=\s+(\d+)", r.text)
	num = int(result.groups()[0])
	return num





def get_battery(n=0):
    """
    This function takes the number of the crane as a parameter and returns a tuple 
    (the battery state associated with the crane: the battery of the master as well as that of the slave)
    """
    global ip_master_n, ip_slave_n, timeout

    ip_master = ip_master_n[n] 
    ip_slave = ip_slave_n[n] 

    r1=requests.get("http://"+ip_master+"/getBat?n=1", timeout=timeout)
    r2=requests.get("http://"+ip_slave+"/getBat?n=2", timeout=timeout)

    if r1.status_code != 200: 
        raise RuntimeError("Please check if the r1 battery is correctly powered")
    
    if r2.status_code != 200: 
        raise RuntimeError("Please check if the r2 battery is correctly powered")
    
    return (int(r1.text), int(r2.text))
   
    
def init(ip):
    """ 
    The purpose of this function is to initialize the IP address of the master and once the IP address of the master is
    initialized to obtain that of the slave thanks to the getOtherEsp function   
    """

    global ip_master_n, ip_slave_n
    ip_master_n.append(ip) 
    ip_slave_n.append( get_other_esp(ip) )
    
 
    return len(ip_master_n)-1   
    
    
    

    
def get_other_esp(ip):
    """
	This function has the role of launching a request to obtain the IP address of the slave
    """
    global timeout
    r = requests.get("http://" + ip + "/getOtherEsp", timeout = timeout)
    if r.status_code != 200:
        raise RuntimeError ("I failed to get the IP address of the slave. Check if the latter is correctly supplied then try again")

    return r.text 


if __name__ == "__main__":

    ip = "172.17.217.217"
    init(ip)
    init(ip)
    start_for(50000000*ureg.nanosecond,MotorChassis,MotorDirectionForward)
    
    """print(set_speed(MotorSpreader, 10, 1))
    print(change_speed(MotorSpreader, 2))"""

