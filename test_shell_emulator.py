import unittest
import zipfile
import os
from io import BytesIO
from main import ShellEmulator  

class TestShellEmulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        
        cls.vfs_zip = BytesIO()
        with zipfile.ZipFile(cls.vfs_zip, mode='w') as zipf:
            
            zipf.writestr("vfs/folder1/", "")
            zipf.writestr("vfs/folder1/file1.txt", "Hello World\n")
            zipf.writestr("vfs/folder2/", "")
            zipf.writestr("vfs/folder2/file2.txt", "Second File\n")

        cls.vfs_zip.seek(0)

        cls.config_path = "test_config.csv"
        with open(cls.config_path, 'w') as f:
            f.write("vfs_path,log_path,startup_script\n")
            f.write("test_vfs.zip,test_log.xml,test_startup.sh\n")

        
        with open("test_vfs.zip", 'wb') as f:
            f.write(cls.vfs_zip.getvalue())

        
        cls.startup_script_path = "test_startup.sh"
        with open(cls.startup_script_path, 'w') as f:
            f.write("#!/bin/bash\necho 'Startup script executed'\n")

    def setUp(self):
        self.emulator = ShellEmulator(self.config_path)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.config_path)
        os.remove("test_vfs.zip")
        os.remove(cls.startup_script_path)

    def test_ls_root(self):
        output = self.emulator.ls()
        
        self.assertIn("folder1", output)
        self.assertIn("folder2", output)

    def test_ls_folder1(self):
        self.emulator.cd("folder1")
        output = self.emulator.ls()
        
        self.assertIn("file1.txt", output)
    
    def test_cd_valid(self):
        self.emulator.cd("folder1")
        self.assertEqual(self.emulator.current_dir, "vfs/folder1/")

    def test_cd_invalid(self):
        output = self.emulator.cd("invalid_folder")
        self.assertEqual(output, "No such directory: invalid_folder")
        
    def test_cp_valid(self):
        output = self.emulator.cp("folder1/file1.txt", "file3.txt")
        self.assertEqual(output, "Copied folder1/file1.txt to file3.txt")
        self.assertIn("file3.txt", self.emulator.ls())
        
    def test_cp_invalid_source(self):
        output = self.emulator.cp("invalid_file.txt", "file3.txt")
        self.assertEqual(output, "No such file: invalid_file.txt")
        
    def test_cat_valid(self):
        output = self.emulator.cat("folder1/file1.txt")
        self.assertEqual(output, "Hello World\n")
        
    def test_cat_invalid(self):
        output = self.emulator.cat("invalid_file.txt")
        self.assertEqual(output, "No such file: invalid_file.txt")
        
    def test_echo(self):
        output = self.emulator.echo("Hello World")
        self.assertEqual(output, "Hello World")
        
if __name__ == '__main__':
    unittest.main()