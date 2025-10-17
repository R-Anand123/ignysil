"""
Ignisyl Firewall Integration Module
Integrates with Windows Firewall to enforce blocking decisions
"""

import subprocess
import platform
import logging
from datetime import datetime

class FirewallController:
    """
    Controls Windows/Linux firewall based on threat detection
    """
    
    def __init__(self):
        self.os_type = platform.system()
        self.blocked_ips = set()
        self.blocked_users = set()
        self.log_file = "firewall_actions.log"
        
        # Setup logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def block_ip_address(self, ip_address, rule_name="Ignisyl_Block"):
        """
        Block an IP address using Windows Firewall
        """
        try:
            if self.os_type == "Windows":
                # Windows Firewall command
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}_{ip_address}" dir=in action=block remoteip={ip_address}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.blocked_ips.add(ip_address)
                    logging.info(f"BLOCKED IP: {ip_address}")
                    return True, f"Successfully blocked {ip_address}"
                else:
                    logging.error(f"Failed to block {ip_address}: {result.stderr}")
                    return False, result.stderr
                    
            elif self.os_type == "Linux":
                # Linux iptables command
                cmd = f'sudo iptables -A INPUT -s {ip_address} -j DROP'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.blocked_ips.add(ip_address)
                    logging.info(f"BLOCKED IP: {ip_address}")
                    return True, f"Successfully blocked {ip_address}"
                else:
                    logging.error(f"Failed to block {ip_address}: {result.stderr}")
                    return False, result.stderr
            else:
                return False, f"Unsupported OS: {self.os_type}"
                
        except Exception as e:
            logging.error(f"Error blocking IP {ip_address}: {str(e)}")
            return False, str(e)
    
    def unblock_ip_address(self, ip_address, rule_name="Ignisyl_Block"):
        """
        Unblock an IP address
        """
        try:
            if self.os_type == "Windows":
                cmd = f'netsh advfirewall firewall delete rule name="{rule_name}_{ip_address}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.blocked_ips.discard(ip_address)
                    logging.info(f"UNBLOCKED IP: {ip_address}")
                    return True, f"Successfully unblocked {ip_address}"
                else:
                    return False, result.stderr
                    
            elif self.os_type == "Linux":
                cmd = f'sudo iptables -D INPUT -s {ip_address} -j DROP'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.blocked_ips.discard(ip_address)
                    logging.info(f"UNBLOCKED IP: {ip_address}")
                    return True, f"Successfully unblocked {ip_address}"
                else:
                    return False, result.stderr
                    
        except Exception as e:
            logging.error(f"Error unblocking IP {ip_address}: {str(e)}")
            return False, str(e)
    
    def block_user_network_access(self, username):
        """
        Block all network access for a specific user (Windows only)
        Requires admin privileges
        """
        try:
            if self.os_type == "Windows":
                # Disable network adapter for user
                cmd = f'netsh advfirewall firewall add rule name="Ignisyl_BlockUser_{username}" dir=out action=block enable=yes profile=any localip=any remoteip=any protocol=any interfacetype=any'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.blocked_users.add(username)
                    logging.info(f"BLOCKED USER NETWORK ACCESS: {username}")
                    return True, f"Successfully blocked network access for {username}"
                else:
                    return False, result.stderr
            else:
                return False, "User-level blocking only supported on Windows"
                
        except Exception as e:
            logging.error(f"Error blocking user {username}: {str(e)}")
            return False, str(e)
    
    def restrict_port_access(self, port, protocol="TCP"):
        """
        Restrict access to a specific port
        """
        try:
            if self.os_type == "Windows":
                cmd = f'netsh advfirewall firewall add rule name="Ignisyl_RestrictPort_{port}" dir=in action=block protocol={protocol} localport={port}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logging.info(f"RESTRICTED PORT: {port}/{protocol}")
                    return True, f"Successfully restricted port {port}"
                else:
                    return False, result.stderr
                    
            elif self.os_type == "Linux":
                cmd = f'sudo iptables -A INPUT -p {protocol.lower()} --dport {port} -j DROP'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logging.info(f"RESTRICTED PORT: {port}/{protocol}")
                    return True, f"Successfully restricted port {port}"
                else:
                    return False, result.stderr
                    
        except Exception as e:
            logging.error(f"Error restricting port {port}: {str(e)}")
            return False, str(e)
    
    def get_firewall_status(self):
        """
        Get current firewall status
        """
        try:
            if self.os_type == "Windows":
                cmd = 'netsh advfirewall show allprofiles state'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return result.stdout
            elif self.os_type == "Linux":
                cmd = 'sudo iptables -L -n'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return result.stdout
            else:
                return "Unsupported OS"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def list_blocked_items(self):
        """
        List all currently blocked IPs and users
        """
        return {
            "blocked_ips": list(self.blocked_ips),
            "blocked_users": list(self.blocked_users),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def get_user_ip_from_activity_log(self, username, pc_name):
        """
        In a real system, this would query Active Directory or DHCP
        to get the user's current IP address
        For now, returns a simulated IP mapping
        """
        # TODO: Implement actual IP lookup from:
        # - Active Directory
        # - DHCP logs
        # - Network monitoring tools
        # - SIEM integration
        
        # Simulated mapping for demonstration
        ip_mapping = {
            "PC-001": "192.168.1.101",
            "PC-002": "192.168.1.102",
            "PC-003": "192.168.1.103",
            "PC-004": "192.168.1.104",
            "PC-005": "192.168.1.105",
            "PC-006": "192.168.1.106",
            "PC-007": "192.168.1.107",
            "PC-008": "192.168.1.108",
        }
        
        return ip_mapping.get(pc_name, None)
    
    def apply_threat_response(self, user, pc, risk_level, threat_type="insider"):
        """
        Automatically apply firewall rules based on threat level
        """
        actions_taken = []
        
        # Get user's IP address
        user_ip = self.get_user_ip_from_activity_log(user, pc)
        
        if risk_level == "High":
            # BLOCK: Complete network isolation
            if user_ip:
                success, msg = self.block_ip_address(user_ip, f"Ignisyl_HighRisk_{user}")
                actions_taken.append(("Block IP", success, msg))
            
            # Also block at user level if Windows
            success, msg = self.block_user_network_access(user)
            actions_taken.append(("Block User", success, msg))
            
            logging.critical(f"HIGH RISK - BLOCKED: User={user}, PC={pc}, IP={user_ip}")
            
        elif risk_level == "Medium":
            # RESTRICT: Block specific high-risk ports
            restricted_ports = [445, 3389, 22, 23]  # SMB, RDP, SSH, Telnet
            for port in restricted_ports:
                success, msg = self.restrict_port_access(port)
                actions_taken.append((f"Restrict Port {port}", success, msg))
            
            logging.warning(f"MEDIUM RISK - RESTRICTED: User={user}, PC={pc}")
        
        return actions_taken


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("IGNISYL FIREWALL CONTROLLER - TEST MODE")
    print("=" * 60)
    
    firewall = FirewallController()
    
    print(f"\n🖥️  Operating System: {firewall.os_type}")
    print(f"📋 Log File: {firewall.log_file}")
    
    print("\n" + "=" * 60)
    print("TESTING FIREWALL FUNCTIONS")
    print("=" * 60)
    
    # Test 1: Check firewall status
    print("\n1️⃣  Current Firewall Status:")
    print("-" * 60)
    status = firewall.get_firewall_status()
    print(status[:500] + "..." if len(status) > 500 else status)
    
    # Test 2: Simulate blocking high-risk user
    print("\n2️⃣  Simulating High-Risk Threat Response:")
    print("-" * 60)
    actions = firewall.apply_threat_response(
        user="john_doe",
        pc="PC-005",
        risk_level="High"
    )
    for action_name, success, message in actions:
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {action_name}: {message}")
    
    # Test 3: List blocked items
    print("\n3️⃣  Currently Blocked Items:")
    print("-" * 60)
    blocked = firewall.list_blocked_items()
    print(f"Blocked IPs: {blocked['blocked_ips']}")
    print(f"Blocked Users: {blocked['blocked_users']}")
    print(f"Timestamp: {blocked['timestamp']}")
    
    print("\n" + "=" * 60)
    print("⚠️  NOTE: Actual firewall modifications require administrator privileges")
    print("=" * 60)
