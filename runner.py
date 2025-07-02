import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import pandas as pd
import datetime
import sys
import shutil
import time
import csv
import configparser

TK_SILENCE_DEPRECATION=1

def check_for_updates_and_restart():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(repo_dir, "config.ini")
    try:
        # Fetch latest changes
        fetch_output = subprocess.check_output(
            ["git", "fetch"],
            cwd=repo_dir,
            stderr=subprocess.STDOUT,
            text=True
        )
        # Get last update time (before pull)
        last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Check if local HEAD is behind origin
        status_output = subprocess.check_output(
            ["git", "status", "-uno"],
            cwd=repo_dir,
            stderr=subprocess.STDOUT,
            text=True
        )
        if "Your branch is behind" in status_output or "have diverged" in status_output:
            # Pull updates
            pull_output = subprocess.check_output(
                ["git", "pull"],
                cwd=repo_dir,
                stderr=subprocess.STDOUT,
                text=True
            )
            print("Repository updated:\n", pull_output)
            # Save last update time to config
            config = configparser.ConfigParser()
            config.read(config_path)
            config["DEFAULT"]["LAST_UPDATE"] = last_update
            with open(config_path, "w") as configfile:
                config.write(configfile)
            # Restart the script
            if messagebox.askokcancel("Restart Required", "Updates have been applied. The application needs to restart.\n\nClick OK to exit. Please relaunch the app manually."):
                sys.exit(0)
        else:
            # Save last update time only if not already set
            config = configparser.ConfigParser()
            config.read(config_path)
            if not config["DEFAULT"].get("LAST_UPDATE"):
                config["DEFAULT"]["LAST_UPDATE"] = last_update
                with open(config_path, "w") as configfile:
                    config.write(configfile)
    except Exception as e:
        print(f"Update check failed: {e}")

check_for_updates_and_restart()

# GitLab login using username and password (for HTTPS)
def gitlab_login(username, password):
    try:
        # Set credentials for git using subprocess
        subprocess.check_call([
            "git", "config", "--global", "credential.helper", "store"
        ])
        # Store credentials in the format required by git-credential-store
        home = os.path.expanduser("~")
        cred_path = os.path.join(home, ".git-credentials")
        with open(cred_path, "w") as cred_file:
            cred_file.write(f"https://{username}:{password}@cicd-gitlab-ee.telkomsel.co.id\n")
        return True
    except Exception as e:
        print(f"GitLab login failed: {e}")
        return False

# Load configuration from config.ini in the same directory as this script
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
config.read(config_path)
defaultHeaderConfig = "DEFAULT"
CONFIG_GIT_PREFIX_URL = config.get(defaultHeaderConfig, "GIT_PREFIX_URL", fallback="")
FOLDER_REPOSITORIES = config.get(defaultHeaderConfig, "FOLDER_REPOSITORIES", fallback="repositories")
FOLDER_HTML_REPORT = config.get(defaultHeaderConfig, "FOLDER_HTML_REPORT", fallback="html_reports")
FOLDER_CSV = config.get(defaultHeaderConfig, "FOLDER_CSV", fallback="csv")
FOLDER_OUTPUT = config.get(defaultHeaderConfig, "FOLDER_OUTPUT", fallback="log")

full_repositories_path = os.path.join(os.getcwd(), FOLDER_REPOSITORIES)
repository = None

# TODO Fix the PATH environment variable to include the necessary paths for newman and git
# Print the PATH environment variable as seen by the terminal (by running a shell)
# os.environ["PATH"] = "/Users/muhammad.l.pradana/.pyenv/versions/3.8.12/bin:/Users/muhammad.l.pradana/.rbenv/shims:/Users/muhammad.l.pradana/.rbenv/shims:/Users/muhammad.l.pradana/.pyenv/shims:/Users/muhammad.l.pradana/bin:/Users/muhammad.l.pradana/flutter/bin:/Users/muhammad.l.pradana/.pyenv/versions/3.8.12/bin:/Library/Frameworks/Python.framework/Versions/3.11/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/Library/Apple/usr/bin:/Applications/VMware Fusion.app/Contents/Public:/Users/muhammad.l.pradana/.pyenv/versions/3.8.12/bin:/Users/muhammad.l.pradana/.rbenv/shims:/Users/muhammad.l.pradana/bin:/Users/muhammad.l.pradana/flutter/bin:/Library/Frameworks/Python.framework/Versions/3.11/bin"
# def get_terminal_path():
#     try:
#         # Use login shell to get the PATH as the terminal would see it
#         output = subprocess.check_output(
#             ["/bin/bash", "-l", "-c", "echo $PATH"],
#             stderr=subprocess.STDOUT,
#             text=True
#         )
#         return output.strip()
#     except Exception as e:
#         return f"Error getting PATH: {e}"
# def get_newman_version():
#     try:
#         output = subprocess.check_output(
#             ["newman", "--version"],
#             stderr=subprocess.STDOUT,
#             text=True
#         )
#         return output.strip()
#     except Exception as e:
#         return f"Error getting Newman version: {e}"
# print("PATH from terminal:", get_terminal_path())
# print("Newman version:", get_newman_version())
# def run_script():
#     script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "script.sh")
#     try:
#         output = subprocess.check_output(
#             ["bash", script_path],
#             stderr=subprocess.STDOUT,
#             text=True
#         )
#         print(output.strip())
#         return output.strip()
#     except subprocess.CalledProcessError as e:
#         print(f"Error: {e.output.strip()}")
#         return f"Error: {e.output.strip()}"
# run_script()  # Call the script to ensure it runs at startup

class DashboardPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        # Show last update from config, centered
        # Create a frame to center the label
        center_frame = tk.Frame(self)
        center_frame.pack(expand=True)
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        config = configparser.ConfigParser()
        config.read(config_path)
        last_update = config.get("DEFAULT", "LAST_UPDATE", fallback="")
        label = tk.Label(center_frame, text=f"Last Update: {last_update}")
        label.pack(pady=(10, 0))
        # Center the frame in the parent
        center_frame.pack_configure(anchor='center')

class ReposPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Add repository (moved to top)
        add_frame = tk.Frame(self)
        add_frame.pack(fill='x', pady=5)
        tk.Label(add_frame, text="Add Repository:").pack(side='left', padx=(0, 5))
        self.repo_name_var = tk.StringVar()
        repo_entry = tk.Entry(add_frame, textvariable=self.repo_name_var)
        repo_entry.pack(side='left', fill='x', expand=True)
        tk.Button(add_frame, text="Fetch", command=self.add_repository).pack(side='left', padx=5)

        # Search bar
        search_frame = tk.Frame(self)
        search_frame.pack(fill='x', pady=5)
        tk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.update_list)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side='left', fill='x', expand=True)

        # Listbox for repositories
        self.repo_listbox = tk.Listbox(self)
        self.repo_listbox.pack(fill='both', expand=True, pady=10)
        self.repo_listbox.bind("<<ListboxSelect>>", self.on_repo_select)

        # Sync info label (moved to bottom, expanded width, scrollable)
        self.sync_info_var = tk.StringVar(value="")
        sync_frame = tk.Frame(self)
        sync_frame.pack(fill='x', pady=10)
        self.sync_info_label = tk.Text(sync_frame, height=4, wrap='word')
        self.sync_info_label.pack(side='left', fill='x', expand=True)
        self.sync_info_label.insert('1.0', self.sync_info_var.get())
        self.sync_info_label.config(state='disabled')
        
        # Add a vertical scrollbar
        sync_scroll = tk.Scrollbar(sync_frame, orient='vertical', command=self.sync_info_label.yview)
        sync_scroll.pack(side='right', fill='y')
        self.sync_info_label['yscrollcommand'] = sync_scroll.set
        
        # Hide sync_info_label initially
        self.sync_info_label.pack_forget()
        sync_scroll.pack_forget()

        # Update sync_info_label when sync_info_var changes
        def update_sync_info(*args):
            self.sync_info_label.config(state='normal')
            self.sync_info_label.delete('1.0', tk.END)
            self.sync_info_label.insert('1.0', self.sync_info_var.get())
            self.sync_info_label.config(state='disabled')
        self.sync_info_var.trace_add('write', update_sync_info)

        self.repositories_folder = full_repositories_path
        self.update_list()
        
    def on_repo_select(self, event):
        selection = self.repo_listbox.curselection()
        if selection:
            repo_name = self.repo_listbox.get(selection[0])
            global repository
            repository = repo_name
            self.controller.show_page("TestExec")
            self.controller.pages["TestExec"].update_list()
            
    def focus_search(self):
        self.search_entry.focus_set()

    def get_repositories(self):
        if not os.path.exists(self.repositories_folder):
            os.makedirs(self.repositories_folder)
        return [
            name for name in os.listdir(self.repositories_folder)
            if os.path.isdir(os.path.join(self.repositories_folder, name))
        ]

    def update_list(self, *args):
        search = self.search_var.get().lower()
        repos = self.get_repositories()
        filtered = [r for r in repos if search in r.lower()]
        self.repo_listbox.delete(0, tk.END)
        for repo in filtered:
            self.repo_listbox.insert(tk.END, repo)

    def add_repository(self):
        repo_name = self.repo_name_var.get().strip()
        if repo_name:
            git_url = f"https://cicd-gitlab-ee.telkomsel.co.id/telkomsel/TSEL-DC-ESB/automation-test/{repo_name}"
 
            repo_path = os.path.join(self.repositories_folder, repo_name)
            try:
                result = subprocess.check_output(
                    ['git', 'clone', git_url, repo_path],
                    stderr=subprocess.STDOUT,
                    text=True
                )
                self.sync_info_var.set(result.strip())
                repository = repo_name
                self.controller.show_page("TestExec")
                self.controller.pages["TestExec"].update_list()
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Clone Error", f"Error cloning repository:\n{e.output.strip()}")
                self.sync_info_var.set(f"Error cloning repository:\n{e.output.strip()}")
            self.update_list()
            self.repo_name_var.set("")

class TestExecPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Initialize selected_excel variable
        self.selected_excel = None
        
        # Add selected repository title label
        self.repo_title_var = tk.StringVar(value="No repository selected")
        self.repo_title_label = tk.Label(self, textvariable=self.repo_title_var, font=("Arial", 14, "bold"))
        self.repo_title_label.pack(pady=(10, 0))
        
        # Search bar
        search_frame = tk.Frame(self)
        search_frame.pack(fill='x', pady=5)
        tk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.update_list)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side='left', fill='x', expand=True)

        # Listbox for Excel files
        self.excel_listbox = tk.Listbox(self)
        self.excel_listbox.pack(fill='both', expand=True, pady=10)
        self.selected_excel = None
        self.excel_listbox.bind("<<ListboxSelect>>", self.on_excel_select)

        # Buttons
        tk.Button(self, text="Run Test Data", command=self.run_test_data).pack(pady=10)
        
        # Progress bar for execution (initially hidden)
        self.progress_var = tk.DoubleVar(value=0)
        progress_frame = tk.Frame(self)
        progress_frame.pack(pady=10, fill='x')
        # Progress label for execution (initially hidden)
        self.execution_progress_label = tk.Label(progress_frame, text="Execution Progress")
        self.execution_progress_label.pack(anchor='w')
        self.progress_bar = tk.Canvas(progress_frame, height=22, bg='white', highlightthickness=1, highlightbackground='gray')
        self.progress_bar.pack(fill='x', padx=10, pady=5)
        self.progress_rect = self.progress_bar.create_rectangle(0, 0, 0, 22, fill='green')
        self.progress_label = tk.Label(progress_frame, text="0%")
        self.progress_label.pack(anchor='w', padx=10)

        # Hide progress bar and label at first
        self.hide_progress_bar()

        self.update_list()
        
    def focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)

    def update_repo_title(self):
        if repository:
            self.repo_title_var.set(f"Repository: {repository}")
        else:
            self.repo_title_var.set("No repository selected")

    def hide_progress_bar(self):
        self.execution_progress_label.pack_forget()
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        
    def show_progress_bar(self):
        self.execution_progress_label.pack(anchor='w')
        self.progress_bar.pack(fill='x', padx=10, pady=5)
        self.progress_label.pack(anchor='w', padx=10)
        # Reset progress bar
        # self.progress_bar.coords(self.progress_rect, 0, 0, 0, 22)
        # self.progress_label.config(text="0%")
        
    def on_excel_select(self, event):
        selection = self.excel_listbox.curselection()
        if selection:
            self.selected_excel = self.excel_listbox.get(selection[0])
        else:
            self.selected_excel = None
    
    def run_test_data(self):
        selection = self.excel_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an Excel file to run.")
            return
        file_name_with_path = self.excel_listbox.get(selection[0])
        file_name = os.path.basename(file_name_with_path)
        
        # Create 'csv' folder inside the repository if it doesn't exist
        repo_path = os.path.join(full_repositories_path, repository)
        csv_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv")
        os.makedirs(csv_folder, exist_ok=True)

        # Convert selected Excel file to CSV in the 'csv' folder
        excel_file_path = os.path.join(repo_path, file_name_with_path)
        csv_file_name = os.path.splitext(os.path.basename(file_name_with_path))[0] + ".csv"
        csv_file_path = os.path.join(csv_folder, csv_file_name)
        print(f"Excel file path: {excel_file_path}")
        print(f"CSV file path: {csv_file_path}")
        self.excel_to_csv(excel_file_path, csv_file_path)
        
        # Prepare variables for the newman command
        suffix_collection = ".postman_collection.json"
        suffix_environment = ".postman_environment.json"
        # Find the collection file in the repository
        # Look for the collection file in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        collection_file = None
        for f in os.listdir(script_dir):
            if f.endswith(suffix_collection):
                collection_file = f
                break
        if not collection_file:
            messagebox.showerror("Collection Not Found", f"No collection file (*{suffix_collection}) found in the script directory.")
            return
        # Remove the suffix_collection from the end if present
        if collection_file.endswith(suffix_collection):
            collection_name = collection_file[:-len(suffix_collection)]
        else:
            collection_name = os.path.splitext(collection_file)[0]
        
        suffix_output = ".txt"

        # Folders (adjust as needed)
        newman_folder = os.path.join(os.getcwd(), "html_reports")
        output_folder = os.path.join(os.getcwd(), "log")
        os.makedirs(newman_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

        # Date for report file
        date_created = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # Paths
        collection_path = collection_name + suffix_collection
        environment_path = collection_name + suffix_environment
        csv_path = os.path.join("csv", csv_file_name)
        report_path = os.path.join("html_reports", f"{collection_name}-{date_created}.html")
        output_path = os.path.join("log", f"{collection_name}{suffix_output}")

        # Build the newman command
        newman_cmd = [
            "newman", 
            "run", collection_path,
            "-e", environment_path,
            "--timeout-script=9999999",
            f"--iteration-data={csv_path}",
            "--insecure",
            "--reporters=htmlextra,cli",
            "--reporter-htmlextra-logs", "true",
            f"--reporter-htmlextra-export={report_path}"
            , f"> {output_path}"
        ]
        print("Running command:", " ".join(newman_cmd))

        # Run newman and redirect output to file using subprocess.run
        try:
            # Wait loop: check progress while process is running
            total_iterations = 0
            if os.path.exists(csv_file_path):
                try:
                    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                        total_iterations = sum(1 for row in reader) - 1  # minus header
                        if total_iterations < 1:
                            total_iterations = 1
                except Exception:
                    total_iterations = 1
            else:
                total_iterations = 1
                
            self.progress_label.config(text="0% (0/{})".format(total_iterations))
            self.progress_bar.coords(self.progress_rect, 0, 0, 0, 22)
            
            # Start the newman process
            process = subprocess.Popen(
                " ".join(newman_cmd),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Make progress bar visible
            self.show_progress_bar()
            
            # Continuously print the current iteration number until the process is complete
            current_iteration = 0
            while process.poll() is None:
                # Try to read the output file and count the number of completed iterations
                if os.path.exists(output_path):
                    try:
                        with open(output_path, "r", encoding="utf-8", errors="ignore") as outfile:
                            lines = outfile.readlines()
                            # Heuristic: count lines that look like iteration results
                            # (You may need to adjust this depending on your newman output format)
                            current_iteration = sum(1 for line in lines if "iteration " in line.lower())
                    except Exception:
                        pass
                percent = int((current_iteration / total_iterations) * 100) if total_iterations else 0
                self.progress_label.config(text=f"{percent}% ({current_iteration}/{total_iterations})")
                bar_width = int(self.progress_bar.winfo_width() * percent / 100)
                self.progress_bar.coords(self.progress_rect, 0, 0, bar_width, 22)
                self.progress_bar.update_idletasks()
                self.progress_label.update_idletasks()
            
                # Update progress bar visually
                self.progress_bar.update()
                self.progress_label.update()
                time.sleep(0.5)

            result = process.wait()

            if result == 1:
                # Make progress bar full
                self.progress_label.config(text="100% ({}/{})".format(total_iterations, total_iterations))
                self.progress_bar.coords(self.progress_rect, 0, 0, self.progress_bar.winfo_width(), 22)
                self.progress_bar.update_idletasks()
                self.progress_label.update_idletasks()
                
                # Open the report file
                try:
                    if sys.platform == "darwin":
                        subprocess.call(["open", report_path])
                    elif sys.platform == "win32":
                        os.startfile(report_path)
                    else:
                        subprocess.call(["xdg-open", report_path])
                except Exception as e:
                    messagebox.showerror("Open Report Error", f"Could not open report file:\n{e}")
            else:
                with open(output_path, "r", encoding="utf-8", errors="ignore") as outfile:
                    error_output = outfile.read()
                messagebox.showerror(
                    "Newman Error",
                    f"Error running newman (exit code {result}):\n{error_output}"
                )
        except Exception as e:
            messagebox.showerror("Execution Error", f"An error occurred:\n{e}")

    def excel_to_csv(self, excel_file, csv_file):
        df = pd.read_excel(excel_file, sheet_name=0, engine=None)
        
        # Loop through every cell value in the DataFrame
        for column in df.columns:
            for index, value in df[column].items():
                if isinstance(value, str) and '\n' in value:
                    df.at[index, column] = value.replace('\n', '|')
        
        # Write the DataFrame to a CSV file
        df.to_csv(csv_file, index=False)

    def get_excel_files(self):
        if repository is None:
            messagebox.showinfo("No Repository Selected", "Please select a repository first.")
            return []
        repo_path = os.path.join(full_repositories_path, repository)
        if not os.path.isdir(repo_path):
            messagebox.showinfo("Repository Not Found", "The selected repository folder does not exist.")
            return []
        excel_files = []
        for root, dirs, files in os.walk(repo_path):
            for f in files:
                if f.lower().endswith('.xlsx'):
                    rel_dir = os.path.relpath(root, repo_path)
                    if rel_dir == ".":
                        display_name = f
                    else:
                        display_name = os.path.join(rel_dir, f)
                    excel_files.append(display_name)
        if not excel_files:
            messagebox.showinfo("No Excel Files", "No Excel (.xlsx) files found in the selected repository.")
        return excel_files

    def update_list(self, *args):
        search = self.search_var.get().lower()
        if repository is None:
            self.excel_listbox.delete(0, tk.END)
            return
        files = self.get_excel_files()
        filtered = [f for f in files if search in f.lower()]
        self.excel_listbox.delete(0, tk.END)
        self.selected_excel = None
        for f in filtered:
            self.excel_listbox.insert(tk.END, f)
        if filtered:
            self.excel_listbox.selection_set(0)
            self.excel_listbox.activate(0)
            self.on_excel_select(None)
            
        self.update_repo_title()
        self.hide_progress_bar()  # Hide progress bar when updating list

class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        tk.Label(self, text="Git Credential Management").pack(pady=10)
        tk.Label(self, text="Folder/Path Configuration").pack(pady=10)

class AutomationUI(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.title("Auto Runner")
        self.pack(fill='both', expand=True)
        self.create_widgets()
        # self.initialize()

    def initialize(self):
        self.parent.title("RUN ON START TEST")       
        self.parent.grid_rowconfigure(0,weight=1)
        self.parent.grid_columnconfigure(0,weight=1)
        self.parent.config(background="red") 

        self.frame = tk.Frame(self.parent)  
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        self.topEntry = tk.Entry(self.frame, background="#006600", foreground="#00ff00")
        self.topEntry.grid(column=0, row=1, sticky="ew")


        yesBut = tk.Button(self.frame, text="Yes")
        yesBut.grid(column=1, row=1)

        query = tk.Label(self.frame, foreground="#00ff00", background="#001a00", anchor="w")
        query.grid(column=1, row=0, columnspan=2, sticky="ew")

    def create_widgets(self):
        # Create a container for navigation buttons
        self.navbar = tk.Frame(self)
        self.navbar.pack(fill='x', pady=(10, 0))

        # Center the navigation buttons using an inner frame
        nav_inner = tk.Frame(self.navbar)
        nav_inner.pack(anchor='center')

        tk.Button(nav_inner, text="Dashboard", command=lambda: self.show_page("Dashboard")).pack(side='left', padx=5)
        tk.Button(nav_inner, text="Repositories", command=lambda: self.show_page("Repos")).pack(side='left', padx=5)
        tk.Button(nav_inner, text="Settings", command=lambda: self.show_page("Settings")).pack(side='left', padx=5)

        # Back button (initially hidden)
        self.back_btn = tk.Button(self, text="Back", command=self.back)
        # Do not pack the back button yet

        # Container for pages
        container = tk.Frame(self, bg="red")
        container.pack(fill='both', expand=True, pady=(0, 10), padx=10)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.pages = {}
        for PageClass, name in [
            (DashboardPage, "Dashboard"),
            (ReposPage, "Repos"),
            (TestExecPage, "TestExec"),
            (SettingsPage, "Settings"),
        ]:
            page = PageClass(container, self)
            self.pages[name] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.current_page_name = "Dashboard"
        self.show_page("Dashboard")
        
    def back(self):
        # If current page is Settings, go directly back to Dashboard
        if self.current_page_name == "Settings":
            self.show_page("Dashboard")
            return
        # Define the order of pages for back navigation
        page_order = ["Dashboard", "Repos", "TestExec"]
        try:
            idx = page_order.index(self.current_page_name)
            prev_idx = max(0, idx - 1)
            prev_page = page_order[prev_idx]
            self.show_page(prev_page)
            # If navigating to Repos, focus the search entry
            if prev_page == "Repos":
                self.pages["Repos"].focus_search()
        except ValueError:
            self.show_page("Dashboard")

    def show_page(self, page_name):
        # Hide back button on Dashboard, show otherwise
        self.current_page_name = page_name  # Update current page name
        if page_name == "Dashboard":
            self.back_btn.pack_forget()
        else:
            self.back_btn.pack(anchor='nw', pady=10, padx=10)
        if page_name == "Repos":
            self.pages["Repos"].focus_search()
        page = self.pages[page_name]
        page.tkraise()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationUI(root)
    app.mainloop()
