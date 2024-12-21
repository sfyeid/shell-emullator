from io import BytesIO
import os
import zipfile
import csv
import xml.etree.ElementTree as ET
import sys
import time

class ShellEmulator:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.vfs_path = self.config['vfs_path']
        self.log_path = self.config['log_path']
        self.startup_script_path = self.config['startup_script']
        
        self.user_name = self.config.get('user_name', 'user')
        self.host_name = self.config.get('host_name', 'localhost')
        self.current_dir = 'vfs/'
            
        if isinstance(self.vfs_path, (str, bytes, os.PathLike)):
            
            self.zip = zipfile.ZipFile(self.vfs_path, "r")
        else:
            
            self.zip = zipfile.ZipFile(fileobj=self.vfs_path, mode="r")

        
        self.file_system = self.load_vfs()

    def load_config(self, config_path):
        """Load configuration from a CSV file."""
        with open(config_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                return row

    def log_action(self, action):
        """Log actions to the XML log file with timestamps."""
        root = ET.Element("log")
        action_elem = ET.SubElement(root, "action")
        action_elem.text = action
        timestamp_elem = ET.SubElement(action_elem, "timestamp")
        timestamp_elem.text = time.strftime("%Y-%m-%d %H:%M:%S")

        tree = ET.ElementTree(root)
        with open(self.log_path, 'ab') as log_file:
            tree.write(log_file, encoding='utf-8', xml_declaration=False)

    def load_vfs(self):
        """Load virtual file system from the zip archive."""
        fs = {}
        for member in self.zip.infolist():
            fs[member.filename] = member
        return fs

    def prompt(self):
        """Return the shell prompt."""
        return f"{self.user_name}@{self.host_name}:{self.current_dir}$ "

    def execute_command(self, command):
        """Parse and execute the entered shell command."""
        parts = command.strip().split()
        if not parts:
            return ""
        cmd, *args = parts

        if cmd == "ls":
            return self.ls()
        elif cmd == "cd":
            return self.cd(args[0] if args else "/")
        elif cmd == "echo":
            return self.echo(" ".join(args))
        elif cmd == "cp":
            return self.cp(args[0], args[1])
        elif cmd == "cat":
            return self.cat(args[0])
        elif cmd == "exit":
            self.exit_emulator()
        else:
            return f"Command not found: {cmd}"

    def ls(self):
        """List directory contents."""
        contents = []
        if not self.current_dir.endswith('/'):
            self.current_dir += '/'
    
        for name in self.file_system:
            if name.startswith(self.current_dir) and name != self.current_dir:
                
                relative_path = name[len(self.current_dir):].strip('/')
                
                
                if '/' not in relative_path and not relative_path.startswith('.'):
                    contents.append(relative_path)
                elif '/' in relative_path:
                    contents.append(relative_path.split('/')[0])
    
        return "\n".join(sorted(set(contents))) if contents else "Empty directory"

    def cd(self, path):
        """Change directory."""
        if path == '/':
            self.current_dir = 'vfs/'
        else:
            
            if not path.endswith('/'):
                path += '/'
            
            new_path = os.path.join(self.current_dir, path)
            
            if any(name.startswith(new_path) for name in self.file_system.keys()):
                self.current_dir = new_path
            else:
                return f"No such directory: {path.strip('/')}"
        
        return ""

    def echo(self, text):
        """Echo the provided text."""
        return text

    def cp(self, source, destination):
        """Copy a file from source to destination."""
        source_path = os.path.join(self.current_dir, source)
        destination_path = os.path.join(self.current_dir, destination)
    
        if source_path not in self.file_system:
            return f"No such file: {source}"
        if destination_path in self.file_system:
            return f"Destination file already exists: {destination}"
    
        source_file = self.file_system[source_path]
        source_data = self.zip.read(source_file)
    
        
        with zipfile.ZipFile(self.vfs_path, 'a') as zipf:
            zipf.writestr(destination_path, source_data)
        self.file_system[destination_path] = zipfile.ZipInfo(destination_path)
    
        
        self.zip = zipfile.ZipFile(self.vfs_path, "r")
    
        return f"Copied {source} to {destination}"

    def cat(self, file_name):
        """Display the contents of a file."""
        file_path = os.path.join(self.current_dir, file_name)
    
        if file_path not in self.file_system:
            return f"No such file: {file_name}"
    
        with self.zip.open(file_path) as file:
            return file.read().decode('utf-8')

    def exit_emulator(self):
        """Exit the shell emulator."""
        print("Exiting the shell emulator.")
        sys.exit(0)

    def run_startup_script(self):
        """Run commands from the startup script."""
        with open(self.startup_script_path, 'r') as script_file:
            for command in script_file:
                command = command.strip()
                if command:  
                    self.execute_command(command)


def main():
    """Entry point for the shell emulator."""
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_config.csv>")
        sys.exit(1)

    config_path = sys.argv[1]
    emulator = ShellEmulator(config_path)

    while True:
        command = input(emulator.prompt())
        output = emulator.execute_command(command)
        if output:
            print(output)


if __name__ == "__main__":
    main()