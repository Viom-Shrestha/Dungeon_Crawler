#!/usr/bin/env python3
"""
Dungeon Crawler Launcher
Choose between text-based and GUI versions of the game
"""

import sys
import os

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_menu():
    """Display the main menu"""
    clear_screen()
    print("=" * 50)
    print("           DUNGEON CRAWLER LAUNCHER")
    print("=" * 50)
    print()
    print("Choose your game mode:")
    print()
    print("1. Text-based Version (Classic)")
    print("   - Terminal-based gameplay")
    print("   - Keyboard input only")
    print("   - No external dependencies")
    print()
    print("2. GUI Version (Modern)")
    print("   - Pygame-based graphics")
    print("   - Mouse and keyboard controls")
    print("   - Visual map and UI panels")
    print()
    print("3. Exit")
    print()
    print("=" * 50)

def check_pygame():
    """Check if Pygame is installed"""
    try:
        import pygame
        return True
    except ImportError:
        return False

def launch_text_version():
    """Launch the text-based version"""
    clear_screen()
    print("Launching Text-based Dungeon Crawler...")
    print("Loading...")
    
    try:
        from dungeon_crawler import main
        main()
    except ImportError as e:
        print(f"Error: Could not import dungeon_crawler module: {e}")
        print("Make sure dungeon_crawler.py is in the same directory.")
        input("Press Enter to continue...")
    except Exception as e:
        print(f"Error running text version: {e}")
        input("Press Enter to continue...")

def launch_gui_version():
    """Launch the GUI version"""
    if not check_pygame():
        clear_screen()
        print("Pygame is not installed!")
        print()
        print("To install Pygame, run:")
        print("pip install pygame")
        print()
        print("Or install from requirements.txt:")
        print("pip install -r requirements.txt")
        print()
        input("Press Enter to continue...")
        return
    
    clear_screen()
    print("Launching GUI Dungeon Crawler...")
    print("Loading Pygame...")
    
    try:
        from dungeon_crawler_gui import main
        main()
    except ImportError as e:
        print(f"Error: Could not import dungeon_crawler_gui module: {e}")
        print("Make sure dungeon_crawler_gui.py is in the same directory.")
        input("Press Enter to continue...")
    except Exception as e:
        print(f"Error running GUI version: {e}")
        input("Press Enter to continue...")

def main():
    """Main launcher function"""
    while True:
        show_menu()
        
        # Check Pygame availability
        pygame_available = check_pygame()
        if not pygame_available:
            print("⚠️  Pygame not installed - GUI version unavailable")
            print("   Install with: pip install pygame")
            print()
        
        try:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == "1":
                launch_text_version()
            elif choice == "2":
                if pygame_available:
                    launch_gui_version()
                else:
                    print("Please install Pygame first!")
                    input("Press Enter to continue...")
            elif choice == "3":
                clear_screen()
                print("Thanks for playing Dungeon Crawler!")
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            clear_screen()
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
