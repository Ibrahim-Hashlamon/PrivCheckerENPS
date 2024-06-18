import os
import sys
import tkinter as tk
from tkinter import messagebox
import logging

# Configure logging
logging.basicConfig(filename='priv_checker.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def find_workdrive():
    hostname = os.environ.get("COMPUTERNAME")
    if not hostname:
        logging.error("Failed to retrieve COMPUTERNAME environment variable")
        return None

    drives = [chr(x) + ":" for x in range(65, 91) if os.path.exists(chr(x) + ":")]
    workdrive = None
    for drive in drives:
        if drive.startswith(("D", "F")) and os.path.exists(os.path.join(drive, hostname)):
            workdrive = drive
            break
    if not workdrive:
        logging.warning("Work drive D: or F: not found or no directory matching the hostname found.")
    return workdrive

def convert_utf16_to_ansi(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-16-le') as f:
            content = f.read()

        if content.startswith('\ufeff'):
            content = content[1:]

        with open(output_file, 'w', encoding='cp1252') as f:
            f.write(content)
    except Exception as e:
        logging.error(f"Error converting file {input_file} to ANSI: {e}")

def write_header(file_path):
    header = "The following User IDs were present in the Privileges table but absent in the Staff Table\n"
    underline = "=" * (len(header) - 1) + "\n"
    try:
        with open(file_path, 'w') as file:
            file.write(header)
            file.write(underline)
    except Exception as e:
        logging.error(f"Error writing header to file {file_path}: {e}")

def get_unique_file_path(base_path):
    counter = 1
    while os.path.exists(f"{base_path}{counter}.txt"):
        counter += 1
    return f"{base_path}{counter}.txt"

def main():
    # Set up logging
    logging.info("Starting Privilege Checker")

    logged_in_user = os.getlogin()
    temp_dir = os.path.join("C:\\Users", logged_in_user, "temp")
    try:
        os.makedirs(temp_dir, exist_ok=True)
    except Exception as e:
        logging.error(f"Error creating temp directory: {e}")

    workdrive = find_workdrive()
    if not workdrive:
        logging.error("Work drive D: or F: not found or no directory matching the hostname found.")
        return

    hostname = os.environ.get("COMPUTERNAME")
    if not hostname:
        logging.error("Failed to retrieve COMPUTERNAME environment variable")
        return

    g_staff_input = os.path.join(workdrive, "COMMON", "G_SUPPORT", "G_STAFF")
    g_staff_output = os.path.join(temp_dir, "G_STAFF.txt")
    convert_utf16_to_ansi(g_staff_input, g_staff_output)

    with open(g_staff_output, 'r', encoding='cp1252') as f:
        g_staff_ids = [line.split()[0] for line in f]

    s_priv_dir = os.path.join(workdrive, hostname, "S_PRIV")
    grouplist = os.listdir(s_priv_dir)
    mismatches_found = False
    base_file_path = os.path.join("C:\\Users", logged_in_user, "Desktop", "PrivChecker")
    file_path = get_unique_file_path(base_file_path)

    for groupname in grouplist:
        input_file = os.path.join(s_priv_dir, groupname)
        output_file = os.path.join(temp_dir, f"{groupname}.txt")
        convert_utf16_to_ansi(input_file, output_file)

        with open(output_file, 'r', encoding='cp1252') as f:
            tempstaff_ids = [line.split()[0] for line in f]

        for staff_id in tempstaff_ids:
            if staff_id not in g_staff_ids:
                if not mismatches_found:
                    mismatches_found = True
                    write_header(file_path)
                try:
                    with open(file_path, 'a') as mismatch_file:
                        mismatch_file.write(f"{staff_id} in group: {groupname}\n")
                except Exception as e:
                    logging.error(f"Error writing mismatch info to file: {e}")

    if not mismatches_found:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("No Mismatches", "No mismatches found.")
    else:
        if os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                logging.error(f"Error opening file: {e}")

    try:
        os.remove(g_staff_output)
        for groupname in grouplist:
            os.remove(os.path.join(temp_dir, f"{groupname}.txt"))
        os.rmdir(temp_dir)
    except Exception as e:
        logging.error(f"Error cleaning up temp files and directories: {e}")

    logging.info("Privilege Checker finished")

if __name__ == "__main__":
    main()
