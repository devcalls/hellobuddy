import os


def display_welcome_screen(version: str):
    """
    Display HelloBuddy welcome banner.
    """

    os.system("cls" if os.name == "nt" else "clear")

    banner = r"""
  _    _ ______ _      _      ____  
 | |  | |  ____| |    | |    / __ \ 
 | |__| | |__  | |    | |   | |  | |
 |  __  |  __| | |    | |   | |  | |
 | |  | | |____| |____| |___| |__| |
 |_|  |_|______|______|______\____/ 
                                    
  ____  _    _ _____  _____ __     __
 |  _ \| |  | |  __ \|  __ \\ \   / /
 | |_) | |  | | |  | | |  | |\ \_/ / 
 |  _ <| |  | | |  | | |  | | \   /  
 | |_) | |__| | |__| | |__| |  | |   
 |____/ \____/|_____/|_____/   |_|   
    """

    print("-" * 60)

    print("-" * 50)  # Visual separator line
    MAROON = "\033[31m"
    CYAN = "\033[36m"
    RESET = "\033[0m"
    print(CYAN + banner)
    print(f"Welcome to HelloBuddy [Version {version}]" + RESET + "\n")
