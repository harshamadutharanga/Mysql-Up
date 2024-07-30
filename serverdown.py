import os
import subprocess
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
import paramiko
import time
import datetime
from ip_config import ip_addresses  # Import the ip_addresses dictionary

def ping_ip(ip_address):
    """ Ping an IP address and return True if successful, False otherwise. """
    try:
        command = ['ping', '-n', '1', ip_address] if os.name == 'nt' else ['ping', '-c', '1', ip_address]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error during ping: {e}")
        return False

def update_progress(step, message):
    """ Update progress bar and process details. """
    progress_var.set(step)
    process_details_label.config(text=message)
    root.update_idletasks()

def reset_progress():
    """ Reset the progress bar and process details. """
    progress_var.set(0)
    process_details_label.config(text="")
    root.update_idletasks()

def check_network():
    """ Check network status based on user input location code. """
    reset_progress()
    location_code = entry.get().strip()
    for category in ip_addresses.values():
        super_center = category.get(location_code)
        if super_center:
            ip = super_center['ip']
            location = super_center['location']
            ping_status = ping_ip(ip)
            result_label.config(text=f"IP: {ip} | Location: {location} | Status: {'Online' if ping_status else 'Offline'}")
            
            # Enable or disable MySQL Status button based on network status
            if ping_status:
                try_btn.config(state=tk.NORMAL)
            else:
                try_btn.config(state=tk.DISABLED)
            return

    messagebox.showerror("Error", "Invalid location code")

def check_mysql_status():
    """ Attempt to SSH into the specified location and execute commands after switching to su. """
    reset_progress()
    location_code = entry.get().strip()
    update_progress(10, "Starting SSH connection...")
    for category in ip_addresses.values():
        super_center = category.get(location_code)
        if super_center:
            ip = super_center['ip']
            username = 'rpdadmin'
            password = 'nilkamal'
            root_password = 'nilkamal'  # Replace with your actual root password
            
            try:
                # Establish SSH connection
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(ip, username=username, password=password, timeout=5)
                update_progress(30, "SSH connection established...")
                
                # Open a shell session
                ssh_shell = ssh_client.invoke_shell()
                
                # Wait for a moment to let the shell start
                time.sleep(1)
                
                # Send 'su' command to switch to root
                ssh_shell.send('su\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print command to switch to root
                
                # Send root password
                ssh_shell.send(root_password + '\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print output to MySQL directory
                update_progress(50, "Switched to root user...")
                
                # Check MySQL service status
                ssh_shell.send('service mysqld status\n')
                time.sleep(2)  # Adjust sleep time based on command execution time
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(70, "Checked MySQL status...")
                
                # Read output to determine MySQL status
                if 'running' in output.lower() and 'pid' in output.lower():
                    # MySQL is running, show message and disable "Run MySQL" button
                    messagebox.showinfo("MySQL Status", "MySQL is running.")
                    run_mysql_btn.config(state=tk.DISABLED)
                else:
                    # MySQL is not running, show message and enable "Run MySQL" button
                    messagebox.showwarning("MySQL Status", "MySQL is not running.")
                    run_mysql_btn.config(state=tk.NORMAL)
                
                # Close SSH connection
                ssh_client.close()
                update_progress(100, "Operation completed.")
                
            except Exception as e:
                print(f"Error during SSH operation: {str(e)}")
                messagebox.showerror("Error", f"SSH operation failed: {str(e)}")
            return

    messagebox.showerror("Error", "Invalid location code")
    update_progress(0, "")


def run_mysql():
    """ Attempt to SSH into the specified location and start MySQL service. """
    reset_progress()
    location_code = entry.get().strip()
    update_progress(10, "Starting SSH connection...")
    for category in ip_addresses.values():
        super_center = category.get(location_code)
        if super_center:
            ip = super_center['ip']
            username = 'rpdadmin'
            password = 'nilkamal'
            root_password = 'nilkamal'  # Replace with your actual root password
            
            try:
                # Establish SSH connection
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(ip, username=username, password=password, timeout=5)
                update_progress(30, "SSH connection established...")
                
                # Open a shell session
                ssh_shell = ssh_client.invoke_shell()
                
                # Wait for a moment to let the shell start
                time.sleep(1)
                
                # Send 'su' command to switch to root
                ssh_shell.send('su\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                
                ssh_shell.send(root_password + '\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(50, "Switched to root user...")
                
                # Clear any initial outputs
                while ssh_shell.recv_ready():
                    ssh_shell.recv(65535)
                
                # Check date on the server
                ssh_shell.send('date\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current date and time
                
                current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Set server date if it doesn't match current date
                if output.strip() != current_date:
                    ssh_shell.send(f'date -s "{current_date}"\n')
                    time.sleep(1)
                    output = ssh_shell.recv(65535).decode('utf-8')
                    print(output.strip())  # Print set date command output
                
                # Remove mysql.sock file if exists
                ssh_shell.send('rm -f /var/lib/mysql/mysql.sock\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(70, "Removed mysql.sock if exists...")
                
                # Start MySQL service
                ssh_shell.send('service mysqld start\n')
                time.sleep(2)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                
                # Check MySQL service status
                ssh_shell.send('service mysqld status\n')
                time.sleep(2)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(90, "Checked MySQL status...")
                
                if 'running' in output.lower() and 'pid' in output.lower():
                    messagebox.showinfo("MySQL Status", "MySQL started successfully.")
                else:
                    messagebox.showwarning("MySQL Status", "Failed to start MySQL.")
                    
                
                # Close SSH connection
                ssh_client.close()
                update_progress(100, "Operation completed.")
                
            except Exception as e:
                print(f"Error during SSH operation: {str(e)}")
                messagebox.showerror("Error", f"SSH operation failed: {str(e)}")
            return

    messagebox.showerror("Error", "Invalid location code")
    update_progress(0, "")

def reset_application():
    """ Reset the entire application to its initial state. """
    entry.delete(0, tk.END)
    result_label.config(text="")
    try_btn.config(state=tk.DISABLED)
    run_mysql_btn.config(state=tk.DISABLED)
    reset_progress()

def server_down():
    """ Simulate server down scenario for testing purposes. """
    
    reset_progress()
    location_code = entry.get().strip()
    update_progress(10, "Starting SSH connection...")
    for category in ip_addresses.values():
        super_center = category.get(location_code)
        if super_center:
            ip = super_center['ip']
            username = 'rpdadmin'
            password = 'nilkamal'
            root_password = 'nilkamal'  # Replace with your actual root password
            
            try:
                # Establish SSH connection
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(ip, username=username, password=password, timeout=5)
                update_progress(30, "SSH connection established...")
                
                # Open a shell session
                ssh_shell = ssh_client.invoke_shell()
                
                # Wait for a moment to let the shell start
                time.sleep(1)
                
                # Send 'su' command to switch to root
                ssh_shell.send('su\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(40, "Switched to root user...")
                
                ssh_shell.send(root_password + '\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(50, "Enter root password...")
                
                # Clear any initial outputs
                while ssh_shell.recv_ready():
                    ssh_shell.recv(65535)
                                
                # Goto Mysql root path
                ssh_shell.send('cd /var/lib/mysql\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(70, "Goto Mysql root path")   
                 
                # Goto Server down
                ssh_shell.send('init 0\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(90, "Goto Server down")    
                
                # After completing the process, show a message box
                messagebox.showinfo("Process Complete", "Serverdown process done. Server is down.")
                           
                # After completing the process, print "serverdown process done"
                print("Server is down")                              
                
                # Close SSH connection
                ssh_client.close()
                update_progress(100, "Operation completed.")
                
            except Exception as e:
                print(f"Error during SSH operation: {str(e)}")
                messagebox.showerror("Error", f"SSH operation failed: {str(e)}")
            return

    messagebox.showerror("Error", "Invalid location code")
    update_progress(0, "")

def restart_mysql():
    """ Attempt to restart MySQL service on the specified location. """
    reset_progress()
    location_code = entry.get().strip()
    update_progress(10, "Starting SSH connection...")
    for category in ip_addresses.values():
        super_center = category.get(location_code)
        if super_center:
            ip = super_center['ip']
            username = 'rpdadmin'
            password = 'nilkamal'
            root_password = 'nilkamal'  # Replace with your actual root password
            
            try:
                # Establish SSH connection
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(ip, username=username, password=password, timeout=5)
                update_progress(10, "SSH connection established...")
                
                # Open a shell session
                ssh_shell = ssh_client.invoke_shell()
                
                # Wait for a moment to let the shell start
                time.sleep(1)
                
                # Send 'su' command to switch to root
                ssh_shell.send('su\n')

                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(20, "Switched to root user...")
                
                # Send 'root' password
                ssh_shell.send(root_password + '\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(30, "Switched to root password...")
                
                # Clear any initial outputs
                while ssh_shell.recv_ready():
                    ssh_shell.recv(65535)
                    
                # Go to MySQL root path
                ssh_shell.send('cd /var/lib/mysql\n')
                time.sleep(1)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(50, "Goto Mysql root path")      
                
                # Restart MySQL service
                ssh_shell.send('service mysqld restart\n')
                time.sleep(2)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(70, "Restarting MySQL service...")
                
                # Check MySQL service status
                ssh_shell.send('service mysqld status\n')
                time.sleep(2)
                output = ssh_shell.recv(65535).decode('utf-8')
                print(output.strip())  # Print current status
                update_progress(90, "Checked MySQL status...")
                
                if 'running' in output.lower() and 'pid' in output.lower():
                    messagebox.showinfo("MySQL Status", "MySQL restarted successfully.")
                else:
                    messagebox.showwarning("MySQL Status", "Failed to restart MySQL.")
                    
                # Close SSH connection
                ssh_client.close()
                update_progress(100, "Operation completed.")
                
            except Exception as e:
                print(f"Error during SSH operation: {str(e)}")
                messagebox.showerror("Error", f"SSH operation failed: {str(e)}")
            return

    messagebox.showerror("Error", "Invalid location code")
    update_progress(0, "")

def toggle_buttons_visibility():
    if switch_var1.get():  # Check if switch_var1 (the toggle variable) is True (ticked)
        response = messagebox.askyesno("Toggle Buttons", "Do you want to make the buttons visible?")
        if response:  # User clicked Yes
            # Keep the toggle (tick) active and make buttons visible
            server_down_btn.grid()
            restart_mysql_btn.grid()
        else:  # User clicked No
            # Untick the toggle and make buttons invisible
            switch_var1.set(False)
            server_down_btn.grid_remove()
            restart_mysql_btn.grid_remove()
    else:  # switch_var1 is False (unticked)
        response = messagebox.askyesno("Toggle Buttons", "Do you want to make the buttons invisible?")
        if response:  # User clicked Yes
            # Tick the toggle and make buttons visible
            switch_var1.set(False)
            server_down_btn.grid_remove()
            restart_mysql_btn.grid_remove()
        else:
            switch_var1.set(True)
            server_down_btn.grid()
            restart_mysql_btn.grid()
            # User clicked No
            # Keep the toggle off (untick) and keep buttons invisible
            # No action needed as per requirement
            pass

# Create the main window
root = ttk.Window(themename="litera")
root.title("Network Checker")
root.geometry("410x480")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(pady=10)

# Input and Actions frame
input_and_button_frame = ttk.Labelframe(main_frame, text="Input and Actions", padding=10)
input_and_button_frame.grid(row=0, column=0, pady=5, padx=5, sticky="w")

input_frame = ttk.Frame(input_and_button_frame)
input_frame.grid(row=0, column=0, pady=5, sticky="w")

ttk.Label(input_frame, text="Enter Location Code").grid(row=0, column=0, pady=5, sticky="w")
entry = ttk.Entry(input_frame, width=20)
entry.grid(row=1, column=0, pady=5)

button_frame = ttk.Frame(input_and_button_frame)
button_frame.grid(row=1, column=0, pady=5, sticky="w")

check_btn = ttk.Button(button_frame, text="Check Network", command=check_network, style="SUCCESS.TButton")
check_btn.grid(row=0, column=0, pady=5, padx=5)

try_btn = ttk.Button(button_frame, text="MySQL Status", command=check_mysql_status, style="INFO.TButton", state=tk.DISABLED)
try_btn.grid(row=0, column=1, pady=5, padx=5)

run_mysql_btn = ttk.Button(button_frame, text="Run MySQL", command=run_mysql, style="WARNING.TButton", state=tk.DISABLED)
run_mysql_btn.grid(row=0, column=2, pady=5, padx=5)

# Action frame with buttons and switch button
action_buttons_frame = ttk.Labelframe(main_frame, text="Actions", padding=10)
action_buttons_frame.grid(row=1, column=0, pady=4, padx=5, sticky="w")

# Set the width of all action buttons
button_width = 12

reset_btn = ttk.Button(action_buttons_frame, text="Reset", command=reset_application, style="WARNING.TButton", width=button_width)
reset_btn.grid(row=0, column=0, pady=5, padx=5)

server_down_btn = ttk.Button(action_buttons_frame, text="Server Down", command=server_down, style="DANGER.TButton", width=button_width)
server_down_btn.grid(row=0, column=1, pady=5, padx=5)
server_down_btn.grid_remove()  # Initially hidden

restart_mysql_btn = ttk.Button(action_buttons_frame, text="Restart MySQL", command=restart_mysql, style="PRIMARY.TButton", width=button_width)
restart_mysql_btn.grid(row=0, column=2, pady=5, padx=5)
restart_mysql_btn.grid_remove()  # Initially hidden

# Switch button
switch_var1 = tk.BooleanVar(value=False)

switch_btn1 = ttk.Checkbutton(action_buttons_frame, text="On|Off", variable=switch_var1, style="Switch.TCheckbutton", command=toggle_buttons_visibility)
switch_btn1.grid(row=1, column=0, pady=5, padx=5, columnspan=2, sticky="w")

result_label = ttk.Label(main_frame, text="")
result_label.grid(row=2, column=0, pady=5)

# Progress frame
progress_frame = ttk.Labelframe(main_frame, text="Progress", padding=10)
progress_frame.grid(row=3, column=0, padx=5, pady=(2, 3), sticky="w")

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=310, mode="determinate", variable=progress_var, maximum=100)
progress_bar.grid(row=0, column=0, pady=5, padx=5)

process_details_label = ttk.Label(progress_frame, text="Devoloped by Harsha")
process_details_label.grid(row=1, column=0, pady=5)

root.mainloop()