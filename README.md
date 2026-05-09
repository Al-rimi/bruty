<p align="center">
  <img src="logo.png" alt="Bruty Logo" width="200">
</p>

# Bruty - Multi-Box Smart Password Brute Forcer

A Python automation tool designed to perform intelligent brute-force attacks on multi-input forms (e.g. PIN pads, password grids, etc.) using pyautogui.

> ## ⚠️ Legal Warning
>
> ### This tool is intended for ethical hacking and authorized security testing only.
> - You may only use Bruty on systems and applications **you own** or have **explicit written permission** to test.
> - Unauthorized use against any service, website, or system without permission is illegal and may violate computer misuse laws.
> - The author is **not responsible** for any misuse, damage, legal consequences, or violations caused by this tool.
>
> Use **responsibly** and **ethically**.

## Features

- **Multi-Box Support**: Fill and submit multiple input fields in a single cycle (ideal when server responses are slow)

- **Persistent Progress**: Automatically saves state so you can pause and resume brute-forcing without losing progress

- **Smart Position Correction**: Automatically retries nearby coordinates if typing fails in a box (toggleable)

- **Random Unused Password Generation**: Never repeats previously tried combinations

- **Highly Configurable**:
  - Adjustable delays between boxes, cycles, and individual actions
  - Custom password length
  - Character sets (digits only, + letters, + special characters)
  - Multiple submission methods (`enter`, `tab_enter`, `click_button`, `ctrl_enter`, `space`)

- **Real-time Progress & Efficiency Tracking**: 
  - Live progress percentage
  - Estimated time remaining
  - Success rate and failed attempts tracking
  - Average cycle time
  - Passwords per minute / per second speed

- **Comprehensive Logging**: All attempts are logged with timestamps in `attempts_log.txt`

- **Live Coordinate Tracker**: Built-in tool to help you easily capture accurate mouse positions

## Quick Start

1. Install required libraries:
```bash
pip install pyautogui keyboard pynput pyperclip
```
2. Run the script:
```bash
python bruty.py
```
3. Choose option `1` or leave blank to start brute force.

4. Follow the on-screen prompts to set up box positions and configuration.

5. Exit at any time by pressing `C`.

## Configuration Settings Explained

When you run the setup, you will configure the following options:

| Setting                      | Description                                                                 | Default Value     |
|-----------------------------|-----------------------------------------------------------------------------|-------------------|
| **Number of Boxes**         | How many input fields to fill per cycle                                     | User input        |
| **Delay Between Boxes**     | Seconds to wait after typing in one box before moving to the next           | 0                 |
| **Delay Between Cycles**    | Seconds to wait after completing one full cycle                            | 0                 |
| **Delay Between Actions**   | Seconds between keystrokes and clicks (lower = faster, higher = more stable)| 0.013             |
| **Position Adjustment**     | Automatically retry nearby positions if typing fails                       | Disabled          |
| **Submission Method**       | How the form is submitted after typing                                      | `enter`           |
| **Password Length**         | Length of each generated password                                           | 4                 |
| **Include Letters**         | Add A-Z and a-z to character set                                            | False             |
| **Include Special Chars**   | Add special characters (!@#$% etc.)                                        | False             |

**Submission Methods Available:**
- `enter` → Press Enter key (most common)
- `tab_enter` → Tab then Enter
- `click_button` → Click a specific submit button
- `ctrl_enter` → Ctrl + Enter
- `space` → Press Space key

---

## Files Created

- `.config` → Saves all your settings and box positions
- `brute_force_state.json` → Saves progress and used passwords
- `attempts_log.txt` → Logs every successful attempt with timestamp

---

## Menu Options

- `1` → Start brute force
- `2` → View current progress and configuration
- `3` → Reset all progress
- `4` → Live coordinate tracker (helpful for positioning)
- `5` → Change settings
- `6` → Exit

**Hotkey during attack:** Press `C` to stop safely and save progress.

---

## Usage Tips

- Use the **Live Coordinate Tracker** (option 4) to find accurate positions.
- Start with small delays and increase them if inputs are missing characters.
- Enable **Position Adjustment** if the target UI moves slightly.
- Always test on a non-critical environment first.

---

## License

This project uses a **Custom Ethical Use License**. See the `LICENSE` file for full details.

**By using Bruty, you agree to use it only for legal and ethical purposes.**

---

**Made with ❤️ for educational and authorized penetration testing.**